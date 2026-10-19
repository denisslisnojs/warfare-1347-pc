# Текстура кожи через ChatGPT (опыт)

Зачем: сравнить с текстурой, которую делает скрипт `Tools/blender/hero_base.py` (`Assets/Art/Characters/Textures/Hero_Skin.png`). Цвет кожи в игре задаётся оттенком из `world/looks.json`, текстура даёт только детали.

Как пользоваться:

1. Чат ChatGPT. Если тот же, где делали значки, сначала вставить строку из раздела ниже.
2. Приложить картинку `ArtSource/concept/skin/body_uv_guide.png`. Это выкройка тела: белые куски кожи, тенями видно глаза, нос, рот, пальцы.
3. Вставить промпт и отправить.
4. Сохранить результат как `ArtSource/concept/skin/chatgpt_skin.png`.
5. Написать Claude «текстура готова». Claude наденет её на модель и покажет рядом со своей.

Если куски на картинке сдвинулись или изменились, попросить: `Keep every piece exactly as in the guide: same outline, size and position. Paint only inside the pieces.`

## Если пишете в тот же чат, где делали значки

```
New task, separate from everything above. Forget the previous style rules. I need a texture for a 3D model, described below.
```

## Промпт

```
The attached image is a UV layout guide of a stylized 3D game character: an adult man for a medieval strategy game with a soft, clean, stylized look. The white and grey shapes are the unwrapped pieces of his skin, and the shading shows their form. The top-left quarter is the head: the face is in the centre (you can see the eye sockets, the nose and the mouth), the ears are on both sides, and the neck and shoulders are below. The top-right quarter is the torso, arms and legs. The bottom-left quarter is the hands and fingers. The bottom-right quarter is the feet and toes.

Paint a hand-painted skin texture for this exact layout:
1. Keep every piece exactly where it is, with exactly the same outline, size and position. Do not move, rotate, rescale or redraw any piece. Paint only inside the pieces.
2. Fill everything with a light, warm European skin tone, even and soft, like a stylized game character, not photorealistic.
3. Add gentle natural colour: a little pink on the cheeks, the tip of the nose and the ears, slightly pinker lips, a soft warm tint on the knuckles, elbows and knees, and slightly lighter nails on the fingers and toes.
4. No pores, no wrinkles, no hair, no eyebrows, no tattoos, no shadows or shading, no outlines, no text.
5. Fill the black background around the pieces with the same skin tone, so there are no dark edges.
6. Square image, 1:1, the same framing as the guide.
```
