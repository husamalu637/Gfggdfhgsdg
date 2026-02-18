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
    """معادلة بواسون الخفيفة: (e^-mean * mean^actual) / factorial(actual)"""
    try:
        return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)
    except:
        return 0

def get_football_data(endpoint):
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

@bot.message_handler(commands=['start'])
def start_radar(message):
    bot.reply_to(message, "🔍 جاري تشغيل الرادار الرياضي... فحص جميع الدوريات عن فرص > 60%")
    
    all_opportunities = ""
    
    for league in LEAGUES:
        standings = get_football_data(f"competitions/{league}/standings")
        matches = get_football_data(f"competitions/{league}/matches?status=SCHEDULED")
        
        if not standings or not matches: continue
        
        team_stats = {t['team']['name']: t for t in standings['standings'][0]['table']}
        
        for m in matches['matches'][:10]:
            h_name, a_name = m['homeTeam']['name'], m['awayTeam']['name']
            
            if h_name in team_stats and a_name in team_stats:
                h, a = team_stats[h_name], team_stats[a_name]
                
                # حساب التوقعات (Lambda)
                exp_h = (h['goalsFor']/h['playedGames']) * (a['goalsAgainst']/a['playedGames']) * 1.1
                exp_a = (a['goalsFor']/a['playedGames']) * (h['goalsAgainst']/h['playedGames'])
                
                p_win, p_loss = 0, 0
                for gh in range(5):
                    for ga in range(5):
                        prob = calculate_poisson(gh, exp_h) * calculate_poisson(ga, exp_a)
                        if gh > ga: p_win += prob
                        elif ga > gh: p_loss += prob
                
                win_chance = p_win * 100
                loss_chance = p_loss * 100
                
                # فلتر الـ 60%
                if win_chance >= 60 or loss_chance >= 60:
                    side = "🏠 فوز الأرض" if win_chance > loss_chance else "🚀 فوز الضيف"
                    chance = max(win_chance, loss_chance)
                    all_opportunities += f"🏆 {league} | {h_name} × {a_name}\n📈 الثقة: {chance:.1f}% ({side})\n---\n"

    if all_opportunities:
        bot.send_message(message.chat.id, "🚀 **الفرص الذهبية المكتشفة:**\n\n" + all_opportunities, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ لا توجد مباريات قوية حالياً.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
    
