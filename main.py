import telebot
import requests
import math
import time

# --- الإعدادات ---
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL'] # الدوريات الكبرى

bot = telebot.TeleBot(BOT_TOKEN)

def poisson_prob(actual, mean):
    return (math.exp(-mean) * pow(mean, actual)) / math.factorial(actual)

def get_data(endpoint):
    url = f"https://api.football-data.org/v4/{endpoint}"
    headers = {'X-Auth-Token': API_KEY}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        return r.json() if r.status_code == 200 else None
    except: return None

def analyze_value_matches():
    results = []
    for league in LEAGUES:
        standings_data = get_data(f"competitions/{league}/standings")
        matches_data = get_data(f"competitions/{league}/matches?status=SCHEDULED")
        
        if not standings_data or not matches_data: continue

        standings = {item['team']['name']: item for item in standings_data['standings'][0]['table']}
        
        for match in matches_data['matches'][:15]: # فحص أول 15 مباراة قادمة في كل دوري
            h_name, a_name = match['homeTeam']['name'], match['awayTeam']['name']
            if h_name in standings and a_name in standings:
                h, a = standings[h_name], standings[a_name]
                
                exp_h = (h['goalsFor']/h['playedGames']) * (a['goalsAgainst']/a['playedGames']) * 1.1
                exp_a = (a['goalsFor']/a['playedGames']) * (h['goalsAgainst']/h['playedGames'])
                
                p_win, p_loss = 0, 0
                score_probs = []
                for gh in range(5):
                    for ga in range(5):
                        p = poisson_prob(gh, exp_h) * poisson_prob(ga, exp_a)
                        if gh > ga: p_win += p
                        elif ga > gh: p_loss += p
                        score_probs.append((f"{gh}-{ga}", p * 100))
                
                max_prob = max(p_win, p_loss) * 100
                if max_prob >= 60: # فلتر القيمة (أكبر من 60%)
                    score_probs.sort(key=lambda x: x[1], reverse=True)
                    results.append({
                        'league': league,
                        'match': f"{h_name} × {a_name}",
                        'win_p': p_win * 100,
                        'loss_p': p_loss * 100,
                        'best_score': score_probs[0][0],
                        'score_p': score_probs[0][1]
                    })
    return results

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🔍 جاري فحص جميع الدوريات الكبرى عن فرص تتجاوز 60%... انتظر قليلاً.")
    
    value_matches = analyze_value_matches()
    
    if not value_matches:
        bot.send_message(message.chat.id, "⚠️ لا توجد مباريات "قيمتها عالية" حالياً في الدوريات الكبرى.")
        return

    report = "🚀 **الفرص الذهبية المكتشفة (>60%):**\n\n"
    for m in value_matches:
        icon = "🏠" if m['win_p'] > m['loss_p'] else "🚀"
        prob = m['win_p'] if m['win_p'] > m['loss_p'] else m['loss_p']
        
        report += (f"🏆 الدوري: {m['league']}\n"
                   f"🏟️ {m['match']}\n"
                   f"📈 نسبة الثقة: {prob:.1f}% {icon}\n"
                   f"🎯 النتيجة الأرجح: {m['best_score']} ({m['score_p']:.1f}%)\n"
                   f"--------------------------\n")
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except: time.sleep(5)
