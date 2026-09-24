import os
import re
import sqlite3
import threading
from datetime import datetime
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# =========================
# سيرفر مصغر لإرضاء منصة Render وفتح البورت (24/7)
# =========================
app = Flask('')


@app.route('/')
def home():
  return 'Cyber Virus Bot is Online 24/7! 🟢'


def run_http():
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)


# تشغيل السيرفر في الخلفية
threading.Thread(target=run_http).start()

# =========================
# إعدادات البوت والخدمات
# =========================

TOKEN = '8506228695:AAH8NlZT-b-zjlSTH6wtTwBazDFlQT50Xp4'
TARGET_USER = '@BoTmz66'  # يوزر حسابك للمسؤول
IMAGE_URL = 'https://cdn.phototourl.com/member/2026-09-23-f246863f-e6e8-440d-844d-03cd92960e4d.jpg'

# حالات المحادثة
WAITING_FOR_PLATFORM_CHOICE = 2
WAITING_FOR_TARGET_INPUT = 3
WAITING_FOR_ACCOUNT_FOLLOWERS = 4
WAITING_FOR_ACCOUNT_USERNAME = 5


# =========================
# إعداد قاعدة البيانات
# =========================


def init_db():
  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            coins INTEGER DEFAULT 0,
            joined_at TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pending_requests (
            user_id INTEGER PRIMARY KEY,
            service_name TEXT,
            target_input TEXT,
            price INTEGER DEFAULT 0
        )
    """)
  conn.commit()
  conn.close()


# =========================
# القائمة الرئيسية
# =========================


async def send_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False
):
  user = update.effective_user
  init_db()

  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute(
      'SELECT user_id, coins FROM users WHERE user_id = ?', (user.id,)
  )
  row = cursor.fetchone()
  if row is None:
    cursor.execute(
        'INSERT INTO users (user_id, username, first_name, coins, joined_at)'
        ' VALUES (?, ?, ?, 0, ?)',
        (
            user.id,
            user.username or '',
            user.first_name or '',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        ),
    )
    conn.commit()
    user_coins = 0
  else:
    user_coins = row[1]
  conn.close()

  welcome_text = (
      '🤖 **أهلاً بك في بوت الفيروس**\n'
      'هذا بوت خاص بالهكر، اختر الخدمة وتصفح فقط.\n\n'
      f'💳 **رصيدك الحالي:** `{user_coins} كوينز`\n\n'
      '⚡ **اختر الخدمة المطلوبة:**'
  )

  keyboard = [
      [
          InlineKeyboardButton('💻 معلومات المالك', callback_data='service_virus'),
          InlineKeyboardButton('🔴 هكر واتساب', callback_data='service_whatsapp'),
      ],
      [
          InlineKeyboardButton(
              '🟢 استرجاع رقم', callback_data='service_recover_whatsapp'
          ),
          InlineKeyboardButton(
              '🔴 استرجاع حساب', callback_data='service_recover_accounts'
          ),
      ],
      [
          InlineKeyboardButton('🟢 هكر إيميل', callback_data='service_email'),
          InlineKeyboardButton('🔴 منصات', callback_data='service_social'),
      ],
      [
          InlineKeyboardButton('👤 حسابي', callback_data='my_account'),
          InlineKeyboardButton('ℹ️ معلومات', callback_data='bot_info'),
      ],
      [
          InlineKeyboardButton('📊 السجل', callback_data='admin_stats'),
          InlineKeyboardButton(
              '💬 شحن كوينز / التواصل',
              url=f'https://t.me/{TARGET_USER.replace("@", "")}',
          ),
      ],
  ]

  reply_markup = InlineKeyboardMarkup(keyboard)

  if is_callback:
    query = update.callback_query
    if query.message.photo:
      await query.edit_message_caption(
          caption=welcome_text, reply_markup=reply_markup, parse_mode='Markdown'
      )
    else:
      await query.edit_message_text(
          text=welcome_text, reply_markup=reply_markup, parse_mode='Markdown'
      )
  else:
    await update.message.reply_photo(
        photo=IMAGE_URL,
        caption=welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await send_main_menu(update, context, is_callback=False)
  return ConversationHandler.END


# =========================
# أمر شحن الكوينز
# =========================


async def charge_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  if not user.username or user.username.lower() != TARGET_USER.replace(
      '@', ''
  ).lower():
    return

  args = context.args
  if len(args) < 2:
    await update.message.reply_text(
        '⚠️ **طريقة الاستخدام:**\n`/charge <آيدي> <العدد>`', parse_mode='Markdown'
    )
    return

  try:
    target_id = int(args[0])
    amount = int(args[1])
  except ValueError:
    await update.message.reply_text('❌ الآيدي والعدد يجب أن يكونا أرقاماً.')
    return

  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute('SELECT coins FROM users WHERE user_id = ?', (target_id,))
  row = cursor.fetchone()
  if row is None:
    cursor.execute(
        'INSERT INTO users (user_id, coins, joined_at) VALUES (?, ?, ?)',
        (target_id, amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    )
  else:
    new_coins = row[0] + amount
    cursor.execute(
        'UPDATE users SET coins = ? WHERE user_id = ?', (new_coins, target_id)
    )
  conn.commit()
  conn.close()

  await update.message.reply_text(
      f'✅ تم إضافة {amount} كوينز للمستخدم `{target_id}` بنجاح.',
      parse_mode='Markdown',
  )


# =========================
# معالجة الضغط على الأزرار
# =========================


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  data = query.data

  if data == 'my_account':
    user = query.from_user
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT coins, joined_at FROM users WHERE user_id = ?', (user.id,)
    )
    row = cursor.fetchone()
    conn.close()
    coins = row[0] if row else 0
    joined = row[1] if row and len(row) > 1 else 'غير معروف'

    text = (
        '👤 **معلومات حسابك:**\n\n'
        f'🆔 الآيدي: `{user.id}`\n'
        f'👤 الاسم: {user.first_name}\n'
        f'💳 الرصيد: `{coins} كوينز`\n'
        f'📅 تاريخ الانضمام: `{joined}`'
    )
    keyboard = [[InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )

  elif data == 'bot_info':
    text = (
        'ℹ️ **معلومات البوت:**\n\n'
        'هذا البوت مخصص لتقديم خدمات رقمية متعددة.\n'
        f'للاتصال بالمسؤول: {TARGET_USER}'
    )
    keyboard = [[InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )

  elif data == 'main_menu':
    await send_main_menu(update, context, is_callback=True)

  elif data.startswith('service_'):
    service_name = data.replace('service_', '')
    text = (
        f'📌 **تفاصيل الخدمة ({service_name})**\n\n'
        'يرجى التواصل مع المالك مباشرة لتنفيذ هذه الخدمة أو شحن رصيدك.'
    )
    keyboard = [
        [
            InlineKeyboardButton(
                '💬 التواصل مع المالك',
                url=f'https://t.me/{TARGET_USER.replace("@", "")}',
            )
        ],
        [InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')],
    ]
    await query.edit_message_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )

  elif data == 'admin_stats':
    user = query.from_user
    if user.username and user.username.lower() == TARGET_USER.replace(
        '@', ''
    ).lower():
      conn = sqlite3.connect('users.db')
      cursor = conn.cursor()
      cursor.execute('SELECT COUNT(*) FROM users')
      total_users = cursor.fetchone()[0]
      conn.close()
      text = (
          f'📊 **لوحة الإحصائيات (خاص بالمسؤول):**\n\n👥 إجمالي المستخدمين:'
          f' `{total_users}`'
      )
    else:
      text = '⚠️ عذراً، هذه الإحصائيات مخصصة للمسؤول فقط.'
    keyboard = [[InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )


# =========================
# تشغيل البوت
# =========================


def main():
  init_db()
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler('start', start))
  application.add_handler(CommandHandler('charge', charge_user))
  application.add_handler(CallbackQueryHandler(button_callback))

  print('Bot is running...')
  application.run_polling()


if __name__ == '__main__':
  main()
