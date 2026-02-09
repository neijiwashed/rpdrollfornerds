import logging, re, random, asyncio, os
from aiogram import Bot, Dispatcher, types, Router
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
router = Router()

def get_roll(text):
    text = text.replace(" ", "").lower()
    match = re.match(r'^(\d*)d(\d+)([+-]\d+)?$', text)
    if not match: return None
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0
    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + mod
    return {"total": total, "natural": rolls if count > 1 else rolls[0], "formula": text}

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    input_text = query.query.strip().lower()
    results = []
    formulas = ["d20", "d100"] if not input_text else [input_text]
    for f in formulas:
        data = get_roll(f)
        if data:
            msg_text = f"({data['formula']}) {data['total']} [{data['natural']}]"
            res_title = f"Кинуть {data['formula']}"
            unique_id = f"RESULT_{data['total']}_{random.randint(1000, 9999)}"
            results.append(types.InlineQueryResultArticle(
                id=unique_id, title=res_title, description="Нажми для броска",
                input_message_content=types.InputTextMessageContent(message_text=msg_text)
            ))
    await query.answer(results, cache_time=0, is_personal=True)

async def handle(request):
    return web.Response(text="Bot is online")

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    
    print("🟢 Бот запускается...")
    await asyncio.gather(
        dp.start_polling(bot, skip_updates=True),
        site.start()
    )

if __name__ == '__main__':
    asyncio.run(main())