#!/usr/bin/env python3
"""Publish a local Codex skill into a GitHub skills catalog repo."""

from __future__ import annotations

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path


IGNORED_NAMES = {
    ".DS_Store",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
}
IGNORED_PATTERNS = ("*.pyc", "*.pyo", "*.bak-*", "*~")
TEXT_SUFFIXES = {
    "",
    ".bash",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
LOCAL_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home|Volumes)/[^\s'\"`)]+")


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=False, check=check)


def capture(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)
    return result.stdout


def looks_like_skills_repo(path: Path) -> bool:
    return (path / "skills").is_dir() and (path / "README.md").exists()


def default_repo_root() -> Path:
    env_root = os.environ.get("SKILLS_REPO_ROOT")
    if env_root:
        return Path(env_root).expanduser()
    cwd = Path.cwd()
    if looks_like_skills_repo(cwd):
        return cwd
    home_default = Path.home() / "Documents/git-repo/skills"
    return home_default


def should_ignore(dir_name: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORED_NAMES:
            ignored.add(name)
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in IGNORED_PATTERNS):
            ignored.add(name)
    return ignored


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def read_text_lossy(path: Path) -> str | None:
    if not is_text_candidate(path):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise SystemExit(f"Missing YAML frontmatter: {skill_md}")
    fields: dict[str, str] = {}
    current_key: str | None = None
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        if raw_line.startswith((" ", "\t")) and current_key:
            fields[current_key] += " " + raw_line.strip()
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        current_key = key.strip()
        fields[current_key] = value.strip().strip('"').strip("'")
    return fields


def description_summary(description: str) -> str:
    first = re.split(r"(?<=[.!?])\s+", description.strip(), maxsplit=1)[0]
    return first if first.endswith((".", "!", "?")) else first + "."


def ensure_clean_target(repo_root: Path, rel_target: Path, force: bool) -> None:
    if not (repo_root / ".git").exists():
        return
    status = capture(["git", "status", "--short", "--", str(rel_target)], cwd=repo_root)
    if status.strip() and not force:
        raise SystemExit(
            f"Target path has uncommitted changes. Commit/stash them or pass --force:\n{status}"
        )


def copy_skill(source: Path, target: Path) -> None:
    preserved_readme: str | None = None
    target_readme = target / "README.md"
    source_readme = source / "README.md"
    if target_readme.exists() and not source_readme.exists():
        preserved_readme = target_readme.read_text(encoding="utf-8")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=should_ignore)
    if preserved_readme is not None and not (target / "README.md").exists():
        (target / "README.md").write_text(preserved_readme, encoding="utf-8")


def rewrite_skill_name(target: Path, dest_name: str) -> None:
    skill_md = target / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    replaced = re.sub(r"(?m)^name:\s*.*$", f"name: {dest_name}", text, count=1)
    if replaced == text:
        raise SystemExit(f"Could not rewrite skill name in {skill_md}")
    skill_md.write_text(replaced, encoding="utf-8")


def scan_local_paths(target: Path) -> list[str]:
    warnings: list[str] = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        text = read_text_lossy(path)
        if text is None:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in LOCAL_PATH_RE.finditer(line):
                warnings.append(f"{path}:{line_no}: {match.group(0)}")
    return warnings


def validate_skill(target: Path) -> None:
    skill_md = target / "SKILL.md"
    if not skill_md.exists():
        raise SystemExit(f"Copied skill is missing SKILL.md: {target}")
    fields = parse_frontmatter(skill_md)
    if fields.get("name") != target.name:
        raise SystemExit(f"SKILL.md name must be {target.name!r}, got {fields.get('name')!r}")
    if not fields.get("description"):
        raise SystemExit("SKILL.md description is required")

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    quick_validate = codex_home / "skills/.system/skill-creator/scripts/quick_validate.py"
    if quick_validate.exists():
        run(["python3", str(quick_validate), str(target)])


def syntax_check(target: Path) -> None:
    python_files = [path for path in sorted(target.rglob("*.py")) if "__pycache__" not in path.parts]
    for path in python_files:
        run(["python3", "-m", "py_compile", str(path)])
    for path in sorted(target.rglob("*.sh")):
        run(["bash", "-n", str(path)])


def remove_generated_files(target: Path) -> None:
    for path in sorted(target.rglob("__pycache__")):
        if path.is_dir():
            shutil.rmtree(path)
    for pattern in ("*.pyc", "*.pyo"):
        for path in sorted(target.rglob(pattern)):
            path.unlink()


def skill_dirs(repo_root: Path) -> list[Path]:
    skills_root = repo_root / "skills"
    if not skills_root.exists():
        return []
    return sorted(path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").exists())


def render_catalog(repo_root: Path, repo_slug: str) -> str:
    sections: list[str] = [
        "## Skills",
        "",
        "Each skill folder has its own README with install and usage details.",
        "",
        "| Skill | Summary |",
        "| --- | --- |",
    ]
    for skill_dir in skill_dirs(repo_root):
        fields = parse_frontmatter(skill_dir / "SKILL.md")
        description = description_summary(fields.get("description", "No description provided."))
        sections.append(f"| [`{skill_dir.name}`](skills/{skill_dir.name}/) | {description} |")
    return "\n".join(sections).rstrip() + "\n"


def update_readme(repo_root: Path, repo_slug: str) -> None:
    readme = repo_root / "README.md"
    if readme.exists():
        original = readme.read_text(encoding="utf-8")
        prefix = original.split("\n## Skills\n", 1)[0].rstrip()
    else:
        prefix = "# Skills\n\nPersonal agent skills that can be installed selectively into Codex."
    body = prefix + "\n\n" + render_catalog(repo_root, repo_slug)
    readme.write_text(body, encoding="utf-8")


def render_skill_readme(skill_dir: Path, repo_slug: str) -> str:
    fields = parse_frontmatter(skill_dir / "SKILL.md")
    description = fields.get("description", "No description provided.")
    lines = [
        f"# {skill_dir.name}",
        "",
        description_summary(description),
        "",
        "## Install",
        "",
        "```bash",
        "python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \\",
        f"  --repo {repo_slug} \\",
        f"  --path skills/{skill_dir.name}",
        "```",
        "",
        "Restart Codex after installing so the skill appears in new sessions.",
        "",
        "## Details",
        "",
        "Agent-facing workflow and implementation details live in [`SKILL.md`](SKILL.md).",
    ]
    scripts_dir = skill_dir / "scripts"
    scripts = sorted(path.name for path in scripts_dir.glob("*") if path.is_file()) if scripts_dir.exists() else []
    if scripts:
        lines.extend(["", "## Scripts", ""])
        for script in scripts:
            lines.append(f"- `scripts/{script}`")
    return "\n".join(lines).rstrip() + "\n"


def ensure_skill_readme(skill_dir: Path, repo_slug: str) -> None:
    readme = skill_dir / "README.md"
    if not readme.exists():
        readme.write_text(render_skill_readme(skill_dir, repo_slug), encoding="utf-8")


def git_commit_push(repo_root: Path, skill_name: str, commit: bool, push: bool) -> None:
    if not commit and not push:
        return
    if not (repo_root / ".git").exists():
        raise SystemExit("--commit/--push require a git repo")
    run(["git", "add", "README.md", f"skills/{skill_name}"], cwd=repo_root)
    status = capture(["git", "status", "--short"], cwd=repo_root)
    if not status.strip():
        print("No git changes to commit.")
    elif commit:
        run(["git", "commit", "-m", f"Add {skill_name} skill"], cwd=repo_root)
    if push:
        run(["git", "push"], cwd=repo_root)


def infer_skill_name_from_cwd() -> str | None:
    cwd = Path.cwd()
    if (cwd / "SKILL.md").exists():
        return cwd.name
    for parent in cwd.parents:
        if (parent / "SKILL.md").exists():
            return parent.name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_name", nargs="?", help="Installed Codex skill folder name")
    parser.add_argument("--dest-name", help="Destination skill folder name in the repo")
    parser.add_argument(
        "--source-root",
        default=str(Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser() / "skills"),
        help="Installed Codex skills root",
    )
    parser.add_argument("--repo-root", default=str(default_repo_root()), help="Skills catalog repo root")
    parser.add_argument("--repo", default=os.environ.get("SKILLS_GITHUB_REPO", "sanghunka/skills"))
    parser.add_argument("--force", action="store_true", help="Replace target even if git reports local changes")
    parser.add_argument("--skip-readme", action="store_true", help="Do not regenerate README.md")
    parser.add_argument("--skip-skill-readme", action="store_true", help="Do not create README.md in the skill folder")
    parser.add_argument(
        "--strict-portability",
        action="store_true",
        help="Fail if copied files contain likely personal absolute paths",
    )
    parser.add_argument("--commit", action="store_true", help="Commit the published skill")
    parser.add_argument("--push", action="store_true", help="Push after committing")
    args = parser.parse_args()

    skill_name = args.skill_name or infer_skill_name_from_cwd()
    if not skill_name:
        raise SystemExit("Skill name is required unless running inside a skill folder.")
    dest_name = args.dest_name or skill_name
    source_root = Path(args.source_root).expanduser().resolve()
    repo_root = Path(args.repo_root).expanduser().resolve()
    source = source_root / skill_name
    target = repo_root / "skills" / dest_name

    if not source.exists():
        raise SystemExit(f"Source skill does not exist: {source}")
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Source is not a Codex skill folder: {source}")
    if not looks_like_skills_repo(repo_root):
        raise SystemExit(f"Repo root does not look like a skills repo: {repo_root}")

    rel_target = Path("skills") / dest_name
    ensure_clean_target(repo_root, rel_target, args.force)
    copy_skill(source, target)
    if dest_name != skill_name:
        rewrite_skill_name(target, dest_name)
    validate_skill(target)
    syntax_check(target)
    remove_generated_files(target)

    warnings = scan_local_paths(target)
    if warnings:
        print("\nPortability warnings:")
        for warning in warnings:
            print(f"  {warning}")
        if args.strict_portability:
            raise SystemExit("Strict portability failed.")

    if not args.skip_skill_readme:
        ensure_skill_readme(target, args.repo)

    if not args.skip_readme:
        update_readme(repo_root, args.repo)

    git_commit_push(repo_root, dest_name, args.commit, args.push)
    print(f"\nPublished {skill_name} -> {target}")
    print(f"Repo: {repo_root}")
    if not args.commit:
        print("Review changes, then commit and push when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
