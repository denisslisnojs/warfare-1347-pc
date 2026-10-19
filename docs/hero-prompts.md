# Чертежи героя через ChatGPT

Зачем: по чертежам Claude подгоняет 3D-модель тела (основа — стилизованное тело из набора Blender Studio «Human Base Meshes», CC0).

Как пользоваться:

1. Новый чат в ChatGPT. Приложить 2 картинки: `docs/style/7-hero-body.png` (выбранные пропорции) и `docs/style/town-view-1-capital.jpg` (как выглядит мир игры).
2. Вставить «Общее задание» и отправить вместе с картинками.
3. Потом по одному промпту на сообщение, по порядку. Первый чертёж (тело) можно попросить 2–3 раза и выбрать лучший: остальные листы должны быть про того же самого героя.
4. Сохранять в `Warfare1347\ArtSource\concept\hero\` под именем из заголовка.
5. Написать Claude «чертежи готовы».

Если на картинке появились надписи — попросить: `Same image without any text, numbers or labels.`
Если виды разной высоты или пропорций — попросить: `Make all views exactly the same height and proportions, aligned to the same guide lines.`
Если поза не та — попросить: `Same character in a strict T-pose: arms straight out horizontally, palms facing down.`

## Если пишете в тот же чат, где делали значки

Вставить перед «Общим заданием»:

```
New task, separate from the icons above. Forget the icon style rules (gold engraving, medallion, transparent background). Now I need character design sheets in a completely different style, described below.
```

## Общее задание

```
I'm making a medieval strategy game for PC, set in the year 1347, with stylized 3D graphics. The attached images show the game world and the body proportions we chose. I need character design sheets for a 3D modeller: the base body of a human soldier in underwear only. It will be modelled in Blender, rigged for animation and later dressed in separate armour pieces.

Character style:
- stylized heroic proportions, about 4 heads tall in total;
- broad shoulders, strong chest, big hands and feet, a clearly visible neck, short sturdy legs;
- simple smooth forms, no small details and no realistic muscles;
- a calm, friendly face with simple dark eyes, a clear nose and eyebrows, no mouth;
- short brown hair;
- medieval linen braies: loose off-white underpants down to mid-thigh, tied with a thin cord at the waist; bare chest, barefoot.

Rules for every sheet:
1. Plain flat light grey background.
2. Orthographic views, no perspective.
3. Even soft lighting, no dramatic shadows.
4. The same character in every view and every sheet, with exactly the same proportions.
5. No text, no labels, no numbers, no watermark.
```

## 1. `hero_sheet_body.png` — тело (главный чертёж)

```
A turnaround model sheet of this character: front view, side view facing left, and back view, side by side at the same scale, standing on the same ground line. Strict T-pose: arms straight out horizontally, palms facing down, feet slightly apart. Draw thin horizontal guide lines across all three views through the top of the head, the chin, the shoulders, the chest, the waist, the crotch, the knees and the ankles. 16:9.
```

## 2. `hero_sheet_head.png` — голова

```
A head turnaround of the same character: front view, side view facing left and a three-quarter view, side by side at the same scale. The same hair and face as before. Thin horizontal guide lines across all views through the top of the head, the eyebrows, the eyes, the tip of the nose and the chin. 16:9.
```

## 3. `hero_sheet_hands.png` — кисти и стопы

```
A hands and feet sheet of the same character: an open hand seen from above and from the side, palm facing down as in the T-pose; a fist gripping a round wooden stick, the way he will hold a sword hilt; a bare foot seen from the side and from above. Simple chunky forms, four fingers and a thumb. 16:9.
```

## 4. `hero_look.png` — как он должен выглядеть в игре

```
The same character in a three-quarter view, standing relaxed with arms down at his sides, shown as a finished 3D game model: soft lighting, simple clean colours, matching the look of the attached game screenshot. 1:1.
```

## 5. `hero_builds.png` — разные телосложения (по желанию)

```
The same base character in three builds side by side, front view, same height: lean, average and heavy. Same face, hair and braies. Plain grey background, no text. 16:9.
```
