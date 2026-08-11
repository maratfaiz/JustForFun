# Иконки Луми — что это и как вставлять

42 UI-иконки, которые заменяют SF Symbols в приложении. Это **не** маскот —
маскот и его сцены описаны отдельно в `LUMI-ASSETS.md`.

---

## 1. Что пришло

Две папки с одинаковым набором имён:

| Папка | Что внутри | Когда брать |
|---|---|---|
| `assets/icons/` | **чёрный силуэт** на прозрачном фоне | основной вариант — цвет задаётся в коде |
| `assets/icons-colored/` | тот же силуэт с уже запечённым цветом | если проще не возиться с tint |

Технические характеристики одинаковые:

| Параметр | Значение |
|---|---|
| Формат | PNG, RGBA |
| Размер | 1024 × 1024 px, квадрат |
| Фон | прозрачный |
| Цвет | один тон, без градиентов внутри иконки |
| Вес | 10–60 КБ |

---

## 2. Как подключать (важно)

Основной набор — **чёрный**. Чёрный цвет здесь ничего не значит: в iOS
шаблонная отрисовка использует только альфа-канал, а сам цвет берётся из
кода. Поэтому:

1. Положить PNG в `Assets.xcassets`.
2. У каждого имиджсета выставить **Render As: Template Image**
   (в инспекторе справа). Без этого иконка останется чёрной и
   `.foregroundColor(...)` не сработает.
3. В коде:

```swift
// было
Image(systemName: "flame.fill")
    .foregroundColor(.orange)

// стало
Image("icon-streak")
    .renderingMode(.template)   // можно и через Render As: Template в каталоге
    .resizable()
    .scaledToFit()
    .frame(width: 24, height: 24)
    .foregroundColor(streakOrange)   // #FF8A55
```

`.renderingMode(.template)` ставится сразу после `Image(...)`, до
`.resizable()`. Цвета из таблицы ниже удобно завести один раз — либо
Color Set'ами в `Assets.xcassets`, либо своим `Color(hex:)`.

Если Template-режим выставлять не хочется — брать файлы из
`assets/icons-colored/`, там цвет уже внутри, и `.foregroundColor` не нужен.

**Размер на экране.** Иконки нарисованы «в край» квадрата, без
встроенных полей. Ставить их в `.frame(width:height:)` 20–28 pt для
инлайновых значков, 28–32 pt для таб-бара, 40–56 pt для карточек
достижений и товаров магазина. Собственный отступ добавлять снаружи
через `.padding()`.

---

## 3. Полный список

Толщина линии у всего набора одна (38 условных единиц на сетке 512),
поэтому иконки можно смешивать на одном экране — они не будут выглядеть
вразнобой.

### Приоритет 1 — видны почти всегда

| Файл | Что нарисовано | Цвет | Где |
|---|---|---|---|
| `icon-streak.png` | огонёк с внутренним язычком | `#FF8A55` | Главная, Профиль, экран серии |
| `icon-lumen.png` | монетка со звездой внутри | `#FFD166` | Главная, Профиль, Магазин, награды |
| `icon-freeze.png` | снежинка | `#8FC3FF` | Главная, Профиль, серия, Магазин |
| `icon-tab-courses.png` | раскрытая книга | `#C3B3FF` / `#6A6088` | Таб-бар |
| `icon-tab-profile.png` | человечек в круге | `#C3B3FF` / `#6A6088` | Таб-бар |

### Приоритет 2 — профиль и достижения

| Файл | Что нарисовано | Цвет | Где |
|---|---|---|---|
| `icon-trophy.png` | кубок | `#FFB020` | «Первый урок» |
| `icon-sunrise.png` | восход над горизонтом | серый | «Ранняя пташка» |
| `icon-journal.png` | блокнот на пружине | серый | «Дневник × 5», курс-техника |
| `icon-seal.png` | щит с галочкой | серый | «Курс пройден» |
| `icon-calendar.png` | календарь | серый | «30 дней подряд» |
| `icon-shop.png` | сумка | `#C9C2E6` | Профиль → Магазин |
| `icon-stats.png` | столбчатый график | `#C9C2E6` | Профиль → Статистика |
| `icon-settings.png` | шестерёнка | `#C9C2E6` | Профиль → Настройки |
| `icon-edit.png` | карандаш | `#9C93C9` | Редактировать профиль |
| `icon-bell.png` | колокольчик | `#9C93C9` | Уведомления |
| `icon-lock.png` | замок | `#8A80B0` | Заблокированный контент |

### Приоритет 3 — магазин

| Файл | Что нарисовано | Цвет | Где |
|---|---|---|---|
| `icon-glasses.png` | очки | `#5B9FFF` | «Очки мечтателя» |
| `icon-crown.png` | корона | `#FF6EC7` | «Звёздная корона» |
| `icon-selfhug.png` | руки, обнимающие сердце | нейтральный | «Самообъятие» |
| `icon-target.png` | мишень | нейтральный | «Фокус на ценностях», цель «Увереннее» |
| `icon-plus.png` | плюс в круге | нейтральный | «Доп. задание дня» |
| `icon-hint.png` | лампочка | `#8B6CF6` | «Подсказка в уроке» |
| `icon-bolt.png` | молния | нейтральный | Фильтр «Бустеры», «Легче с тревогой», «Смелость» |

### Приоритет 4 — онбординг

| Файл | Что нарисовано | Где |
|---|---|---|
| `icon-critic-voice.png` | пузырь с «!» | «Сильно критикую себя» |
| `icon-clock.png` | часы | «Трудно отстаивать границы» |
| `icon-heart-outline.png` | сердце контуром | «Недостаточно хорош(а)» |
| `icon-anxiety.png` | «!» в круге | «Тревожность и стресс» |
| `icon-question.png` | «?» в круге | «Другое» |
| `icon-book.png` | закрытая книга | Формат «Чтение» |
| `icon-headphones.png` | наушники | Формат «Аудио», курс про критика |
| `icon-tap.png` | палец, касающийся экрана | Формат «Интерактив» |
| `icon-smile.png` | улыбающееся лицо | «Меньше критики» |
| `icon-heart-fill.png` | залитое сердце | «Ценить себя», «Самосострадание», «Забота» |

### Приоритет 5 — внутри упражнений

| Файл | Что нарисовано | Где |
|---|---|---|
| `icon-friends.png` | два человечка | ex6, «что сказал бы друг» |
| `icon-letter.png` | конверт | ex8, письмо поддержки |
| `icon-message.png` | сообщение | ex9 |
| `icon-call.png` | телефонная трубка | ex9 |
| `icon-magic.png` | палочка с искрами | ex9, «свой вариант» |
| `icon-quote.png` | открывающая кавычка | карточка аффирмации |
| `icon-ambience-silence.png` | луна | Медитация: «Тишина» |
| `icon-ambience-rain.png` | дождевое облако | Медитация: «Дождь» |
| `icon-ambience-ocean.png` | волны | Медитация: «Океан» |

---

## 4. Замена в коде: таблица соответствий

Прямая карта «старый SF Symbol → новый ассет». Если в коде встречается
системное имя слева — менять на имя справа.

| SF Symbol | Файл |
|---|---|
| `flame.fill` | `icon-streak` |
| `star.circle.fill` / валюта | `icon-lumen` |
| `snowflake` | `icon-freeze` |
| `book.fill` (таб) | `icon-tab-courses` |
| `person.crop.circle.fill` (таб) | `icon-tab-profile` |
| `trophy.fill` | `icon-trophy` |
| `sunrise.fill` | `icon-sunrise` |
| `book.closed.fill` | `icon-book` |
| `note.text` | `icon-journal` |
| `checkmark.seal.fill` | `icon-seal` |
| `calendar` | `icon-calendar` |
| `bag.fill` | `icon-shop` |
| `chart.bar.fill` | `icon-stats` |
| `gearshape.fill` | `icon-settings` |
| `pencil` | `icon-edit` |
| `bell.fill` | `icon-bell` |
| `lock.fill` | `icon-lock` |
| `eyeglasses` | `icon-glasses` |
| `crown.fill` | `icon-crown` |
| `target` | `icon-target` |
| `plus.circle.fill` | `icon-plus` |
| `lightbulb.fill` | `icon-hint` |
| `bolt.fill` | `icon-bolt` |
| `exclamationmark.bubble.fill` | `icon-critic-voice` |
| `clock.fill` | `icon-clock` |
| `heart` | `icon-heart-outline` |
| `heart.fill` | `icon-heart-fill` |
| `exclamationmark.circle.fill` | `icon-anxiety` |
| `questionmark.circle.fill` | `icon-question` |
| `headphones` | `icon-headphones` |
| `hand.tap.fill` | `icon-tap` |
| `face.smiling` | `icon-smile` |
| `person.2.fill` | `icon-friends` |
| `envelope.fill` | `icon-letter` |
| `message.fill` | `icon-message` |
| `phone.fill` | `icon-call` |
| `wand.and.stars` | `icon-magic` |
| `quote.opening` | `icon-quote` |
| `moon.fill` | `icon-ambience-silence` |
| `cloud.rain.fill` | `icon-ambience-rain` |
| `water.waves` | `icon-ambience-ocean` |

---

## 5. Откуда берутся файлы

Иконки, как и маскот, **генерируются кодом** — `icons.py` на Pillow. Любую
можно пересобрать в другом размере или поправить форму, не открывая
редактор.

```bash
pip install pillow

# весь набор, чёрные силуэты, 1024 px
python3 icons.py --export assets/icons --size 1024

# тот же набор с запечённым цветом
python3 icons.py --export assets/icons-colored --size 1024 --colored

# одна иконка
python3 icons.py --one icon-streak --out /tmp/streak.png --size 512

# лист набора для проверки
python3 icons.py
```

### Как устроен файл

* Логическая сетка **512 × 512**, суперсэмплинг ×4, уменьшение LANCZOS —
  отсюда гладкие края. Любая координата проходит через `s()` / `sbox()`.
* Базовая толщина линии — `W = 38`. Менять её стоит только для всего
  набора сразу, иначе иконки рассинхронизируются по весу.
* Каждая иконка — функция, которая рисует в `L`-маску: `255` кладёт
  форму, `0` вырезает. Цвет накладывается один раз в конце, в
  `render_icon()`.
* Примитивы: `line`, `disc`, `ring`, `arc`, `rrect`, `poly` (с
  per-vertex скруглением), `sparkle`, `heart_pts`, `merged` (повернуть
  и подмешать), `clipped` (обрезать по маске).

### Как добавить иконку

```python
def icon_new(m):
    d = ImageDraw.Draw(m)
    ring(d, C, C, 158, 34)
    line(d, [(C, 166), (C, 346)], 36)

ICONS["icon-new"] = (icon_new, "#C9C2E6", "Описание для листа")
PRIORITY[3].append("icon-new")
```

---

## 6. Грабли

1. **Не забыть Template Image.** Самая частая ошибка — иконка вставлена,
   но остаётся чёрной, потому что имиджсет отрисовывается как обычная
   картинка.
2. **Не масштабировать непропорционально.** Файлы квадратные, ставить
   через `.scaledToFit()`.
3. **Не смешивать наборы.** Либо весь экран из `icons/` с tint, либо весь
   из `icons-colored/`. Иначе часть значков не будет реагировать на смену
   темы.
4. **Не перерисовывать поверх.** Если нужна другая форма — правится
   функция в `icons.py` и пересобирается набор, тогда толщина линии
   остаётся общей.
