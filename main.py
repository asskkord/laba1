import os

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import yt_dlp

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot, Dispatcher
import asyncio
import logging




TOKEN = '7414232508:AAEczCMQryhbnH3I1ufj9u5STIcv8_j6IGc'
IMAGE_API_URL = ''

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()


router = Router()

# Клавиатура с основными кнопками, которые пользователи могут нажать

# Создаём инлайн-кнопку для генерации изображений
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
        f"Рад познакомиться! 😊\n\n"
        f"Что бы вы хотели сделать? 🤔",
        reply_markup=kb_main
    )


# Обработчик для кнопки с ссылкой на GitHub
@router.callback_query(F.data == 'urlOfGitHub')
async def ret_to_mainkb(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('https://github.com/asskkord/laba1.git', reply_markup=kb_main)


async def download_audio(anime_title):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')  # Создаем папку для загрузки, если ее нет

    ydl_opts = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': f'downloads/{anime_title}.mp3',
    }

    try:
        # Используем yt-dlp для скачивания аудио
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{anime_title} мэшап", download=True)
            if search_results['entries']:
                audio_file = f"downloads/{anime_title}.mp3"
                return audio_file if os.path.exists(audio_file) else None
            else:
                return None
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return None


# Обработчик для кнопки "find a music"
@router.callback_query(F.data == 'find_music')
async def transitToAudioFunc(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Введите текстовый запрос для получения аудиофайла. 🎶"
    )
    await state.set_state(Form.audio_get)
    await callback_query.answer()


@router.message(Form.audio_get)
async def InputNameOfMusic(message: types.Message, state: FSMContext):
    audio_file = await download_audio(message.text)
    if audio_file and os.path.exists(audio_file):
        with open(audio_file, 'rb') as file:
            audio_byte_io = FSInputFile(audio_file)
            await state.clear()
            await message.answer_audio(audio_byte_io)
        os.remove(audio_file)  # Удаляем файл после отправки
    else:
        await message.reply("Не удалось найти мэшап")


# Словарь с заранее заготовленными изображениями
images_dict = {
    "гора": "images/mountain.jpg",
    "лес": "images/forest.jpg",
    "река": "images/river.jpg"
}


# Обработчик для кнопки "Generate images"
@router.callback_query(F.data == 'generate_image')
async def gen_image_callback(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.answer(
        "Введите название изображения (гора, лес, река). 🖼"
    )
    await state.set_state(Form.waiting_for_prompt)
    await callback_query.answer()


@router.message(Form.waiting_for_prompt)
async def send_image(message: Message, state: FSMContext):
    image_name = message.text.lower()  # Приводим к нижнему регистру для сопоставления

    if image_name in images_dict:
        image_path = images_dict[image_name]

        if os.path.exists(image_path):
            # Передаем путь к файлу вместо объекта BufferedReader
            photo = types.FSInputFile(image_path)
            await message.answer_photo(photo)
            await message.answer(f'Вот ваше изображение: {image_name}.')
        else:
            await message.answer("Изображение не найдено.")
    else:
        await message.answer("Извините, я не знаю такого изображения.")

    await state.clear()  # Сбрасываем состояние после обработки запроса

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except:
        print("exit")
