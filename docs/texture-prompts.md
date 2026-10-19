# Текстуры мира через ChatGPT

Как пользоваться:

1. Новый чат в ChatGPT. Приложить 2–3 скриншота карты (крупно город с полями, средне — лес и горы).
2. Вставить «Общее задание» (ниже) и отправить вместе со скриншотами.
3. Дальше по одной текстуре на сообщение: вставить её промпт, скачать картинку, сохранить в
   `Warfare1347\ArtSource\textures\` под именем из заголовка (например `grass.png`).
4. Сказать Claude «текстуры готовы» — он сам подгонит их под игру (яркость, швы, размер, служебный канал).

Если на картинке видны стыки — попросить: `Make it truly seamless: the left edge must continue into the right edge and the top into the bottom.`
Если есть тени или «солнце» — попросить: `Same texture, but with completely flat, even lighting and no shadows.`

Начинаем с трёх самых заметных: `grass`, `rock`, `forest_floor`. Остальные — когда эти понравятся в игре.

## Общее задание

```
I'm making a stylized 3D medieval world map for a strategy game, similar to the campaign map in Mount & Blade. The attached screenshots show how it looks now. I need a set of textures to replace the ground and building textures.

Rules for EVERY texture you make:
1. Square image, 1:1.
2. Seamless and tileable on all four edges: when I tile it 2x2, there must be no visible seams.
3. Strictly top-down orthographic view (camera looking straight down at the surface), no perspective, no horizon. For walls and bark: straight front view.
4. Flat, even, diffuse lighting: no cast shadows, no sun direction, no highlights, no vignette, no darkening at the edges.
5. Uniform detail over the whole image: no single large object, no focal point, no border or frame.
6. No text, letters, labels, logos or watermarks.
7. Style: high-quality realistic game texture, like in modern AAA strategy games: natural materials with fine, sharp, believable detail, high resolution. Natural, harmonious colours that fit the attached screenshots.
8. Clean and readable from above: medium contrast, details clear but not noisy, no clutter.

I will ask for the textures one by one. Reply "OK" now.
```

## Первые три

### grass

```
Texture "grass": a meadow seen from straight above, about 15 x 15 meters of ground. Short green grass with gentle variation of lighter and darker grass clumps, a few tiny wildflowers (white and yellow) and rare small spots of bare soil. Follow all the rules.
```

### rock

```
Texture "rock": a mountain rock surface seen face-on, about 25 x 25 meters of cliff. Grey-brown weathered stone with cracks, layered strata and small ledges. No plants, no snow. Follow all the rules.
```

### forest_floor

```
Texture "forest_floor": the floor of a deciduous forest seen from straight above, about 10 x 10 meters of ground under oaks and birches. Fallen leaves, patches of moss, small twigs and a few ferns. No tree trunks, no shadows of trees. Follow all the rules.
```

## Остальная земля

Детали крупнее, чем у первых трёх: мелкие травинки с высоты камеры сливаются.

### steppe

```
Texture "steppe": dry steppe grassland seen from straight above, about 30 x 30 meters. Clumps of feather grass and sagebrush, yellow and straw-coloured dry patches, bare dusty soil between them. Features large enough to read from far away, no tiny uniform noise. Follow all the rules.
```

### desert

```
Texture "desert": desert sand seen from straight above, about 40 x 40 meters. Wind ripples of different sizes, slightly darker and lighter sand drifts, a few scattered stones. Features large enough to read from far away. Follow all the rules.
```

### snow

```
Texture "snow": snow surface seen from straight above, about 40 x 40 meters. Wind-blown drifts and ridges, soft blue-grey shading in the hollows, no sparkles, no footprints. Features large enough to read from far away. Follow all the rules.
```

### tundra

```
Texture "tundra": tundra ground seen from straight above, about 30 x 30 meters. Patchwork of green and rusty moss, pale lichen, grey stones and small puddles of dark water, sparse dwarf shrubs. Features large enough to read from far away. Follow all the rules.
```

### farm

```
Texture "farm": medieval crop fields seen from straight above, about 60 x 60 meters. Patchwork of narrow strips: ripe wheat, young green crops and brown ploughed earth with furrows, slightly irregular like fields worked by hand. Follow all the rules.
```

### taiga_floor

```
Texture "taiga_floor": the floor of a northern coniferous forest seen from straight above, about 15 x 15 meters. Brown fallen needles, green moss cushions, small pine cones, grey lichen, a few blueberry shrubs. Features large enough to read from far away. Follow all the rules.
```

### forest

```
Texture "forest": dense deciduous forest seen from high above, about 150 x 150 meters. A continuous canopy of rounded oak and beech crowns in varied greens, small dark gaps between crowns. No ground visible, no clearings, no roads. Follow all the rules.
```

### taiga

```
Texture "taiga": dense northern coniferous forest seen from high above, about 150 x 150 meters. A continuous canopy of pointed spruce and pine crowns in dark blue-greens, small dark gaps between crowns. No ground visible, no clearings. Follow all the rules.
```

## Вода

### water

```
Texture "water": a seamless grayscale height map of a calm sea surface seen from straight above, about 20 x 20 meters. Overlapping small waves and ripples running in slightly different directions; white = wave crests, black = troughs, smooth gradients. Grayscale only, no colour, no foam, no lighting. Follow all the rules.
```

### foam

```
Texture "foam": a seamless pattern of white sea foam seen from straight above, about 10 x 10 meters: streaks, lace and clusters of bubbles on a pure black background. Black and white only. Follow all the rules.
```

## Постройки

### stone

```
Texture "stone": medieval castle wall masonry, straight front view, about 2 x 2 meters. Irregular light stone blocks with mortar joints. Follow all the rules.
```

### plaster

```
Texture "plaster": whitewashed plaster wall, straight front view, about 2 x 2 meters. Subtle stains, small cracks and slightly uneven surface. Follow all the rules.
```

### planks

```
Texture "planks": wooden wall of vertical boards, straight front view, about 2 x 2 meters. Visible wood grain and narrow gaps between boards. Follow all the rules.
```

### logs

```
Texture "logs": log cabin wall of horizontal round logs, straight front view, about 2 x 2 meters. Follow all the rules.
```

### tiles

```
Texture "tiles": terracotta roof tiles in overlapping rows, seen straight on, about 2 x 2 meters. Follow all the rules.
```

### shingles

```
Texture "shingles": wooden roof shingles in overlapping rows, seen straight on, about 2 x 2 meters. Follow all the rules.
```

### slate

```
Texture "slate": dark grey slate roof tiles in overlapping rows, seen straight on, about 2 x 2 meters. Follow all the rules.
```

### mudbrick

```
Texture "mudbrick": wall of sun-dried mud bricks with patches of clay plaster, straight front view, about 2 x 2 meters. Follow all the rules.
```

### thatch

```
Texture "thatch": thatched straw roof seen straight on, about 2 x 2 meters. Dense layered bundles of golden-grey straw. Follow all the rules.
```

### brick

```
Texture "brick": medieval red-brown brick wall, straight front view, about 2 x 2 meters, with light mortar joints. Follow all the rules.
```

### paving

```
Texture "paving": cobblestone street paving seen from straight above, about 3 x 3 meters. Rounded stones of different sizes with packed dirt between them. Follow all the rules.
```

### felt

```
Texture "felt": thick white-grey felt of a nomad yurt, straight front view, about 1 x 1 meter. Soft woolly surface with faint stitching lines. Follow all the rules.
```

## Деревья

### leaves

```
Texture "leaves": dense foliage of a broadleaf tree crown, close-up, about 1 x 1 meter. Overlapping green leaves of several shades. Follow all the rules.
```

### needles

```
Texture "needles": dense spruce and pine needles, close-up, about 1 x 1 meter. Follow all the rules.
```

### bark

```
Texture "bark": oak tree bark, straight front view, about 1 x 1 meter, with vertical furrows. Follow all the rules.
```

### birch

```
Texture "birch": birch bark, straight front view, about 1 x 1 meter. White bark with black horizontal marks. Follow all the rules.
```
