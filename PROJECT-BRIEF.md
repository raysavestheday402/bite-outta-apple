# Bite Outta Apple: project brief

## What it is
**Apple TV Library** is a kid-friendly web portal for our family's purchased Apple TV / iTunes **kids** movies and shows. It's saved to Lilly's iPad home screen as **TV Library**, using the raysavestheday icon. Tapping a poster opens that title in the Apple TV app.

## Where things live
- **Live site:** https://raysavesthedaylibrary.netlify.app (Netlify, deployed from GitHub)
- **Code:** GitHub `raysavestheday402/bite-outta-apple`, private. It's pushed with GitHub Desktop, and Netlify redeploys on every push.
- **Local folders:**
  - `C:\Users\raysa\Claude Files\bite-out-of-appl`: the repo folder
  - `C:\Users\raysa\Claude Files\Apple TV Archive\Covers`: original high-res covers, `details.json` and `apple-links.json`
  - `C:\Users\raysa\Claude Files\raysavestheday_icon_package`: icon source files
- The empty public repo `bite-out-of-appl` on GitHub is unused and can be deleted.

## Library
- **152 titles:** 134 movies and 18 shows.
- **Kids titles only:** animated, plus kids live-action such as the Rocky & Bullwinkle and Sonic movies.
- **Covers:** every one was checked against its title. They come from TMDB at 600px, with two added by hand (The Land of Sometimes, A Scooby-Doo! Valentine Bouquet).
- **Apple TV links:** 130 open the title directly. The other 22 open an Apple TV search.
- **Ratings:** G, PG and TV-Y/Y7/G/PG, plus My Life as a Zucchini (PG-13, kept on purpose).

## Features
- **Two views:** a poster **Grid**, or iPod-style **Cover Flow** with a toggle, swiping, a scrubber, and a Play in Apple TV button.
- **Picture filters for a non-reader:** ⭐ All · 🎬 Movies · 📺 Shows · 🏰 Disney & Pixar · 🎄 Holidays · ❤️ Favorites. Favorites are saved per device.
- **Look:** bright icon-blue background with light rays, the icon in the header, a gold "Apple TV Library" wordmark, and no Lilly name anywhere.
- **Kid-proof:** no long-press popups, no text selection, no double-tap zoom.

## How to update the library
1. Edit `tools/cover_rows.json`. The title list inside `tools/get_covers.py` needs the same change, or ask Claude to regenerate it.
2. Run `python tools/get_covers.py`. It asks for the TMDB API key the first time and saves it in `keys.txt`, which is never committed.
3. Run `python tools/build_data.py "path\to\Covers"` (needs `pip install pillow`).
4. Commit and push in GitHub Desktop, and Netlify updates automatically.

## iPad requirements for Play (not Buy)
- The iPad's Apple Account owns the title. Being in the same Family Sharing group with **Purchase Sharing** on counts.
- None of the purchases are hidden.
- Screen Time content limits allow the title's rating.

## Open items
- Test on the iPad: add to Home Screen, then tap Shrek and check it shows **Play**.
- If any title shows Buy, add a backup "Open Apple TV app" button.
- Optional: delete the empty `bite-out-of-appl` repo.
