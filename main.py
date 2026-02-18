import telebot
import requests
import math
import time

# --- الإعدادات (تأكد من صحة المفاتيح) ---
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
# الدوريات التي سيفحصها البوت تلقائياً
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL'] 

bot = telebot.TeleBot(BOT_TOKEN)

def poisson_prob(actual, mean):
    """حساب توزيع بواسون رياضياً بدون مكتبات خارجية"""
    try:
        # المعادلة: (e^-mean * mean^actual) / actual!
        return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)
    except: return 0

def get_data(endpoint):
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def scan_value_matches():
    """مسح شامل للدوريات للبحث عن فرص > 60%"""
    value_list = []
    for league in LEAGUES:
        standings_data = get_data(f"competitions/{league}/standings")
        matches_data = get_data(f"competitions/{league}/matches?status=SCHEDULED")
        
        if not standings_data or not matches_data: continue

        # ترتيب الفرق
        table = standings_data['standings'][0]['table']
        standings = {item['team']['name']: item for item in table}
        
        for match in matches_data['matches'][:12]: # فحص القادم
            h_team = match['homeTeam']['name']
            a_team = match['awayTeam']['name']
            
            if h_team in standings and a_team in standings:
                h_stat, a_stat = standings[h_team], standings[a_team]
                
                # حساب متوسط الأهداف المتوقع (Lambda)
                # ضربنا في 1.1 لتعويض عامل الأرض
                exp_h = (h_stat['goalsFor']/h_stat['playedGames']) * (a_stat['goalsAgainst']/a_stat['playedGames']) * 1.1
                exp_a = (a_stat['goalsFor']/a_stat['playedGames']) * (h_stat['goalsAgainst']/h_stat['playedGames'])
                
                p_win, p_loss = 0, 0
                all_scores = []
                
                # مصفوفة النتائج الممكنة
                for gh in range(5):
                    for ga in range(5):
                        prob = poisson_prob(gh, exp_h) * poisson_prob(ga, exp_a)
                        if gh > ga: p_win += prob
                        elif ga > gh: p_loss += prob
                        all_scores.append((f"{gh}-{ga}", prob * 100))
                
                # تحديد النسبة الأعلى وفحص فلتر الـ 60%
                win_chance = p_win * 100
                loss_chance = p_loss * 100
                max_chance = max(win_chance, loss_chance)
                
                if max_chance >= 60:
                    all_scores.sort(key=lambda x: x[1], reverse=True)
                    value_list.append({
                        'league': league,
                        'match': f"{h_team} × {a_team}",
                        'prob': max_chance,
                        'pick': "🏠 فوز الأرض" if win_chance > loss_chance else "🚀 فوز الضيف",
                        'score': all_scores[0][0],
                        'score_p': all_scores[0][1]
                    })
    return value_list

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, "🔍 جاري تشغيل الرادار... جاري فحص جميع الدوريات الكبرى عن فرص تتجاوز 60%.")
    
    found = scan_value_matches()
    
    if not found:
        bot.send_message(message.chat.id, "⚠️ لا توجد مباريات 'قوية رياضياً' حالياً (أعلى من 60%). جرب لاحقاً.")
        return

    msg = "🚀 **الفرص الذهبية الحالية (>60%):**\n\n"
    for m in found:
        msg += (f"🏆 الدوري: {m['league']}\n"
                f"🏟️ {m['match']}\n"
                f"📈 الثقة: {m['prob']:.1f}% ({m['pick']})\n"
                f"🎯 النتيجة الأرجح: {m['score']} ({m['score_p']:.1f}%)\n"
                f"--------------------------\n")
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except:
            time.sleep(5)
