"""Sanity checks for data.js and posters/ before pushing. No downloads, no extra packages.
Usage: python tools/check_data.py"""
import json, os, re, sys
from libtools import items

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..")
# ratings are not checked or shown (Ray, Oct 2026): the library is whatever he owns
BANNED_WORDS = ("lilly",)  # never show the kid's name on the site

src = open(os.path.join(SITE, "data.js"), encoding="utf-8").read()
lib = json.loads(src[src.index("["):src.rindex("]") + 1])
problems = []
ids = [x["id"] for x in lib]
for dup in sorted({i for i in ids if ids.count(i) > 1}):
    problems.append(f"duplicate id {dup}")
for x in lib:
    who = f'{x["id"]} {x["title"]}'
    if x["kind"] not in ("movie", "tv"):
        problems.append(f"{who}: kind is {x['kind']!r}")
    if not x.get("poster"):
        problems.append(f"{who}: no poster")
    elif not os.path.exists(os.path.join(SITE, x["poster"])):
        problems.append(f"{who}: missing file {x['poster']}")
    if not x.get("thumb"):
        problems.append(f"{who}: no thumbnail (run tools/build_data.py)")
    elif not os.path.exists(os.path.join(SITE, x["thumb"])):
        problems.append(f"{who}: missing file {x['thumb']}")
    if not re.match(r"^https://tv\.apple\.com/", x["link"]):
        problems.append(f"{who}: link isn't an Apple TV link")
used = {os.path.basename(x["poster"]) for x in lib if x.get("poster")}
for f in sorted(set(os.listdir(os.path.join(SITE, "posters"))) - used):
    problems.append(f"posters/{f} isn't used by any title")
used_thumbs = {os.path.basename(x["thumb"]) for x in lib if x.get("thumb")}
thumbs_dir = os.path.join(SITE, "thumbs")
for f in sorted(set(os.listdir(thumbs_dir) if os.path.isdir(thumbs_dir) else []) - used_thumbs):
    problems.append(f"thumbs/{f} isn't used by any title")
# every text file Netlify serves from the repo root, not just the app
served = ["icons/manifest.webmanifest"] + [f for f in os.listdir(SITE) if f.lower().endswith((".html", ".js", ".md", ".json", ".txt"))]
for name in served:
    text = open(os.path.join(SITE, name), encoding="utf-8").read().lower()
    for w in BANNED_WORDS:
        if w in text:
            problems.append(f"{name} mentions {w!r}")
for name in ("apple_links.json", "cover_rows.json"):
    try:
        json.load(open(os.path.join(HERE, name), encoding="utf-8"))
    except ValueError:
        problems.append(f"tools/{name} is damaged (a leftover merge conflict?)")
seen = {}
for x in lib:  # two titles opening the same Apple TV page usually means one link is wrong
    if x["direct"]:
        tv_id = x["link"].split("?")[0].rstrip("/").rsplit("/", 1)[-1]
        if tv_id in seen:
            problems.append(f"{x['id']} {x['title']}: same Apple TV link as {seen[tv_id]}")
        seen[tv_id] = f"{x['id']} {x['title']}"

movies = sum(x["kind"] == "movie" for x in lib)
plus = sum("plus" in x.get("tags", []) for x in lib)
print(f"{len(lib)} titles | {movies} movies, {len(lib) - movies} shows | {plus} Apple TV+ | {sum(x['direct'] for x in lib)} direct links")
pending = [it["key"] for it in items() if it["key"] not in set(ids)]
if pending:
    print(f"{len(pending)} titles in cover_rows.json aren't on the site yet (run tools/update_library.py): {' '.join(pending)}")
search = [f'{x["id"]} {x["title"]}' for x in lib if not x["direct"]]
if search:
    print(f"{len(search)} still open an Apple TV search instead of the title (run tools/find_apple_links.py):")
    print("  " + "\n  ".join(search))
print("\n".join(problems) if problems else "All good.")
sys.exit(1 if problems else 0)
