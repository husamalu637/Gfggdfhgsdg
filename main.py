import telebot
import requests
import math
import time

# --- الإعدادات (ضع مفاتيحك هنا) ---
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
# قائمة الدوريات التي سيقوم البوت بمسحها تلقائياً
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL'] 

bot = telebot.TeleBot(BOT_TOKEN)

def poisson_prob(actual, mean):
    """حساب معادلة بواسون يدوياً لتوفير المساحة والكفاءة"""
    try:
        return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)
    except: return 0

def get_data(endpoint):
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def scan_all_leagues():
    """وظيفة المسح الشامل للبحث عن الفرص الذهبية > 60%"""
    value_matches = []
    for league in LEAGUES:
        standings_data = get_data(f"competitions/{league}/standings")
        matches_data = get_data(f"competitions/{league}/matches?status=SCHEDULED")
        
        if not standings_data or not matches_data: continue

        # تنظيم ترتيب الدوري في قاموس ليسهل الوصول إليه
        standings = {item['team']['name']: item for item in standings_data['standings'][0]['table']}
        
        # فحص أول 10 مباريات قادمة في كل دوري
        for match in matches_data['matches'][:10]:
            h_name = match['homeTeam']['name']
            a_name = match['awayTeam']['name']
            
            if h_name in standings and a_name in standings:
                h, a = standings[h_name], standings[a_name]
                
                # حساب متوسط الأهداف المتوقع (Lambda)
                exp_h = (h['goalsFor']/h['playedGames']) * (a['goalsAgainst']/a['playedGames']) * 1.1
                exp_a = (a['goalsFor']/a['playedGames']) * (h['goalsAgainst']/h['playedGames'])
                
                p_win, p_loss = 0, 0
                score_probs = []
                
                # حساب الاحتمالات لجميع النتائج من 0-0 إلى 4-4
                for gh in range(5):
                    for ga in range(5):
                        p = poisson_prob(gh, exp_h) * poisson_prob(ga, exp_a)
                        if gh > ga: p_win += p
                        elif ga > gh: p_loss += p
                        score_probs.append((f"{gh}-{ga}", p * 100))
                
                # تحديد النسبة الأعلى (فوز صاحب الأرض أو الضيف)
                max_prob = max(p_win, p_loss) * 100
                
                # فلتر القيمة: فقط المباريات التي تتخطى 60%
                if max_prob >= 60:
                    score_probs.sort(key=lambda x: x[1], reverse=True)
                    value_matches.append({
                        'league': league,
                        'match': f"{h_name} × {a_name}",
                        'prob': max_prob,
                        'side': "🏠 فوز الأرض" if p_win > p_loss else "🚀 فوز الضيف",
                        'best_score': score_probs[0][0],
                        'score_p': score_probs[0][1]
                    })
    return value_matches

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔍 جاري فحص جميع الدوريات الكبرى... سأرسل لك فقط الفرص التي تتجاوز نسبة نجاحها 60%.")
    
    matches = scan_all_leagues()
    
    if not matches:
        bot.send_message(message.chat.id, "⚠️ لا توجد مباريات بنسبة ثقة أعلى من 60% في الوقت الحالي.")
        return

    report = "🚀 **الفرص الذهبية المكتشفة (>60%):**\n\n"
    for m in matches:
        report += (f"🏆 الدوري: {m['league']}\n"
                   f"🏟️ {m['match']}\n"
                   f"📈 الثقة: {m['prob']:.1f}% ({m['side']})\n"
                   f"🎯 النتيجة الأرجح: {m['best_score']} ({m['score_p']:.1f}%)\n"
                   f"--------------------------\n")
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except: time.sleep(5)
