# bite-outta-apple 🍎

**Apple TV Library**: a kid-friendly, tap-a-poster launcher for our family's purchased Apple TV / iTunes movies and shows. It's built to live on an iPad home screen.

**Live:** https://raysavesthedaylibrary.netlify.app (Netlify redeploys on every push).

- **Two ways to browse:** a big poster **Grid**, or a classic iPod-style **Cover Flow** you swipe through one cover at a time.
- **One tap opens the movie in the Apple TV app**, so it's ready to play. Titles without a known Apple TV ID open an Apple TV search for that name instead.
- **Made for a kid who can't read yet:** picture filters (⭐ All · 🎬 Movies · 📺 Shows · 🏰 Disney & Pixar · 🎄 Holidays · ❤️ Favorites), large tap targets, and no long-press popups or accidental zoom.
- **Favorites** are saved on each device.
- **No frameworks and no build step.** It's plain HTML, CSS and JavaScript.

## What's in here

| Path | What it is |
|---|---|
| `index.html` | The whole app: layout, styles and code. |
| `data.js` | The library: 152 titles with year, rating, poster and Apple TV link. Generated, so don't edit it by hand. |
| `posters/` | Cover art, 600 px wide. |
| `icons/` | Home-screen icon, favicons and `manifest.webmanifest`. |
| `tools/get_covers.py` | Downloads posters (TMDB → fanart.tv → Wikipedia), details, and Apple TV links (Wikidata). |
| `tools/build_data.py` | Rebuilds `data.js` and `posters/` from the downloaded covers. |
| `tools/cover_rows.json` | The title list. Both scripts read it, so it's the only place to edit. |
| `tools/check_data.py` | Quick offline checks (posters present, kids ratings, links) to run before pushing. |
| `CLAUDE.md` | Project rules and notes for working on this with Claude. |

## Put it on the iPad

1. Host this folder anywhere that serves static files. Netlify Drop (drag the folder in) and GitHub Pages both work.
2. On the iPad, open the link in **Safari**.
3. Tap **Share → Add to Home Screen**.

It opens full-screen with its own icon, labeled **TV Library**.

For a poster to show **Play** instead of **Buy**, the iPad's Apple Account has to own the title. Being in the same Family Sharing group with **Purchase Sharing** turned on counts. Screen Time content limits also have to allow the title's rating.

## Updating the library

1. Add or remove titles in `tools/cover_rows.json` (the field meanings are in `CLAUDE.md`). Give new titles the next unused number.
2. Install Pillow once: `pip install -r tools/requirements.txt`.
3. Run `python tools/get_covers.py`. It asks once for a free TMDB API key and stores it in `tools/keys.txt`, which is git-ignored and never committed. Covers land in `tools/Covers/`.
4. Run `python tools/build_data.py`. With no path it reads `tools/Covers/`; you can also pass a folder, like `python tools/build_data.py "path\to\Covers"`.
5. Run `python tools/check_data.py`, then commit and push.

## Credits

Posters and details come from TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB. Some posters come from Wikipedia and fanart.tv, and Apple TV IDs come from Wikidata. All artwork belongs to its respective studios, and this is a personal, non-commercial family project.
