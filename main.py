import logging, re, random, asyncio, os
from aiogram import Bot, Dispatcher, types, Router
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
router = Router()

def get_roll_data(text):
    text = text.replace(" ", "").lower()
    match = re.match(r'^(\d*)d(\d+)([+-]\d+)?$', text)
    if not match: return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0
    return {"count": count, "sides": sides, "mod": mod, "formula": text}

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    input_text = query.query.strip().lower()
    results = []
    
    formulas = ["d20", "d100"] if not input_text else [input_text]
    
    for f in formulas:
        data = get_roll_data(f)
        if not data: continue
        
        rolls = [random.randint(1, data['sides']) for _ in range(data['count'])]
        
        total_classic = sum(rolls) + data['mod']
        res_classic = f"({data['formula']}) {total_classic} [{', '.join(map(str, rolls)) if data['count'] > 1 else rolls[0]}]"
        
        title_classic = f"Классика {data['formula']}" if data['count'] > 1 and data['mod'] != 0 else f"Бросить {data['formula']}"
        
        results.append(types.InlineQueryResultArticle(
            id=f"classic_{random.getrandbits(64)}",
            title=title_classic,
            description="Нажмите, чтобы выполнить бросок",
            input_message_content=types.InputTextMessageContent(message_text=res_classic)
        ))

        if data['count'] > 1 and data['mod'] != 0:
            rolls_modded = [r + data['mod'] for r in rolls]
            total_each = sum(rolls_modded)
            res_each = f"({data['formula']} к каждому) {total_each} [{', '.join(map(str, rolls_modded))}]"
            
            results.append(types.InlineQueryResultArticle(
                id=f"each_{random.getrandbits(64)}",
                title=f"К каждому {data['formula']}",
                description="Нажмите, чтобы выполнить бросок",
                input_message_content=types.InputTextMessageContent(message_text=res_each)
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
    
    await asyncio.gather(dp.start_polling(bot, skip_updates=True), site.start())

if __name__ == '__main__':
    asyncio.run(main())
