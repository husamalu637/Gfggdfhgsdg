import telebot
import requests
import math
import time
import logging

# إعداد السجلات
logging.basicConfig(level=logging.INFO)

API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'

bot = telebot.TeleBot(BOT_TOKEN)

def poisson_probability(actual, mean):
    """حساب معادلة بواسون يدوياً لتوفير المساحة"""
    # Formula: (e^-mean * mean^actual) / factorial(actual)
    return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)

def get_data(endpoint):
    url = f"https://api.football-data.org/v4/competitions/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 **المحلل الرياضي (النسخة الخفيفة)**\nأرسل كود الدوري (PL, CL, PD) للبدء.")

@bot.message_handler(func=lambda m: len(m.text) <= 4)
def analyze(message):
    league = message.text.upper()
    bot.send_message(message.chat.id, f"⏳ جاري تحليل {league}...")
    
    standings_data = get_data(f"{league}/standings")
    matches_data = get_data(f"{league}/matches?status=SCHEDULED")
    
    if not standings_data or not matches_data:
        bot.reply_to(message, "❌ خطأ في البيانات.")
        return

    standings = {item['team']['name']: item for item in standings_data['standings'][0]['table']}
    
    for match in matches_data['matches'][:8]:
        h_name, a_name = match['homeTeam']['name'], match['awayTeam']['name']
        if h_name in standings and a_name in standings:
            h, a = standings[h_name], standings[a_name]
            
            # حساب المتوسطات
            exp_h = (h['goalsFor']/h['playedGames']) * (a['goalsAgainst']/a['playedGames']) * 1.1
            exp_a = (a['goalsFor']/a['playedGames']) * (h['goalsAgainst']/h['playedGames'])
            
            # حساب التوقعات
            p_win, p_draw, p_loss = 0, 0, 0
            scores = []
            for gh in range(5):
                for ga in range(5):
                    p = poisson_probability(gh, exp_h) * poisson_probability(ga, exp_a)
                    if gh > ga: p_win += p
                    elif gh == ga: p_draw += p
                    else: p_loss += p
                    scores.append((f"{gh}-{ga}", p * 100))
            
            scores.sort(key=lambda x: x[1], reverse=True)
            res = (f"🏟️ **{h_name} × {a_name}**\n"
                   f"🏠 {p_win*100:.1f}% | 🤝 {p_draw*100:.1f}% | 🚀 {p_loss*100:.1f}%\n"
                   f"🎯 النتائج الأرجح: {scores[0][0]} ({scores[0][1]:.1f}%)\n"
                   f"--------------------------")
            bot.send_message(message.chat.id, res, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except: time.sleep(5)
            
