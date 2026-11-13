#!/usr/bin/env python3
"""Package ClipForge for upload or install.

Usage:
  python tools/build.py              # writes dist/*.zip
  python tools/build.py --install    # also copies the skills to ~/.claude/skills

Builds four self-contained skills from the one source in this repo:

  clip-forge      works out the kind of video itself (and accepts the three
                  commands typed at the start of a message)
  clip-gameplay   fixed to gameplay mode
  clip-podcast    fixed to podcast mode
  clip-video      fixed to general-video mode

The three command skills are the main SKILL.md with a different name,
description and a "mode is fixed" note from commands/<name>.md. Each zip holds
one folder, <name>/SKILL.md plus scripts, assets and references, which is the
shape the Claude app expects for a skill upload.
"""
import argparse
import os
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SHARED = ("scripts", "assets", "references")
SKIP_DIRS = {"__pycache__"}
SKIP_EXT = (".pyc",)


def split_front_matter(text):
    """Return (front matter block including the --- lines, body)."""
    if not text.startswith("---"):
        sys.exit("SKILL.md has no front matter")
    end = text.index("\n---", 3)
    cut = text.index("\n", end + 1) + 1
    return text[:cut], text[cut:]


def skill_texts():
    with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as fh:
        main = fh.read()
    _, body = split_front_matter(main)
    out = {"clip-forge": main}
    cmd_dir = os.path.join(ROOT, "commands")
    for name in sorted(os.listdir(cmd_dir)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(cmd_dir, name), encoding="utf-8") as fh:
            front, note = split_front_matter(fh.read())
        out[name[:-3]] = front + "\n" + note.strip() + "\n" + body
    return out


def shared_files():
    for top in SHARED:
        for base, dirs, files in os.walk(os.path.join(ROOT, top)):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for f in sorted(files):
                if not f.endswith(SKIP_EXT):
                    full = os.path.join(base, f)
                    yield full, os.path.relpath(full, ROOT).replace(os.sep, "/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true",
                    help="copy the skills to ~/.claude/skills (Claude Code)")
    args = ap.parse_args()

    os.makedirs(DIST, exist_ok=True)
    files = list(shared_files())
    for name, text in skill_texts().items():
        path = os.path.join(DIST, f"{name}.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr(f"{name}/SKILL.md", text)
            for full, rel in files:
                z.write(full, f"{name}/{rel}")
        print(f"{path}  ({os.path.getsize(path) // 1024} KB)")

        if args.install:
            dest = os.path.join(os.path.expanduser("~"), ".claude", "skills", name)
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            os.makedirs(dest)
            with open(os.path.join(dest, "SKILL.md"), "w", encoding="utf-8",
                      newline="\n") as fh:
                fh.write(text)
            for full, rel in files:
                target = os.path.join(dest, rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(full, target)
            print(f"installed -> {dest}")


if __name__ == "__main__":
    main()
