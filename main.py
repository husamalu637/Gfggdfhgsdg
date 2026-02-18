import telebot, requests, math, time

# الإعدادات
API_KEY = 'Be9acf1ac42f43bc9c7599d2c8588ec9'
BOT_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
LEAGUES = ['PL', 'PD', 'SA', 'BL1', 'FL1', 'CL']

bot = telebot.TeleBot(BOT_TOKEN)

def poisson(k, m):
    """معادلة بواسون يدوية خفيفة جداً"""
    return (math.exp(-m) * pow(m, k)) / math.factorial(k)

@bot.message_handler(commands=['start'])
def run_radar(message):
    bot.send_message(message.chat.id, "📡 جاري فحص الدوريات عن فرص > 60%...")
    report = ""
    for lg in LEAGUES:
        try:
            # جلب البيانات
            s_url = f"https://api.football-data.org/v4/competitions/{lg}/standings"
            m_url = f"https://api.football-data.org/v4/competitions/{lg}/matches?status=SCHEDULED"
            h = {'X-Auth-Token': API_KEY}
            
            standings = requests.get(s_url, headers=h).json()
            matches = requests.get(m_url, headers=h).json()
            
            table = {t['team']['name']: t for t in standings['standings'][0]['table']}
            
            for m in matches['matches'][:10]:
                h_n, a_n = m['homeTeam']['name'], m['awayTeam']['name']
                if h_n in table and a_n in table:
                    h_s, a_s = table[h_n], table[a_n]
                    # حساب القوة المتوقعة
                    eh = (h_s['goalsFor']/h_s['playedGames']) * (a_s['goalsAgainst']/a_s['playedGames']) * 1.1
                    ea = (a_s['goalsFor']/a_s['playedGames']) * (h_s['goalsAgainst']/h_s['playedGames'])
                    
                    p_win, p_loss = 0, 0
                    for i in range(5):
                        for j in range(5):
                            prob = poisson(i, eh) * poisson(j, ea)
                            if i > j: p_win += prob
                            elif j > i: p_loss += prob
                    
                    if p_win > 0.6 or p_loss > 0.6:
                        side = "🏠" if p_win > p_loss else "🚀"
                        report += f"🏆 {lg} | {h_n} × {a_n}\n📈 الثقة: {max(p_win, p_loss)*100:.1f}% {side}\n---\n"
        except: continue

    bot.send_message(message.chat.id, report if report else "⚠️ لا توجد مباريات قوية حالياً.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
