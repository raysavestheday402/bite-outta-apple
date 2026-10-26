"""
get_covers.py  (version 7 - posters, details, and Apple TV links)
Gets the best poster for every kids title in the Apple TV Library portal.

Where it looks, best first:
  1. TMDB (themoviedb.org)  - official posters for movies AND tall posters for TV shows
  2. fanart.tv              - high-quality posters, used when TMDB has none
  3. Wikipedia              - the poster on each title's exact Wikipedia page
  4. Apple TV               - the poster find_apple_links.py saw on the title's Apple TV page

TMDB and fanart.tv need a free personal API key. The script asks for them the first time
and saves them in keys.txt next to this script, so you only enter them once.
Without keys it still works, using Wikipedia and Apple TV only.

The titles come from cover_rows.json. Everything is saved to the Covers folder: tools/Covers, or the
folder you name with --covers "C:\\path\\to\\Covers" (remembered for next time).

Usage:
  python tools/get_covers.py              every title (replaces covers it finds again)
  python tools/get_covers.py --missing    only titles that don't have a cover yet (keeps hand-picked covers)
  python tools/get_covers.py 010a 151     only these ids
"""
import json, os, re, sys, time, csv, urllib.request, urllib.parse, urllib.error
from libtools import HERE, APPLE_LINKS, items, covers_dir, cover_files, load_json, say, pause

ARGS = sys.argv[1:]
OUT = covers_dir(ARGS[ARGS.index("--covers") + 1] if "--covers" in ARGS else None)
KEYS = os.path.join(HERE, "keys.txt")
os.makedirs(OUT, exist_ok=True)
UA = "AppleTVLibraryCovers/4.0 (personal, non-commercial) Python-urllib"
WIKI_BAD = ("novel", "book", "album", "soundtrack", "video game", "song", "franchise")

# ---------- keys ----------
def load_keys():
    keys = {}
    if os.path.exists(KEYS):
        for line in open(KEYS, encoding="utf-8"):
            if "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip().upper()] = v.strip()
    changed = False
    if "TMDB" not in keys:
        say("TMDB key (from themoviedb.org > Settings > API). Paste the 'API Key' or the long", "c")
        say("'API Read Access Token', then press Enter. Press Enter alone to skip TMDB:", "c")
        keys["TMDB"] = input("> ").strip(); changed = True
    if "FANART" not in keys:
        say("fanart.tv personal API key (from fanart.tv > your profile > API). Enter alone to skip:", "c")
        keys["FANART"] = input("> ").strip(); changed = True
    if changed:
        with open(KEYS, "w", encoding="utf-8") as f:
            f.write(f"TMDB={keys['TMDB']}\nFANART={keys['FANART']}\n")
        say("Saved keys to keys.txt (delete that file to enter new keys).\n", "d")
    return keys.get("TMDB", ""), keys.get("FANART", "")

# ---------- web ----------
def fetch(url, headers=None, tries=4):
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and "themoviedb" in url:
                raise PermissionError("TMDB key was rejected")
            if e.code == 404:
                return None
            if e.code in (429, 503) and i < tries - 1:
                wait = e.headers.get("Retry-After")
                wait = min(int(wait), 20) if (wait and wait.isdigit()) else 4 * (i + 1)
                say(f"   (busy - waiting {wait}s)", "d")
                time.sleep(wait)
            else:
                time.sleep(1.5)
        except PermissionError:
            raise
        except Exception:
            time.sleep(1.5)
    return None

def getjson(url, headers=None):
    raw = fetch(url, headers)
    try:
        return json.loads(raw.decode("utf-8")) if raw else None
    except Exception:
        return None

def norm(s):
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"^(the|a|an)\s+", "", s)
    return re.sub(r"[^a-z0-9]", "", s)

def safe(s):
    return re.sub(r'[\\/:*?"<>|]', "", s).strip()

# ---------- TMDB ----------
class TMDB:
    def __init__(self, key):
        self.key = key
        self.bearer = len(key) > 40
    def get(self, path, **params):
        params.setdefault("language", "en-US")
        if not self.bearer:
            params["api_key"] = self.key
        hdr = {"Authorization": f"Bearer {self.key}"} if self.bearer else {}
        js = getjson("https://api.themoviedb.org/3" + path + "?" + urllib.parse.urlencode(params), hdr)
        time.sleep(0.12)
        return js
    def find(self, kind, names, year):
        """Return (result, sure) for the best match, or (None, False)."""
        wanted = {norm(n) for n in names if n}
        best, best_score = None, -999
        for name in names:
            if kind == "tv":
                js = self.get("/search/tv", query=name, include_adult="false")
            else:
                js = self.get("/search/movie", query=name, include_adult="false")
            for r in (js or {}).get("results", [])[:10]:
                title = r.get("name") if kind == "tv" else r.get("title")
                orig = r.get("original_name") if kind == "tv" else r.get("original_title")
                date = r.get("first_air_date") if kind == "tv" else r.get("release_date")
                y = int(date[:4]) if date and date[:4].isdigit() else None
                s = 0
                if norm(title) in wanted or norm(orig) in wanted: s += 100
                elif any(w and (norm(title).startswith(w) or w.startswith(norm(title))) for w in wanted): s += 40
                else: continue
                if year and y:
                    d = abs(y - int(year))
                    s += 60 if d == 0 else (35 if d == 1 else -80)
                if not r.get("poster_path"): s -= 50
                s += min(r.get("popularity", 0), 50) / 10
                if s > best_score:
                    best, best_score = r, s
            if best_score >= 160:
                break
        if not best or best_score < 90:
            return None, False
        return best, (best_score >= 160 or (not year and best_score >= 100))
    def poster(self, r):
        p = r.get("poster_path")
        return f"https://image.tmdb.org/t/p/w780{p}" if p else None
    def tvdb_id(self, tmdb_id):
        js = self.get(f"/tv/{tmdb_id}/external_ids")
        return (js or {}).get("tvdb_id")

# ---------- fanart.tv ----------
def fanart_poster(key, kind, ident):
    if not key or not ident:
        return None
    url = f"https://webservice.fanart.tv/v3/{'tv' if kind == 'tv' else 'movies'}/{ident}?api_key={key}"
    js = getjson(url)
    time.sleep(0.2)
    if not js:
        return None
    arts = js.get("tvposter" if kind == "tv" else "movieposter") or []
    arts = sorted(arts, key=lambda a: (a.get("lang") not in ("en", "00", ""), -int(a.get("likes") or 0)))
    return arts[0]["url"] if arts else None

# ---------- Wikipedia (exact pages) ----------
QIDS = {}
def wiki_lookup(titles):
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        p = {"action": "query", "format": "json", "formatversion": 2, "redirects": 1,
             "prop": "pageimages|description|pageprops", "ppprop": "wikibase_item",
             "piprop": "original|thumbnail", "pithumbsize": 600,
             "pilicense": "any", "titles": "|".join(chunk)}
        js = getjson("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p))
        q = (js or {}).get("query", {})
        name = {t: t for t in chunk}
        for m in q.get("normalized", []) + q.get("redirects", []):
            for k, v in name.items():
                if v == m["from"]:
                    name[k] = m["to"]
        pages = {pg["title"]: pg for pg in q.get("pages", []) if not pg.get("missing")}
        for asked, final in name.items():
            pg = pages.get(final)
            if not pg:
                continue
            q = (pg.get("pageprops") or {}).get("wikibase_item")
            if q:
                QIDS[asked] = q
            if any(b in (pg.get("description") or "").lower() for b in WIKI_BAD):
                continue
            o, t = pg.get("original") or {}, pg.get("thumbnail") or {}
            src = o.get("source") if o.get("width", 9999) <= 1200 else t.get("source")
            src = src or t.get("source")
            if src and not src.lower().endswith(".svg"):
                out[asked] = src
        time.sleep(1)
    return out

# ---------- saving ----------
def clear(key):
    for f in os.listdir(OUT):
        if f.startswith(key + " - "):
            try: os.remove(os.path.join(OUT, f))
            except OSError: pass

def download(url):
    data = fetch(url, {"Accept": "image/*"})
    return data if data and len(data) > 1500 else None

def write(data, prefix, label):
    ext = ".png" if data[:4] == b"\x89PNG" else ".jpg"
    fn = f"{prefix} - {safe(label)}{ext}"
    with open(os.path.join(OUT, fn), "wb") as f:
        f.write(data)
    return fn

# ---------- Apple TV links (from Wikidata) ----------
def sparql(query):
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    req = urllib.request.Request("https://query.wikidata.org/sparql", data=data,
                                 headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8")).get("results", {}).get("bindings", [])
        except Exception:
            time.sleep(5)
    return []

UMC = 'FILTER(isLiteral(?v) && STRSTARTS(STR(?v), "umc.cmc."))'

def apple_links(entries):
    """entries: {n3: {"kind":..., "tmdb": id or None, "qid": Q or None}} -> {n3: {"kind":..., "id": umc...}}"""
    found = {}
    qids = sorted({e["qid"] for e in entries.values() if e.get("qid")})
    by_q = {}
    for i in range(0, len(qids), 80):
        vals = " ".join("wd:" + q for q in qids[i:i + 80])
        for b in sparql(f"SELECT ?item ?v WHERE {{ VALUES ?item {{ {vals} }} ?item ?p ?v . {UMC} }}"):
            by_q[b["item"]["value"].rsplit("/", 1)[-1]] = b["v"]["value"]
        time.sleep(1)
    by_tmdb = {}
    for kind, prop in (("movie", "P4947"), ("tv", "P4983")):
        ids = sorted({str(e["tmdb"]) for e in entries.values() if e.get("tmdb") and e["kind"] == kind})
        for i in range(0, len(ids), 80):
            vals = " ".join(f'"{x}"' for x in ids[i:i + 80])
            for b in sparql(f"SELECT ?tm ?v WHERE {{ VALUES ?tm {{ {vals} }} ?item wdt:{prop} ?tm . ?item ?p ?v . {UMC} }}"):
                by_tmdb[(kind, b["tm"]["value"])] = b["v"]["value"]
            time.sleep(1)
    for n3, e in entries.items():
        umc = by_tmdb.get((e["kind"], str(e.get("tmdb")))) or by_q.get(e.get("qid") or "")
        if umc:
            found[n3] = {"kind": e["kind"], "id": umc}
    return found

# ---------- details (year, rating, runtime, summary) ----------
META = {}
def details(tm, tid):
    if not tm or not tid:
        return {}
    kind, ident = tid
    try:
        if kind == "tv":
            js = tm.get(f"/tv/{ident}", append_to_response="content_ratings") or {}
            rating = next((x.get("rating") for x in (js.get("content_ratings") or {}).get("results", []) if x.get("iso_3166_1") == "US"), "")
            return dict(tmdb_id=ident, kind="tv", title=js.get("name"), year=(js.get("first_air_date") or "")[:4],
                        rating=rating, seasons=js.get("number_of_seasons"), genres=[g["name"] for g in js.get("genres", [])],
                        overview=js.get("overview", ""))
        js = tm.get(f"/movie/{ident}", append_to_response="release_dates") or {}
        rating = ""
        for c in (js.get("release_dates") or {}).get("results", []):
            if c.get("iso_3166_1") == "US":
                rating = next((d.get("certification") for d in c.get("release_dates", []) if d.get("certification")), "")
        return dict(tmdb_id=ident, kind="movie", title=js.get("title"), year=(js.get("release_date") or "")[:4],
                    rating=rating, runtime=js.get("runtime"), genres=[g["name"] for g in js.get("genres", [])],
                    overview=js.get("overview", ""))
    except PermissionError:
        raise
    except Exception:
        return {}

# ---------- main ----------
def find_one(tm, fkey, wiki, kind, names, year, wiki_titles, apple_art=None):
    """Try TMDB, then fanart.tv, then Wikipedia, then Apple TV. Returns (url, source, sure, found, tmdb id)."""
    if tm:
        r, sure = tm.find(kind, names, year)
        if r:
            title = r.get("name") if kind == "tv" else r.get("title")
            date = (r.get("first_air_date") if kind == "tv" else r.get("release_date")) or ""
            found = f"{title} ({date[:4]})"
            url = tm.poster(r)
            if url:
                return url, "TMDB", sure, found, (kind, r["id"])
            ident = tm.tvdb_id(r["id"]) if kind == "tv" else r["id"]
            url = fanart_poster(fkey, kind, ident)
            if url:
                return url, "fanart.tv", sure, found, (kind, r["id"])
    for t in wiki_titles:
        if t in wiki:
            return wiki[t], "Wikipedia", True, t, None
    if apple_art:
        return apple_art["art"], "Apple TV", True, apple_art.get("found") or names[0], None
    return None, None, False, "", None

def main():
    only = {a for a in ARGS if re.fullmatch(r"\d{3}[a-z]?", a)}
    have = cover_files(OUT)
    todo = [it for it in items() if (not only or it["key"] in only) and not ("--missing" in ARGS and it["key"] in have)]
    if not todo:
        say("Every title already has a cover.", "g")
        return
    tkey, fkey = load_keys()
    tm = TMDB(tkey) if tkey else None
    if tm:
        try:
            tm.get("/configuration")
        except PermissionError:
            say("TMDB didn't accept that key. Delete keys.txt and run again to re-enter it.", "r")
            tm = None
    say("Sources: " + ", ".join(s for s, on in (("TMDB", tm), ("fanart.tv", fkey), ("Wikipedia", True), ("Apple TV", True)) if on), "c")

    say("Looking up Wikipedia pages (backup source)...", "d")
    wiki = wiki_lookup(sorted({t for it in todo for t in it["wiki"]}))
    apple = load_json(APPLE_LINKS)
    say(f"Getting covers for {len(todo)} titles into: {OUT}\n", "c")

    log = []
    LINKS_IN = {}
    for it in todo:
        key, label = it["key"], it["title"] or it["label"]
        say(f"[{key}] {label}")
        try:
            art = apple.get(key) if (apple.get(key) or {}).get("art") else None
            url, src, sure, found, tid = find_one(tm, fkey, wiki, it["kind"], it["names"], it["year"], it["wiki"], art)
            data = download(url) if url else None
            if data:
                clear(key)
                fn = write(data, key, found if it["choice"] else it["label"])
                META[key] = details(tm, tid)
                LINKS_IN[key] = {"kind": it["kind"], "tmdb": tid[1] if tid else None,
                                 "qid": next((QIDS[t] for t in it["wiki"] if t in QIDS), None)}
                status = "CHOICE" if it["choice"] else ("OK" if sure else "CHECK")
                say(f"   {found}  [{src}]", "g" if sure else "y")
                log.append(dict(number=key, title=label, found=found, source=src, file=fn, status=status))
            else:
                old = have.get(key)
                say("   not found" + (" - keeping the one already there" if old else ""), "r")
                log.append(dict(number=key, title=label, found="", source="", file=old or "", status="NOT FOUND"))
        except PermissionError:
            say("TMDB stopped accepting the key - continuing without it.", "r")
            tm = None

    say("\nLooking up Apple TV links on Wikidata...", "c")
    links = apple_links(LINKS_IN)
    say(f"Wikidata had direct Apple TV links for {len(links)} of {len(LINKS_IN)} titles.", "c")
    # merge into what's already in the folder, so a --missing run keeps everything found before
    for name, new in (("apple-links.json", links), ("details.json", {k: v for k, v in META.items() if v})):
        path = os.path.join(OUT, name)
        merged = load_json(path)
        merged.update(new)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=1, ensure_ascii=False)
    with open(os.path.join(OUT, "covers-log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    with open(os.path.join(OUT, "covers-log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["number", "title", "found", "source", "file", "status"])
        w.writeheader(); w.writerows(log)
    ok = sum(x["status"] in ("OK", "CHOICE") for x in log)
    chk = sum(x["status"] == "CHECK" for x in log)
    bad = sum(x["status"] == "NOT FOUND" for x in log)
    say(f"\nDone. {ok} matched, {chk} to double-check, {bad} not found.", "c")
    if chk or bad:
        say("Open covers-log.csv in the Covers folder to see which ones.", "d")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nStopped. Run it again any time.", "y")
    if "--no-pause" not in ARGS:
        pause()
