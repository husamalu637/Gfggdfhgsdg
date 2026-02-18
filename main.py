import telebot
import requests
import scipy.stats as stats
import time
import logging

# إعداد السجلات (Logs) لمتابعة عمل البوت على السيرفر
logging.basicConfig(level=logging.INFO)

# --- ضع مفاتيحك هنا ---
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'

bot = telebot.TeleBot(BOT_TOKEN)

def get_standings(league_code):
    """جلب ترتيب الدوري لقياس القوة الهجومية والدفاعية"""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()['standings'][0]['table']
            return {item['team']['name']: item for item in data}
    except Exception as e:
        logging.error(f"Error fetching standings: {e}")
    return None

def get_upcoming_matches(league_code):
    """جلب المباريات الحقيقية القادمة المجدولة"""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches?status=SCHEDULED"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()['matches'][:10] # تحليل القادمة فقط
    except Exception as e:
        logging.error(f"Error fetching matches: {e}")
    return None

@bot.message_handler(commands=['start', 'help'])
def start_command(message):
    msg = (
        "📊 **محلل مباريات كرة القدم الذكي (v2.0)**\n\n"
        "أرسل كود الدوري لتحليل احتمالات النتائج:\n"
        "🇬🇧 الدوري الإنجليزي: `PL`\n"
        "🇪🇺 دوري الأبطال: `CL`\n"
        "🇪🇸 الدوري الإسباني: `PD`\n"
        "🇮🇹 الدوري الإيطالي: `SA`\n"
        "🇩🇪 الدوري الألماني: `BL1`"
    )
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(func=lambda m: len(m.text) <= 4)
def handle_analysis(message):
    league = message.text.upper()
    bot.send_message(message.chat.id, f"⏳ جاري سحب البيانات وتحليل مباريات {league}...")
    
    standings = get_standings(league)
    matches = get_upcoming_matches(league)
    
    if not standings or not matches:
        bot.reply_to(message, "❌ لم أجد بيانات متاحة حالياً. تأكد من الكود أو الـ API.")
        return

    for match in matches:
        h_name = match['homeTeam']['name']
        a_name = match['awayTeam']['name']
        
        if h_name in standings and a_name in standings:
            h_d, a_d = standings[h_name], standings[a_name]
            
            # حساب متوسط الأهداف المتوقع (Lambda) بناءً على بواسون
            exp_h = (h_d['goalsFor']/h_d['playedGames']) * (a_d['goalsAgainst']/a_d['playedGames']) * 1.10
            exp_a = (a_d['goalsFor']/a_d['playedGames']) * (h_d['goalsAgainst']/h_d['playedGames'])
            
            p_win, p_draw, p_loss = 0, 0, 0
            score_probs = []
            
            # مصفوفة الاحتمالات الرقمية
            for gh in range(5):
                for ga in range(5):
                    p = stats.poisson.pmf(gh, exp_h) * stats.poisson.pmf(ga, exp_a)
                    if gh > ga: p_win += p
                    elif gh == ga: p_draw += p
                    else: p_loss += p
                    score_probs.append((f"{gh}-{ga}", p * 100))

            score_probs.sort(key=lambda x: x[1], reverse=True)

            res = (f"🏟️ **{h_name} × {a_name}**\n"
                   f"📅 التاريخ: {match['utcDate'].split('T')[0]}\n"
                   f"--------------------------\n"
                   f"🏠 فوز: {p_win*100:.1f}% | 🤝 تعادل: {p_draw*100:.1f}% | 🚀 خسارة: {p_loss*100:.1f}%\n\n"
                   f"🎯 **أهم النتائج المحتملة:**\n"
                   f"✅ {score_probs[0][0]} ({score_probs[0][1]:.1f}%)\n"
                   f"✅ {score_probs[1][0]} ({score_probs[1][1]:.1f}%)\n"
                   f"✅ {score_probs[2][0]} ({score_probs[2][1]:.1f}%)\n"
                   f"--------------------------")
            bot.send_message(message.chat.id, res, parse_mode="Markdown")

# تشغيل مستمر للسيرفر
if __name__ == "__main__":
    while True:
        try:
            logging.info("Bot is starting...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"Connection lost, retrying in 5 seconds: {e}")
            time.sleep(5)
