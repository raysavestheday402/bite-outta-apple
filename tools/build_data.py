"""Rebuilds data.js and posters/ from a Covers folder made by get_covers.py.
Usage: python tools/build_data.py ["path\\to\\Covers"]   (needs Pillow: pip install -r tools/requirements.txt)
With no path it uses tools/Covers, which is where get_covers.py saves everything."""
import json, os, re, sys, shutil
from PIL import Image, PngImagePlugin
PngImagePlugin.MAX_TEXT_CHUNK = 100 * 1024 * 1024

HERE = os.path.dirname(os.path.abspath(__file__))
COVERS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "Covers")  # where get_covers.py saves them
SITE = os.path.join(HERE, "..")
POST = os.path.join(SITE, "posters")
if not os.path.isdir(COVERS):  # check before wiping posters/
    sys.exit(f"Covers folder not found: {COVERS}")
shutil.rmtree(POST, ignore_errors=True); os.makedirs(POST)

rows = json.load(open(os.path.join(HERE, "cover_rows.json"), encoding="utf-8"))
def jload(name):
    p = os.path.join(COVERS, name)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
details, links = jload("details.json"), jload("apple-links.json")

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

files = {}
for f in os.listdir(COVERS):
    m = re.match(r"(\d{3}[a-z]?) - (.+)\.(jpg|png)$", f, re.I)
    if m: files[m.group(1)] = (f, m.group(2))

lib = []; report = []
for r in rows:
    n3 = f"{r['n']:03d}"
    keys = sorted(k for k in files if k[:3] == n3) or [n3]
    if r["label"].startswith("Steven Spielberg Presents"):
        if r["mode"] == "skip": continue
    for key in keys:
        label = r["label"]; kind = "tv" if r["kind"] == "tv" or r["n"] <= 17 else "movie"
        if label.startswith("Halloweentown"): kind = "movie"
        title = DISPLAY.get(label, label)
        if len(key) == 4:  # a/b/c/d choices -> separate shows named from the file
            title = re.sub(r"^Steven Spielberg Presents\s+", "", files[key][1])
            title = re.sub(r"\s*\(\d{4}\)$", "", title)
        d = details.get(key, {}) or {}
        year = d.get("year") or ("" if label in NO_YEAR else YEARS.get(r["n"], ""))
        poster = None
        if key in files:
            size = save_poster(os.path.join(COVERS, files[key][0]), os.path.join(POST, f"{key}.jpg"))
            poster = f"posters/{key}.jpg"
        else:
            report.append(f"{key} {title}: NO COVER")
        lk = links.get(key)
        if lk:
            link = f"https://tv.apple.com/us/{'show' if lk['kind'] == 'tv' else 'movie'}/{slug(title)}/{lk['id']}"
        else:
            link = "https://tv.apple.com/us/search?term=" + re.sub(r"\s+", "%20", re.sub(r"[^\w\s'&!:.-]", "", title))
        tags = []
        if label in DISNEY: tags.append("disney")
        if label in HOLIDAY: tags.append("holiday")
        lib.append(dict(id=key, title=title, kind=kind, year=str(year or ""), rating=d.get("rating", ""),
                        poster=poster, link=link, direct=bool(lk), tags=tags))

with open(os.path.join(SITE, "data.js"), "w", encoding="utf-8") as f:
    f.write("/* raysavestheday library data - generated, do not edit by hand */\n")
    f.write("window.LIBRARY = " + json.dumps(lib, ensure_ascii=False, indent=0) + ";\n")
print(len(lib), "titles |", sum(1 for x in lib if x["kind"] == "movie"), "movies,", sum(1 for x in lib if x["kind"] == "tv"), "shows |",
      sum(x["direct"] for x in lib), "direct links |", sum(1 for x in lib if not x["poster"]), "without poster")
print("\n".join(report))
