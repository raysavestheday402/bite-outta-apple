# Movie Library

A kid-friendly launcher for the family's movies and shows. Tap a poster and it opens
in Apple TV or Netflix and plays.

**Live:** https://raysavesthedaylibrary.netlify.app

## Adding titles

1. In GitHub Desktop: **Fetch origin**, then **Pull origin**.
2. Add a row per title to `tools/cover_rows.json`, using the next unused number.
3. Open the `tools` folder and double-click **Update Library.bat**.
4. Look over the new covers, then **Commit** and **Push**. Netlify deploys in about a minute.

## What's in here

Plain HTML, CSS and JavaScript. No build step, so a push is a deploy.

| | |
|---|---|
| `index.html` | the whole app: markup, styles and script |
| `data.js` | the library. Generated - don't edit by hand |
| `posters/`, `thumbs/` | cover art. Generated |
| `icons/` | home-screen icon and manifest |
| `sw.js` | offline support |
| `tools/` | the scripts that build `data.js` and the posters |

## Credits

Posters and details come from [TMDB](https://www.themoviedb.org). This product uses the
TMDB API but is not endorsed or certified by TMDB. Some posters come from Wikipedia and
fanart.tv. All artwork belongs to its respective studios. This is a personal,
non-commercial family project.
