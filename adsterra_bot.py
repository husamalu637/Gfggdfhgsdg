import telebot
from flask import Flask, request
import threading

# --- الإعدادات الأساسية ---
# التوكن الخاص بك
API_TOKEN = '8557316031:AAFKVZdf0oDHZExhPqop_RRapxw4ZAjs2MQ'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# رابط الربح الخاص بك (Smartlink) مع إضافة subid للتتبع
MY_DIRECT_LINK = "https://www.effectivegatecpm.com/xaeg3i863?key=23cf5c1f0aa47c762d8b1fc9de714230&subid="

# قاعدة بيانات وهمية لتخزين الأرصدة (تتصفر عند إعادة التشغيل)
user_balances = {}

# --- دالة البداية ---
@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = str(message.from_user.id)
    if user_id not in user_balances:
        user_balances[user_id] = 0.0
    
    # صنع رابط فريد لكل مستخدم باستخدام معرفه الخاص
    personal_link = f"{MY_DIRECT_LINK}{user_id}"
    
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("💰 شاهد واربح الآن", url=personal_link))
    markup.add(telebot.types.InlineKeyboardButton("🏦 رصيدي الحالي", callback_data="check_balance"))
    
    bot.send_message(
        message.chat.id, 
        f"أهلاً بك {message.from_user.first_name}!\n\n"
        "✅ سيتم إضافة الربح تلقائياً فور مشاهدة الإعلان.\n"
        "✅ لا تخرج من الصفحة قبل اكتمال التحميل لضمان احتساب المكافأة.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "check_balance")
def balance(call):
    user_id = str(call.from_user.id)
    current = user_balances.get(user_id, 0.0)
    bot.answer_callback_query(call.id, f"رصيدك الحالي: {round(current, 3)}$", show_alert=True)

# --- نظام التأكيد التلقائي (Postback Webhook) ---
@app.route('/adsterra_callback')
def adsterra_callback():
    # استلام معرف المستخدم المرسل من Adsterra
    user_id = request.args.get('user_id') 
    
    if user_id:
        # قيمة الربح المضافة للمستخدم (يمكنك تعديلها)
        reward = 0.01 
        if user_id in user_balances:
            user_balances[user_id] += reward
        else:
            user_balances[user_id] = reward
            
        # إرسال إشعار فوري للمستخدم داخل البوت لتأكيد العملية
        try:
            bot.send_message(user_id, f"✅ مبروك! تم تأكيد مشاهدتك بنجاح وأضيف {reward}$ لحسابك.")
        except:
            pass
        return "SUCCESS", 200
    return "INVALID_REQUEST", 400

# --- تشغيل البوت والسيرفر معاً ---
def run_telebot():
    bot.infinity_polling()

if __name__ == "__main__":
    # تشغيل البوت في خيط (Thread) منفصل لضمان استجابة الـ Webhook
    threading.Thread(target=run_telebot).start()
    
    # --- التعديل الهام هنا: المنفذ 8000 ليتوافق مع Koyeb ---
    app.run(host='0.0.0.0', port=8000)
