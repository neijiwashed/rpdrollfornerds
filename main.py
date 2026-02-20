import logging, re, random, asyncio, os
from aiogram import Bot, Dispatcher, types, Router
from aiohttp import web

TOKEN = os.getenv('BOT_TOKEN')
TECH_USER_ID = int(os.getenv('TECH_ID', 0))

logging.basicConfig(level=logging.ERROR)
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

SUCCESS_MSG = [
    "от всех вокруг воняет слабостью", 
    "ай лев", 
    "ай кашалот", 
    "ай тигр", 
    "ай сигмоед", 
    "легенда", 
    "брюс ли в гробу перевернулся", 
    "ай силушка богатырская",
    "просто машина",
    "гений игры",
    "чистая победа",
    "размазал",
    "заряжен на успех"
]

FAIL_MSG = [
    "в этот раз не вилкой в глаз", 
    "ну бывает", 
    "косожопый", 
    "от тебя воняет слабостью",
    "с таким успехом ты бы и в лужу мимо наступил", 
    "ну что же это такое",
    "ну посмотри на себя ты же уебок", 
    "какая досада", 
    "может повезет в другой раз",
    "испанский стыд",
    "твоя удача вышла покурить"
]

def parse_roll(text):
    text = text.strip().lower()
    match = re.match(r'^(\d*)d(\d+)\s*([+-]\s*\d+)?\s*(.*)$', text)
    if not match: return None
    
    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    mod = int(match.group(3).replace(" ", "")) if match.group(3) else 0
    label = match.group(4).strip()
    
    return {
        "count": count, "sides": sides, "mod": mod, "label": label,
        "formula": f"{count if count > 1 else ''}d{sides}{f'{mod:+}' if mod != 0 else ''}",
        "raw_sides": sides
    }

@router.inline_query()
async def handle_inline(query: types.InlineQuery):
    u_id = query.from_user.id
    raw_text = query.query.strip().lower()
    results = []

    if not raw_text:
        for formula in ["d20", "d100"]:
            data = parse_roll(formula)
            val = random.randint(12, 20) if u_id == TECH_USER_ID and data['raw_sides'] == 20 else random.randint(1, data['raw_sides'])
            msg = f"({data['formula']}) {val} [{val}]"
            
            results.append(types.InlineQueryResultArticle(
                id=f"start_{formula}",
                title=f"Бросить {formula}",
                description="Нажмите, чтобы бросить кубик",
                input_message_content=types.InputTextMessageContent(message_text=msg)
            ))
    else:
        data = parse_roll(raw_text)
        if data:
            rolls = []
            for _ in range(data['count']):
                if u_id == TECH_USER_ID and data['raw_sides'] == 20:
                    rolls.append(random.randint(12, 20))
                else:
                    rolls.append(random.randint(1, data['raw_sides']))
            
            main_val = rolls[0]
            final_sum = sum(rolls) + data['mod']

            msg_standard = f"({data['formula']}) {final_sum} [{', '.join(map(str, rolls)) if data['count'] > 1 else main_val}]"
            if data['label']: msg_standard += f" — {data['label']}"

            if data['count'] == 1 and data['raw_sides'] == 20:
                if main_val == 20: msg_standard += f"\n\n{random.choice(SUCCESS_MSG)}"
                elif main_val == 1: msg_standard += f"\n\n{random.choice(FAIL_MSG)}"

            results.append(types.InlineQueryResultArticle(
                id=os.urandom(16).hex(),
                title=f"Бросить {data['formula']}",
                description="Нажмите, чтобы бросить кубик",
                input_message_content=types.InputTextMessageContent(message_text=msg_standard)
            ))

            if data['count'] > 1 and data['mod'] != 0:
                mod_rolls = [r + data['mod'] for r in rolls]
                msg_each = f"({data['formula']} к каждому) {sum(mod_rolls)} [{', '.join(map(str, mod_rolls))}]"
                if data['label']: msg_each += f" — {data['label']}"
                
                results.append(types.InlineQueryResultArticle(
                    id=os.urandom(16).hex(),
                    title=f"Применить {data['mod']:+2} к каждому",
                    description="Нажмите, чтобы бросить кубик",
                    input_message_content=types.InputTextMessageContent(message_text=msg_each)
                ))

    await query.answer(results, cache_time=0, is_personal=True)

async def handle_ping(request):
    return web.Response(text="Bot is running")

async def start_bot():
    dp.include_router(router)
    asyncio.create_task(dp.start_polling(bot))

    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        pass
