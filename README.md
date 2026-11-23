# Play Request

A tasting game built on the five basic tastes — sweet, sour, salty, bitter and umami — and their 31 combinations.

**Live:** https://platinum00001.github.io/play-request/

Pick one flavor to start. A new combo opens when it extends any combo you have already tried by exactly one flavor. You can reach the Peak in five tastings; you do not have to fill every square. Each combo lists classic examples plus dishes from Falmouth and Woods Hole restaurants. Items marked **From the menu** use a published dish name; **Suggested** items are informed ideas you should confirm before you go.

Progress is saved in the browser. Optional sign-in (email, later Google and Facebook) syncs the same path across devices.

Plain HTML, CSS and vanilla JS. No build step. All paths are relative, so the site works under `/play-request/` on GitHub Pages.

## Local

```bash
python3 -m http.server 8765 --directory .
# open http://localhost:8765
node tests/unlock.test.js
node tests/paths.test.js
```

## Docs

- `docs/SETUP.md` — schema, redirect URL, admin SQL, Resend
- `docs/FACEBOOK-GOOGLE-LOGIN-SETUP.md` — exact OAuth callback URLs
- `docs/SUGGESTIONS.md` — ideas for later
- `play-request-board-game.pdf` — printable tabletop version
- `data/play-request-restaurants-dishes.csv` — restaurant and dish export

This is a new app. Earlier related projects: [Flavor Quest](https://github.com/platinum00001/flavor-quest) and [Flavor Escape](https://github.com/platinum00001/flavor-escape).
