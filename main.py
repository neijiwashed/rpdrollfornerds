import logging, re, random, asyncio, os
from aiogram import Bot, Dispatcher, types, Router
from aiohttp import web

API_TOKEN = os.getenv('BOT_TOKEN')

logging.basicConfig(level=logging.ERROR)
bot = Bot(token=API_TOKEN)
router = Router()

CRIT_SUCCESS_PHRASES = [
    "от всех вокруг воняет слабостью", "ай лев", "ай кашалот", "ай тигр", 
    "ай сигмоед", "легенда", "брюс ли в гробу перевернулся", "ай силушка богатырская",
    "просто машина", "гений игры", "чистая победа", "размазал", "бог рандома сегодня с тобой",
    "заряжен на успех", "вызывайте санитаров, тут маньяк везения"
]

CRIT_FAIL_PHRASES = [
    "в этот раз не вилкой в глаз", "ну бывает", "косожопый", "от тебя воняет слабостью",
    "с таким успехом ты бы и в лужу мимо наступил", "ну что же это такое",
    "ну посмотри на себя ты же уебок", "какая досада", "может повезет в другой раз",
    "удали игру", "полный провал", "испанский стыд", "минус вайб", "карма настигла",
    "твоя удача вышла покурить"
]

def get_roll_data(text):
    text = text.strip().lower()
    match = re.match(r'^(\d*)d(\d+)\s*([+-]\s*\d+)?\s*(.*)$', text)
    if not match: return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    mod = int(match.group(3).replace(" ", "")) if match.group(3) else 0
    description = match.group(4).strip()
    
    return {
        "count": count, "sides": sides, "mod": mod, 
        "formula": f"{count if count > 1 else ''}d{sides}{f'{mod:+}' if mod != 0 else ''}", 
        "text": description
    }

@router.inline_query()
async def inline_handler(query: types.InlineQuery):
    input_text = query.query.strip().lower()
    options_to_process = [input_text] if input_text else ["d20", "d100"]

    results = []
    for opt in options_to_process:
        data = get_roll_data(opt)
        if not data: continue

        rolls = [random.randint(1, data['sides']) for _ in range(data['count'])]
        raw_roll = rolls[0]
        total = sum(rolls) + data['mod']
        
        res_text = f"({data['formula']}) {total} [{', '.join(map(str, rolls)) if data['count'] > 1 else raw_roll}]"
        if data['text']: res_text += f" — {data['text']}"
        
        if data['count'] == 1 and data['sides'] == 20:
            if raw_roll == 20:
                res_text += f"\n\n{random.choice(CRIT_SUCCESS_PHRASES)}"
            elif raw_roll == 1:
                res_text += f"\n\n{random.choice(CRIT_FAIL_PHRASES)}"

        results.append(types.InlineQueryResultArticle(
            id=os.urandom(16).hex(),
            title=f"Бросить {data['formula']}",
            description="Нажмите, чтобы бросить кубик",
            input_message_content=types.InputTextMessageContent(message_text=res_text)
        ))

        if data['count'] > 1 and data['mod'] != 0:
            mod_rolls = [r + data['mod'] for r in rolls]
            res_each = f"({data['formula']} к каждому) {sum(mod_rolls)} [{', '.join(map(str, mod_rolls))}]"
            if data['text']: res_each += f" — {data['text']}"
            
            results.append(types.InlineQueryResultArticle(
                id=os.urandom(16).hex(),
                title=f"Применить {data['mod']:+2} к каждому",
                description="Нажмите, чтобы бросить кубик",
                input_message_content=types.InputTextMessageContent(message_text=res_each)
            ))

    await query.answer(results, cache_time=0, is_personal=True)

async def handle(request): return web.Response(text="Bot is running")

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
