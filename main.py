import logging
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

# ===== AYARLAR =====
TELEGRAM_TOKEN = "8335704519:AAGEOdWFuXWS-qnlHOMF_zJI42Xd3Bc_tGI"
NANOBANANA_API_KEY = "edb4ae873917a1fb07693f522d0aea9a"
NANOBANANA_URL = "https://api.nanobananaapi.ai/v1/image"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

user_lang = {}
user_mode = {}

# ===== DİL METİNLERİ =====
TEXT = {
    "tr": {
        "welcome": "👋 Hoş geldin!\nLütfen dil seç:",
        "menu": "Ne yapmak istiyorsun?",
        "gen": "🖼 Resim Oluştur",
        "edit": "✏️ Resim Düzenle",
        "prompt": "Detaylı olarak ne istediğini yaz:",
        "send_photo": "Lütfen düzenlenecek resmi gönder:",
    },
    "tk": {
        "welcome": "👋 Hoş geldiň!\nDil saýla:",
        "menu": "Näme etmek isleýärsiň?",
        "gen": "🖼 Surat Döretmek",
        "edit": "✏️ Surat Üýtgetmek",
        "prompt": "Islegiňi örän detal bilen ýaz:",
        "send_photo": "Üýtgediljek suraty iber:",
    }
}

# ===== START =====
@dp.message(CommandStart())
async def start(msg: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇹🇷 Türkçe", callback_data="lang_tr")
    kb.button(text="🇹🇲 Türkmençe", callback_data="lang_tk")
    await msg.answer("Dil seç / Dil saýla:", reply_markup=kb.as_markup())

# ===== DİL SEÇİMİ =====
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_lang(cb: types.CallbackQuery):
    lang = cb.data.split("_")[1]
    user_lang[cb.from_user.id] = lang

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXT[lang]["gen"], callback_data="gen")],
        [InlineKeyboardButton(text=TEXT[lang]["edit"], callback_data="edit")]
    ])
    await cb.message.answer(TEXT[lang]["menu"], reply_markup=kb)

# ===== MOD SEÇİM =====
@dp.callback_query(lambda c: c.data in ["gen", "edit"])
async def set_mode(cb: types.CallbackQuery):
    user_mode[cb.from_user.id] = cb.data
    lang = user_lang.get(cb.from_user.id, "tr")

    if cb.data == "gen":
        await cb.message.answer(TEXT[lang]["prompt"])
    else:
        await cb.message.answer(TEXT[lang]["send_photo"])

# ===== RESİM OLUŞTUR =====
@dp.message(lambda m: m.from_user.id in user_mode and user_mode[m.from_user.id] == "gen")
async def generate_image(msg: types.Message):
    prompt = msg.text

    payload = {
        "prompt": prompt,
        "quality": "ultra",
        "detail": "maximum"
    }

    headers = {
        "Authorization": f"Bearer {NANOBANANA_API_KEY}"
    }

    r = requests.post(NANOBANANA_URL + "/generate", json=payload, headers=headers)
    img_url = r.json()["image_url"]

    await msg.answer_photo(photo=img_url)

# ===== RESİM DÜZENLE =====
@dp.message(lambda m: m.photo)
async def edit_image(msg: types.Message):
    lang = user_lang.get(msg.from_user.id, "tr")

    await msg.answer(TEXT[lang]["prompt"])
    photo = msg.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file.file_path}"

    user_mode[msg.from_user.id] = {"edit_photo": file_url}

@dp.message(lambda m: isinstance(user_mode.get(m.from_user.id), dict))
async def edit_prompt(msg: types.Message):
    data = user_mode[msg.from_user.id]
    prompt = msg.text

    payload = {
        "image": data["edit_photo"],
        "prompt": prompt,
        "detail": "ultra",
        "realism": "max"
    }

    headers = {
        "Authorization": f"Bearer {NANOBANANA_API_KEY}"
    }

    r = requests.post(NANOBANANA_URL + "/edit", json=payload, headers=headers)
    img_url = r.json()["image_url"]

    await msg.answer_photo(photo=img_url)
    user_mode[msg.from_user.id] = None

# ===== ÇALIŞTIR =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
