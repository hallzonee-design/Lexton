import asyncio
import json
import os
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# НАСТРОЙКИ
BOT_TOKEN = "8796485876:AAEAn_lmU8d_O60YC98UDpznXZhOFirM3mM"
ADMIN_ID = 8617203586
ADMIN_USERNAME = "lexxtoon"  # без @, маленькими
SECRET_CODE = "JSDOEBDO-DKFENDO-EKEDJFODKF"

START_DATE = datetime(2026, 5, 18)

BASE_PRICE = 968
INCREASE_RATE = 1.0020
VIP_BASE_PRICE = 1200
VIP_INCREASE_RATE = 1.0011

MSK_TZ = timezone(timedelta(hours=3))
DISTRIBUTION_DATETIME_MSK = datetime(2026, 6, 1, 5, 0, 0, tzinfo=MSK_TZ)

ZIP_FILE_PATH = "otvet.zip"
DATA_FILE = "bot_data.json"
LOGS_FILE = "logs.json"

# Состояния для FSM
class AdminStates(StatesGroup):
    waiting_for_username = State()
    waiting_for_vip_username = State()

logs = []

def load_logs():
    global logs
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)

def save_logs():
    with open(LOGS_FILE, "w", encoding="utf-8") as f:
        json.dump(logs[-100:], f, ensure_ascii=False, indent=2)

def add_log(user_id, username, action):
    logs.append({
        "time": datetime.now(MSK_TZ).strftime("%d.%m.%Y %H:%M:%S"),
        "user_id": user_id,
        "username": username or f"ID:{user_id}",
        "action": action
    })
    save_logs()

load_logs()

def get_current_price(vip=False):
    now = datetime.now()
    periods = (now - START_DATE).days // 13
    if vip:
        return round(VIP_BASE_PRICE * (VIP_INCREASE_RATE ** periods))
    return round(BASE_PRICE * (INCREASE_RATE ** periods))

def get_next_price_date():
    now = datetime.now()
    current_period = (now - START_DATE).days // 13
    next_date = START_DATE + timedelta(days=(current_period + 1) * 13)
    return next_date.strftime("%d.%m.%Y")

data = {"users": {}, "distribution_done": False}

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

load_data()
if "users" not in data:
    data["users"] = {}
if "distribution_done" not in data:
    data["distribution_done"] = False
save_data()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Клавиатуры
def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📦 Купить ответы")],
            [types.KeyboardButton(text="👑 VIP ответы")],
            [types.KeyboardButton(text="📋 Мои покупки"), types.KeyboardButton(text="ℹ️ Поддержка")]
        ],
        resize_keyboard=True
    )

def admin_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="➕ Подтвердить оплату")],
            [types.KeyboardButton(text="👑 VIP подтвердить")],
            [types.KeyboardButton(text="📊 Статистика"), types.KeyboardButton(text="📝 Логи")],
            [types.KeyboardButton(text="📨 Рассылка сейчас")]
        ],
        resize_keyboard=True
    )

# СТАРТ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or ""
    
    add_log(uid, username, "Запустил бота")
    
    if uid == ADMIN_ID:
        await message.answer(
            "👑 <b>Админ-панель</b>\nВыбери действие:",
            reply_markup=admin_keyboard()
        )
    else:
        price = get_current_price()
        vip_price = get_current_price(vip=True)
        next_date = get_next_price_date()
        
        await message.answer(
            f"🎓 <b>Ответы на ОГЭ 2026</b>\n\n"
            f"Реальные варианты, решённые заранее.\n"
            f"Файл придёт <b>за 5-6 часов до экзамена</b>.\n\n"
            f"💸 <b>Стандарт:</b> {price}₽ (+0.20% каждые 13 дней)\n"
            f"👑 <b>VIP:</b> {vip_price}₽ (+0.11% каждые 13 дней)\n\n"
            f"📅 Повышение цен: <b>{next_date}</b>\n\n"
            f"👇 Выбирай тариф:",
            reply_markup=main_keyboard()
        )

# КНОПКА "КУПИТЬ ОТВЕТЫ"
@dp.message(F.text == "📦 Купить ответы")
async def buy_answers(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or ""
    add_log(uid, username, "Нажал 'Купить ответы'")
    
    price = get_current_price()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить (Ozon)", url="https://finance.ozon.ru/apps/sbp/ozonbankpay/019b01bd-6df5-7ae2-a466-f09a95dac173")],
        [InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    
    await message.answer(
        f"📦 <b>Стандартный доступ</b>\n\n"
        f"💳 Стоимость: <b>{price}₽</b>\n\n"
        f"1️⃣ Нажми <b>«Оплатить»</b> и переведи точную сумму\n"
        f"2️⃣ Нажми <b>«Написать админу»</b> и пришли скриншот оплаты\n\n"
        f"✅ После проверки получишь уведомление\n"
        f"📆 Файл придёт за 5-6 часов до экзамена",
        reply_markup=kb
    )

# КНОПКА "VIP ОТВЕТЫ"
@dp.message(F.text == "👑 VIP ответы")
async def buy_vip(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or ""
    add_log(uid, username, "Нажал 'VIP ответы'")
    
    vip_price = get_current_price(vip=True)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить VIP (Ozon)", url="https://finance.ozon.ru/apps/sbp/ozonbankpay/019b01bd-6df5-7ae2-a466-f09a95dac173")],
        [InlineKeyboardButton(text="✍️ Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    
    await message.answer(
        f"👑 <b>VIP доступ</b>\n\n"
        f"💳 Стоимость: <b>{vip_price}₽</b>\n\n"
        f"📋 Что входит:\n"
        f"• ВСЕ ответы на все предметы\n"
        f"• ПОДРОБНЫЕ решения каждого задания\n"
        f"• САМЫЕ точные варианты\n\n"
        f"1️⃣ Нажми <b>«Оплатить»</b> и переведи точную сумму\n"
        f"2️⃣ Нажми <b>«Написать админу»</b> и пришли скриншот\n\n"
        f"✅ После проверки получишь уведомление\n"
        f"📆 Файл придёт за 5-6 часов до экзамена",
        reply_markup=kb
    )

# КНОПКА "МОИ ПОКУПКИ"
@dp.message(F.text == "📋 Мои покупки")
async def my_purchases(message: types.Message):
    uid = str(message.from_user.id)
    username = message.from_user.username or ""
    add_log(message.from_user.id, username, "Проверил покупки")
    
    user = data["users"].get(uid, {})
    
    if user.get("vip"):
        status = "👑 VIP доступ активен\n📆 Файл придёт за 5-6 часов до экзамена"
    elif user.get("paid"):
        status = "📦 Стандартный доступ активен\n📆 Файл придёт за 5-6 часов до экзамена"
    else:
        status = "❌ Нет активных покупок"
    
    await message.answer(f"<b>Ваш статус:</b>\n{status}")

# КНОПКА "ПОДДЕРЖКА" - СРАЗУ ОТКРЫВАЕТ ЧАТ С АДМИНОМ
@dp.message(F.text == "ℹ️ Поддержка")
async def support(message: types.Message):
    uid = message.from_user.id
    username = message.from_user.username or ""
    add_log(uid, username, "Нажал 'Поддержка'")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать админу", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    
    await message.answer(
        "📬 <b>Нужна помощь?</b>\n\n"
        "Нажми кнопку ниже чтобы сразу перейти в чат с админом:\n"
        f"<code>@{ADMIN_USERNAME}</code>",
        reply_markup=kb
    )

# ========== АДМИН-КНОПКИ ==========

# КНОПКА "ПОДТВЕРДИТЬ ОПЛАТУ"
@dp.message(F.text == "➕ Подтвердить оплату", F.from_user.id == ADMIN_ID)
async def admin_accept_button(message: types.Message, state: FSMContext):
    await message.answer("Введи @username пользователя для подтверждения СТАНДАРТ:")
    await state.set_state(AdminStates.waiting_for_username)

@dp.message(AdminStates.waiting_for_username)
async def process_accept_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lstrip("@").lower()
    
    found = False
    for uid, u in data["users"].items():
        if u.get("username", "").lower() == username:
            data["users"][uid]["paid"] = True
            save_data()
            add_log(message.from_user.id, "admin", f"Подтвердил стандарт @{username}")
            
            await message.answer(f"✅ Стандарт для @{username} подтверждён!")
            try:
                await bot.send_message(
                    int(uid),
                    "✅ <b>Оплата подтверждена!</b>\n\n"
                    "📆 Файл с ответами придёт <b>за 5-6 часов до экзамена</b>.\n"
                    "Мы подготовили для вас лучшие варианты!"
                )
            except:
                pass
            found = True
            break
    
    if not found:
        await message.answer(f"❌ @{username} не найден в базе. Пусть сначала запустит бота.")
    
    await state.clear()

# КНОПКА "VIP ПОДТВЕРДИТЬ"
@dp.message(F.text == "👑 VIP подтвердить", F.from_user.id == ADMIN_ID)
async def admin_vip_button(message: types.Message, state: FSMContext):
    await message.answer("Введи @username для VIP подтверждения:")
    await state.set_state(AdminStates.waiting_for_vip_username)

@dp.message(AdminStates.waiting_for_vip_username)
async def process_vip_username(message: types.Message, state: FSMContext):
    username = message.text.strip().lstrip("@").lower()
    
    found = False
    for uid, u in data["users"].items():
        if u.get("username", "").lower() == username:
            data["users"][uid]["paid"] = True
            data["users"][uid]["vip"] = True
            save_data()
            add_log(message.from_user.id, "admin", f"Подтвердил VIP @{username}")
            
            await message.answer(f"✅ VIP для @{username} подтверждён!")
            try:
                await bot.send_message(
                    int(uid),
                    "✅ <b>VIP доступ активирован!</b>\n\n"
                    "Вы получите:\n"
                    "• ВСЕ ответы на все предметы\n"
                    "• ПОДРОБНЫЕ решения каждого задания\n"
                    "• САМЫЕ точные варианты\n\n"
                    "📆 Файл придёт <b>за 5-6 часов до экзамена</b>"
                )
            except:
                pass
            found = True
            break
    
    if not found:
        await message.answer(f"❌ @{username} не найден. Пусть сначала запустит бота.")
    
    await state.clear()

# КНОПКА "СТАТИСТИКА"
@dp.message(F.text == "📊 Статистика", F.from_user.id == ADMIN_ID)
async def admin_stats(message: types.Message):
    users = data.get("users", {})
    total = len(users)
    paid = sum(1 for u in users.values() if u.get("paid"))
    vip = sum(1 for u in users.values() if u.get("vip"))
    standard = paid - vip
    
    await message.answer(
        "📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"💰 Всего оплатило: <b>{paid}</b>\n"
        f"📦 Стандарт: <b>{standard}</b>\n"
        f"👑 VIP: <b>{vip}</b>\n\n"
        f"💵 Стандарт: <b>{get_current_price()}₽</b>\n"
        f"💎 VIP: <b>{get_current_price(vip=True)}₽</b>\n"
        f"📅 Повышение цен: <b>{get_next_price_date()}</b>"
    )

# КНОПКА "ЛОГИ"
@dp.message(F.text == "📝 Логи", F.from_user.id == ADMIN_ID)
async def admin_logs(message: types.Message):
    if not logs:
        await message.answer("📝 Логов пока нет")
        return
    
    recent = logs[-20:]
    text = "📝 <b>Последние действия:</b>\n\n"
    for log in reversed(recent):
        text += f"🕐 {log['time']}\n👤 @{log['username']}\n📌 {log['action']}\n\n"
    
    await message.answer(text)

# КНОПКА "РАССЫЛКА СЕЙЧАС"
@dp.message(F.text == "📨 Рассылка сейчас", F.from_user.id == ADMIN_ID)
async def admin_broadcast_button(message: types.Message):
    await broadcast_zip(message)

# Сохранение пользователей
@dp.message()
async def save_user(message: types.Message):
    uid = str(message.from_user.id)
    username = message.from_user.username or ""
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "username": username,
            "paid": False,
            "vip": False,
            "zip_sent": False
        }
        add_log(message.from_user.id, username, "Первый раз в боте")
    else:
        if data["users"][uid].get("username") != username:
            data["users"][uid]["username"] = username
    
    if "vip" not in data["users"][uid]:
        data["users"][uid]["vip"] = False
    
    save_data()

# Секретный код
@dp.message(F.text == SECRET_CODE, F.from_user.id == ADMIN_ID)
async def secret_broadcast(message: types.Message):
    await broadcast_zip(message)

async def broadcast_zip(trigger=None):
    if not os.path.exists(ZIP_FILE_PATH):
        if trigger:
            await trigger.answer("❌ Файл otvet.zip не найден")
        return
    
    standard_users = [uid for uid, u in data["users"].items() 
                     if u.get("paid") and not u.get("vip") and not u.get("zip_sent")]
    vip_users = [uid for uid, u in data["users"].items() 
                if u.get("vip") and not u.get("zip_sent")]
    
    if not standard_users and not vip_users:
        if trigger:
            await trigger.answer("Нет пользователей для отправки")
        return
    
    sent_standard = 0
    sent_vip = 0
    
    # Отправка VIP
    for uid in vip_users:
        try:
            await bot.send_document(
                int(uid),
                FSInputFile(ZIP_FILE_PATH),
                caption="👑 Ваши VIP ответы на ОГЭ! Полные решения всех заданий. Мы подготовили для вас самые точные варианты. Удачи!"
            )
            data["users"][uid]["zip_sent"] = True
            sent_vip += 1
            add_log(int(uid), data["users"][uid].get("username"), "Получил VIP файл")
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Ошибка VIP {uid}: {e}")
    
    # Отправка стандарт
    for uid in standard_users:
        try:
            await bot.send_document(
                int(uid),
                FSInputFile(ZIP_FILE_PATH),
                caption="📦 Ваши ответы на ОГЭ! Мы подготовили для вас лучшие варианты. Удачи на экзамене!"
            )
            data["users"][uid]["zip_sent"] = True
            sent_standard += 1
            add_log(int(uid), data["users"][uid].get("username"), "Получил стандарт файл")
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Ошибка стандарт {uid}: {e}")
    
    save_data()
    if trigger:
        await trigger.answer(
            f"✅ Рассылка завершена!\n"
            f"👑 VIP: {sent_vip}\n"
            f"📦 Стандарт: {sent_standard}"
        )

async def scheduled():
    if data.get("distribution_done"):
        return
    now = datetime.now(MSK_TZ)
    target = DISTRIBUTION_DATETIME_MSK
    if now >= target:
        await broadcast_zip()
        data["distribution_done"] = True
        save_data()
    else:
        wait_seconds = (target - now).total_seconds()
        print(f"Ожидание {wait_seconds:.0f} сек...")
        await asyncio.sleep(wait_seconds)
        await broadcast_zip()
        data["distribution_done"] = True
        save_data()

async def main():
    asyncio.create_task(scheduled())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())