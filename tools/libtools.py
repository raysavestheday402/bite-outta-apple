"""Shared helpers for the library tools: the title list, the Covers folder, and title matching.
Not run on its own; get_covers.py, find_apple_links.py, build_data.py and update_library.py import it."""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..")
ROWS = os.path.join(HERE, "cover_rows.json")
APPLE_LINKS = os.path.join(HERE, "apple_links.json")      # committed: direct links found on Apple TV or pasted by hand
COVERS_SETTING = os.path.join(HERE, "covers_folder.txt")  # git-ignored: the Covers folder used last time
DEFAULT_COVERS = os.path.join(HERE, "Covers")


def load_rows(include_skipped=False):
    rows = json.load(open(ROWS, encoding="utf-8"))
    return rows if include_skipped else [r for r in rows if r.get("mode") != "skip"]


def items(rows=None):
    """One entry per title on the site. A row with "choices" (a collection or a group) becomes
    one title per choice, keyed 010a, 010b, ... Each entry is a dict with key, n, row, choice (or None),
    label, title (None means build_data names it), kind, term, year, names, wiki, apple, link, tags."""
    out = []
    for r in rows if rows is not None else load_rows():
        n3 = f"{r['n']:03d}"
        if "choices" in r:
            for i, ch in enumerate(r["choices"]):
                if ch.get("skip"):  # removed, but keeps its place so later letters (and saved favorites) don't shift
                    continue
                wiki = [r["wiki"][i]] if i < len(r.get("wiki", [])) else []
                out.append(dict(key=f"{n3}{chr(97 + i)}", n=r["n"], row=r, choice=ch, label=r["label"],
                                title=ch.get("title"), kind=ch["kind"], term=ch["term"], year=ch.get("year", ""),
                                names=[ch["term"]] + ch.get("alts", []), wiki=wiki, apple=ch.get("apple") or ch.get("title") or ch["term"], link=ch.get("link"),
                                tags=list(r.get("tags", [])) + [t for t in ch.get("tags", []) if t not in r.get("tags", [])]))
        else:
            out.append(dict(key=n3, n=r["n"], row=r, choice=None, label=r["label"], title=r.get("title"), kind=r["kind"],
                            term=r["term"], year=r.get("year", ""), names=[r["term"]] + r.get("alts", []),
                            wiki=r.get("wiki", []), apple=r.get("apple") or r["term"], link=r.get("link"), tags=list(r.get("tags", []))))
    return out


def site_library():
    """{id: entry} from the committed data.js: what the site has now (links, years, ratings, posters)."""
    try:
        src = open(os.path.join(SITE, "data.js"), encoding="utf-8").read()
        return {x["id"]: x for x in json.loads(src[src.index("["):src.rindex("]") + 1])}
    except (OSError, ValueError):
        return {}


def has_poster(key):
    return os.path.exists(os.path.join(SITE, "posters", f"{key}.jpg"))


def covers_dir(arg=None, remember=True):
    """The Covers folder: the path given, else the one used last time, else tools/Covers."""
    path = arg
    if not path and os.path.exists(COVERS_SETTING):
        path = open(COVERS_SETTING, encoding="utf-8").read().strip() or None
    path = os.path.abspath(path or DEFAULT_COVERS)
    if arg and remember:
        with open(COVERS_SETTING, "w", encoding="utf-8") as f:
            f.write(path + "\n")
    return path


def cover_files(folder):
    """{key: filename} for every cover in the folder ("010a - Halloweentown (1998).jpg" -> "010a")."""
    files = {}
    if os.path.isdir(folder):
        for f in sorted(os.listdir(folder)):
            m = re.match(r"(\d{3}[a-z]?) - (.+)\.(jpg|jpeg|png)$", f, re.I)
            if m:
                files.setdefault(m.group(1), f)
    return files


def load_json(path):
    try:
        return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    except ValueError as e:
        # never carry on with an empty list: that would quietly drop every link in it
        raise SystemExit(f"\n{path} is damaged ({e}).\n"
                         "If it has <<<<<<< or >>>>>>> lines, GitHub Desktop left a merge conflict in it. Ask Claude to fix it.")


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def norm(s):
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"^(the|a|an)\s+", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


if os.name == "nt":
    os.system("")  # turn on colors in the Windows console
def say(s, c=None):
    codes = {"g": "92", "y": "93", "r": "91", "c": "96", "d": "90"}
    print(f"\033[{codes[c]}m{s}\033[0m" if c else s, flush=True)


def pause():
    """Keep a double-clicked window open at the end."""
    if sys.stdin and sys.stdin.isatty():
        try:
            input("\nPress Enter to close this window...")
        except EOFError:
            pass
