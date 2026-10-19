import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIB = os.path.join(ROOT, "ArtSource", "audio", "library")

NOTES = {
    "rpg-audio": "Бытовые звуки: монеты, кошели, книги, двери, ткань, ножи, шаги",
    "impact-sounds": "Удары по металлу, дереву, стеклу, колокол, шаги по разной земле",
    "casino-audio": "Карты, фишки, кости: пригодятся для игр в таверне",
    "interface-sounds": "Щелчки и подтверждения для меню",
    "ui-audio": "Ещё щелчки и переключатели для меню",
    "music-jingles": "Короткие музыкальные заставки: щипковые струны, ударные и другие",
    "voiceover-pack": "Голос диктора на английском",
    "voiceover-pack-fighter": "Боевые выкрики диктора на английском",
    "sci-fi-sounds": "Фантастика, для нашей игры почти не подходит",
    "digital-audio": "Электронные звуки, для нашей игры почти не подходят",
}

rows = []
count = 0
for source in sorted(os.listdir(LIB)):
    src_dir = os.path.join(LIB, source)
    if not os.path.isdir(src_dir):
        continue
    for pack in sorted(os.listdir(src_dir)):
        pack_dir = os.path.join(src_dir, pack)
        if not os.path.isdir(pack_dir):
            continue
        files = []
        for base, _, names in os.walk(pack_dir):
            for n in sorted(names):
                if n.lower().endswith((".ogg", ".wav", ".mp3")):
                    files.append(os.path.relpath(os.path.join(base, n), LIB).replace(os.sep, "/"))
        count += len(files)
        items = "\n".join(
            f'<li><button onclick="play(this)" data-src="{html.escape(f)}">▶</button> {html.escape(os.path.splitext(os.path.basename(f))[0])}</li>' for f in files)
        rows.append(f"<section><h2>{html.escape(source)} / {html.escape(pack)} <small>{len(files)} звуков. {html.escape(NOTES.get(pack, ''))}</small></h2><ul>{items}</ul></section>")

page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Звуки Warfare 1347</title>
<style>
body{{background:#1b1510;color:#f2e8d0;font:15px Georgia,serif;margin:24px}}
h1{{color:#e8c070}} h2{{color:#e8c070;font-size:18px;margin-top:28px}} small{{color:#b8a888;font-size:13px;font-weight:normal}}
ul{{columns:4;list-style:none;padding:0}} li{{margin:2px 0;break-inside:avoid}}
button{{background:#3a2c1c;color:#e8c070;border:1px solid #8a6a38;cursor:pointer;width:28px}}
button.on{{background:#8a6a38;color:#1b1510}}
</style></head><body>
<h1>Библиотека звуков</h1><p>{count} звуков, все с лицензией CC0: можно использовать в игре без указания автора. Нажмите ▶, чтобы послушать.</p>
{''.join(rows)}
<script>
let cur=null,btn=null;
function play(b){{ if(cur){{cur.pause(); btn.classList.remove('on');}} cur=new Audio(b.dataset.src); btn=b; b.classList.add('on'); cur.onended=()=>b.classList.remove('on'); cur.play(); }}
</script></body></html>"""
open(os.path.join(LIB, "index.html"), "w", encoding="utf-8").write(page)
print("index.html:", count, "sounds")
