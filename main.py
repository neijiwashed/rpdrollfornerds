import logging, re, random, asyncio, os
from aiogram import Bot, Dispatcher, types, Router
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
router = Router()

def roll_dice(text):
    text = text.replace(" ", "").lower()
    match = re.match(r'^(\d*)d(\d+)([+-]\d+)?$', text)
    if not match: return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    mod = int(match.group(3)) if match.group(3) else 0
    
    rolls = [random.randint(1, sides) for _ in range(count)]
    
    return {
        "rolls": rolls,
        "mod": mod,
        "count": count,
        "sides": sides,
        "formula": text
    }

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    input_text = query.query.strip().lower()
    results = []
    
    formulas = ["d20", "d100"] if not input_text else [input_text]
    
    for f in formulas:
        data = roll_dice(f)
        if not data: continue
        
        total_sum = sum(data['rolls']) + data['mod']
        rolls_str = str(data['rolls']) if data['count'] > 1 else str(data['rolls'][0])
        
        mod_str = ""
        if data['mod'] > 0: mod_str = f"+{data['mod']}"
        elif data['mod'] < 0: mod_str = f"{data['mod']}"

        msg_text_1 = f"🎲 ({data['formula']}): {total_sum}\nКубы: {rolls_str} {mod_str}"
        
        results.append(types.InlineQueryResultArticle(
            id=f"RES_SUM_{random.randint(10000, 99999)}",
            title=f"Кинуть {data['formula']} (к итогу)",
            description=f"Результат: {total_sum}",
            input_message_content=types.InputTextMessageContent(message_text=msg_text_1)
        ))

        if data['count'] > 1 and data['mod'] != 0:
            rolls_modified = [r + data['mod'] for r in data['rolls']]
            total_per_die = sum(rolls_modified)
            
            msg_text_2 = f"🔥 ({data['formula']} к каждому): {total_per_die}\nКубы: {rolls_modified}"
            
            results.append(types.InlineQueryResultArticle(
                id=f"RES_EACH_{random.randint(10000, 99999)}",
                title=f"Кинуть {data['formula']} (к каждому)",
                description=f"Результат: {total_per_die} (бонус {mod_str} к кости)",
                input_message_content=types.InputTextMessageContent(message_text=msg_text_2)
            ))

    await query.answer(results, cache_time=0, is_personal=True)

async def handle(request):
    return web.Response(text="Bot is online and rolling!")

async def main():
    dp = Dispatcher()
    dp.include_router(router)
    
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    
    print("🟢 Бот запущен с новой функцией двойного подсчета...")
    await asyncio.gather(
        dp.start_polling(bot, skip_updates=True),
        site.start()
    )

if __name__ == '__main__':
    asyncio.run(main())
