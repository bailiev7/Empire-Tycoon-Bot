import random
from itertools import combinations
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
)
from PIL import Image, ImageDraw, ImageFilter

poker = Router()

# Активные столы
poker_tables = {}

suits = ["♠️", "❤️", "♦️", "♣️"]
ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
rank_values = {r: i for i, r in enumerate(ranks, start=2)}


# ===================== Утилиты ======================

def new_deck():
    return [f"card_{r}{s}" for r in ranks for s in suits]


def card_to_filename(card: str) -> str:
    return f"cards/{card}.png"


def pretty(card: str) -> str:
    return card.replace("card_", "")


def get_rank(card: str) -> str:
    if card.startswith("card_"):
        card = card[5:]  # убираем "card_"
    for s in ["♠️", "❤️", "♦️", "♣️"]:
        card = card.replace(s, "")
    return card


# ===================== Визуализация карт ======================

def render_cards(cards: list[str], out_path="cards/temp.png") -> str:
    if not cards:
        return "cards/empty.png"

    # Загружаем карты в высоком разрешении
    images = [Image.open(card_to_filename(c)).convert("RGBA").resize((500, 700), Image.LANCZOS) for c in cards]
    w, h = images[0].size

    table_width = len(images) * (w - 100) + 200
    table_height = h + 200
    table_bg = Image.new("RGBA", (table_width, table_height), (0, 100, 0, 255))
    draw = ImageDraw.Draw(table_bg)

    # Текстура сукна точками
    for x in range(0, table_width, 15):
        for y in range(0, table_height, 15):
            draw.point((x, y), fill=(0, 120, 0, 255))

    # Мягкий блик на столе
    light = Image.new("RGBA", (table_width, table_height), (255, 255, 255, 0))
    light_draw = ImageDraw.Draw(light)
    light_draw.ellipse([table_width // 4, table_height // 4, 3 * table_width // 4, 3 * table_height // 4],
                       fill=(255, 255, 255, 30))
    light = light.filter(ImageFilter.GaussianBlur(80))
    table_bg = Image.alpha_composite(table_bg, light)

    # Размещаем карты с наклоном и тенью
    for i, img in enumerate(images):
        offset_x = 100 + i * (w - 150)
        offset_y = 100
        angle = -10 + i * 5
        rotated_img = img.rotate(angle, expand=True)

        # тень
        shadow = Image.new("RGBA", rotated_img.size, (0, 0, 0, 120))
        table_bg.paste(shadow, (offset_x + 20, offset_y + 20), shadow)

        table_bg.paste(rotated_img, (offset_x, offset_y), rotated_img)

    table_bg.save(out_path)
    return out_path


# ===================== Оценка комбинаций ======================

def evaluate_hand(cards: list[str]) -> tuple:
    values = []
    for c in cards:
        rank = get_rank(c)
        if rank not in rank_values:
            raise ValueError(f"Неизвестный ранг карты: {c}")
        values.append(rank_values[rank])

    suits_cards = [c[-1] for c in cards]
    counts = {v: values.count(v) for v in set(values)}
    sorted_vals = sorted(values, reverse=True)

    flush = None
    for s in suits:
        suited = [values[i] for i in range(len(cards)) if suits_cards[i] == s]
        if len(suited) >= 5:
            flush = sorted(suited, reverse=True)

    unique_vals = sorted(set(values))
    if 14 in unique_vals:
        unique_vals.insert(0, 1)
    straight = None
    for i in range(len(unique_vals) - 4):
        window = unique_vals[i:i + 5]
        if window[-1] - window[0] == 4:
            straight = window[-1]

    if flush:
        for comb in combinations(flush, 5):
            if max(comb) - min(comb) == 4 and len(set(comb)) == 5:
                if max(comb) == 14:
                    return 10, "Royal Flush", sorted(comb, reverse=True)
                return 9, "Straight Flush", sorted(comb, reverse=True)

    for v, cnt in counts.items():
        if cnt == 4:
            kickers = [x for x in sorted_vals if x != v]
            return 8, "Four of a Kind", [v] * 4 + kickers[:1]

    three = [v for v, cnt in counts.items() if cnt == 3]
    pair = [v for v, cnt in counts.items() if cnt >= 2 and v not in three]
    if three and pair:
        return 7, "Full House", [max(three)] * 3 + [max(pair)] * 2

    if flush:
        return 6, "Flush", flush[:5]

    if straight:
        return 5, "Straight", [straight, straight - 1, straight - 2, straight - 3, straight - 4]

    if three:
        kickers = [x for x in sorted_vals if x != max(three)]
        return 4, "Three of a Kind", [max(three)] * 3 + kickers[:2]

    pairs = sorted([v for v, cnt in counts.items() if cnt == 2], reverse=True)
    if len(pairs) >= 2:
        kicker = [x for x in sorted_vals if x not in pairs]
        return 3, "Two Pair", [pairs[0]] * 2 + [pairs[1]] * 2 + kicker[:1]

    if pairs:
        kicker = [x for x in sorted_vals if x != pairs[0]]
        return 2, "One Pair", [pairs[0]] * 2 + kicker[:3]

    return 1, "High Card", sorted_vals[:5]


def hand_name(cards):
    _, name, _ = evaluate_hand(cards)
    return name


# ===================== Клавиатуры ======================

def get_keyboard(table_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Чек / Колл", callback_data=f"poker_call_{table_id}")],
        [InlineKeyboardButton(text="💰 Рейз", callback_data=f"poker_raise_{table_id}")],
        [InlineKeyboardButton(text="❌ Фолд", callback_data=f"poker_fold_{table_id}")]
    ])


# ===================== Команды ======================

#@poker.message(F.text == "/poker")
async def cmd_poker(message: Message):
    table_id = message.chat.id
    if table_id in poker_tables:
        await message.answer("♣️ В этом чате уже есть активный стол!")
        return

    poker_tables[table_id] = {
        "players": [],
        "deck": new_deck(),
        "community": [],
        "stage": "waiting",
        "current": 0,
        "moves_this_round": 0
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✋ Присоединиться", callback_data=f"join_poker_{table_id}")],
        [InlineKeyboardButton(text="▶️ Начать", callback_data=f"start_poker_{table_id}")]
    ])

    await message.answer("♠️ Игра в покер создана!\nЖмите 'Присоединиться'.", reply_markup=kb)


@poker.callback_query(F.data.startswith("join_poker_"))
async def join_poker(callback: CallbackQuery):
    table_id = int(callback.data.split("_")[-1])
    user = callback.from_user
    table = poker_tables.get(table_id)

    if not table:
        await callback.answer("Стол не найден.", show_alert=True)
        return

    if any(p["id"] == user.id for p in table["players"]):
        await callback.answer("Вы уже за столом!", show_alert=True)
        return

    table["players"].append({"id": user.id, "name": user.first_name, "hand": [], "active": True})

    await callback.message.edit_text(
        "♠️ Игроки за столом:\n" +
        "\n".join([p["name"] for p in table["players"]]),
        reply_markup=callback.message.reply_markup
    )


@poker.callback_query(F.data.startswith("start_poker_"))
async def start_poker(callback: CallbackQuery):
    await callback.answer("⚙ В разработке")
    return

    table_id = int(callback.data.split("_")[-1])
    table = poker_tables.get(table_id)

    if not table or len(table["players"]) < 2:
        await callback.answer("Нужно минимум 2 игрока!", show_alert=True)
        return

    random.shuffle(table["deck"])

    # Раздаём каждому по 2 карты
    for player in table["players"]:
        player["hand"] = [table["deck"].pop(), table["deck"].pop()]
        try:
            img = render_cards(player["hand"], f"cards/hand_{player['id']}.png")
            await callback.bot.send_photo(
                player["id"],
                photo=FSInputFile(img),
                caption=f"🃏 Ваши карты: {pretty(player['hand'][0])} {pretty(player['hand'][1])}"
            )
        except:
            pass

    table["stage"] = "preflop"
    table["current"] = 0
    table["moves_this_round"] = 0

    await callback.message.edit_text("♠️ Раздача завершена! Первый игрок начинает.")
    await next_turn(callback.message, table_id)


# ===================== Ходы игроков ======================

async def next_turn(message: Message, table_id: int):
    table = poker_tables[table_id]

    active_players = [p for p in table["players"] if p["active"]]
    if len(active_players) == 1:
        await message.answer(f"🏆 Победитель: {active_players[0]['name']} (остался один)")
        del poker_tables[table_id]
        return

    player = table["players"][table["current"]]
    if not player["active"]:
        table["current"] = (table["current"] + 1) % len(table["players"])
        await next_turn(message, table_id)
        return

    await message.answer(f"👉 Ход игрока: {player['name']}", reply_markup=get_keyboard(table_id))


async def advance_stage(message: Message, table_id: int):
    table = poker_tables[table_id]

    if table["stage"] == "preflop":
        table["community"] = [table["deck"].pop() for _ in range(3)]
        table["stage"] = "flop"
    elif table["stage"] == "flop":
        table["community"].append(table["deck"].pop())
        table["stage"] = "turn"
    elif table["stage"] == "turn":
        table["community"].append(table["deck"].pop())
        table["stage"] = "river"
    else:
        results = []
        for p in table["players"]:
            if p["active"]:
                combo = evaluate_hand(p["hand"] + table["community"])
                results.append((combo, p))
        winner = max(results, key=lambda x: x[0])
        winners = [p for c, p in results if c == winner[0]]

        text = "🔔 Шоудаун!\n\n"
        for combo, p in results:
            text += f"{p['name']}: {hand_name(p['hand'] + table['community'])}\n"

        if len(winners) == 1:
            text += f"\n🏆 Победитель: {winners[0]['name']}!"
        else:
            text += "\n🤝 Ничья между: " + ", ".join(p["name"] for p in winners)

        await message.answer(text)
        del poker_tables[table_id]
        return

    table_img = render_cards(table["community"], "cards/table.png")
    await message.answer_photo(
        FSInputFile(table_img),
        caption=f"Карты на столе: {' '.join(pretty(c) for c in table['community'])}"
    )

    for p in table["players"]:
        if p["active"]:
            try:
                await message.bot.send_message(
                    p["id"],
                    f"👉 Текущая комбинация: {hand_name(p['hand'] + table['community'])}"
                )
            except:
                pass

    table["current"] = 0
    table["moves_this_round"] = 0
    await next_turn(message, table_id)


async def player_move(callback: CallbackQuery, action: str):
    table_id = int(callback.data.split("_")[-1])
    table = poker_tables[table_id]
    player = table["players"][table["current"]]

    if action == "call":
        await callback.message.answer(f"{player['name']} сделал ЧЕК / КОЛЛ")
    elif action == "raise":
        await callback.message.answer(f"{player['name']} сделал РЕЙЗ (пока без суммы)")
    elif action == "fold":
        player["active"] = False
        await callback.message.answer(f"{player['name']} сбросил карты (ФОЛД)")

    table["current"] = (table["current"] + 1) % len(table["players"])
    table["moves_this_round"] += 1

    active_count = len([p for p in table["players"] if p["active"]])
    if table["moves_this_round"] >= active_count:
        await advance_stage(callback.message, table_id)
    else:
        await next_turn(callback.message, table_id)


# ===================== Обработчики кнопок ======================

@poker.callback_query(F.data.startswith("poker_call_"))
async def action_call(callback: CallbackQuery):
    await player_move(callback, "call")


@poker.callback_query(F.data.startswith("poker_raise_"))
async def action_raise(callback: CallbackQuery):
    await player_move(callback, "raise")


@poker.callback_query(F.data.startswith("poker_fold_"))
async def action_fold(callback: CallbackQuery):
    await player_move(callback, "fold")
