# bite-outta-apple 🍎

**Apple TV Library**: a kid-friendly, tap-a-poster launcher for our family's purchased Apple TV / iTunes movies and shows. It's built to live on an iPad home screen.

**Live:** https://raysavesthedaylibrary.netlify.app (Netlify redeploys on every push).

- **Two ways to browse:** a big poster **Grid**, or a classic iPod-style **Cover Flow** you swipe through one cover at a time.
- **One tap opens the movie in the Apple TV app**, so it's ready to play. Titles without a known Apple TV ID open an Apple TV search for that name instead.
- **Made for a kid who can't read yet:** no search or filters, just big covers to tap, large tap targets, and no long-press popups or accidental zoom.
- **Apple TV+ kids titles** (Peanuts, Fraggle Rock, Wolfwalkers…) show up with everything else and also have their own ➕ chip. They play only while the iPad has an Apple TV+ subscription.
- **Works without Wi‑Fi:** the app and every poster are saved on the iPad. With no Wi‑Fi, a red alert shows a green **Open Downloads** button that opens the Apple TV app, where downloaded titles still play.
- **Broken links:** tap the small 🔗 on a title if it doesn't open right. A note at the bottom of the page counts them and has Copy list, to paste to Claude.
- **No frameworks and no build step.** It's plain HTML, CSS and JavaScript.

## What's in here

| Path | What it is |
|---|---|
| `index.html` | The whole app: layout, styles and code. |
| `sw.js` | Saves the app and posters on the device so it opens offline. |
| `data.js` | The library: every title with year, rating, poster and Apple TV link. Generated, so don't edit it by hand. |
| `posters/` | Cover art, 600 px wide. |
| `icons/` | Home-screen icon, favicons and `manifest.webmanifest`. |
| `tools/Update Library.bat` | Double-click to run the whole update (below). |
| `tools/update_library.py` | Runs the four steps below in order. |
| `tools/find_apple_links.py` | Finds each title's own Apple TV page so it opens the title, not a search. Saves to `tools/apple_links.json`. |
| `tools/get_covers.py` | Downloads posters (TMDB → fanart.tv → Wikipedia → Apple TV), details, and Apple TV links (Wikidata). |
| `tools/build_data.py` | Rebuilds `data.js` and `posters/` from the downloaded covers. |
| `tools/cover_rows.json` | The title list. Every script reads it, so it's the only place to edit. |
| `tools/apple_links.json` | Direct Apple TV links found by `find_apple_links.py` or pasted by hand. Committed. |
| `tools/check_data.py` | Quick offline checks (posters present, kids ratings, links) to run before pushing. |
| `CLAUDE.md` | Project rules and notes for working on this with Claude. |

## Put it on the iPad

1. Host this folder anywhere that serves static files. Netlify Drop (drag the folder in) and GitHub Pages both work.
2. On the iPad, open the link in **Safari**.
3. Tap **Share → Add to Home Screen**.

It opens full-screen with its own icon, labeled **TV Library**.

For a poster to show **Play** instead of **Buy**, the iPad's Apple Account has to own the title. Being in the same Family Sharing group with **Purchase Sharing** turned on counts. Screen Time content limits also have to allow the title's rating.

## Updating the library

### One-time setup (Windows)

1. Install Python from [python.org](https://www.python.org/downloads/). On the first installer screen, tick **Add python.exe to PATH**.
2. Open **Command Prompt**, go to the repo folder and install Pillow:
   ```
   cd "C:\Users\raysa\Claude Files\bite-out-of-appl"
   pip install -r tools\requirements.txt
   ```
3. Have a free TMDB API key ready (themoviedb.org → Settings → API). The first run asks for it and saves it in `tools\keys.txt`, which is git-ignored and never committed.

### Every update

1. In GitHub Desktop, pull the latest changes.
2. Add or remove titles in `tools/cover_rows.json` if you want to (field meanings are in `CLAUDE.md`). Give new titles the next unused number.
3. In GitHub Desktop choose **Repository → Show in Explorer**, open the `tools` folder there and double-click **`Update Library.bat`**. It has to be this folder, the one GitHub Desktop uses, or the results won't show up as changes to push. (To use your Covers archive for new covers, run `python tools\update_library.py "C:\Users\raysa\Claude Files\Apple TV Archive\Covers"` once from that folder; it's remembered after that. It isn't required: the site's own posters, years, ratings and links are kept either way.)
4. It runs four steps:
   - **Covers** (`get_covers.py --missing`): downloads covers, years, ratings and Wikidata's Apple TV ids only for titles that have no cover yet, in the Covers folder or on the site.
   - **Apple TV links** (`find_apple_links.py`): searches Apple TV only for titles that still have no direct link after that. Titles that already open directly are never re-checked. If the first 3 searches find nothing, it stops instead of grinding through the list. What happened to each title is saved in `apple-links-log.csv` in the Covers folder.
   - **Build** (`build_data.py`): rewrites `data.js` and `posters/`. A new title shows up once it has a cover.
   - **Check** (`check_data.py`): lists anything wrong, and any titles that still open a search.
5. Look over the new posters, then commit and push in GitHub Desktop. Netlify deploys in about a minute.

### If a title still opens a search

Find it in the Apple TV app (or at tv.apple.com), tap **Share → Copy Link**, then paste it in with its id from `data.js` or `cover_rows.json`. Links from another country's store or for an episode work too. If a title's link is broken rather than a search, the same `--set` fixes it, or run `python tools\find_apple_links.py 105` to look that one up again.

```
python tools\find_apple_links.py --set 105 "https://tv.apple.com/us/movie/the-pout-pout-fish/umc.cmc.xxxxx"
```

Run the update again (or just `python tools\build_data.py`) and push.

### Collections

A box set like *Halloweentown: 4-Movie Collection* is one row with a `choices` list, one entry per movie. Each movie gets its own poster and its own Apple TV link (ids `010a` to `010d`). Buying the collection puts every movie in it in your Apple TV library, so each one opens to **Play**.

## Credits

Posters and details come from TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB. Some posters come from Wikipedia and fanart.tv, and Apple TV IDs come from Wikidata and Apple TV's own search. All artwork belongs to its respective studios, and this is a personal, non-commercial family project.
