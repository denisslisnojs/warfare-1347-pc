import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "ArtSource", "reference")

NOTES = {
    "castle-kit": "стены, башни, ворота, мосты, флаги",
    "fantasy-town-kit": "дома, крыши, лавки, колодцы, заборы",
    "retro-fantasy-kit": "постройки и предметы в стиле старых игр",
    "graveyard-kit": "часовни, ограды, кресты, фонари",
    "pirate-kit": "корабли, причалы, бочки, пушки",
    "watercraft-kit": "лодки и корабли",
    "nature-kit": "деревья, камни, трава, скалы",
    "mini-forest": "маленький лес",
    "survival-kit": "инструменты, палатки, костры, сундуки",
    "furniture-kit": "мебель для таверны и залов",
    "food-kit": "еда: для рынка и таверны",
    "mini-dungeon": "подземелье, сундуки, оружие",
    "modular-dungeon-kit": "стены и залы подземелий",
    "mini-arena": "римская арена",
    "mini-characters": "человечки",
    "tower-defense-kit": "башни, стены, дорожки",
    "hexagon-kit": "клетки карты: замки, деревни, леса",
    "mini-market": "рыночные лотки и товары",
}


def previews(kit_dir):
    for sub in ("Previews", "Isometric"):
        d = os.path.join(kit_dir, sub)
        if os.path.isdir(d):
            names = sorted(n for n in os.listdir(d) if n.lower().endswith(".png"))
            if sub == "Isometric":
                names = [n for n in names if n.endswith("_SE.png") or n.endswith("_NE.png") and n.replace("_NE", "_SE") not in names]
            return [os.path.join(sub, n) for n in names]
    return []


sections = []
total = 0
for source in sorted(os.listdir(LIB)):
    sdir = os.path.join(LIB, source)
    if not os.path.isdir(sdir):
        continue
    for kit in sorted(os.listdir(sdir)):
        kdir = os.path.join(sdir, kit)
        if not os.path.isdir(kdir):
            continue
        items = previews(kdir)
        total += len(items)
        cards = "".join(
            f'<figure><img loading="lazy" src="{html.escape(source)}/{html.escape(kit)}/{html.escape(p.replace(os.sep, "/"))}"><figcaption>{html.escape(os.path.splitext(os.path.basename(p))[0].replace("_SE", "").replace("_NE", ""))}</figcaption></figure>'
            for p in items)
        sections.append(f'<section><h2>{html.escape(kit)} <small>{len(items)} моделей. {html.escape(NOTES.get(kit, ""))}</small></h2>'
                        f'<img class="hero" loading="lazy" src="{html.escape(source)}/{html.escape(kit)}/_preview.png"><div class="grid">{cards}</div></section>')

page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Образцы моделей</title>
<style>
body{{background:#1b1510;color:#f2e8d0;font:15px Georgia,serif;margin:24px}}
h1,h2{{color:#e8c070}} h2{{margin-top:36px}} small{{color:#b8a888;font-size:13px;font-weight:normal}}
.hero{{max-width:720px;width:100%;border:1px solid #8a6a38;display:block;margin:8px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}}
figure{{margin:0;background:#2a2016;border:1px solid #4a3a26;padding:4px;text-align:center}}
figure img{{width:100%;aspect-ratio:1;object-fit:contain}} figcaption{{font-size:11px;color:#c8b890;word-break:break-all}}
</style></head><body>
<h1>Образцы моделей</h1><p>{total} моделей из наборов Kenney, лицензия CC0. Это образцы: смотрим силуэты и пропорции, а свои модели делаем в Blender в нашем стиле.</p>
{''.join(sections)}
</body></html>"""
open(os.path.join(LIB, "index.html"), "w", encoding="utf-8").write(page)
print("index.html:", total, "models")
