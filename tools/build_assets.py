#!/usr/bin/env python3
"""Build favicons, OG image, and the printable board-game PDF."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

ROOT = Path(__file__).resolve().parents[1]
BARLOW = "/usr/share/fonts/truetype/sand-box/google/Barlow/Barlow-Regular.ttf"
BARLOW_B = "/usr/share/fonts/truetype/sand-box/google/Barlow/Barlow-Bold.ttf"
COND_B = "/usr/share/fonts/truetype/sand-box/google/Barlow Condensed/BarlowCondensed-Bold.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"

CHAR = (27, 30, 35)
SUN = (253, 203, 46)
GOLD = (189, 131, 34)
CREAM = (251, 248, 241)
TASTE_C = {
    "sweet": (226, 93, 122), "sour": (124, 179, 66), "salty": (58, 124, 165),
    "bitter": (107, 58, 160), "umami": (192, 96, 58),
}
TASTE_HEX = {"sweet": "#e25d7a", "sour": "#7cb342", "salty": "#3a7ca5", "bitter": "#6b3aa0", "umami": "#c0603a"}
BLURBS = {
    "sweet": "Honey, ripe fruit, sugar. The taste that rounds a dish.",
    "sour": "Lemon, vinegar, fermentation. The taste that wakes everything up.",
    "salty": "Sea, soy, cheese. The taste that makes food taste like itself.",
    "bitter": "Coffee, dark greens, cocoa. The grown-up edge of flavor.",
    "umami": "Broth, mushroom, tomato, aged cheese. The deep, savory taste.",
}

def font(path, size):
    return ImageFont.truetype(path, size)

def circle_mark(size, text="PR"):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, size - 3, size - 3), fill=SUN + (255,), outline=GOLD + (255,), width=max(2, size // 18))
    f = font(SERIF_B, int(size * 0.38))
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - size * 0.02), text, font=f, fill=CHAR + (255,))
    return im

def wrap_text(text, font_name, size, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if stringWidth(trial, font_name, size) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [""]

def build_images():
    (ROOT / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<circle cx="32" cy="32" r="30" fill="#fdcb2e" stroke="#bd8322" stroke-width="3"/>'
        '<text x="32" y="40" text-anchor="middle" font-family="Georgia, serif" font-weight="700" font-size="22" fill="#1b1e23">PR</text>'
        "</svg>\n"
    )
    for name, size in [("favicon-32.png", 32), ("apple-touch-icon.png", 180), ("icons/icon-192.png", 192), ("icons/icon-512.png", 512)]:
        (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
        circle_mark(size).convert("RGB").save(ROOT / name, "PNG")

    og = Image.new("RGB", (1200, 630), CHAR)
    d = ImageDraw.Draw(og)
    d.rectangle((0, 0, 1200, 8), fill=SUN)
    for i, t in enumerate(["sweet", "sour", "salty", "bitter", "umami"]):
        d.ellipse((70 + i * 70, 80, 106 + i * 70, 116), fill=TASTE_C[t])
    mark = circle_mark(160)
    og.paste(mark, (980, 70), mark)
    d.text((70, 140), "PLAY REQUEST", font=font(COND_B, 96), fill=SUN)
    d.text((70, 250), "Taste your way up.", font=font(SERIF_I, 48), fill=CREAM)
    d.text((70, 340), "31 combinations of sweet, sour, salty,", font=font(BARLOW, 32), fill=(207, 202, 190))
    d.text((70, 384), "bitter and umami. Falmouth & Woods Hole.", font=font(BARLOW, 32), fill=(207, 202, 190))
    d.rectangle((70, 470, 420, 478), fill=GOLD)
    d.text((70, 500), "platinum00001.github.io/play-request", font=font(BARLOW_B, 26), fill=SUN)
    og.save(ROOT / "og.jpg", "JPEG", quality=90)

def dashed_rect(c, x, y, w, h):
    c.saveState()
    c.setDash(3, 3)
    c.setStrokeColor(HexColor("#bd8322"))
    c.setLineWidth(0.6)
    c.rect(x, y, w, h, fill=0, stroke=1)
    c.restoreState()

def build_pdf():
    pdfmetrics.registerFont(TTFont("Barlow", BARLOW))
    pdfmetrics.registerFont(TTFont("Barlow-Bold", BARLOW_B))
    pdfmetrics.registerFont(TTFont("Cond-Bold", COND_B))
    pdfmetrics.registerFont(TTFont("Serif", SERIF))
    pdfmetrics.registerFont(TTFont("Serif-Bold", SERIF_B))
    pdfmetrics.registerFont(TTFont("Serif-Italic", SERIF_I))

    combos = json.loads((ROOT / "data/combos.json").read_text())
    dishes = json.loads((ROOT / "data/dishes.json").read_text())
    combo_name = {x["id"]: x["name"] for x in combos}
    picked, seen = [], set()
    for src in ("menu", "suggested"):
        for d in dishes:
            if d["source"] != src:
                continue
            key = (d["restaurantId"], d["dish"])
            if key in seen:
                continue
            seen.add(key)
            picked.append(d)
    picked = picked[:48]

    pdf_path = ROOT / "play-request-board-game.pdf"
    c = canvas.Canvas(str(pdf_path), pagesize=letter)
    W, H = letter
    CHAR_c = HexColor("#1b1e23")
    NAVY_c = HexColor("#0b1a3b")
    SUN_c = HexColor("#fdcb2e")
    GOLD_c = HexColor("#bd8322")
    CREAM_c = HexColor("#fbf8f1")
    INK = HexColor("#1d2433")

    def foot(label, width=None):
        width = width or W
        c.setFillColor(GOLD_c)
        c.rect(0, 0, width, 18, fill=1, stroke=0)
        c.setFillColor(CHAR_c)
        c.setFont("Barlow", 8)
        c.drawString(0.5 * inch, 5, "Play Request  ·  Falmouth & Woods Hole  ·  " + label)
        c.drawRightString(width - 0.5 * inch, 5, "platinum00001.github.io/play-request")

    # Cover
    c.setFillColor(CHAR_c)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(SUN_c)
    c.rect(0, H - 12, W, 12, fill=1, stroke=0)
    c.setFont("Cond-Bold", 16)
    c.drawString(0.75 * inch, H - 1.1 * inch, "A TASTING GAME")
    c.setFillColor(white)
    c.setFont("Serif-Bold", 36)
    c.drawString(0.75 * inch, H - 1.85 * inch, "Play Request")
    c.setFillColor(SUN_c)
    c.setFont("Serif-Italic", 18)
    c.drawString(0.75 * inch, H - 2.3 * inch, "Taste your way up.")
    c.setFillColor(HexColor("#cfcabe"))
    c.setFont("Barlow", 12)
    y = H - 3.05 * inch
    for line in [
        "Five basic tastes. Thirty-one combinations.",
        "Pick one flavor to start. A new combo opens when it",
        "extends any combo you have already tried by exactly",
        "one flavor. You can reach the Peak in five tastings —",
        "you do not have to fill every square.",
        "",
        "Play at the table with these cards, or play online at",
        "platinum00001.github.io/play-request",
        "",
        "Dishes marked From the menu use a published name",
        "(checked 23 November 2026, America/New York).",
        "Suggested items are ideas — confirm before you go.",
    ]:
        c.drawString(0.75 * inch, y, line)
        y -= 16
    for i, t in enumerate(["sweet", "sour", "salty", "bitter", "umami"]):
        c.setFillColor(HexColor(TASTE_HEX[t]))
        c.circle(1.0 * inch + i * 0.6 * inch, 2.15 * inch, 14, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Cond-Bold", 7)
        c.drawCentredString(1.0 * inch + i * 0.6 * inch, 1.6 * inch, t.upper())
    c.setFillColor(SUN_c)
    c.setFont("Barlow-Bold", 10)
    c.drawString(0.75 * inch, 0.85 * inch, "Print in color if you can. Cardstock is nicer for the cards.")
    c.showPage()

    # Rules
    c.setFillColor(CREAM_c)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY_c)
    c.setFont("Serif-Bold", 22)
    c.drawString(0.7 * inch, H - 0.7 * inch, "Rules")
    c.setStrokeColor(GOLD_c)
    c.setLineWidth(1.2)
    c.line(0.7 * inch, H - 0.82 * inch, 7.8 * inch, H - 0.82 * inch)
    blocks = [
        ("Players", "1-4 people, or a cooperative kitchen table. Solo play is fine."),
        ("Setup", "Give each player a tasting passport (last pages) and a pencil. Place the board in the middle. Shuffle the restaurant and dish cards. Leave the five flavor cards face up."),
        ("Start", "Each player picks one single flavor to begin (two players may pick the same one). Mark that single on your passport and on the board with your initial or a token."),
        ("Unlock rule", "A combo is open for you when it extends any combo you have already tried by exactly one flavor. All five singles are always open. You never need to fill a whole level to climb. Example: try Sweet, and every pair that includes Sweet opens. Try Sweet + Sour, and every trio that is Sweet + Sour + one more flavor opens."),
        ("A turn", "Do one of the following: (1) Taste an open combo you have not tried — play a matching dish card, name a real food, or go eat it. Mark it. Optionally rate it 1-5 and jot what you ate. (2) Draw two dish cards, keep one, discard the other. If the kept card's combo is already open for you, you may taste it immediately. (3) If you actually order a dish in that spirit at a listed restaurant, taste the combo."),
        ("Winning", "First player to taste The Peak (all five flavors in one dish) wins. Or play to a time limit and count unique combos. Or cooperate to open the whole board."),
        ("Honesty", "Suggested cards are ideas, not a promise the dish is on the menu today. If you play in a restaurant, be a good guest. Alcohol examples are optional. The unlock rule, the 31 spaces, and the local dishes match the online game."),
    ]
    y = H - 1.15 * inch
    for title, body in blocks:
        c.setFillColor(GOLD_c)
        c.setFont("Cond-Bold", 11)
        c.drawString(0.7 * inch, y, title.upper())
        y -= 14
        c.setFillColor(INK)
        c.setFont("Barlow", 10)
        for line in wrap_text(body, "Barlow", 10, 7.1 * inch):
            c.drawString(0.7 * inch, y, line)
            y -= 13
        y -= 8
    foot("Rules")
    c.showPage()

    # Board landscape
    LW, LH = landscape(letter)
    c.setPageSize((LW, LH))
    c.setFillColor(CREAM_c)
    c.rect(0, 0, LW, LH, fill=1, stroke=0)
    c.setFillColor(NAVY_c)
    c.setFont("Serif-Bold", 18)
    c.drawString(0.5 * inch, LH - 0.45 * inch, "The board — 31 combinations")
    c.setFont("Barlow", 9)
    c.setFillColor(INK)
    c.drawString(0.5 * inch, LH - 0.62 * inch, "Mark a square when you taste it. A new square opens when it adds exactly one flavor to something you already tried.")
    levels = {n: [x for x in combos if x["level"] == n] for n in range(1, 6)}
    rows = [
        (5, LH - 1.5 * inch, 2.2 * inch, 1.0 * inch),
        (4, LH - 2.65 * inch, 1.85 * inch, 0.92 * inch),
        (3, LH - 3.8 * inch, 0.98 * inch, 0.92 * inch),
        (2, LH - 4.95 * inch, 0.98 * inch, 0.92 * inch),
        (1, LH - 6.15 * inch, 1.6 * inch, 0.95 * inch),
    ]
    for lv, y, box_w, box_h in rows:
        items = levels[lv]
        n = len(items)
        gap = 0.07 * inch
        total = n * box_w + (n - 1) * gap
        x0 = (LW - total) / 2
        c.setFillColor(GOLD_c)
        c.setFont("Cond-Bold", 8)
        c.drawString(0.35 * inch, y + box_h / 2, "L" + str(lv))
        for i, combo in enumerate(items):
            x = x0 + i * (box_w + gap)
            c.setStrokeColor(GOLD_c)
            c.setLineWidth(1)
            c.setFillColor(white)
            c.roundRect(x, y, box_w, box_h, 5, fill=1, stroke=1)
            dots = combo["tastes"]
            gx = x + (box_w - (len(dots) * 11 - 3)) / 2
            for j, t in enumerate(dots):
                c.setFillColor(HexColor(TASTE_HEX[t]))
                c.circle(gx + j * 11 + 4, y + box_h - 11, 3.6, fill=1, stroke=0)
            if combo["level"] == 5:
                short = "THE PEAK"
                fsize = 9
            elif combo["level"] == 1:
                short = combo["name"]
                fsize = 10
            else:
                short = " + ".join(t[:2].upper() for t in combo["tastes"])
                fsize = 7 if lv >= 3 else 8
            c.setFillColor(NAVY_c)
            c.setFont("Cond-Bold", fsize)
            lines = wrap_text(short, "Cond-Bold", fsize, box_w - 8)
            ny = y + box_h - 26
            for line in lines[:3]:
                c.drawCentredString(x + box_w / 2, ny, line)
                ny -= 9
            c.setStrokeColor(GOLD_c)
            c.rect(x + box_w - 13, y + 6, 7, 7, fill=0, stroke=1)
    foot("Board — landscape; rotate or print two-sided as you like", LW)
    c.showPage()

    # Flavor cards (portrait, 5 mid-size cards)
    c.setPageSize(letter)
    W, H = letter
    c.setFillColor(CREAM_c)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(NAVY_c)
    c.setFont("Serif-Bold", 16)
    c.drawString(0.5 * inch, H - 0.5 * inch, "Flavor cards")
    c.setFont("Barlow", 9)
    c.setFillColor(INK)
    c.drawString(0.5 * inch, H - 0.68 * inch, "Cut on the dashed lines. Keep these face up on the table.")
    # layout: 3 on top, 2 centered below
    cw, ch = 2.4 * inch, 3.35 * inch
    tastes = ["sweet", "sour", "salty", "bitter", "umami"]
    positions = []
    gapx, gapy = 0.15 * inch, 0.18 * inch
    row1_w = 3 * cw + 2 * gapx
    x0 = (W - row1_w) / 2
    y1 = H - 0.9 * inch - ch
    for i in range(3):
        positions.append((x0 + i * (cw + gapx), y1, tastes[i]))
    row2_w = 2 * cw + gapx
    x1 = (W - row2_w) / 2
    y2 = y1 - gapy - ch
    for i in range(2):
        positions.append((x1 + i * (cw + gapx), y2, tastes[3 + i]))
    for x, y, t in positions:
        dashed_rect(c, x, y, cw, ch)
        c.setFillColor(HexColor(TASTE_HEX[t]))
        c.roundRect(x + 6, y + 6, cw - 12, ch - 12, 8, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Cond-Bold", 20)
        c.drawCentredString(x + cw / 2, y + ch / 2 + 10, t.upper())
        c.setFont("Barlow", 8)
        body = wrap_text(BLURBS[t], "Barlow", 8, cw - 28)
        ny = y + ch / 2 - 12
        for line in body:
            c.drawCentredString(x + cw / 2, ny, line)
            ny -= 11
        c.setFont("Cond-Bold", 8)
        c.drawCentredString(x + cw / 2, y + 18, "LEVEL 1  ·  ALWAYS OPEN")
    foot("Flavor cards")
    c.showPage()

    # Dish cards: 8 per page (2x4)
    cw, ch = 3.5 * inch, 2.2 * inch
    per = 8
    pages = (len(picked) + per - 1) // per
    for p in range(pages):
        c.setFillColor(CREAM_c)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(NAVY_c)
        c.setFont("Serif-Bold", 14)
        c.drawString(0.5 * inch, H - 0.45 * inch, "Restaurant & dish cards  (%s of %s)" % (p + 1, pages))
        c.setFont("Barlow", 8)
        c.setFillColor(INK)
        c.drawString(0.5 * inch, H - 0.6 * inch, "Cut on the dashed lines. Play a card to taste its combo if that combo is open for you.")
        chunk = picked[p * per:(p + 1) * per]
        for i, d in enumerate(chunk):
            col, row = i % 2, i // 2
            x = 0.5 * inch + col * (cw + 0.2 * inch)
            y = H - 0.8 * inch - (row + 1) * (ch + 0.12 * inch)
            dashed_rect(c, x, y, cw, ch)
            c.setFillColor(white)
            c.setStrokeColor(GOLD_c)
            c.setDash()
            c.roundRect(x + 4, y + 4, cw - 8, ch - 8, 6, fill=1, stroke=1)
            tag = "FROM THE MENU" if d["source"] == "menu" else "SUGGESTED"
            c.setFillColor(HexColor("#2d6a3a") if d["source"] == "menu" else HexColor("#8a6200"))
            c.setFont("Cond-Bold", 7)
            c.drawString(x + 12, y + ch - 22, tag)
            c.setFillColor(NAVY_c)
            c.setFont("Serif-Bold", 10)
            ny = y + ch - 38
            for line in wrap_text(d["dish"], "Serif-Bold", 10, cw - 28)[:2]:
                c.drawString(x + 12, ny, line)
                ny -= 12
            c.setFont("Barlow-Bold", 8)
            c.setFillColor(INK)
            c.drawString(x + 12, ny - 2, d["restaurantName"])
            c.setFont("Barlow", 8)
            c.drawString(x + 12, ny - 13, d["town"] + (" · " + d["area"] if d["area"] and d["area"] != d["town"] else ""))
            c.setFillColor(GOLD_c)
            c.setFont("Cond-Bold", 8)
            c.drawString(x + 12, y + 14, (combo_name.get(d["comboId"], d["comboId"]))[:42])
        foot("Dish cards")
        c.showPage()

    # Passport (2 per page, print twice if needed)
    for copy in range(2):
        c.setFillColor(CREAM_c)
        c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(NAVY_c)
        c.setFont("Serif-Bold", 18)
        c.drawString(0.6 * inch, H - 0.55 * inch, "Tasting passport")
        c.setFont("Barlow", 10)
        c.setFillColor(INK)
        c.drawString(0.6 * inch, H - 0.75 * inch, "Player: ______________________    Date: ______________    Starting flavor: ______________")
        y = H - 1.05 * inch
        for lv in range(1, 6):
            items = [x for x in combos if x["level"] == lv]
            title = {1: "Level 1 — Singles", 2: "Level 2 — Pairs", 3: "Level 3 — Trios", 4: "Level 4 — Quads", 5: "Level 5 — The Peak"}[lv]
            c.setFillColor(GOLD_c)
            c.setFont("Cond-Bold", 10)
            c.drawString(0.6 * inch, y, title.upper())
            y -= 14
            for combo in items:
                c.setStrokeColor(GOLD_c)
                c.rect(0.6 * inch, y - 1, 8, 8, fill=0, stroke=1)
                c.setFillColor(NAVY_c)
                c.setFont("Barlow", 8)
                c.drawString(0.6 * inch + 14, y, combo["name"][:38])
                c.setStrokeColor(HexColor("#e7dcc6"))
                c.line(3.55 * inch, y, 7.9 * inch, y)
                c.setFillColor(HexColor("#5a6272"))
                c.setFont("Barlow", 6)
                c.drawString(3.55 * inch, y + 2, "dish / place / 1-5")
                y -= 16
            y -= 4
        c.setFillColor(INK)
        c.setFont("Barlow", 8)
        c.drawString(0.6 * inch, 0.4 * inch, "A combo opens when it adds exactly one flavor to something you already tried. You do not have to fill every square.")
        foot("Passport (print one per player)")
        c.showPage()

    c.save()
    return pdf_path

def main():
    build_images()
    p = build_pdf()
    print("images +", p, "bytes", p.stat().st_size)

if __name__ == "__main__":
    main()
