# Ideas to make Play Request better

These are optional next steps, not promises. The live app already works as a tasting journal with a clear unlock path and local restaurant ideas.

## Badges and a passport

- The site already awards badges (first sip, pair, trio, quad, Peak, level-clears). Make them feel more like stamps: a date, the dish, and the restaurant, collected on a “passport” page you can screenshot or print.
- Offer a printable stamp card (we already ship a tasting passport in the board-game PDF). A café could initial a box when you order the suggested dish.
- Seasonal badge trails: “Woods Hole dock walk” (Shuckers, Landfall, Quicks Hole, Pie in the Sky) or “Main Street Falmouth.”

## QR codes at restaurants

- Flavor Quest already has QR check-in. Play Request could reuse that idea more lightly: a small table tent or sticker whose code opens the matching combo (`index.html?combo=salty-umami`) with that restaurant pre-selected.
- Start with Cape Island Café, since it is in the network and already has a full menu mapping.
- Keep it optional. Nobody should have to scan to enjoy lunch.

## Leaderboards (carefully)

- A public “most combos this month” board is fun but can shame people or leak who eats where. Better options:
  - Opt-in only, first name or a nickname, no restaurant history on the public board.
  - Friends or a household code, not a global ranking.
  - A cooperative town goal (“Falmouth has logged 500 unique tastings”) with no individual names.

## Richer restaurant data

- Revisit “suggested” dishes as official menus are confirmed; move them to “from the menu.”
- Add Mashpee, Sandwich and the Islands later, without losing the tight Falmouth / Woods Hole focus.
- Let a restaurant owner claim a listing and correct a dish (staff approval first).
- Note seasonal closures more precisely (Shuckers, Jim’s Clam Shack, and others).

## Play feel

- A “today’s suggested tasting” based on what the player has open and what is nearby.
- A map view of restaurants, colored by which open combos they can help with.
- A short guided first session: pick Sweet, we send you to Island Lime Cooler at Cape Island Café or lemonade at Pie in the Sky.
- Offline mode (the data is already static JSON; a service worker would make the board work on the ferry).
- Optional photo of the dish, kept on-device or in a private bucket, never public by default.

## Tabletop and events

- Run a Play Request night at Cape Island Café: five small tastes, one path to the Peak, paper passports.
- Sell or give away a small card deck (the PDF is the prototype).
- A kids’ / family rules variant that stays with sweets, sours and salties, and skips alcohol examples (the site already treats stout as optional).

## Accounts and community

- Once Google and Facebook logins are on, a “continue as…” return visit should drop you back on the board, not only the account page.
- Optional public “I tried this” notes, moderated, so a combo page can show real local reports.
- Staff tools to feature a dish of the week without a code change.

## Cross-links to the earlier games

- Flavor Quest and Flavor Escape already exist. A shared “taste ID” could let a Peak in Play Request unlock a cosmetic in Escape, or a Quest check-in count as a tasting here — only if that stays fun and not obligatory.
