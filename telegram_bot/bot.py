"""
BreastHealth Monitor - Telegram Bot
"""
import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile
from dotenv import load_dotenv

load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Create bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()


# States for FSM
class InputStates(StatesGroup):
    waiting_for_temps = State()
    waiting_for_image = State()


# Keyboards
def get_main_keyboard():
    """Main menu keyboard."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Текущий статус", callback_data="status")],
        [InlineKeyboardButton(text="📝 Ввести температуры", callback_data="input_temps")],
        [InlineKeyboardButton(text="📷 Загрузить термограмму", callback_data="upload_image")],
        [InlineKeyboardButton(text="📈 История", callback_data="history")],
        [InlineKeyboardButton(text="🤖 AI Анализ", callback_data="ai_analysis")]
    ])
    return keyboard


def get_risk_emoji(risk_level: str) -> str:
    """Get emoji for risk level."""
    return {
        "NORMAL": "✅",
        "ELEVATED": "⚠️",
        "HIGH": "🔴"
    }.get(risk_level, "❓")


# Handlers
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start command handler."""
    await message.answer(
        "🩺 <b>BreastHealth Monitor</b>\n\n"
        "Добро пожаловать в систему мониторинга здоровья молочных желез.\n\n"
        "Выберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Help command handler."""
    help_text = """
🩺 <b>BreastHealth Monitor - Справка</b>

<b>Доступные команды:</b>
/start - Главное меню
/status - Текущий статус
/input - Ввести температуры вручную
/history - История измерений
/help - Эта справка

<b>Как использовать:</b>
1️⃣ Введите температуры с 8 зон вручную
2️⃣ Или загрузите термограмму
3️⃣ Система проанализирует данные
4️⃣ Получите заключение и рекомендации

⚠️ <i>Система не заменяет консультацию врача!</i>
"""
    await message.answer(help_text, parse_mode="HTML")


@router.callback_query(F.data == "status")
async def callback_status(callback: types.CallbackQuery):
    """Status callback handler."""
    await callback.answer()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/analysis/current") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("status") == "no_data":
                        await callback.message.answer(
                            "📊 <b>Статус</b>\n\n"
                            "Нет данных для анализа.\n"
                            "Добавьте измерение или загрузите термограмму.",
                            parse_mode="HTML",
                            reply_markup=get_main_keyboard()
                        )
                        return
                    
                    measurement = data.get("measurement", {})
                    analysis = data.get("analysis", {})
                    risk_emoji = get_risk_emoji(analysis.get("risk_level", ""))
                    
                    status_text = f"""
📊 <b>Текущий статус</b>

🌡️ <b>Последнее измерение:</b>
• Левая грудь: {measurement.get('avg_left', 0):.1f}°C
• Правая грудь: {measurement.get('avg_right', 0):.1f}°C
• Асимметрия: {measurement.get('asymmetry', 0):.2f}°C

{risk_emoji} <b>Уровень риска:</b> {analysis.get('risk_level', 'Неизвестно')}

📅 Время: {measurement.get('timestamp', '')[:16]}
"""
                    await callback.message.answer(
                        status_text,
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard()
                    )
                else:
                    await callback.message.answer(
                        "❌ Ошибка получения данных. Сервер недоступен.",
                        reply_markup=get_main_keyboard()
                    )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка подключения к серверу.\n\n<i>{str(e)}</i>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data == "input_temps")
async def callback_input_temps(callback: types.CallbackQuery, state: FSMContext):
    """Start temperature input."""
    await callback.answer()
    await state.set_state(InputStates.waiting_for_temps)
    
    await callback.message.answer(
        "📝 <b>Ввод температур</b>\n\n"
        "Введите 8 значений температуры через пробел или запятую.\n"
        "Порядок: L1, L2, L3, L4, R1, R2, R3, R4\n\n"
        "<i>Пример: 36.4 36.5 36.3 36.4 36.8 37.0 36.9 36.7</i>\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )


@router.message(InputStates.waiting_for_temps)
async def process_temps_input(message: types.Message, state: FSMContext):
    """Process temperature input."""
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Ввод отменён.", reply_markup=get_main_keyboard())
        return
    
    # Parse temperatures
    text = message.text.replace(",", " ")
    parts = text.split()
    
    try:
        temps = [float(p) for p in parts]
        if len(temps) != 8:
            raise ValueError("Нужно 8 значений")
        
        # Validate range
        for t in temps:
            if not (30 <= t <= 45):
                raise ValueError(f"Температура {t} вне диапазона 30-45°C")
        
        # Send to API
        async with aiohttp.ClientSession() as session:
            payload = {
                "sensor_1": temps[0], "sensor_2": temps[1],
                "sensor_3": temps[2], "sensor_4": temps[3],
                "sensor_5": temps[4], "sensor_6": temps[5],
                "sensor_7": temps[6], "sensor_8": temps[7],
                "source": "telegram"
            }
            async with session.post(f"{API_URL}/api/measurements", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    risk_emoji = get_risk_emoji(data.get("risk_level", ""))
                    
                    result_text = f"""
✅ <b>Данные сохранены!</b>

📊 <b>Результаты анализа:</b>
• Средняя слева: {data['metrics']['avg_left']:.1f}°C
• Средняя справа: {data['metrics']['avg_right']:.1f}°C
• Асимметрия: {data['metrics']['asymmetry']:.2f}°C

{risk_emoji} <b>Уровень риска:</b> {data['risk_level']}

<b>Заключение:</b>
{data['conclusion'][:500]}
"""
                    await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_keyboard())
                else:
                    await message.answer("❌ Ошибка сохранения данных.", reply_markup=get_main_keyboard())
        
        await state.clear()
        
    except ValueError as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}\n\n"
            "Попробуйте ещё раз или отправьте /cancel для отмены.",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка подключения: {str(e)}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()


@router.callback_query(F.data == "upload_image")
async def callback_upload_image(callback: types.CallbackQuery, state: FSMContext):
    """Start image upload."""
    await callback.answer()
    await state.set_state(InputStates.waiting_for_image)
    
    await callback.message.answer(
        "📷 <b>Загрузка термограммы</b>\n\n"
        "Отправьте инфракрасное изображение молочных желез.\n"
        "Поддерживаемые форматы: JPG, PNG\n\n"
        "Для отмены отправьте /cancel",
        parse_mode="HTML"
    )


@router.message(InputStates.waiting_for_image, F.photo)
async def process_image_upload(message: types.Message, state: FSMContext):
    """Process uploaded image."""
    await message.answer("⏳ Анализируем изображение...")
    
    try:
        # Get file
        photo = message.photo[-1]  # Get highest resolution
        file = await bot.get_file(photo.file_id)
        file_path = file.file_path
        
        # Download file
        file_content = await bot.download_file(file_path)
        
        # Upload to API
        async with aiohttp.ClientSession() as session:
            form = aiohttp.FormData()
            form.add_field('file', file_content.read(), filename='thermal.jpg', content_type='image/jpeg')
            
            async with session.post(f"{API_URL}/api/images/upload", data=form) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    risk_emoji = get_risk_emoji(data.get("risk_level", ""))
                    
                    result_text = f"""
✅ <b>Изображение проанализировано!</b>

📊 <b>Извлечённые температуры:</b>
{', '.join([f"{t:.1f}°C" for t in data['extracted_temps']])}

• Средняя слева: {data['metrics']['avg_left']:.1f}°C
• Средняя справа: {data['metrics']['avg_right']:.1f}°C
• Асимметрия: {data['metrics']['asymmetry']:.2f}°C

{risk_emoji} <b>Уровень риска:</b> {data['risk_level']}

<b>Заключение:</b>
{data['conclusion'][:500]}
"""
                    await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_keyboard())
                else:
                    await message.answer("❌ Ошибка анализа изображения.", reply_markup=get_main_keyboard())
        
        await state.clear()
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )
        await state.clear()


@router.callback_query(F.data == "history")
async def callback_history(callback: types.CallbackQuery):
    """History callback handler."""
    await callback.answer()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/analysis/history?limit=5") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if not data:
                        await callback.message.answer(
                            "📈 <b>История</b>\n\nНет записей.",
                            parse_mode="HTML",
                            reply_markup=get_main_keyboard()
                        )
                        return
                    
                    history_text = "📈 <b>Последние измерения:</b>\n\n"
                    for item in data[:5]:
                        risk_emoji = get_risk_emoji(item.get("risk_level", ""))
                        history_text += (
                            f"{risk_emoji} {item['timestamp'][:16]}\n"
                            f"   L: {item['avg_left']:.1f}°C | R: {item['avg_right']:.1f}°C | "
                            f"Δ: {item['asymmetry']:.2f}°C\n\n"
                        )
                    
                    await callback.message.answer(
                        history_text,
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard()
                    )
                else:
                    await callback.message.answer("❌ Ошибка загрузки истории.", reply_markup=get_main_keyboard())
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )


@router.callback_query(F.data == "ai_analysis")
async def callback_ai_analysis(callback: types.CallbackQuery):
    """AI Analysis callback."""
    await callback.answer()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/api/analysis/current") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    if data.get("status") == "no_data":
                        await callback.message.answer(
                            "🤖 <b>AI Анализ</b>\n\nНет данных для анализа.",
                            parse_mode="HTML",
                            reply_markup=get_main_keyboard()
                        )
                        return
                    
                    analysis = data.get("analysis", {})
                    conclusion = analysis.get("conclusion", "Нет заключения")
                    
                    await callback.message.answer(
                        f"🤖 <b>AI Анализ</b>\n\n{conclusion}",
                        parse_mode="HTML",
                        reply_markup=get_main_keyboard()
                    )
    except Exception as e:
        await callback.message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel current operation."""
    await state.clear()
    await message.answer("❌ Действие отменено.", reply_markup=get_main_keyboard())


# Register router
dp.include_router(router)


async def main():
    """Main entry point."""
    if not BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set!")
        return
    
    print("🤖 Starting BreastHealth Monitor Telegram Bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
