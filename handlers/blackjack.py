import os
import random
import sqlite3
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, \
    InputMediaPhoto
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from __init__ import *  # cursor, conn, bot и т.д.

blackjack = Router()

CARDS_PATH = "cards"
FONT_PATH = "PlayfairDisplay.ttf"

# ======= Конфигурация карт =======
suit_map = {"H": "❤️", "S": "♠️", "D": "♦️", "C": "♣️"}
card_values = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10,
    "J": 10, "Q": 10, "K": 10, "A": 11
}

blackjack_timers = {}  # user_id -> asyncio.Task


class Blackjack(StatesGroup):
    bet = State()


# ======= Подсчет очков =======
def hand_value(hand: list) -> int:
    """Считаем очки в руке с учетом правил Блэкджека"""
    value = 0
    aces_as_eleven = 0

    for card in hand:
        rank = card.replace("card_", "")
        for symbol in suit_map.values():
            rank = rank.replace(symbol, "")
        if rank.upper() == "A":
            if aces_as_eleven < 2:
                value += 11
                aces_as_eleven += 1
            else:
                value += 1
        else:
            value += card_values.get(rank.upper(), 0)

    while value > 21 and aces_as_eleven > 0:
        value -= 10
        aces_as_eleven -= 1

    return value


# ======= Генерация колоды =======
def generate_deck() -> list:
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    suits = ["H", "S", "D", "C"]
    deck = [f"card_{rank}{suit_map[s]}" for rank in ranks for s in suits]
    random.shuffle(deck)
    return deck


def card_to_filename(card: str) -> str:
    return f"{card}.png"


def blackjack_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Взять карту", callback_data=f"hit_{user_id}"),
                          InlineKeyboardButton(text="Хватит", callback_data=f"stand_{user_id}")]]
    )


# ======= Рисуем стол =======
def render_table(player_cards: list, dealer_cards: list, player_value: int, dealer_value: int, user_id: int,
                 hide_dealer: bool = True) -> str:
    display_dealer = [dealer_cards[0]] + ["back"] * (len(dealer_cards) - 1) if hide_dealer else dealer_cards
    CARD_WIDTH, CARD_HEIGHT = 80, 120
    CARD_SPACING = 20
    TEXT_PADDING = 20
    SHADOW_OFFSET = 3
    SHADOW_COLOR = (0, 0, 0, 70)
    SHADOW_BLUR = 5
    SHADOW_ROUNDING = 5

    def load_images(cards: list) -> list:
        images = []
        for card in cards:
            path = os.path.join(CARDS_PATH, card_to_filename(card))
            if not os.path.exists(path):
                raise FileNotFoundError(f"Файл карты не найден: {path}")
            img = Image.open(path).convert("RGBA").resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
            images.append(img)
        return images

    dealer_imgs = load_images(display_dealer)
    player_imgs = load_images(player_cards)
    table = Image.open(os.path.join(CARDS_PATH, "table.png")).convert("RGBA")
    width, height = table.size
    draw = ImageDraw.Draw(table)
    try:
        font = ImageFont.truetype(FONT_PATH, 28)
    except:
        font = ImageFont.load_default()

    draw.text((width // 2 - 60, TEXT_PADDING - 20),
              f"Дилер: {dealer_value if not hide_dealer else '?'}", fill="white", font=font)
    draw.text((width // 2 - 60, height // 2 + TEXT_PADDING - 20),
              f"Игрок: {player_value}", fill="white", font=font)

    def calc_positions(images: list, y_start: int):
        n = len(images)
        total_width = n * CARD_WIDTH + (n - 1) * CARD_SPACING
        x_start = max((width - total_width) // 2, 0)
        positions = [(x_start + i * (CARD_WIDTH + CARD_SPACING), y_start) for i in range(n)]
        return positions

    dealer_positions = calc_positions(dealer_imgs, y_start=TEXT_PADDING + 40)
    player_positions = calc_positions(player_imgs, y_start=height // 2 + TEXT_PADDING + 40)

    def add_shadow(img: Image.Image, pos: tuple):
        shadow_mask = Image.new("L", img.size, 0)
        draw_local = ImageDraw.Draw(shadow_mask)
        draw_local.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=SHADOW_ROUNDING, fill=255)
        shadow = Image.new("RGBA", img.size, SHADOW_COLOR)
        shadow.putalpha(shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
        table.paste(shadow, (pos[0] + SHADOW_OFFSET, pos[1] + SHADOW_OFFSET), shadow_mask)

    for img, pos in zip(dealer_imgs, dealer_positions):
        add_shadow(img, pos)
        table.paste(img, pos, img)
    for img, pos in zip(player_imgs, player_positions):
        add_shadow(img, pos)
        table.paste(img, pos, img)

    output_dir = "casino_playing"
    os.makedirs(output_dir, exist_ok=True)
    output_path = f"{output_dir}/table_{user_id}.png"
    table.save(output_path)
    return output_path


# ======= Таймер на 5 минут =======
async def blackjack_timeout(user_id: int, chat_id: int):
    try:
        await asyncio.sleep(300)  # 5 минут
        cursor.execute("SELECT if_playing, bet FROM blackjack WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        if not row or row[0] != "True":
            return

        bet = row[1]
        cursor.execute("DELETE FROM blackjack WHERE user_id=?", (user_id,))
        conn.commit()

        await bot.send_message(
            chat_id=chat_id,
            text=f"⏰ <a href='tg://user?id={user_id}'>Время вышло!</a>\n"
                 f"Вы проиграли ставку {bet:,}₽.",
        )
    except asyncio.CancelledError:
        # Таймер был отменён (новая игра началась)
        return
    finally:
        blackjack_timers.pop(user_id, None)


@blackjack.callback_query(F.data.startswith("go_blackjack_"))
async def cmd_go_blackjack(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cursor.execute("SELECT if_playing FROM blackjack WHERE user_id = ?", (user_id,))
    if_playing = cursor.fetchone()
    if if_playing and if_playing[0] == "True":
        await callback.answer("❌ Вы уже играете в Blackjack!")
        return

    await state.set_state(Blackjack.bet)
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"delete_message_{callback.from_user.id}")]
    ])
    await bot.send_message(chat_id=callback.message.chat.id,
                           text="💰 Введите желаемую ставку!",
                           reply_markup=inline_kb)


# ======= Обработка ставки =======
@blackjack.message(Blackjack.bet)
async def process_bet(message: Message, state: FSMContext):
    bet = message.text
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"delete_message_{message.from_user.id}")]
    ])

    if not bet.isdigit():
        await message.reply("❌ Мне нужна только ставка, без букв (например 100000)", reply_markup=inline_kb)
        return

    if int(bet) < 10000:
        await message.reply("❌ Ставка слишком маленькая! Минимальная ставка - 10,000₽", reply_markup=inline_kb)
        return

    cursor.execute("SELECT rubles FROM game WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    if not row:
        await message.reply("❌ Профиль не найден или нет баланса.")
        return
    rubles = row[0]

    if rubles < int(bet):
        await message.reply(f"❌ У вас недостаточно денег на балансе!\n💳Ваш баланс: {rubles:,}₽", reply_markup=inline_kb)
        return

    await state.update_data(bet=int(bet))
    inline_kb_confirm = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✔ Подтвердить", callback_data=f"start_blackjack_{message.from_user.id}"),
         InlineKeyboardButton(text="❌ Отменить", callback_data=f"delete_message_{message.from_user.id}")]
    ])
    await message.reply(f"💰 Подтвердите вашу ставку {int(bet):,}₽!", reply_markup=inline_kb_confirm)


# ======= Начало игры =======
@blackjack.callback_query(F.data.startswith("start_blackjack_"))
async def cmd_blackjack(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    bet = data.get("bet")
    if not bet or not str(bet).isdigit():
        await callback.answer("❌ Ставка не найдена.")
        await state.clear()
        return
    bet = int(bet)
    await state.clear()

    user_id = callback.from_user.id
    cursor.execute("SELECT rubles FROM game WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if not row:
        await callback.answer("❌ Профиль не найден.")
        return
    rubles = row[0]
    if rubles < bet:
        await callback.answer(f"❌ Недостаточно средств!\n💳Баланс: {rubles:,}₽")
        return

    # Снимаем ставку
    rubles -= bet
    cursor.execute("UPDATE game SET rubles=? WHERE user_id=?", (rubles, user_id))
    conn.commit()

    # Если есть старый таймер, отменяем
    if user_id in blackjack_timers:
        blackjack_timers[user_id].cancel()
        del blackjack_timers[user_id]

    # Генерация рук
    deck = generate_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]

    # Сохраняем игру в БД
    cursor.execute("DELETE FROM blackjack WHERE user_id=?", (user_id,))
    cursor.execute(
        "INSERT INTO blackjack (user_id, if_playing, deck, player_hand, dealer_hand, bet) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, "True", ",".join(deck), ",".join(player_hand), ",".join(dealer_hand), bet)
    )
    conn.commit()

    table_img = render_table(player_hand, dealer_hand, hand_value(player_hand), hand_value(dealer_hand), user_id,
                             hide_dealer=True)
    sent_msg = await bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=FSInputFile(table_img),
        caption=f"🃏 Ваш ход!\n💰 Ставка: {bet:,}₽\n💳 Баланс: {rubles:,}₽",
        reply_markup=blackjack_kb(user_id)
    )

    # Запускаем таймер
    task = asyncio.create_task(blackjack_timeout(user_id, sent_msg.chat.id))
    blackjack_timers[user_id] = task


@blackjack.callback_query(F.data.startswith(("hit", "stand")))
async def game_turn(callback: CallbackQuery):
    raw = callback.data
    action, target_user_id = raw.split("_", 1)
    target_user_id = int(target_user_id)

    cursor.execute("SELECT if_playing, deck, player_hand, dealer_hand, bet FROM blackjack WHERE user_id=?", (target_user_id,))
    row = cursor.fetchone()
    if not row:
        await callback.answer("Игра не найдена.")
        return

    if_playing, deck, player_hand, dealer_hand, bet = row
    if if_playing != "True":
        await callback.answer("❌ Игра уже завершена!")
        return

    deck = deck.split(",") if deck else []
    player_hand = player_hand.split(",") if player_hand else []
    dealer_hand = dealer_hand.split(",") if dealer_hand else []
    bet = int(bet)

    cursor.execute("SELECT rubles FROM game WHERE user_id=?", (target_user_id,))
    rubles = cursor.fetchone()[0]

    # --- HIT ---
    if action == "hit":
        if not deck:
            await callback.answer("❌ Карты в колоде закончились.")
            return

        player_hand.append(deck.pop())
        cursor.execute("UPDATE blackjack SET deck=?, player_hand=? WHERE user_id=?",
                       (",".join(deck), ",".join(player_hand), target_user_id))
        conn.commit()

        player_val = hand_value(player_hand)
        if player_val > 21:
            while hand_value(dealer_hand) < 17 and deck:
                dealer_hand.append(deck.pop())
            dealer_val = hand_value(dealer_hand)
            cursor.execute("UPDATE blackjack SET deck=?, dealer_hand=? WHERE user_id=?",
                           (",".join(deck), ",".join(dealer_hand), target_user_id))
            conn.commit()

            if dealer_val > 21:
                result = "⚔ Ничья! У обоих перебор."
                rubles += bet
            else:
                result = "🚫 Перебор! Вы проиграли."

            table_img = render_table(player_hand, dealer_hand, player_val, dealer_val, target_user_id, hide_dealer=False)
            await bot.edit_message_media(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                media=InputMediaPhoto(media=FSInputFile(table_img),
                                      caption=f"{result}\n💰 Ставка была: {bet:,}₽\n💳 Баланс: {rubles:,}₽"),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
            )
            cursor.execute("UPDATE game SET rubles=? WHERE user_id=?", (rubles, target_user_id))
            cursor.execute("DELETE FROM blackjack WHERE user_id=?", (target_user_id,))
            conn.commit()
            return

        table_img = render_table(player_hand, dealer_hand, player_val, hand_value(dealer_hand), target_user_id, hide_dealer=True)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=FSInputFile(table_img),
                                  caption=f"🃏 Ваш ход!\n💰 Ставка: {bet:,}₽\n💳 Баланс: {rubles:,}₽"),
            reply_markup=blackjack_kb(target_user_id)
        )
        return

    # --- STAND ---
    if action == "stand":
        while hand_value(dealer_hand) < 17 and deck:
            dealer_hand.append(deck.pop())

        player_val = hand_value(player_hand)
        dealer_val = hand_value(dealer_hand)
        cursor.execute("UPDATE blackjack SET deck=?, dealer_hand=? WHERE user_id=?",
                       (",".join(deck), ",".join(dealer_hand), target_user_id))
        conn.commit()

        if dealer_val > 21 or player_val > dealer_val:
            result = "🎉 Вы выиграли!"
            rubles += bet * 2
        elif dealer_val == player_val:
            result = "🤝 Ничья!"
            rubles += bet
        else:
            result = "🚫 Вы проиграли!"

        table_img = render_table(player_hand, dealer_hand, player_val, dealer_val, target_user_id, hide_dealer=False)
        await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=InputMediaPhoto(media=FSInputFile(table_img),
                                  caption=f"{result}\n💰 Ставка была: {bet:,}₽\n💳 Баланс: {rubles:,}₽"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[])
        )
        cursor.execute("UPDATE game SET rubles=? WHERE user_id=?", (rubles, target_user_id))
        cursor.execute("DELETE FROM blackjack WHERE user_id=?", (target_user_id,))
        conn.commit()
        return
