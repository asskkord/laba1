import os
import asyncio
import logging
import requests
import yt_dlp
from aiogram import F, Router, types, Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Константы для токенов API
IMAGE_TOKEN = "FJIuYF5ujpnZIxRtpcRUCYuCtpMjaP-RMwU_pc1UJx4"
TOKEN = '7414232508:AAEczCMQryhbnH3I1ufj9u5STIcv8_j6IGc'

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# Клавиатура с основными кнопками для пользователей
kb_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🖼️ Генерация изображений', callback_data='generate_image')],
    [InlineKeyboardButton(text="🎶 Найти музыку", callback_data='find_music')],
    [InlineKeyboardButton(text="🔗 Где проект?", callback_data='urlOfGitHub')]
])

# Класс для состояний в FSM
class Form(StatesGroup):
    waiting_for_prompt = State()  # Ожидание ввода запроса для генерации изображения
    audio_get = State()  # Ожидание ввода названия музыки

# Обработчик команды /start
@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Что бы вы хотели сделать? 🤔",
        reply_markup=kb_main
    )

# Обработчик для кнопки с ссылкой на GitHub
@router.callback_query(F.data == 'urlOfGitHub')
async def ret_to_mainkb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('https://github.com/asskkord/laba1.git', reply_markup=kb_main)

# Функция для загрузки аудио по запросу пользователя
async def download_audio(sound: str) -> str:
    if not os.path.exists('downloads'):
        os.makedirs('downloads')  # Создаем папку для загрузки, если ее нет

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': f'downloads/{sound}.mp3',
    }

    try:
        # Используем yt-dlp для скачивания аудио
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{sound} мэшап", download=True)
            if search_results['entries']:
                audio_file = f"downloads/{sound}.mp3"
                return audio_file if os.path.exists(audio_file) else None
            return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None

# Обработчик для кнопки "Найти музыку"
@router.callback_query(F.data == 'find_music')
async def transit_to_audio_func(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите текстовый запрос для получения аудиофайла. 🎶")
    await state.set_state(Form.audio_get)
    await callback_query.answer()

# Обработчик получения названия музыки от пользователя
@router.message(Form.audio_get)
async def input_name_of_music(message: types.Message, state: FSMContext):
    audio_file = await download_audio(message.text)
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as file:
            audio_byte_io = FSInputFile(audio_file)
            await state.clear()
            await message.answer_audio(
                audio=audio_byte_io,
                caption="Вот аудио, которое соответствует вашему запросу.",
                reply_markup=kb_main
            )
        os.remove(audio_file)  # Удаляем файл после отправки
    else:
        await message.reply("Не удалось найти аудио.")

# Обработчик для кнопки "Генерация изображений"
@router.callback_query(F.data == "generate_image")
async def handle_image_generation(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текстовый запрос для получения изображения. 🖼")
    await state.set_state(Form.waiting_for_prompt)

# Обработчик получения запроса на изображение от пользователя
@router.message(Form.waiting_for_prompt)
async def process_image_query(message: Message, state: FSMContext):
    query = message.text.strip()
    image_url = fetch_image_url(query)

    if image_url:
        await message.answer_photo(
            photo=image_url,
            caption="Вот изображение, которое соответствует вашему запросу.",
            reply_markup=kb_main
        )
    else:
        await message.reply(
            "Не удалось найти подходящее изображение по вашему запросу. "
            "Попробуйте переформулировать запрос или добавьте больше деталей.",
            reply_markup=kb_main
        )
    await state.clear()

# Функция для получения URL изображения по запросу через API Unsplash
def fetch_image_url(query: str) -> str:
    api_url = f"https://api.unsplash.com/photos/random?query={query}&client_id={IMAGE_TOKEN}"
    response = requests.get(api_url)
    response.raise_for_status()  # Проверка на ошибки HTTP
    data = response.json()
    return data.get("urls", {}).get("regular", "")

# Основная функция для запуска бота
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)  # Настройка уровня логирования
    try:
        asyncio.run(main())
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")