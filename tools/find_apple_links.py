"""
find_apple_links.py - finds the direct Apple TV page for titles that need one.

It only looks up titles that need it: new titles that aren't on the site yet (like the Apple TV+ ones)
and titles that still open an Apple TV search. Titles that already open directly are left alone.

How it looks, best first:
  1. Apple TV's own search (the same one tv.apple.com uses). Works for purchases and Apple TV+ originals.
  2. The tv.apple.com search page itself.
  3. The iTunes Store search (purchases only), following the store link to its Apple TV page.

A match is used straight away when the title, year and movie/show all agree. When it isn't sure,
it shows what it found and asks you to pick (just press Enter to skip that one).
Results go in tools/apple_links.json, which is committed, so each title only has to be found once.

Usage (from the repo folder):
  python tools/find_apple_links.py                 look up new titles and titles that open a search
  python tools/find_apple_links.py 105 010a        look up just these ids (use this for a link you know is broken)
  python tools/find_apple_links.py --yes           don't ask; skip anything it isn't sure about
  python tools/find_apple_links.py --set 105 https://tv.apple.com/us/movie/the-pout-pout-fish/umc.cmc.xxxx
                                                    use a link you copied yourself (Apple TV app: Share > Copy Link)
  python tools/find_apple_links.py --covers "C:\\path\\to\\Covers"   which Covers folder to check for links found earlier
"""
import json, os, re, sys, time, urllib.request, urllib.parse, urllib.error
from libtools import (APPLE_LINKS, items, site_library, covers_dir, load_json, save_json, norm, say, pause)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
UMC = re.compile(r"umc\.cmc\.[a-z0-9]+")
PAGE = re.compile(r"(?:https://tv\.apple\.com)?/us/(movie|show)/([a-z0-9%-]+)/(umc\.cmc\.[a-z0-9]+)")
# The public settings tv.apple.com's web page sends with its own searches.
UTS = {"caller": "web", "locale": "en-US", "pfm": "web", "sf": "143441", "v": "90",
       "utscf": "OjAAAAAAAAA~", "utsk": "6e3013c6d6fae3c2::::::235656c069bb0efb"}


# ---------- web ----------
def fetch(url, accept="application/json", tries=2):
    """Returns (final_url, text) or (None, None)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept, "Accept-Language": "en-US"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.geturl(), r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                return None, None
            time.sleep(3 * (i + 1))
        except Exception:
            time.sleep(2 * (i + 1))
    return None, None


def year_of(v):
    if isinstance(v, (int, float)) and v > 10 ** 10:  # milliseconds since 1970
        return time.gmtime(v / 1000).tm_year
    m = re.match(r"(\d{4})", str(v or ""))
    return int(m.group(1)) if m else None


# ---------- 1. Apple TV search ----------
def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def art_url(images):
    """A tall poster from an Apple TV result, if it has one."""
    for name, im in (images or {}).items():
        if isinstance(im, dict) and im.get("url") and im.get("width") and im.get("height") and im["height"] > im["width"]:
            w = min(int(im["width"]), 1000); h = round(w * im["height"] / im["width"])
            return im["url"].replace("{w}", str(w)).replace("{h}", str(h)).replace("{c}", "").replace("{f}", "jpg")
    return None


UTS_STATS = {"asked": 0, "answered": 0}

def search_uts(term):
    q = dict(UTS, searchTerm=term)
    _, text = fetch("https://uts-api.itunes.apple.com/uts/v3/search?" + urllib.parse.urlencode(q))
    UTS_STATS["asked"] += 1
    UTS_STATS["answered"] += bool(text)
    try:
        js = json.loads(text) if text else None
    except ValueError:
        js = None
    out, seen = [], set()
    for d in walk(js):
        kind = {"movie": "movie", "show": "tv"}.get(str(d.get("type", "")).lower())
        ident = d.get("id")
        if not kind or not isinstance(ident, str) or not UMC.fullmatch(ident) or ident in seen or not d.get("title"):
            continue
        seen.add(ident)
        url = d.get("url") if str(d.get("url", "")).startswith("https://tv.apple.com/") else None
        out.append(dict(title=d["title"], kind=kind, id=ident, url=url,
                        year=year_of(d.get("releaseDate") or d.get("releaseYear")), art=art_url(d.get("images"))))
    return out


# ---------- 2. tv.apple.com search page ----------
def search_page(term):
    _, text = fetch("https://tv.apple.com/us/search?term=" + urllib.parse.quote(term), accept="text/html")
    out, seen = [], set()
    for kind, slug, ident in PAGE.findall(text or ""):
        if ident not in seen:
            seen.add(ident)
            out.append(dict(title=urllib.parse.unquote(slug).replace("-", " "), kind="tv" if kind == "show" else "movie",
                            id=ident, url=None, year=None, art=None, from_slug=True))
    return out


# ---------- 3. iTunes Store search ----------
def search_itunes(term, kind):
    p = {"term": term, "country": "us", "limit": 8}
    p.update({"media": "movie", "entity": "movie"} if kind == "movie" else {"media": "tvShow", "entity": "tvSeason"})
    _, text = fetch("https://itunes.apple.com/search?" + urllib.parse.urlencode(p))
    try:
        results = json.loads(text).get("results", []) if text else []
    except ValueError:
        results = []
    out = []
    for r in results:
        title = r.get("trackName") if kind == "movie" else (r.get("artistName") or re.sub(r",\s*(Season|Vol\.?|Volume|Series).*$", "", r.get("collectionName", "")))
        store = r.get("trackViewUrl") if kind == "movie" else r.get("collectionViewUrl")
        if not title or not store:
            continue
        final, page = fetch(store, accept="text/html")  # store links forward to the Apple TV page
        hay = (final or "") + " " + (page or "")
        show = re.search(r"showId=(umc\.cmc\.[a-z0-9]+)", hay) or re.search(r"/show/[^/\"]+/(umc\.cmc\.[a-z0-9]+)", hay)
        mov = re.search(r"/movie/[^/\"]+/(umc\.cmc\.[a-z0-9]+)", hay)
        m = show if kind == "tv" else mov
        if m:
            art = (r.get("artworkUrl100") or "").replace("100x100bb", "600x900bb") or None
            out.append(dict(title=title, kind=kind, id=m.group(1), url=None, year=year_of(r.get("releaseDate")), art=art))
        time.sleep(0.4)
        if len(out) >= 3:
            break
    return out


# ---------- matching ----------
def score(c, want_title, want_kind, want_year):
    a, b = norm(c["title"]), norm(want_title)
    if a == b: s = 100
    elif a and b and (a.startswith(b) or b.startswith(a)): s = 45
    else: return None
    s += 30 if c["kind"] == want_kind else -15
    if want_year and c.get("year"):
        d = abs(int(c["year"]) - int(want_year))
        s += 40 if d == 0 else (25 if d == 1 else -60)
    return s


def best_for(it, title):
    """Returns (sure_match or None, [candidates best first])."""
    want_year = str(it["year"] or "")
    want_year = int(want_year) if want_year.isdigit() else None
    terms = [it["apple"]] + [t for t in (title, it["term"]) if t and t != it["apple"]]
    cands = []
    for source in ("uts", "page", "itunes"):
        for term in terms[:2] if source == "uts" else terms[:1]:  # the slower sources get one try
            if source == "uts": found = search_uts(term)
            elif source == "page": found = search_page(term)
            else: found = search_itunes(term, it["kind"])
            time.sleep(0.6)
            for c in found:
                s = score(c, title, it["kind"], want_year)
                if s is not None and all(c["id"] != x["id"] for _, x in cands):
                    cands.append((s, c))
            cands.sort(key=lambda x: -x[0])
            top = cands[0] if cands else None
            # sure: same name and kind, and the year agrees (or there's no year to check)
            if top and top[0] >= 130 and (not want_year or not top[1].get("year") or top[0] >= 155):
                if len(cands) == 1 or cands[1][0] < top[0] - 20:
                    return top[1], [c for _, c in cands]
        if cands and cands[0][0] >= 100:
            break  # a good-but-unsure match; asking beats trying slower sources
    return None, [c for _, c in cands]


def describe(c):
    kind = "show" if c["kind"] == "tv" else "movie"
    return f"{c['title']}" + (f" ({c['year']})" if c.get("year") else "") + f" - {kind} - {c['id']}"


def ask(cands):
    for i, c in enumerate(cands[:5], 1):
        say(f"     {i}. {describe(c)}", "y")
    try:
        a = input("     Type a number to use it, or press Enter to skip: ").strip()
    except EOFError:
        return None
    return cands[int(a) - 1] if a.isdigit() and 1 <= int(a) <= min(5, len(cands)) else None


def entry(c, title):
    e = {"kind": c["kind"], "id": c["id"], "found": describe(c).rsplit(" - ", 1)[0], "for": title}
    if c.get("art"):
        e["art"] = c["art"]
    return e


def pasted(url, title):
    """An apple_links.json entry for a link copied from the Apple TV app. Links from another country's
    store (tv.apple.com/ca/..., ?l=fr) are switched to the US store. Episode links are kept whole."""
    m = re.match(r"https://tv\.apple\.com/(?:[a-z]{2}/)?(movie|show|season|episode)/([^/?#]+)/(umc\.cmc\.[a-z0-9]+)", url.strip())
    if not m:
        raise ValueError("That doesn't look like an Apple TV link (it should look like https://tv.apple.com/us/movie/.../umc.cmc...).")
    kind, slug, ident = m.groups()
    show = re.search(r"showId=(umc\.cmc\.[a-z0-9]+)", url)
    e = {"kind": "movie" if kind == "movie" else "tv", "id": ident, "found": "pasted by hand", "for": title}
    if kind in ("season", "episode"):
        e["url"] = f"https://tv.apple.com/us/{kind}/{slug}/{ident}" + (f"?showId={show.group(1)}" if show else "")
    return e


# ---------- main ----------
def main(argv):
    links = load_json(APPLE_LINKS)
    if "--set" in argv:
        i = argv.index("--set")
        try:
            key, url = argv[i + 1], argv[i + 2]
        except IndexError:
            sys.exit("Usage: python tools/find_apple_links.py --set 105 https://tv.apple.com/us/movie/.../umc.cmc.xxxx")
        known = {x["key"]: x for x in items()}
        if key not in known:
            sys.exit(f"No title with id {key} in cover_rows.json.")
        try:
            links[key] = pasted(url, known[key]["title"] or known[key]["label"])
        except ValueError as e:
            sys.exit(str(e))
        save_json(APPLE_LINKS, links)
        say(f"Saved {key} -> {links[key].get('url') or links[key]['id']}. Now run build_data.py (or update_library.py).", "g")
        return

    yes = "--yes" in argv
    folder = None
    if "--covers" in argv:
        folder = argv[argv.index("--covers") + 1]
    wikidata = load_json(os.path.join(covers_dir(folder), "apple-links.json"))
    site = site_library()
    only = {a for a in argv if re.fullmatch(r"\d{3}[a-z]?", a)}
    todo = []
    for it in items():
        k = it["key"]
        if only:
            if k in only: todo.append(it)
        elif k not in links and k not in wikidata and not (site.get(k) or {}).get("direct"):
            todo.append(it)  # new, or still opens a search
    if not todo:
        say("Nothing to look up: every title already opens directly.", "g")
        return
    say(f"Looking up {len(todo)} titles on Apple TV (new titles and ones that open a search)...\n", "c")
    got = skipped = 0
    log = []
    logfile = os.path.join(covers_dir(folder), "apple-links-log.csv")
    try:
        for num, it in enumerate(todo, 1):
            if num == 4 and UTS_STATS["asked"] and not UTS_STATS["answered"]:
                say("   (Apple TV's search isn't answering, so this will be slow and find little. "
                    "Pasting links with --set works without it.)", "r")
            got, skipped = look_up(it, num, len(todo), links, yes, log, got, skipped)
    finally:
        if log:
            os.makedirs(os.path.dirname(logfile), exist_ok=True)
            with open(logfile, "w", encoding="utf-8", newline="") as f:
                f.write("id,title,result\n" + "".join(f'{k},"{t.replace(chr(34), "")}",{r}\n' for k, t, r in log))
    say(f"\nDone. {got} direct links saved to tools/apple_links.json, {skipped} still open a search.", "c")
    say(f"A list of what happened to each title is in {logfile}", "d")
    if skipped:
        say("For the rest, find the title in the Apple TV app, tap Share > Copy Link, and run:", "d")
        say('   python tools/find_apple_links.py --set <id> "<link>"', "d")


def look_up(it, num, total, links, yes, log, got, skipped):
    title = it["title"] or it["term"]
    say(f"[{num}/{total}] {it['key']} {title}" + (f" ({it['year']})" if it["year"] else ""))
    sure, cands = best_for(it, title)
    pick = sure
    if sure:
        say(f"   {describe(sure)}", "g")
    elif cands and not yes:
        say("   Not sure which one this is:", "y")
        pick = ask(cands)
    elif not cands:
        say("   nothing found on Apple TV", "r")
    else:
        say(f"   not sure ({len(cands)} possible) - skipped", "y")
    if pick:
        links[it["key"]] = entry(pick, title)
        save_json(APPLE_LINKS, links)  # save as we go, so stopping early keeps what was found
        log.append((it["key"], title, "found " + pick["id"]))
        return got + 1, skipped
    log.append((it["key"], title, "not sure" if cands else "nothing found"))
    return got, skipped + 1


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        say("\nStopped. Links found so far are saved.", "y")
    if "--no-pause" not in sys.argv:
        pause()
