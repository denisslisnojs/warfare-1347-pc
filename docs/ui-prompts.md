# Оформление меню через ChatGPT

Как пользоваться:

1. Новый чат в ChatGPT. Приложить 2 скриншота: вид города (`docs/style/town-view-1-capital.jpg`) и карту с панелью даты сверху (`docs/map_edge_east.jpg`). Прикладывать только к первому сообщению — дальше ChatGPT их помнит.
2. Вставить «Общее задание» (ниже) и отправить вместе со скриншотами.
3. Сначала — концепт всего экрана (промпт 1). Он нужен только чтобы договориться о стиле, в игру не идёт.
   Если концепт нравится — дальше по одной детали на сообщение (промпты 2–6).
4. Сохранять в `Warfare1347\ArtSource\ui\` под именем из заголовка (например `ui_panel.png`).
5. Сказать Claude «оформление готово» — он сам разрежет детали так, чтобы они растягивались под любой экран, и подключит в игру.

Если фон не прозрачный — попросить: `Same image, but as a PNG with a fully transparent background.`
Если на детали появился текст — попросить: `Same image without any text or letters.`

## Общее задание

```
I'm making a medieval strategy game for PC (year 1347), similar to Mount & Blade: Bannerlord. The attached screenshots show the game: a stylized 3D world, and the current interface — dark panels with warm gold text and a serif font. I need art for the interface of the settlement screen: when the player enters a town, castle or village, a menu panel appears on the left side over a slightly blurred 3D view of the settlement.

Style for everything: dark aged wood or dark leather with a thin trim of worn gold / brass ornament, subtle medieval motifs (simple knotwork, rivets, small heraldic corner pieces). Elegant and readable, not overloaded. Warm colours that fit the screenshots.

Rules for every interface piece (not for the concept):
1. PNG with a fully transparent background around the piece.
2. Straight front view, no perspective, no tilt.
3. No text, letters, numbers, logos or watermarks.
4. No drop shadow outside the piece, no glow outside the piece.
5. Sharp, clean edges, high resolution.
6. Decoration only in the corners and at the ends; the straight parts between them must be plain and uniform, so the piece can be stretched in a game engine without distortion.
```

## 1. `ui_concept.png` — концепт экрана (только для обсуждения)

```
Make a concept mockup of the whole settlement screen, 16:9. Background: the attached town screenshot, slightly blurred. On the left, a tall menu panel about one third of the screen width: at the top the town name on a ribbon with the owner's coat of arms, under it a short description, then a vertical list of 6 menu buttons: Barracks, Market, Tavern, Arena, Lord's Castle, Leave. Text is allowed in this mockup only.
```

## 2. `ui_panel.png` — фон меню

```
The background panel of the menu, without any buttons or text. Tall rectangle, proportions 2:3, 1024 x 1536. A dark wooden or leather board with a thin gold ornamental frame of the same width on all four sides; decorated corners; the middle is calm and even so text is readable on it.
```

## 3. `ui_button.png` и `ui_button_hover.png` — кнопка

```
One menu button plate, without text. Wide rectangle, proportions 4:1, 1024 x 256. Dark wood or leather with a thin gold border; small decorative caps at the left and right ends; the middle part plain and uniform.
```

Потом в том же чате:

```
The same button, highlighted version for when the mouse is over it: slightly lighter, the gold border brighter and warmer. Same size, same shape, everything else identical.
```

## 4. `ui_title.png` — лента под название

```
A ribbon or banner plate for the settlement name, without text. Proportions 4:1, 1024 x 256. Deep red or dark cloth with a gold edge, ends cut like a swallowtail or folded ribbon; the middle plain and uniform.
```

## 5. `ui_divider.png` — разделитель

```
A thin horizontal ornamental divider line for separating parts of the menu. Proportions 8:1, 1024 x 128. Gold, with a small ornament in the centre and tapering ends.
```

## 6. Значки пунктов меню (по желанию, после остального)

Один промпт на значок, имена файлов: `icon_barracks.png`, `icon_market.png`, `icon_tavern.png`, `icon_arena.png`,
`icon_lord.png`, `icon_throne.png`, `icon_militia.png`, `icon_trade.png`, `icon_elder.png`, `icon_leave.png`.

```
A small square icon for the menu item "Barracks" (crossed spears and a shield). 1:1, 512 x 512, transparent background. Engraved gold on a dark round medallion, simple and readable at small size, same style as the panel and buttons.
```

Для остальных заменить название и рисунок в скобках: рынок (весы и мешок), таверна (кружка), арена (скрещённые мечи над ристалищем),
замок лорда (башня), тронный зал (корона), казармы ополчения (вилы и топор), торговля с крестьянами (сноп и монета),
староста (посох), покинуть (открытые ворота).

## 7. Значки рынка

Делать в том же чате, где делали меню (чтобы стиль совпал). Сначала один пробный значок — `icon_goods.png`.
Если понравился — дальше по одному на сообщение, заменяя имя и рисунок по списку ниже.
Сохранять в `Warfare1347\ArtSource\ui\` под точным именем файла.

```
A small square icon for the market category "Goods" (a sack of grain, a jug and a roll of cloth). 1:1, 512 x 512, PNG with a fully transparent background. Engraved gold on a dark round medallion with a thin gold rim, simple and readable at small size, same style as the panel and buttons. No text.
```

Вкладки (5):

| Файл | Название (для промпта) | Рисунок (в скобках) |
|---|---|---|
| `icon_goods.png` | Goods | a sack of grain, a jug and a roll of cloth |
| `icon_armor.png` | Armour | a mail shirt with a helmet above it |
| `icon_melee.png` | Melee weapons | a sword and an axe crossed over a round shield |
| `icon_ranged.png` | Ranged weapons | a bow with a nocked arrow and a crossbow behind it |
| `icon_horses.png` | Horses | a horse head with a bridle |

Слоты героя на рынке (сейчас нужны только эти 6): `icon_helmets`, `icon_body`, `icon_gloves`, `icon_legs`, `icon_mounts`, `icon_barding`; слоты оружия берут значок `icon_melee`.
Остальные из таблицы пригодятся позже, для строк предметов в списках — их можно не делать сейчас.

Подкатегории (14):

| Файл | Название | Рисунок |
|---|---|---|
| `icon_helmets.png` | Helmets | a medieval knight's helmet |
| `icon_body.png` | Body armour | a mail coat with a breastplate |
| `icon_gloves.png` | Gloves | a plate gauntlet |
| `icon_legs.png` | Leg armour | a pair of greaves and a boot |
| `icon_swords.png` | Swords | a straight medieval sword, point down |
| `icon_axes.png` | Axes | a bearded battle axe |
| `icon_spears.png` | Spears | a spear and a polearm crossed |
| `icon_shields.png` | Shields | a heater shield |
| `icon_bows.png` | Bows | a longbow |
| `icon_crossbows.png` | Crossbows | a crossbow |
| `icon_throwing.png` | Throwing weapons | two javelins and a throwing axe |
| `icon_ammo.png` | Ammunition | a quiver with arrows and a few bolts |
| `icon_mounts.png` | Mounts | a saddled horse, side view |
| `icon_barding.png` | Horse armour | a horse head in a metal chanfron with a cloth caparison |

И монета для цен: `icon_gold.png` — Gold (a stack of gold coins).

### Значки слотов героя (без медальона)

В слотах значок рисуется бледным силуэтом внутри рамки, поэтому для них — только сам предмет, без круглого медальона.
Имена файлов: `icon_helmets.png`, `icon_body.png`, `icon_gloves.png`, `icon_legs.png`, `icon_mounts.png`, `icon_barding.png`.

```
A small square icon for the equipment slot "Helmet": a medieval knight's helmet, front three-quarter view. 1:1, 512 x 512, PNG with a fully transparent background. Engraved gold object only, no medallion, no frame, no background shape. Same gold style as the previous icons, simple bold silhouette readable at small size. No text.
```

### Кнопка сброса на рынке

Файл `icon_reset.png`, в том же чате, что значки вкладок (с медальоном):

```
A small square icon for the button "Reset": a circular arrow turning back, like an undo sign. 1:1, 512 x 512, PNG with a fully transparent background. Engraved gold on a dark round medallion with a thin gold rim, same style as the category icons. No text.
```

### Кнопки случайного выбора в редакторе персонажа

Файлы `icon_dice.png` и `icon_dice_all.png`, в том же чате, что значок сброса (с медальоном). Сохранить в `ArtSource/ui/`.

`icon_dice.png` — случайно в одной вкладке:

```
A small square icon for the button "Random": a single six-sided die, three-quarter view, showing dots. 1:1, 512 x 512, PNG with a fully transparent background. Engraved gold on a dark round medallion with a thin gold rim, exactly the same style as the reset icon. No text.
```

`icon_dice_all.png` — случайно всё:

```
A small square icon for the button "Randomize everything": two six-sided dice tumbling together, three-quarter view, showing dots. 1:1, 512 x 512, PNG with a fully transparent background. Engraved gold on a dark round medallion with a thin gold rim, exactly the same style as the reset icon. No text.
```

### Фон редактора персонажа

Сохранять в `ArtSource/ui/` как `editor_bg_1.png` … `editor_bg_4.png`. Перед первым промптом в том же чате вставить:

```
New task: a background image for the character creation screen of the same medieval strategy game (year 1347). Rules for every variant: 16:9, 1920 x 1080; painterly stylized look matching the game screenshots; warm, dim, moody lighting; the left third is darker and calm (a menu panel will cover it); the centre-right is an empty floor area where a 3D character will stand, nothing in front of it; soft focus, no sharp details that compete with the character; no people, no animals, no text, no logo.
```

1. `editor_bg_1.png` — шатёр:
```
Variant 1: the inside of a large medieval army tent at night: canvas walls lit by warm lantern light, a wooden chest, a weapon rack and a folded banner in the background, trampled straw on the ground.
```
2. `editor_bg_2.png` — зал замка:
```
Variant 2: a stone castle hall: tall arched windows with pale moonlight, a large hearth glowing on the right, heraldic banners on the walls, a worn stone floor.
```
3. `editor_bg_3.png` — таверна:
```
Variant 3: a cosy village tavern after closing: heavy timber beams, a fire in the stone fireplace, barrels and a long table pushed to the walls, warm amber light, wooden floor.
```
4. `editor_bg_4.png` — лагерь в сумерках:
```
Variant 4: an army camp on a hill at dusk: distant tents and campfires, a fortress silhouette on the horizon, an orange and violet sky, trampled grass in the foreground.
```

### Вкладки редактора персонажа

Файлы `icon_tab_body.png`, `icon_tab_face.png`, `icon_tab_eyes.png`, `icon_tab_hair.png`, в том же чате, что кубики. Сохранить в `ArtSource/ui/`.

```
Four small square icons for the tabs of a character creation screen, one image per message, in exactly the same style as the dice and reset icons: engraved gold on a dark round medallion with a thin gold rim. 1:1, 512 x 512, PNG with a fully transparent background. No text.
1) icon_tab_body: a simple standing human figure silhouette, front view.
2) icon_tab_face: a man's head and face in profile.
3) icon_tab_eyes: a single open eye with an eyebrow.
4) icon_tab_hair: a comb next to a lock of hair and a short beard.
```

### Картины держав для экрана выбора

Файлы `faction_vallerois.png`, `faction_varden.png`, `faction_vinland.png`, `faction_grim.png`, `faction_azhar.png`, `faction_khordan.png`. Сохранить в `ArtSource/ui/factions/`. Сначала общее задание, потом по одному варианту на сообщение.

```
New task: six paintings for the faction selection screen of the same medieval strategy game (year 1347), one per message, all in one consistent style. Style: loose painterly illustration, like a concept art sketch with visible brush strokes and soft watercolour washes; the picture is a vignette whose edges dissolve into a dark smoky background, as if painted on dark paper. Composition: a landscape of the faction's land with its typical architecture, and one small lone figure in the foreground seen from behind, looking at it. 4:3, 1600 x 1200. No text, no logo, no frame.
```

1. `faction_vallerois.png`: `Kingdom of Vallerois: a rich western European valley with vineyards and fields, a stone castle and a cathedral above a river town, a knight with a lance on a hill. Warm golden light, red and gold banners.`
2. `faction_varden.png`: `Principality of Varden: a wide northern river in deep forests, wooden walls and a tall wooden tower, an onion-domed church, early winter with snow on the roofs, a warrior in a fur cloak. Cold blue and green light.`
3. `faction_vinland.png`: `Kingdom of Vinland: a cold sea coast with a harbour full of longships, long timber halls and a grey stone church, a shield bearer on the rocks. Grey sea, dark blue banners with a silver raven.`
4. `faction_grim.png`: `Grimian Empire: a great imperial city between two seas, domes, colonnades and an aqueduct, a legionary with a tall shield on the steps. Purple and gold evening light.`
5. `faction_azhar.png`: `Sultanate of Azhar: a desert oasis city with green domes, minarets and palm gardens behind sandstone walls, a rider in a turban with a spear. Hot golden haze, green and gold banners.`
6. `faction_khordan.png`: `Khordan Khaganate: an endless steppe under a vast sky, felt yurts around a stone citadel, a horse archer on a small steppe horse. Turquoise sky and golden grass.`

### Знамёна держав для карточек выбора

Файлы `banner_vallerois.png` … `banner_khordan.png`, сохранить в `ArtSource/ui/factions/`. Приложить к общему заданию картинки гербов из `Assets/StreamingAssets/Data/world/ui/` (`emblem_*.png`).

```
New task: six heraldic banners for the faction selection screen, one per message, all in one consistent style. A tall vertical cloth banner hanging from a short wooden crossbar, with a swallowtail cut at the bottom, flat front view, simple and minimal: the field colour of the faction with its emblem in the centre, a thin trim along the edges, soft painted cloth texture, gentle folds. 2:3, 1024 x 1536, PNG with a fully transparent background. No text, no pole, no people. The attached emblems show each faction's symbol.
```

1. `banner_vallerois.png`: `Kingdom of Vallerois: deep red field, gold trim, its emblem in gold.`
2. `banner_varden.png`: `Principality of Varden: dark green field, gold trim, its emblem.`
3. `banner_vinland.png`: `Kingdom of Vinland: dark blue field, silver trim, a silver raven above a sea wave.`
4. `banner_grim.png`: `Grimian Empire: purple field, gold trim, a gold eagle in a laurel wreath.`
5. `banner_azhar.png`: `Sultanate of Azhar: dark green field, gold trim, a gold sun disc with a falcon.`
6. `banner_khordan.png`: `Khordan Khaganate: turquoise field, gold trim, a rising gold sun with nine rays over steppe hills.`

### Карточки держав (вместо знамён)

Файлы `card_vallerois.png` … `card_khordan.png`, сохранить в `ArtSource/ui/factions/`. В тот же чат, где большие картины, приложить гербы (`emblem_*.png`).

```
New task: six small cards for the faction selection list, one per message, in the same painterly style as the six large paintings above, but much more minimal. Each card: one simple iconic scene of the faction's land with a large calm sky, few details, a limited palette of the faction's colours, and the faction's emblem clearly shown on a single banner or shield standing in the foreground. Soft dark smoky edges like the paintings. Portrait 4:5, 1024 x 1280. No text, no people, no frame. The attached emblems show each faction's symbol.
```

По одному сообщению: `Vallerois`, `Varden`, `Vinland`, `Grimian Empire`, `Azhar`, `Khordan` (например: `Card 1: Kingdom of Vallerois.`).
