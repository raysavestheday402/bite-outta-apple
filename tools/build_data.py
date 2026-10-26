"""Rebuilds data.js and posters/ from the title list, a Covers folder made by get_covers.py, and what the site has now.
Usage: python tools/build_data.py ["path\\to\\Covers"]   (needs Pillow: pip install -r tools/requirements.txt)
With no path it uses the Covers folder used last time, or tools/Covers.

For each title, best first:
  cover:  the Covers folder, then the poster already in posters/ (a split collection can borrow the box-set cover)
  link:   a "link" in cover_rows.json, then tools/apple_links.json, then the Covers folder's apple-links.json, then the direct link already in data.js
  year/rating: the Covers folder's details.json, then what data.js already has
So the Covers folder only needs the new titles; nothing on the site is lost if it's empty.
A title with no cover anywhere is left off the site until it has one."""
import json, os, re, sys, shutil, tempfile
from PIL import Image, PngImagePlugin
from libtools import SITE, APPLE_LINKS, load_rows, items, site_library, covers_dir, cover_files, load_json
PngImagePlugin.MAX_TEXT_CHUNK = 100 * 1024 * 1024

COVERS = covers_dir(sys.argv[1] if len(sys.argv) > 1 else None)
POST = os.path.join(SITE, "posters")
if not os.path.isdir(COVERS):  # check before wiping posters/
    sys.exit(f"Covers folder not found: {COVERS}")
rows = load_rows()
details = load_json(os.path.join(COVERS, "details.json"))
links = load_json(os.path.join(COVERS, "apple-links.json"))
links.update(load_json(APPLE_LINKS))
OLD = site_library()
KEEP = tempfile.mkdtemp()  # the current posters, so titles without a file in Covers keep theirs
if os.path.isdir(POST):
    shutil.copytree(POST, KEEP, dirs_exist_ok=True)
shutil.rmtree(POST, ignore_errors=True); os.makedirs(POST)


YEARS = {r["n"]: r["year"] for r in rows if r["year"]}

DISPLAY = {
 "Aladdin (1992)": "Aladdin", "Anastasia (1997)": "Anastasia", "Charlotte's Web (1973)": "Charlotte's Web",
 "Cinderella (1950)": "Cinderella", "Elf (2003)": "Elf", "Freaky Friday (2003)": "Freaky Friday", "Tarzan (1999)": "Tarzan",
 "Dr. Seuss' How the Grinch Stole Christmas (2000)": "How the Grinch Stole Christmas",
 "How the Grinch Stole Christmas (animated)": "How the Grinch Stole Christmas!",
 "Illumination Presents: Dr. Seuss' The Grinch": "The Grinch", "The Little Mermaid (animated)": "The Little Mermaid",
 "The Little Mermaid (live action)": "The Little Mermaid", "PAW Patrol movie": "PAW Patrol: The Dino Movie",
 "Spy Kids 3: Game Over": "Spy Kids 3-D: Game Over", "Willy Wonka and the Chocolate Factory": "Willy Wonka & the Chocolate Factory",
 "E.T. The Extra-Terrestrial": "E.T. the Extra-Terrestrial",
 "A Scooby-Doo Valentine": "A Scooby-Doo! Valentine Bouquet",
}
NO_YEAR = {"The Land of Sometimes", "A Scooby-Doo Valentine"}
DISNEY = set("""Aladdin (1992)|Atlantis: The Lost Empire|Beauty and the Beast|Big Hero 6|A Bug's Life|Cars|Cars 2|Cars 3|Cinderella (1950)|Elio|The Emperor's New Groove|Encanto|An Extremely Goofy Movie|Finding Dory|Finding Nemo|Freaky Friday (2003)|Frozen|George of the Jungle|Herbie: Fully Loaded|Hercules|Hocus Pocus|Holes|Home on the Range|Hoppers|Inspector Gadget|Kronk's New Groove|Lady and the Tramp|Lilo & Stitch|Lilo & Stitch 2: Stitch Has a Glitch|The Lion King|The Little Mermaid (animated)|The Little Mermaid (live action)|Mary Poppins|Mary Poppins Returns|Pinocchio|Pocahontas|The Princess Diaries|The Santa Clause|The Santa Clause 2|The Santa Clause 3: The Escape Clause|Tarzan (1999)|Toy Story|Toy Story 2|Toy Story 3|Toy Story 4|Toy Story 5|Zootopia 2|Halloweentown: 4-Movie Collection""".split("|"))
HOLIDAY = set("""Dr. Seuss' How the Grinch Stole Christmas (2000)|How the Grinch Stole Christmas (animated)|Illumination Presents: Dr. Seuss' The Grinch|Elf (2003)|Rudolph the Red-Nosed Reindeer|The Santa Clause|The Santa Clause 2|The Santa Clause 3: The Escape Clause|Hocus Pocus|Halloweentown: 4-Movie Collection|Casper|Scooby-Doo and the Witch's Ghost|Scooby-Doo! Frankencreepy|A Scooby-Doo Valentine""".split("|"))

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-") or "title"

def save_poster(src, out):
    im = Image.open(src).convert("RGB")
    if im.width > 600:
        im = im.resize((600, round(im.height * 600 / im.width)), Image.LANCZOS)
    im.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    return im.size

files = cover_files(COVERS)

lib = []; report = []; waiting = []
for it in items(rows):
    key, label = it["key"], it["label"]
    title = it["title"] or DISPLAY.get(label, label)
    if it["choice"] and not it["title"] and key in files:  # older choice rows are named from the cover file
        title = re.sub(r"^Steven Spielberg Presents\s+", "", files[key].split(" - ", 1)[1].rsplit(".", 1)[0])
        title = re.sub(r"\s*\(\d{4}\)$", "", title)
    d = details.get(key, {}) or {}
    old = OLD.get(key) or {}
    box = (OLD.get(key[:3]) or {}) if it["choice"] else {}  # a split collection starts from the box set's entry
    year = d.get("year") or old.get("year") or ("" if label in NO_YEAR else str((it["choice"] or {}).get("year") or YEARS.get(it["n"], "")))
    rating = d.get("rating") or old.get("rating") or box.get("rating", "")
    kept = os.path.join(KEEP, f"{key}.jpg")
    if key in files:
        save_poster(os.path.join(COVERS, files[key]), os.path.join(POST, f"{key}.jpg"))
    elif os.path.exists(kept):
        shutil.copyfile(kept, os.path.join(POST, f"{key}.jpg"))
    elif it["choice"] and (key[:3] in files or os.path.exists(os.path.join(KEEP, f"{key[:3]}.jpg"))):
        if key[:3] in files:
            save_poster(os.path.join(COVERS, files[key[:3]]), os.path.join(POST, f"{key}.jpg"))
        else:
            shutil.copyfile(os.path.join(KEEP, f"{key[:3]}.jpg"), os.path.join(POST, f"{key}.jpg"))
        report.append(f"{key} {title}: using the {key[:3]} cover until it has its own")
    else:
        waiting.append(f"{key} {title}")
        continue
    poster = f"posters/{key}.jpg"
    lk = links.get(key)
    if it["link"]:  # a link pasted into cover_rows.json wins over everything
        link, lk = it["link"], {"url": it["link"]}
    elif lk and lk.get("url"):
        link = lk["url"]
    elif lk:
        link = f"https://tv.apple.com/us/{'show' if lk['kind'] == 'tv' else 'movie'}/{slug(title)}/{lk['id']}"
    elif old.get("direct"):
        link = old["link"]
    else:
        link = "https://tv.apple.com/us/search?term=" + re.sub(r"\s+", "%20", re.sub(r"[^\w\s'&!:.-]", "", title))
    tags = []
    if label in DISNEY or "disney" in it["tags"]: tags.append("disney")
    if label in HOLIDAY or "holiday" in it["tags"]: tags.append("holiday")
    tags += [t for t in it["tags"] if t not in tags]
    lib.append(dict(id=key, title=title, kind=it["kind"], year=str(year or ""), rating=rating,
                    poster=poster, link=link, direct=bool(lk) or bool(old.get("direct") and link == old.get("link")), tags=tags))

with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
    f.write("/* raysavestheday library data - generated, do not edit by hand */\n")
    f.write("window.LIBRARY = " + json.dumps(lib, ensure_ascii=False, indent=0) + ";\n")
print(len(lib), "titles |", sum(1 for x in lib if x["kind"] == "movie"), "movies,", sum(1 for x in lib if x["kind"] == "tv"), "shows |",
      sum(x["direct"] for x in lib), "direct links")
shutil.rmtree(KEEP, ignore_errors=True)
print("\n".join(report))
if waiting:
    print(f"{len(waiting)} titles are left off until they have a cover (run get_covers.py --missing):")
    print("  " + "\n  ".join(waiting))
