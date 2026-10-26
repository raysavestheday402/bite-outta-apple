"""
update_library.py - the whole library update in one go. Double-click "Update Library.bat", or run:
  python tools/update_library.py                         uses the Covers folder from last time (or tools/Covers)
  python tools/update_library.py "C:\\path\\to\\Covers"   uses (and remembers) this Covers folder

It runs, in order:
  1. get_covers.py         covers, details and Wikidata's Apple TV ids, only for titles with no cover yet
  2. find_apple_links.py   searches Apple TV only for titles that still have no direct link after step 1
  3. build_data.py         rebuilds data.js and posters/
  4. check_data.py         checks everything before you push
Then commit and push with GitHub Desktop.
"""
import os, subprocess, sys
from libtools import HERE, covers_dir, say, pause


def run(script, *args):
    say(f"\n=== {script} ===", "c")
    return subprocess.call([sys.executable, os.path.join(HERE, script), *args]) == 0


def pillow():
    """build_data needs Pillow. Install it the first time instead of stopping with an error."""
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        say("Installing Pillow (needed once to make the posters)...", "c")
        return subprocess.call([sys.executable, "-m", "pip", "install", "-r", os.path.join(HERE, "requirements.txt")]) == 0


def main():
    folder = covers_dir(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None)
    os.makedirs(folder, exist_ok=True)
    say("Update Library - version 4 (looks up only new titles and search links)", "c")
    say(f"Covers folder: {folder}", "d")
    extra = ["--yes"] if "--yes" in sys.argv else []
    run("get_covers.py", "--covers", folder, "--missing", "--no-pause")
    run("find_apple_links.py", "--covers", folder, "--no-pause", *extra)
    if not pillow():
        say("Couldn't install Pillow. Open Command Prompt and run:  python -m pip install pillow  then run this again.", "r")
        return
    if not run("build_data.py", folder):
        say("build_data.py stopped with an error (see above). Nothing to push yet.", "r")
        return
    if run("check_data.py"):
        say("\nAll done. Open GitHub Desktop, look over the changes, then Commit and Push.", "g")
    else:
        say("\nThe checks above found problems. Fix those (or ask Claude) before pushing.", "y")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nStopped.", "y")
    pause()
