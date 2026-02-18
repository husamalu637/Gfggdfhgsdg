import telebot
import requests
import math
import time

# --- الإعدادات ---
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL'] # الدوريات الكبرى

bot = telebot.TeleBot(BOT_TOKEN)

def calculate_poisson(actual, mean):
    """معادلة بواسون يدوية لتوفير المساحة: (e^-mean * mean^actual) / factorial(actual)"""
    try:
        return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)
    except:
        return 0

def get_data(endpoint):
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@bot.message_handler(commands=['start'])
def start_radar(message):
    bot.send_message(message.chat.id, "🔍 جاري تشغيل الرادار... جاري فحص جميع الدوريات الكبرى عن فرص تتجاوز 60%.")
    
    results = ""
    for league in LEAGUES:
        standings = get_data(f"competitions/{league}/standings")
        matches = get_data(f"competitions/{league}/matches?status=SCHEDULED")
        
        if not standings or not matches: continue
        
        table = {t['team']['name']: t for t in standings['standings'][0]['table']}
        
        for m in matches['matches'][:10]:
            h_name, a_name = m['homeTeam']['name'], m['awayTeam']['name']
            
            if h_name in table and a_name in table:
                h, a = table[h_name], table[a_name]
                
                # حساب Lambda (متوسط الأهداف المتوقع)
                exp_h = (h['goalsFor']/max(h['playedGames'],1)) * (a['goalsAgainst']/max(a['playedGames'],1)) * 1.1
                exp_a = (a['goalsFor']/max(a['playedGames'],1)) * (h['goalsAgainst']/max(h['playedGames'],1))
                
                p_win, p_loss = 0, 0
                for gh in range(5):
                    for ga in range(5):
                        prob = calculate_poisson(gh, exp_h) * calculate_poisson(ga, exp_a)
                        if gh > ga: p_win += prob
                        elif ga > gh: p_loss += prob
                
                win_pct, loss_pct = p_win * 100, p_loss * 100
                
                # فلتر القيمة (تجاوز 60%)
                if win_pct >= 60 or loss_pct >= 60:
                    side = "🏠 صاحب الأرض" if win_pct > loss_pct else "🚀 الضيف"
                    chance = max(win_pct, loss_pct)
                    results += f"🏆 {league} | {h_name} × {a_name}\n📈 الثقة: {chance:.1f}% ({side})\n---\n"

    if results:
        bot.send_message(message.chat.id, "🚀 **الفرص الذهبية المكتشفة:**\n\n" + results, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ لا توجد مباريات قوية حالياً تتخطى 60%.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
    
