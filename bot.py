import os
import logging
import requests
from telebot import TeleBot, types

# Logging စနစ် ထည့်သွင်းခြင်း
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- CONFIGURATION (ချိတ်ဆက်မှု အချက်အလက်များ) ---
BOT_TOKEN = "8200542829:AAGFoxStZVHPeeC40Ot5N-ZYwzUUGHOkLBk"
SUPABASE_URL = "https://afpvblziolrzqvpjpavx.supabase.co"
SUPABASE_KEY = "sb_publishable_CGOy-EQwsAuwoPsnDqeGig_1gfI1WyV"
ADMIN_ID = 7136162037
# ------------------------------------------------

bot = TeleBot(BOT_TOKEN)
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

user_states = {}

def is_admin(user_id):
    return user_id == ADMIN_ID

def main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🛒 Available Accounts"))
    if is_admin(user_id):
        markup.row(types.KeyboardButton("👨‍💻 Admin Panel"))
    return markup

def admin_menu():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("➕ Add New Account", callback_data="admin_add"))
    markup.row(types.InlineKeyboardButton("⚙️ Manage/Edit Status", callback_data="admin_manage"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id, 
        "👋 Welcome to MLBB Account Store Bot!\nအောက်က ခလုတ်တွေကို သုံးပြီး ရောင်းရန်ရှိသော အကောင့်များကို ကြည့်ရှုနိုင်ပါသည်။", 
        reply_markup=main_menu(message.from_user.id)
    )

@bot.message_handler(func=lambda m: m.text == "🛒 Available Accounts")
def view_accounts(message):
    url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts?status=eq.Available&select=*"
    try: 
        res = requests.get(url, headers=headers).json()
        if not isinstance(res, list):
            bot.send_message(message.chat.id, "😔 လောလောဆယ် ရောင်းရန်အကောင့် မရှိသေးပါခင်ဗျာ။")
            return
    except: 
        bot.send_message(message.chat.id, "❌ ဒေတာဘေ့စ် ချိတ်ဆက်မှု အဆင်မပြေပါ။")
        return

    if not res:
        bot.send_message(message.chat.id, "😔 လောလောဆယ် ရောင်းရန်အကောင့် မရှိသေးပါခင်ဗျာ။")
        return

    for acc in res:
        if not isinstance(acc, dict): 
            continue
        
        text = (f"🆔 **Account ID:** {acc.get('id', 'N/A')}\n"
                f"📌 **Title:** {acc.get('title', 'N/A')}\n"
                f"📝 **Details:** {acc.get('details', 'N/A')}\n"
                f"💰 **Price:** {acc.get('price', 'N/A')}\n"
                f"🟢 **Status:** {acc.get('status', 'N/A')}")
                
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📩 Buy This Account", callback_data=f"buy_{acc.get('id')}"))

        if acc.get('image_url'):
            try:
                bot.send_photo(message.chat.id, acc['image_url'], caption=text, parse_mode="Markdown", reply_markup=markup)
            except:
                bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "👨‍💻 Admin Panel")
def admin_panel(message):
    if not is_admin(message.from_user.id): 
        return
    bot.send_message(message.chat.id, "Welcome Back Admin! ဘာလုပ်လိုပါသလဲခင်ဗျာ။", reply_markup=admin_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data.startswith("buy_"):
        acc_id = call.data.split("_")[1]
        bot.answer_callback_query(call.id, "Order တင်လိုက်ပါပြီ!")
        bot.send_message(call.message.chat.id, "✅ Order တင်ပြီးပါပြီ။ Admin က ကျောင်းဆင်းချိန် (သို့) အားလပ်ချိန်တွင် ချက်ချင်းဆက်သွယ်ပေးပါလိမ့်မည်။")
        
        user_info = f"@{call.from_user.username}" if call.from_user.username else f"ID: {call.from_user.id}"
        bot.send_message(ADMIN_ID, f"🔔 **Order Alert!**\nဝယ်သူ {user_info} က Account ID: {acc_id} ကို ဝယ်ယူရန် 'Buy' ခလုတ်နှိပ်လိုက်ပါသည်။")

    elif call.data == "admin_add":
        bot.send_message(call.message.chat.id, "အကောင့်ခေါင်းစဉ် ပေးပါ (ဥပမာ- VIP Account):")
        user_states[call.from_user.id] = {'step': 'title'}

    elif call.data == "admin_manage":
        url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts?select=*"
        try:
            accounts = requests.get(url, headers=headers).json()
        except:
            bot.send_message(call.message.chat.id, "Error connecting to database.")
            return
            
        if not accounts or not isinstance(accounts, list):
            bot.send_message(call.message.chat.id, "ဒေတာဘေ့စ်ထဲမှာ အကောင့်မရှိသေးပါ။")
            return
            
        markup = types.InlineKeyboardMarkup()
        for acc in accounts:
            if not isinstance(acc, dict): continue
            status_icon = "🟢" if acc.get('status') == "Available" else "🔴"
            markup.row(types.InlineKeyboardButton(f"{status_icon} ID: {acc.get('id')} - {acc.get('price')}", callback_data=f"manage_{acc.get('id')}"))
        bot.send_message(call.message.chat.id, "ပြင်ဆင်လိုသည့် အကောင့်ကို ရွေးချယ်ပါ-", reply_markup=markup)

    elif call.data.startswith("manage_"):
        acc_id = call.data.split("_")[1]
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("🟢 Set Available", callback_data=f"set_avail_{acc_id}"),
            types.InlineKeyboardButton("🔴 Set Sold Out", callback_data=f"set_sold_{acc_id}")
        )
        markup.row(types.InlineKeyboardButton("🗑 Delete Account", callback_data=f"delete_{acc_id}"))
        bot.send_message(call.message.chat.id, f"Account ID: {acc_id} ကို ဘာလုပ်မလဲ။", reply_markup=markup)

    elif call.data.startswith("set_avail_"):
        acc_id = call.data.split("_")[2]
        url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts?id=eq.{acc_id}"
        requests.patch(url, json={"status": "Available"}, headers=headers)
        bot.answer_callback_query(call.id, "Status Updated!")
        bot.edit_message_text("✅ ပြင်ဆင်ပြီးပါပြီ။ ဝယ်သူများ ပြန်လည်မြင်တွေ့နိုင်ပါပြီ။", call.message.chat.id, call.message.message_id)

    elif call.data.startswith("set_sold_"):
        acc_id = call.data.split("_")[2]
        url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts?id=eq.{acc_id}"
        requests.patch(url, json={"status": "Sold Out"}, headers=headers)
        bot.answer_callback_query(call.id, "Status Updated!")
        bot.edit_message_text("✅ ပြင်ဆင်ပြီးပါပြီ။ ဝယ်သူတွေဆီမှာ ပျောက်သွားပါပြီ။", call.message.chat.id, call.message.message_id)
        
    elif call.data.startswith("delete_"):
        acc_id = call.data.split("_")[1]
        url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts?id=eq.{acc_id}"
        requests.delete(url, headers=headers)
        bot.answer_callback_query(call.id, "Deleted!")
        bot.edit_message_text("🗑 အကောင့်ကို ဖျက်လိုက်ပါပြီ။", call.message.chat.id, call.message.message_id)

@bot.message_handler(func=lambda m: m.from_user.id in user_states)
def handle_admin_input(message):
    state = user_states[message.from_user.id]
    if state['step'] == 'title':
        state['title'] = message.text
        state['step'] = 'details'
        bot.send_message(message.chat.id, "အကောင့်အသေးစိတ် (Skins/Heroes/Emblem) ရေးပေးပါ:")
    elif state['step'] == 'details':
        state['details'] = message.text
        state['step'] = 'price'
        bot.send_message(message.chat.id, "ဈေးနှုန်း သတ်မှတ်ပေးပါ (ဥပမာ- 45,000 MMK):")
    elif state['step'] == 'price':
        state['price'] = message.text
        state['step'] = 'image'
        bot.send_message(message.chat.id, "အကောင့်ပုံရဲ့ Direct Link ကို ပို့ပေးပါ (ပုံမထည့်ချင်ပါက 'no' ဟု ရိုက်ပါ):")
    elif state['step'] == 'image':
        img = message.text
        image_url = None if img.lower() == 'no' else img
        
        url = f"{SUPABASE_URL}/rest/v1/mlbb_accounts"
        data = {
            "title": state['title'],
            "details": state['details'],
            "price": state['price'],
            "image_url": image_url,
            "status": "Available"
        }
        requests.post(url, json=data, headers=headers)
        bot.send_message(message.chat.id, "🎉 အကောင့်အသစ်ကို တင်ပြီးပါပြီ။")
        del user_states[message.from_user.id]

if __name__ == "__main__":
    bot.infinity_polling()
      
