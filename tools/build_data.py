#!/usr/bin/env python3
"""Build data/restaurants.json, data/dishes.json, data/combos.json and a Drive CSV."""
from __future__ import annotations
import csv, json, re, unicodedata
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_IN = Path("/workspace/rex-build/data/falmouth_restaurants.csv")
CHECKED = "2026-11-23"

TASTES = [
    {"id": "sweet", "name": "Sweet", "color": "#e25d7a", "blurb": "Sugar, honey, ripe fruit — the taste that rounds a dish.", "examples": ["honey", "ripe mango", "vanilla ice cream"]},
    {"id": "sour", "name": "Sour", "color": "#7cb342", "blurb": "Lemon, vinegar, fermentation — the taste that wakes everything up.", "examples": ["lemon", "plain yogurt", "pickle brine"]},
    {"id": "salty", "name": "Salty", "color": "#3a7ca5", "blurb": "Sea, soy, cheese — the taste that makes food taste like itself.", "examples": ["pretzels", "sea salt", "soy sauce"]},
    {"id": "bitter", "name": "Bitter", "color": "#6b3aa0", "blurb": "Coffee, dark greens, cocoa — the grown-up edge of flavor.", "examples": ["black coffee", "dark chocolate", "arugula"]},
    {"id": "umami", "name": "Umami", "color": "#c0603a", "blurb": "Broth, mushroom, tomato, aged cheese — the deep, savory taste.", "examples": ["Parmesan", "miso", "roasted mushrooms"]},
]
ORDER = ["sweet", "sour", "salty", "bitter", "umami"]
NAME = {t["id"]: t["name"] for t in TASTES}

CLASSICS = {
    "sweet": ["Honey on toast", "Ripe mango", "Vanilla ice cream"],
    "sour": ["A squeeze of lemon", "Plain yogurt", "Dill pickle"],
    "salty": ["A pretzel", "Sea-salted tomato", "Soy sauce on rice"],
    "bitter": ["Black coffee", "A square of unsweetened chocolate", "Arugula salad"],
    "umami": ["Shaved Parmesan", "Miso soup", "Sautéed mushrooms"],
    "sour-sweet": ["Lemonade", "Berry jam with citrus", "Sweet-and-sour sauce"],
    "salty-sweet": ["Salted caramel", "Chocolate-covered pretzels", "Kettle corn"],
    "bitter-sweet": ["Dark chocolate", "A mocha", "Candied grapefruit peel"],
    "sweet-umami": ["Teriyaki", "Honey-glazed ham", "Ketchup"],
    "salty-sour": ["Salt-and-vinegar chips", "Pickled olives", "Ceviche"],
    "bitter-sour": ["Grapefruit", "An IPA with lemon", " unsweetened cranberry"],
    "sour-umami": ["Tomato sauce", "Worcestershire", "Kimchi"],
    "bitter-salty": ["Salted dark chocolate", "Olives", "Tonic with a pinch of salt"],
    "salty-umami": ["Soy sauce", "Miso soup", "Anchovies"],
    "bitter-umami": ["Espresso with a Parmesan bite", "Broccolini with garlic", "Dark beer stew"],
    "salty-sour-sweet": ["Sweet chili sauce", "Salted lime soda (chamoy)", "Pad Thai's sweet-sour-salt baseline"],
    "bitter-sour-sweet": ["An Aperol spritz", "Candied grapefruit", "Campari and orange"],
    "sour-sweet-umami": ["Ketchup", "BBQ sauce", "Sweet chili with fish sauce"],
    "bitter-salty-sweet": ["Salted mocha", "Maple-bourbon glaze", "Candied bacon with coffee"],
    "salty-sweet-umami": ["Teriyaki", "Honey-soy glaze", "Bacon jam"],
    "bitter-sweet-umami": ["Mole sauce", "Coffee-rubbed steak with brown sugar"],
    "bitter-salty-sour": ["A Negroni", "Grapefruit with a salt rim", "A hoppy gose"],
    "salty-sour-umami": ["Fish-sauce vinaigrette", "Poke", "Caesar dressing"],
    "bitter-sour-umami": ["Tomato-espresso braise", "Nam prik", "Radicchio with anchovy"],
    "bitter-salty-umami": ["Cacio e pepe with broccoli rabe", "Soy-braised bitter greens", "Marmite on toast with coffee"],
    "bitter-salty-sour-sweet": ["Salted lemon dark chocolate", "A Paloma with grapefruit bitters"],
    "salty-sour-sweet-umami": ["Pad Thai", "A well-built poke bowl", "Hawaiian pizza (the argument starter)"],
    "bitter-sour-sweet-umami": ["Som tum (green papaya salad) variations", "A tamarind-coffee glaze"],
    "bitter-salty-sweet-umami": ["Mole negro", "A coffee-soy caramel glaze"],
    "bitter-salty-sour-umami": ["Caesar salad", "A dirty martini with lemon and olive"],
    "bitter-salty-sour-sweet-umami": ["A great mole with lime", "Complex ramen with a squeeze of lime", "A burger with pickles, cheese, a sweet bun, bitter greens and salt"],
}
# fix typo
CLASSICS["bitter-sour"] = ["Grapefruit", "An IPA with lemon", "Unsweetened cranberry"]

LEVEL_NAME = {1: "Singles", 2: "Pairs", 3: "Trios", 4: "Quads", 5: "The Peak"}
LEVEL_BLURB = {
    1: "Pick any one taste to begin. You do not have to try them all first.",
    2: "Once you have tried a flavor, every pair that adds one new flavor to it opens.",
    3: "A trio opens when it extends any pair you have already tried by one flavor.",
    4: "A quad opens when it extends any trio you have already tried by one flavor.",
    5: "The Peak opens when it extends any quad you have already tried — all five tastes in one bite.",
}

def combo_id(tastes):
    return "-".join(sorted(tastes, key=lambda x: ORDER.index(x) if False else x))  # alpha

def cid(tastes):
    return "-".join(sorted(tastes))

def combo_name(tastes):
    tastes = list(tastes)
    if len(tastes) == 5:
        return "The Peak — all five"
    if len(tastes) == 4:
        missing = [NAME[t] for t in ORDER if t not in tastes][0]
        listed = " + ".join(NAME[t] for t in sorted(tastes))
        return f"{listed} (everything except {missing})"
    return " + ".join(NAME[t] for t in sorted(tastes))

def build_combos():
    out = []
    for n in range(1, 6):
        for grp in combinations(ORDER, n):
            tastes = list(grp)
            i = cid(tastes)
            out.append({
                "id": i,
                "level": n,
                "levelName": LEVEL_NAME[n],
                "tastes": sorted(tastes),
                "name": combo_name(tastes),
                "blurb": LEVEL_BLURB[n] if n > 1 else TASTES[ORDER.index(tastes[0])]["blurb"] if len(tastes)==1 and tastes[0] in ORDER else "",
                "classics": CLASSICS.get(i, []),
                "colors": [next(t["color"] for t in TASTES if t["id"] == x) for x in sorted(tastes)],
            })
    # nicer blurbs for singles
    for c in out:
        if c["level"] == 1:
            c["blurb"] = next(t["blurb"] for t in TASTES if t["id"] == c["tastes"][0])
    out.sort(key=lambda c: (c["level"], c["id"]))
    return out

def slug(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def load_restaurants():
    rows = list(csv.DictReader(CSV_IN.open(encoding="utf-8")))
    rests = []
    for r in rows:
        rests.append({
            "id": slug(r["name"]),
            "name": r["name"],
            "address": r["address"],
            "street": r["street"],
            "village": r["village"],
            "town": r["town"] if r["town"] == "Woods Hole" else "Falmouth",
            "area": r["village"] or r["town"],
            "zip": r["zip"],
            "lat": float(r["lat"]) if r["lat"] else None,
            "lng": float(r["lng"]) if r["lng"] else None,
            "phone": r["phone"],
            "website": r["website"],
            "category": r["category"],
            "hours": r["hours"],
            "description": r["description"],
            "notes": r["notes"],
            "source_urls": [u.strip() for u in (r["source_urls"] or "").split("|") if u.strip()],
            "listed_on": r["checked_on"],
            "featured": False,
        })
    extras = [
        {
            "id": "cape-island-cafe",
            "name": "Cape Island Café",
            "address": "316 Gifford St, Falmouth, MA 02540",
            "street": "316 Gifford St",
            "village": "Falmouth",
            "town": "Falmouth",
            "area": "Gifford Street",
            "zip": "02540",
            "lat": 41.5687,
            "lng": -70.6149,
            "phone": "(774) 247-5263",
            "website": "https://capeislandcafe.com/",
            "category": "Café / Lunch",
            "hours": "Lunch Mon–Fri, 11:00 AM–3:00 PM",
            "description": "Neighborhood lunch café: wraps, salads, soups and bowls at 316 Gifford Street, Falmouth.",
            "notes": "James's café — featured Play Request kitchen.",
            "source_urls": ["https://capeislandcafe.com/"],
            "listed_on": CHECKED,
            "featured": True,
        },
        {
            "id": "maison-villatte-woods-hole",
            "name": "Maison Villatte Woods Hole",
            "address": "22 Luscombe Ave, Woods Hole, MA 02543",
            "street": "22 Luscombe Ave",
            "village": "Woods Hole",
            "town": "Woods Hole",
            "area": "Woods Hole",
            "zip": "02543",
            "lat": 41.5234,
            "lng": -70.6697,
            "phone": "(774) 255-9105",
            "website": "",
            "category": "Café / Bakery",
            "hours": "",
            "description": "A Woods Hole shop of the Falmouth French bakery, for breads, pastries and coffee by the ferry.",
            "notes": "Added Nov 2026; not in the original 69-restaurant list. Sister of Maison Villatte on Main Street.",
            "source_urls": ["https://woodshole.com/eat/"],
            "listed_on": CHECKED,
            "featured": False,
        },
        {
            "id": "woods-hole-market",
            "name": "Woods Hole Market & General Store",
            "address": "87 Water St, Woods Hole, MA 02543",
            "street": "87 Water St",
            "village": "Woods Hole",
            "town": "Woods Hole",
            "area": "Woods Hole",
            "zip": "02543",
            "lat": 41.5248,
            "lng": -70.6710,
            "phone": "(508) 540-4792",
            "website": "https://www.woodsholemarket.com/",
            "category": "Market / Deli",
            "hours": "",
            "description": "General store and deli on Water Street: groceries, baked goods, lobster rolls, ice cream and smoothies.",
            "notes": "Added Nov 2026; not in the original 69-restaurant list.",
            "source_urls": ["https://www.woodsholemarket.com/", "https://woodshole.com/eat/"],
            "listed_on": CHECKED,
            "featured": False,
        },
    ]
    have = {r["id"] for r in rests}
    for e in extras:
        if e["id"] not in have:
            rests.append(e)
    rests.sort(key=lambda r: (0 if r.get("featured") else 1, 0 if r["town"]=="Woods Hole" else 1, r["name"].lower()))
    return rests

# dish: restaurant_id, dish, combo_id, source ('menu'|'suggested'), note, source_url
# source=menu only when the dish name was taken from a published menu or official site (checked 2026-11-23 or the café site).
DISHES = [
    # ---- Cape Island Café (full menu, capeislandcafe.com, 2026-11-23) ----
    ("cape-island-cafe", "Coffee", "bitter", "menu", "Regular or decaf coffee from the lunch menu.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Iced Espresso Cream", "bitter-sweet", "menu", "A sweet cream espresso drink on the café beverage list.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Island Lime Cooler", "sour-sweet", "menu", "A house lime cooler from the beverage list.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Cranberry Citrus Sparkler", "sour-sweet", "menu", "Cranberry and citrus soda from the beverage list.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Island Berry Punch", "sweet", "menu", "A fruit-forward house punch from the beverage list.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Ginger Lime Fizz", "sour-sweet", "menu", "Ginger and lime fizz from the beverage list.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Salmon Bowl", "sour-umami", "menu", "Salmon, rice, spinach, cucumber, avocado and red onion with house lime vinaigrette.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Cape Road Chili", "salty-sour-umami", "menu", "Beef, kidney and black beans, tomato, onion and peppers, cheddar on top.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Chili Bowl", "salty-sour-umami", "menu", "Cape Road Chili over rice with cheddar, red onion and tomato.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Kale & Bean Soup", "bitter-sour-umami", "menu", "Kale, kidney beans, tomato, onion, garlic, shredded chicken and broth.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Roasted Tomato & Red Pepper soup", "sour-sweet-umami", "menu", "Roasted tomato, red pepper, onion, garlic and broth.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Harbor Chop Salad", "salty-sour-umami", "menu", "Chopped romaine and spinach with chicken, bacon, egg, tomato, cucumber, red onion and cheddar.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Caesar Salad", "bitter-salty-sour-umami", "menu", "Romaine, fresh-grated Parmesan, croutons and Caesar dressing.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Chicken Caesar Wrap", "bitter-salty-sour-umami", "menu", "Chicken, romaine, Parmesan, croutons and Caesar dressing in a wrap.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Cashew Chicken Salad Plate", "sweet-umami", "menu", "Chicken, cashews, cranberries and red onion in mayo, over greens.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Cashew Chicken Wrap", "sweet-umami", "menu", "Cashew chicken salad (cranberries, cashews) with spinach and tomato.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Kale Crunch", "bitter-salty-sweet", "menu", "Kale, cabbage, cranberries, cashews, feta and chicken.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Island Chef Salad", "salty-sour-umami", "menu", "Romaine, ham, egg, cucumber, cheddar, bacon, olives and pepperoncini.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Southwest Rice Bowl", "salty-sour-sweet-umami", "menu", "Chicken, black beans, corn, cheddar, tomato and red onion over rice.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Chicken Bacon Black Bean Wrap", "salty-umami", "menu", "Chicken, bacon, black beans, cheddar, spinach and tomato.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "BLT Wrap", "salty-umami", "menu", "Bacon, romaine and tomato on spinach, wheat or white.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Ham & Cheese Wrap", "salty-sour", "menu", "Ham, cheddar, bacon, cabbage, tomato and pepperoncini.", "https://capeislandcafe.com/"),
    ("cape-island-cafe", "Honey Mustard (on a build-your-own plate)", "sour-sweet", "menu", "A dressing option on the build-your-own lunch plate.", "https://capeislandcafe.com/"),

    # ---- Water Street Kitchen (Toast menu, 2026-11-23) ----
    ("water-street-kitchen", "Rosemary Focaccia", "salty", "menu", "Whipped ricotta, rosemary oil and smoked salt.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Key Lime Custard", "sour-sweet", "menu", "Toasted meringue, graham crumble and candied lime.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Chocolate Basque Cheesecake", "bitter-sweet", "menu", "With hazelnut, orange and pink peppercorn.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Apple Almond Tart", "salty-sweet-umami", "menu", "Miso cashew brittle, ginger and maple butter glaze.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Miso Eggplant", "sour-umami", "menu", "Scallion, sesame and lemon.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Smoked Bluefish Pâté", "salty-sour-umami", "menu", "Served with house beer mustard, pickles and crostini.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Water Street Burger", "salty-sour-sweet-umami", "menu", "Braised short rib, smoked gouda and roasted tomato on a potato bun with aioli, togarashi fries and a pickle.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Cioppino", "salty-sour-umami", "menu", "Lobster, littlenecks, mussels and cod in tomato-fennel broth, with squid-ink bread.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Grilled Sippewissett Oysters", "salty-sour-umami", "menu", "Duck crackling, scallion and pickled ginger.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Scottish Salmon", "sour-sweet-umami", "menu", "Braised beets, roasted shallots, blood orange and herb crème fraîche.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Long Island Duck Breast and Leg", "bitter-sweet-umami", "menu", "Butternut squash purée, grilled red cabbage, rosemary pecan granola and cider reduction.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Black Bass Tempura", "sour-sweet-umami", "menu", "Coconut nuoc cham, eggplant, sweet pepper, cherry tomato, Thai basil and cilantro.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "NY Strip Steak", "salty-sweet-umami", "menu", "Jasmine rice cake, grilled pepper, baby bok choy, sesame, peanut and sweet soy demi.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Curry Roasted Spaghetti Squash", "bitter-sour-sweet-umami", "menu", "Chana masala, green tomato apple chutney, broccolini, spiced cashews and cilantro.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),
    ("water-street-kitchen", "Pan Roasted Cod", "bitter-salty-umami", "menu", "Confit fingerling potato, bacon-braised kale and yellow pepper purée.", "https://order.toasttab.com/online/water-street-kitchen-56-water-street"),

    # ---- The Captain Kidd (thecaptainkidd.com/menus, 2026-11-23) ----
    ("the-captain-kidd", "New England Clam Chowder", "salty-umami", "menu", "The house chowder, cup or bowl.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Today's Oyster Selection", "salty-sour", "menu", "Shucked to order with black pepper mignonette, lemon and cocktail sauce.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Traditional Cape Cod Lobster Roll", "salty-sour-umami", "menu", "Lemon mayo and Boston bibb lettuce on a brioche, with fries or chips.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Classic Fish n' Chips", "salty-sour", "menu", "Cod with fries and slaw.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Stuffed Quahog", "salty-umami", "menu", "Local hard-shell clam with linguica, drawn butter and lemon.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Fried Calamari", "salty-sour", "menu", "With cherry pepper and roasted red pepper aioli.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Shredded Kale salad", "bitter-salty-sour", "menu", "Almond, shaved Parmesan and lemon vinaigrette.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Seasonal Salad", "bitter-sour-sweet", "menu", "Arugula, quinoa, red and yellow beets, candied walnut, goat cheese and balsamic vinaigrette.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Crispy Brussels Sprouts", "bitter-salty", "menu", "With a Parmesan dipping sauce.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Pretzel Bites", "salty", "menu", "Beer cheese and stone-ground mustard.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Waldorf Chicken Salad sandwich", "sweet", "menu", "Chicken, mayo, walnut, apple and cranberry on sourdough.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Cape Cod Reuben", "salty-sour-umami", "menu", "Fried cod, Swiss, slaw and thousand island on marble rye.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "French Onion soup", "salty-sweet-umami", "menu", "With crostini and Swiss.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Crab Cakes", "sour-sweet-umami", "menu", "Pineapple salsa, roasted red pepper aioli and arugula.", "https://www.thecaptainkidd.com/menus"),
    ("the-captain-kidd", "Caesar Salad", "bitter-salty-sour-umami", "menu", "Homemade baked crouton, Parmesan and Caesar dressing.", "https://www.thecaptainkidd.com/menus"),

    # ---- Shuckers (shuckerswoodshole.com 2026 all-day menu) ----
    ("shuckers-world-famous-raw-bar", "Oysters, shucked to order", "salty", "menu", "Daily selection from the raw bar, served chilled.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Shuckers Sampler", "salty", "menu", "Two oysters, two littlenecks, two cherrystones and two shrimp.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Murph's Famous Baked Stuffed Scrod", "salty-umami", "menu", "Cod baked with lobster stuffing, finished with beurre blanc. Featured on Diners, Drive-Ins and Dives.", "https://www.shuckerswoodshole.com/"),
    ("shuckers-world-famous-raw-bar", "Cape Spinach salad", "bitter-sour-sweet", "menu", "Baby spinach, cranberries, almonds, goat cheese, red onion and tomatoes with apple vinaigrette.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Bang Bang Shrimp", "sour-sweet", "menu", "Crispy shrimp in spicy bang bang sauce with scallions.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Ahi Tuna Nachos", "salty-sweet-umami", "menu", "Wonton crisps with ahi tuna, avocado, jalapeño, scallions, spicy mayo and a sweet soy glaze.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Tuna Poke Bowl", "salty-umami", "menu", "Ahi tuna over sushi rice with seaweed salad, avocado, edamame and a garlic-soy drizzle.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Lobster Stuffed Avocado", "sour-umami", "menu", "Avocado filled with lobster salad and cilantro-lime aioli.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Sushi Oysters", "salty-sour-umami", "menu", "Six oysters crowned with tuna sashimi and a soy-ginger mignonette.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "New England Clam Chowder", "salty-umami", "menu", "The homemade classic, served in a mug.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Cape Cod Reuben", "salty-sour-umami", "menu", "Fried cod, Swiss and Thousand Island on marble rye.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),
    ("shuckers-world-famous-raw-bar", "Steamed Lobster dinner", "salty-sweet-umami", "menu", "Native lobster with mussels, potato, corn and drawn butter.", "https://www.shuckerswoodshole.com/Menus/2026_Menus/Shuckers_2026_All_Day_Menu.pdf"),

    # ---- Quicks Hole Taqueria (quicksholetaqueria.com/menu, 2026-11-23) ----
    ("quicks-hole-taqueria", "The Original Lobster Taco", "salty-sour-umami", "menu", "Cabbage, pico de gallo, queso fresco and Baja sauce — the taco they are known for.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Wicked Fresh Salad", "bitter-sour", "menu", "Chopped kale, red quinoa, black beans, pickled red onion, corn, queso fresco and cumin-lime vinaigrette.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Fish & Chips", "salty-sour", "menu", "Fried beer-battered cod with cole slaw and tartar sauce.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Lobster Roll", "sour-umami", "menu", "Lobster salad, bibb lettuce, toasted oversized roll and a lemon wedge.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Sweet Pork taco", "sweet", "menu", "Slow-roasted sweet pork as a taco filling, from the official taco list.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Churro Bites", "sweet", "menu", "A dessert on the official menu.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Quicks Mex Salad", "salty-sour", "menu", "Romaine, black beans, corn, tomato, poblano, red onion, cheeses, tortilla chips and Quicks ranch.", "https://quicksholetaqueria.com/menu"),
    ("quicks-hole-taqueria", "Blackened Mahi Mahi Sandwich", "salty-sour", "menu", "Tomato jalapeño relish, bibb lettuce, tomato, red onion and garlic aioli.", "https://quicksholetaqueria.com/menu"),

    # ---- Landfall (landfallwoodshole.com/menu/dinner, 2026-11-23) ----
    ("landfall-restaurant", "Boiled Lobster", "salty-umami", "menu", "A classic boiled lobster dinner, served with Portuguese toast and garlic butter.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Savannah Lobster", "salty-sweet-umami", "menu", "Lobster stuffed with lobster, mushrooms and shallots in a Jarlsberg sherried cream sauce.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Broiled Scrod with cranberry chutney", "salty-sweet", "menu", "Broiled scrod with seasoned crumbs, finished with cranberry chutney (or lobster sauce).", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Broiled or Fried Scallops", "salty-sour-umami", "menu", "The broiled version is served with roasted tomatoes, feta and black olives.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Seafood Newburg", "salty-sweet-umami", "menu", "Lobster, shrimp, scallops and swordfish in a creamed sherry sauce over linguine.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Fried Fisherman’s Platter", "salty", "menu", "Fried scallops, scrod, clams and shrimp.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Chicken Francaise", "sour-umami", "menu", "Battered chicken sautéed with lemon, white wine, tomatoes and mushrooms over linguine.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Filet Mignon", "salty-umami", "menu", "Tenderloin with sautéed mushrooms and a demi-glaze.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Steak Tips", "salty-sweet-umami", "menu", "Bourbon-marinated sirloin medallions, from the lighter-side list.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Fish & Chips w/Cole Slaw", "salty-sour", "menu", "From the lighter-side dinner list.", "https://www.landfallwoodshole.com/menu/dinner/"),
    ("landfall-restaurant", "Lobster Roll", "salty-umami", "menu", "From the lighter-side dinner list.", "https://www.landfallwoodshole.com/menu/dinner/"),

    # ---- Pie in the Sky (piecoffee.com official site copy) ----
    ("pie-in-the-sky-bakery-and-cafe", "A slice of house-baked pie", "sweet", "menu", "Handmade pies are a headline item on the bakery's official site.", "https://www.piecoffee.com/"),
    ("pie-in-the-sky-bakery-and-cafe", "Housemade lemonade", "sour-sweet", "menu", "Named on the official site among house drinks.", "https://www.piecoffee.com/"),
    ("pie-in-the-sky-bakery-and-cafe", "House-roasted espresso or coffee", "bitter", "menu", "Coffees, espresso and nitro cold brew are roasted in house — a core offering on the official site.", "https://www.piecoffee.com/"),
    ("pie-in-the-sky-bakery-and-cafe", "Homemade chowder or soup", "salty-umami", "menu", "The official site lists homemade soups and chowders with sandwiches and quiche.", "https://www.piecoffee.com/"),
    ("pie-in-the-sky-bakery-and-cafe", "Butter croissant", "salty-sweet", "menu", "Handmade croissants are listed on the official site. Butter and pastry sweetness, with a salted crust.", "https://www.piecoffee.com/"),

    # ---- Coffee Obsession ----
    ("coffee-obsession-woods-hole", "Espresso", "bitter", "menu", "Espresso and coffee are the core offering advertised on the shop's official site.", "https://www.coffeeobsession.com/"),
    ("coffee-obsession-falmouth", "Espresso", "bitter", "menu", "Espresso and coffee are the core offering advertised on the shop's official site.", "https://www.coffeeobsession.com/"),
    ("coffee-obsession-woods-hole", "A sweet café drink (latte or mocha)", "bitter-sweet", "suggested", "A typical espresso-bar drink here; confirm the current board for the exact name.", "https://www.coffeeobsession.com/"),

    # ---- Añejo (anejo.cc dinner menu, 2026-11-23) ----
    ("anejo-mexican-bistro", "Guacamole", "salty-sour", "menu", "Listed under antojitos; add bacon if you want more salt and umami.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Spicy Fried Pickles", "sour", "menu", "House-made fried pickles with chipotle ranch.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Main Street Corn", "salty-sour-sweet", "menu", "Grilled corn, garlic-chili aioli, cotija and grilled lime.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Mango Habanero Bang Bang Shrimp", "sour-sweet", "menu", "With mango-cucumber pico, radish, bibb lettuce, cabbage and cilantro aioli.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Añejo Wings with sweet agave mole", "bitter-sweet-umami", "menu", "The sweet agave mole option, with almonds and cilantro. Contains nuts.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Chipotle Stung Lobster Bisque", "salty-sweet-umami", "menu", "With grilled corn-poblano pico and tortilla hay.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Shrimp & Avocado salad", "sour-sweet-umami", "menu", "Spiced grilled shrimp, mixed greens, avocado, mango, pickled red onion, pepitas and coconut lime dressing.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Verde Rice Bowl", "salty-sour-sweet-umami", "menu", "Verde rice, pineapple, rajas, black beans, avocado, pico, pickled onions and grilled lime.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Poblano Mole Enchiladas", "bitter-salty-sweet-umami", "menu", "Ancho-braised chicken or chipotle-braised beef with mole poblano, Oaxaca-jack and sour cream. Contains nuts.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Coliflor Frita tacos", "bitter-salty-sour-sweet", "menu", "Crispy buffalo cauliflower, blue cheese, onion, cilantro and golden raisins on house corn tortillas.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Steak Ranchero", "bitter-salty-sour-sweet-umami", "menu", "Coffee-chile rubbed strip sirloin, charro beans, chile lime fries, chimichurri and salsa roja — a rare all-five plate from a published menu.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Tijuana Caesar", "bitter-salty-sour-umami", "menu", "Romaine, tortilla hay, house Caesar, black beans, tomato-corn pico and cotija.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Churros & Chocolate", "bitter-sweet", "menu", "From the dessert list.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Pork Carnitas tacos", "salty-sour-umami", "menu", "Slow-roasted pork, house corn tortillas, Oaxaca-jack, salsa verde, onion, cotija and cilantro.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),
    ("anejo-mexican-bistro", "Pollo Elotes tacos", "salty-sweet-umami", "menu", "Chicken al pastor, poblano-corn pico, cumin-chili aioli, Oaxaca-jack and cotija.", "https://www.anejo.cc/menus?menu=new-dinner-menu"),

    # ---- Woods Hole Market & Maison Villatte WH ----
    ("woods-hole-market", "Lobster roll", "salty-umami", "menu", "Lobster rolls are listed among the market's prepared foods on its official site and the Woods Hole village eat guide.", "https://www.woodsholemarket.com/"),
    ("woods-hole-market", "A scoop of ice cream", "sweet", "suggested", "Ice cream is mentioned in village guides; confirm the case for today's flavors.", "https://www.woodsholemarket.com/"),
    ("maison-villatte-woods-hole", "Butter croissant or morning pastry", "sweet", "suggested", "Typical of this French bakery's case; confirm today's bake board.", ""),
    ("maison-villatte-woods-hole", "Jambon-beurre on a baguette", "salty-umami", "suggested", "A classic ham-and-butter baguette, in the style this bakery is known for. Confirm it is on today's board.", ""),
    ("maison-villatte", "Butter croissant or morning pastry", "sweet", "suggested", "Typical of the Main Street bakery case; confirm today's bake board.", ""),
    ("maison-villatte", "A dark chocolate pastry or tart", "bitter-sweet", "suggested", "A likely case item at a French pâtisserie. Confirm today's bake board.", ""),

    # ---- Other Falmouth / Woods Hole, clearly suggested unless noted ----
    ("quahog-republic-leeside-pub", "A cup of clam chowder", "salty-umami", "suggested", "A typical Woods Hole pub bowl; confirm the current Leeside menu.", "https://www.quahogrepublic.com/leeside"),
    ("quahog-republic-leeside-pub", "Fish and chips", "salty-sour", "suggested", "A typical pub plate with slaw or malt vinegar. Confirm the current menu.", "https://www.quahogrepublic.com/leeside"),
    ("pickle-jar-kitchen", "A breakfast plate with pickles or a tangy side", "sour", "suggested", "The kitchen's name hints at a sour streak; confirm today's brunch board at picklejarkitchen.com.", "https://picklejarkitchen.com"),
    ("pickle-jar-kitchen", "Pancakes or a sweet brunch plate", "sweet", "suggested", "Typical of this breakfast-and-lunch kitchen. Confirm today's menu.", "https://picklejarkitchen.com"),
    ("osteria-la-civetta", "Handmade pasta with Parmesan", "salty-umami", "suggested", "This osteria is known for handmade pasta. Confirm the current menu at osterialacivetta.com.", "https://www.osterialacivetta.com/"),
    ("osteria-la-civetta", "Tiramisu or a bitter-sweet dessert", "bitter-sweet", "suggested", "A classic Italian finish; confirm it is on tonight's dessert list.", "https://www.osterialacivetta.com/"),
    ("osteria-la-civetta", "A bitter-greens salad (radicchio or arugula)", "bitter", "suggested", "A typical osteria starter. Confirm the current antipasti.", "https://www.osterialacivetta.com/"),
    ("la-cucina-sul-mare", "A lemony seafood pasta", "sour-umami", "suggested", "In the style of this Italian seafood kitchen. Confirm the current menu.", "https://www.lacucinasulmare.com/"),
    ("la-cucina-sul-mare", "An anchovy or puttanesca-style pasta", "bitter-salty-umami", "suggested", "A typical Italian savory-bitter plate if it is on the menu. Confirm tonight's list.", "https://www.lacucinasulmare.com/"),
    ("liam-maguires-irish-pub", "Fish and chips with malt vinegar", "salty-sour", "suggested", "A classic Irish-pub plate. Confirm the current menu at liammaguire.com.", "https://liammaguire.com/"),
    ("liam-maguires-irish-pub", "Shepherd's pie", "salty-umami", "suggested", "A typical pub main. Confirm the current menu.", "https://liammaguire.com/"),
    ("liam-maguires-irish-pub", "A pint of stout", "bitter", "suggested", "If you drink alcohol: a dry stout is a clean bitter tasting. Skip if you prefer not to.", "https://liammaguire.com/"),
    ("cafe-grounded", "A black coffee", "bitter", "suggested", "A straightforward bitter tasting at this café. Confirm the current drink list.", "http://cafe-grounded.com/"),
    ("golden-swan-indian-cuisine", "Mango lassi", "sour-sweet", "suggested", "A typical Indian-restaurant yogurt drink. Confirm it is offered.", ""),
    ("golden-swan-indian-cuisine", "A mixed grill or tikka with chutney", "salty-sour-sweet-umami", "suggested", "Tandoori spice, yogurt tang, chutney sweetness and savory meat — confirm today's menu.", ""),
    ("golden-swan-indian-cuisine", "Saag or palak with bitter greens", "bitter-umami", "suggested", "A spinach or mustard-green curry, if it is on the menu.", ""),
    ("tiger-ramen", "A bowl of tonkotsu or shoyu ramen", "salty-umami", "suggested", "Typical of a ramen shop. Confirm the current bowls at tigerramencapecod.com.", "https://www.tigerramencapecod.com/"),
    ("tiger-ramen", "Ramen with extra lime, greens and a sweet finish (corn or tare)", "bitter-salty-sour-sweet-umami", "suggested", "A composed ramen can reach all five tastes if you add greens and citrus. Confirm toppings on the current menu.", "https://www.tigerramencapecod.com/"),
    ("doggz-and-hoggz", "Pulled pork with vinegar slaw and sauce", "salty-sour-sweet-umami", "suggested", "A typical BBQ plate. Confirm today's meats and sauces at doggzhoggz.com.", "https://www.doggzhoggz.com/"),
    ("doggz-and-hoggz", "A burnt-end or barky rib with sauce", "bitter-salty-sweet-umami", "suggested", "Bark brings bitter; sauce brings sweet. Confirm today's pit list.", "https://www.doggzhoggz.com/"),
    ("taco-blanco", "A salsa-heavy taco with lime", "salty-sour-umami", "suggested", "Typical of this taqueria. Confirm the current taco list at tacoblanco.cc.", "https://www.tacoblanco.cc/"),
    ("betsys-diner", "A short stack of pancakes", "sweet", "suggested", "A classic diner breakfast. Confirm today's breakfast menu.", ""),
    ("betsys-diner", "A diner cheeseburger with pickle", "salty-sour-umami", "suggested", "A typical diner burger. Confirm the current menu.", ""),
    ("persys-place", "A sweet breakfast plate (pancakes or French toast)", "sweet", "suggested", "Persy's is known for large breakfast plates. Confirm today's menu at persysplace.com.", "https://persysplace.com/"),
    ("asia-restaurant", "Sweet-and-sour pork or chicken", "sour-sweet", "suggested", "A typical Chinese-restaurant classic. Confirm it is on asiafalmouth.com.", "https://www.asiafalmouth.com/"),
    ("asia-restaurant", "A soy-forward stir-fry", "salty-umami", "suggested", "Typical of the house. Confirm the current menu.", "https://www.asiafalmouth.com/"),
    ("thai-kitchen", "Pad Thai", "bitter-salty-sour-sweet-umami", "suggested", "Classic pad Thai is often cited as a five-taste dish (tamarind, fish sauce, sugar, lime, and a bitter edge from lime rind or Chinese broccoli). Confirm it is on thaikitchenma.com.", "https://www.thaikitchenma.com/"),
    ("thai-kitchen", "Tom yum soup", "sour-umami", "suggested", "A typical hot-and-sour Thai soup. Confirm the current menu.", "https://www.thaikitchenma.com/"),
    ("thai-kitchen", "Green papaya salad (som tum), if offered", "bitter-salty-sour-sweet", "suggested", "A classic four-to-five-taste salad. Confirm it is on the menu before you go.", "https://www.thaikitchenma.com/"),
    ("sweet-rice", "A sweet-savory rice or noodle bowl", "salty-sweet-umami", "suggested", "In the style of this Teaticket Asian kitchen. Confirm the current menu at sweetricecapecod.com.", "https://www.sweetricecapecod.com/"),
    ("smittys-homemade-ice-cream", "A scoop of a sweet house flavor", "sweet", "suggested", "A straightforward sweet tasting. Confirm today's board at smittysicecreamcapecod.com.", "https://smittysicecreamcapecod.com/"),
    ("smittys-homemade-ice-cream", "Salted caramel or sweet-and-salty flavor, if on the board", "salty-sweet", "suggested", "Only if that flavor is actually on today's board.", "https://smittysicecreamcapecod.com/"),
    ("holy-cow-ice-cream-cafe", "A scoop of a sweet house flavor", "sweet", "suggested", "Confirm today's board at holycowicecreamcafe.com.", "https://holycowicecreamcafe.com/"),
    ("holy-cow-ice-cream-cafe", "Coffee or mocha ice cream, if on the board", "bitter-sweet", "suggested", "Only if a coffee flavor is actually being scooped today.", "https://holycowicecreamcafe.com/"),
    ("epic-oyster", "Oysters on the half shell with lemon or mignonette", "salty-sour", "suggested", "The natural tasting at an oyster bar. Confirm the current raw-bar card at eatepicoyster.com.", "https://www.eatepicoyster.com/"),
    ("epic-oyster", "A plain oyster, no sauce", "salty", "suggested", "The cleanest salty tasting — just seawater and shell.", "https://www.eatepicoyster.com/"),
    ("flying-bridge-restaurant", "A lobster roll", "salty-umami", "suggested", "A typical harbor-front order. Confirm the current menu at flyingbridgerestaurant.com.", "https://flyingbridgerestaurant.com/"),
    ("jims-clam-shack", "Fried whole-belly clams", "salty-umami", "suggested", "A Falmouth Harbor classic when the shack is open. Confirm seasonal hours.", ""),
    ("seafood-sams", "Fried clams or a fish sandwich", "salty", "suggested", "Typical of this casual seafood counter. Confirm today's board.", ""),
    ("the-black-dog-heights-cafe", "A Black Dog muffin or sweet baked good", "sweet", "suggested", "A typical café counter item. Confirm today's bake case.", "https://theblackdog.com/pages/heights-cafe-falmouth"),
    ("the-black-dog-heights-cafe", "Chowder, if offered", "salty-umami", "suggested", "Confirm the current café menu.", "https://theblackdog.com/pages/heights-cafe-falmouth"),
    ("the-buffalo-jump-at-coonamessett-farm", "A farm salad with bitter greens", "bitter", "suggested", "A likely plate at this farm café. Confirm the current menu at thebuffalojumpfalmouth.com.", "https://thebuffalojumpfalmouth.com/"),
    ("the-buffalo-jump-at-coonamessett-farm", "A dish using farm produce with a vinaigrette", "bitter-sour", "suggested", "Confirm today's board — this changes with the farm.", "https://thebuffalojumpfalmouth.com/"),
    ("chapoquoit-grill", "A bistro steak or mushroom plate", "salty-umami", "suggested", "In the style of this West Falmouth American grill. Confirm the current menu.", "https://www.chapoquoitgrillwestfalmouth.com/"),
    ("the-glass-onion", "A composed seasonal entrée", "salty-sour-sweet-umami", "suggested", "This New American kitchen often builds complex plates. Confirm tonight's menu before you go — it changes.", ""),
    ("bucatino-restaurant-and-wine-bar", "A bitter-greens side or pasta (broccoli rabe, radicchio)", "bitter-umami", "suggested", "Typical of an Italian wine bar. Confirm the current menu at bucawinebar.com.", "https://www.bucawinebar.com/"),
    ("little-rossa", "A salty-savory pizza (pepperoni, olive, or anchovy)", "salty-umami", "suggested", "Confirm today's pies at littlerossa.com.", "https://littlerossa.com/"),
    ("little-rossa", "A pizza with hot honey, if offered", "salty-sweet", "suggested", "Only if a sweet-hot drizzle is on the current menu.", "https://littlerossa.com/"),
    ("tap-city-grille", "A pub burger with pickle and cheese", "salty-sour-umami", "suggested", "A typical grille burger. Confirm the Falmouth menu at tapcitygrille.com.", "https://www.tapcitygrille.com/falmouth"),
    ("daily-brew-coffee-house-and-lounge", "A black coffee or espresso", "bitter", "suggested", "A straightforward bitter tasting. Confirm the current drink list.", ""),
    ("mary-ellens-portuguese-bakery", "A sweet malasada or pastry, if offered", "sweet", "suggested", "Typical of a Portuguese bakery case. Confirm today's bake.", ""),
    ("cape-cod-bagel-co", "A salted bagel with cream cheese", "salty", "suggested", "A simple salty tasting. Confirm today's bagel board.", ""),
    ("moonakis-cafe", "A sweet breakfast plate", "sweet", "suggested", "Typical of this Waquoit breakfast café. Confirm today's menu at moonakiscafe.com.", "https://moonakiscafe.com/"),
    ("the-lantern-room", "A composed seafood plate", "salty-umami", "suggested", "Confirm the current North Falmouth menu at lanternroomcapecod.com.", "https://www.lanternroomcapecod.com/"),
    ("falmouth-raw-bar", "Oysters or littlenecks with lemon", "salty-sour", "suggested", "The point of a raw bar. Confirm the current card at falmouthrawbar.com.", "https://www.falmouthrawbar.com/"),
    ("green-pond-fish-market", "A lobster roll or fried seafood plate, if the market is serving", "salty-umami", "suggested", "Confirm they are serving prepared food today at greenpondfish.com.", "https://www.greenpondfish.com/"),
    ("casa-vallarta", "A salsa-and-lime taco or enchilada plate", "salty-sour-umami", "suggested", "Typical of this Mexican restaurant. Confirm the current menu at casavallarta.us.", "https://www.casavallarta.us/"),
    ("devour-eatery", "A composed sandwich with a tangy slaw or pickle", "salty-sour", "suggested", "In the style of this Main Street lunch counter. Confirm today's menu at devoureatery.com.", "https://www.devoureatery.com/"),
    ("bourbon-and-butter-sugar-shed", "A sweet bakery treat", "sweet", "suggested", "A sugar-shed tasting. Confirm today's case at bourbonbutterbakingco.com.", "https://www.bourbonbutterbakingco.com/"),
    ("djs-famous-wings-family-sports-pub", "Wings with a buffalo or vinegary sauce", "salty-sour", "suggested", "Confirm sauces on the current menu at djsfamouswings.com.", "https://djsfamouswings.com/"),
    ("djs-famous-wings-family-sports-pub", "Wings with a sweet glaze (BBQ or honey)", "salty-sweet", "suggested", "Only if that sauce is on the board today.", "https://djsfamouswings.com/"),
    ("tiger-ramen", "Miso soup, if offered as a side", "umami", "suggested", "Miso is a textbook umami tasting (it will also taste salty). Confirm it is on the current menu.", "https://www.tigerramencapecod.com/"),
    ("osteria-la-civetta", "A mushroom antipasto or a bite of aged Parmesan, if offered", "umami", "suggested", "Mushrooms and aged cheese are clean umami tastings. Confirm the current antipasti.", "https://www.osterialacivetta.com/"),
    ("chapoquoit-grill", "Sauteed mushrooms, if offered as a side", "umami", "suggested", "A simple mushroom saute is a clean umami tasting. Confirm tonight's sides.", "https://www.chapoquoitgrillwestfalmouth.com/"),
]

def build_dishes(rests):
    by_id = {r["id"]: r for r in rests}
    dishes = []
    missing = []
    for i, (rid, dish, combo, source, note, url) in enumerate(DISHES, 1):
        if rid not in by_id:
            missing.append(rid)
            continue
        r = by_id[rid]
        dishes.append({
            "id": f"{rid}-{i}",
            "restaurantId": rid,
            "restaurantName": r["name"],
            "town": r["town"],
            "area": r["area"],
            "category": r["category"],
            "website": r["website"],
            "dish": dish,
            "comboId": combo,
            "source": source,  # menu | suggested
            "note": note,
            "sourceUrl": url,
            "checkedOn": CHECKED,
            "featured": bool(r.get("featured")),
        })
    if missing:
        raise SystemExit("Unknown restaurant ids: " + ", ".join(sorted(set(missing))))
    return dishes

def coverage(combos, dishes):
    have = {c["id"]: [] for c in combos}
    for d in dishes:
        have[d["comboId"]].append(d)
    missing = [i for i, v in have.items() if not v]
    return have, missing

def write_csv(path: Path, rests, dishes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["restaurant_id","restaurant_name","town","area","category","address","phone","website",
              "dish","combo_id","combo_name","source","note","source_url","checked_on","featured"]
    combo_name_map = {c["id"]: c["name"] for c in build_combos()}
    by = {r["id"]: r for r in rests}
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in dishes:
            r = by[d["restaurantId"]]
            w.writerow({
                "restaurant_id": d["restaurantId"],
                "restaurant_name": d["restaurantName"],
                "town": d["town"],
                "area": d["area"],
                "category": d["category"],
                "address": r["address"],
                "phone": r["phone"],
                "website": d["website"],
                "dish": d["dish"],
                "combo_id": d["comboId"],
                "combo_name": combo_name_map.get(d["comboId"], d["comboId"]),
                "source": d["source"],
                "note": d["note"],
                "source_url": d["sourceUrl"],
                "checked_on": d["checkedOn"],
                "featured": "yes" if d["featured"] else "",
            })

def main():
    combos = build_combos()
    rests = load_restaurants()
    dishes = build_dishes(rests)
    have, missing = coverage(combos, dishes)
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    (data / "tastes.json").write_text(json.dumps(TASTES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "combos.json").write_text(json.dumps(combos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "restaurants.json").write_text(json.dumps(rests, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (data / "dishes.json").write_text(json.dumps(dishes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_csv(data / "play-request-restaurants-dishes.csv", rests, dishes)
    print(f"restaurants {len(rests)} (Woods Hole {sum(1 for r in rests if r['town']=='Woods Hole')}, Falmouth {sum(1 for r in rests if r['town']=='Falmouth')})")
    print(f"dishes {len(dishes)}  menu={sum(1 for d in dishes if d['source']=='menu')}  suggested={sum(1 for d in dishes if d['source']=='suggested')}")
    print(f"combos {len(combos)}  missing dish coverage: {missing or 'none'}")
    for c in combos:
        n = len(have[c["id"]])
        m = sum(1 for d in have[c["id"]] if d["source"]=="menu")
        print(f"  L{c['level']} {c['id']:36} {n:2} dishes ({m} from menu)")

if __name__ == "__main__":
    main()
