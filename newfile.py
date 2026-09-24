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

TOKEN = '8506228695:AAE3Sy2VXlbgPijeWgF-YmdVpDOakvHpCfM'
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

  if row:
    new_coins = row[0] + amount
    cursor.execute(
        'UPDATE users SET coins = ? WHERE user_id = ?', (new_coins, target_id)
    )
    conn.commit()
    conn.close()

    try:
      await context.bot.send_message(
          chat_id=target_id,
          text=(
              '🎉 **تم شحن حسابك بنجاح!**\n\n'
              f'💰 الإضافة: `+{amount} كوينز`\n'
              f'💳 رصيدك الحالي: `{new_coins} كوينز`'
          ),
          parse_mode='Markdown',
      )
    except Exception:
      pass

    await update.message.reply_text(
        f'✅ تم شحن `{target_id}` بـ `{amount}` كوينز بنجاح! الإجمالي:'
        f' `{new_coins}`',
        parse_mode='Markdown',
    )
  else:
    conn.close()
    await update.message.reply_text('❌ المستخدم غير موجود في قاعدة البيانات.')


# =========================
# أمر رد المالك وتحديد السعر
# =========================


async def admin_set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  if not user.username or user.username.lower() != TARGET_USER.replace(
      '@', ''
  ).lower():
    return

  args = context.args
  if len(args) < 2:
    await update.message.reply_text(
        '⚠️ **طريقة الاستخدام:**\n`/price <آيدي_المستخدم> <السعر>`',
        parse_mode='Markdown',
    )
    return

  try:
    target_user_id = int(args[0])
    price = int(args[1])
  except ValueError:
    await update.message.reply_text(
        '❌ الآيدي والسعر يجب أن يكونا أرقاماً صحيحة.'
    )
    return

  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute(
      'SELECT service_name, target_input FROM pending_requests WHERE user_id ='
      ' ?',
      (target_user_id,),
  )
  row = cursor.fetchone()

  if not row:
    conn.close()
    await update.message.reply_text(
        '❌ لا يوجد طلب معلق لهذا المستخدم أو أن الطلب انتهى.'
    )
    return

  s_name, target_input = row

  cursor.execute(
      'UPDATE pending_requests SET price = ? WHERE user_id = ?',
      (price, target_user_id),
  )
  conn.commit()
  conn.close()

  user_keyboard = [
      [
          InlineKeyboardButton(
              '✅ تأكيد', callback_data=f'order_confirm_{target_user_id}_{price}'
          ),
          InlineKeyboardButton(
              '❌ رفض', callback_data=f'order_reject_{target_user_id}'
          ),
      ]
  ]

  try:
    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            '💬 **رسالة من إدارة البوت:**\n\n'
            f'سعر خدمة {s_name} مقابل {target_input} هو **{price} كوينز**\n\n'
            '💳 للشحن أو التواصل استخدم الأزرار في القائمة الرئيسية.'
        ),
        reply_markup=InlineKeyboardMarkup(user_keyboard),
        parse_mode='Markdown',
    )
    await update.message.reply_text(
        f'✅ تم إرسال السعر ({price} كوينز) للعميل بنجاح!'
    )
  except Exception as e:
    await update.message.reply_text(f'❌ فشل إرسال الرسالة للعميل. الخطأ: {e}')


# =========================
# التعامل مع الأزرار
# =========================


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user = update.effective_user

  if query.data.startswith('order_confirm_'):
    parts = query.data.split('_')
    target_user_id = int(parts[2])
    price = int(parts[3])

    if user.id != target_user_id:
      await query.answer('هذا الزر ليس مخصصاً لك!', show_alert=True)
      return

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user.id,))
    row = cursor.fetchone()
    user_coins = row[0] if row else 0

    if user_coins < price:
      conn.close()
      await query.answer(
          '❌ عذراً، رصيدك غير كافي! اشحن كوينز أولاً.', show_alert=True
      )
      await context.bot.send_message(
          chat_id=user.id,
          text=(
              '❌ **عذراً رصيدك غير كافي!**\n\n'
              f'💰 رصيدك الحالي: `{user_coins}` كوينز\n'
              f'⚠️ السعر المطلوب: `{price}` كوينز\n\n'
              '💳 يرجى شحن رصيدك عبر التواصل مع المالك من القائمة الرئيسية.'
          ),
          parse_mode='Markdown',
      )
      return

    new_coins = user_coins - price
    cursor.execute(
        'UPDATE users SET coins = ? WHERE user_id = ?', (new_coins, user.id)
    )
    cursor.execute('DELETE FROM pending_requests WHERE user_id = ?', (user.id,))
    conn.commit()
    conn.close()

    await query.message.edit_text(
        text=query.message.text
        + '\n\n✅ **تم تأكيد الطلب وخصم الكوينز بنجاح!**',
        parse_mode='Markdown',
    )

    success_msg = (
        '✅ **تم تأكيد طلبك بنجاح!**\n\n'
        '🔄 جاري الآن تنفيذ الاختراق...\n'
        '⏳ **المدة المتوقعة:** 4 أيام.\n\n'
        f'💳 تم خصم `{price}` كوينز من رصيدك.\n'
        f'💳 رصيدك الحالي: `{new_coins} كوينز`'
    )

    keyboard = [
        [
            InlineKeyboardButton(
                '💬 مراسلة المالك للشحن',
                url=f'https://t.me/{TARGET_USER.replace("@", "")}',
            )
        ],
        [InlineKeyboardButton('🔙 القائمة الرئيسية', callback_data='main_menu')],
    ]

    await context.bot.send_photo(
        chat_id=user.id,
        photo=IMAGE_URL,
        caption=success_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return

  elif query.data.startswith('order_reject_'):
    target_user_id = int(query.data.split('_')[2])
    if user.id != target_user_id:
      await query.answer('هذا الزر ليس مخصصاً لك!', show_alert=True)
      return

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM pending_requests WHERE user_id = ?', (user.id,))
    conn.commit()
    conn.close()

    await query.message.edit_text(
        text=query.message.text + '\n\n❌ **تم رفض الطلب وإلغاؤه.**',
        parse_mode='Markdown',
    )
    return

  if query.data == 'verify' or query.data == 'main_menu':
    await send_main_menu(update, context, is_callback=True)
    return ConversationHandler.END

  elif query.data == 'service_virus':
    owner_text = (
        '💻 **[ معلومات مالك البوت ]**\n'
        '👤 **الاسم:** فيروز | هكر سعودي\n'
        '⭐ **الخبرة:** متعلم منذ 10 سنوات\n'
        '🔒 **الأمان:** أمين مليون بالمئة\n'
        '📞 **التواصل والشحن:** للتواصل مع المالك أو شحن الكوينز عبر الزر أدناه.'
    )
    keyboard = [
        [
            InlineKeyboardButton(
                '💬 مراسلة المالك للشحن',
                url=f'https://t.me/{TARGET_USER.replace("@", "")}',
            )
        ],
        [InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')],
    ]
    await query.edit_message_caption(
        caption=owner_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return ConversationHandler.END

  elif query.data == 'my_account':
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT coins FROM users WHERE user_id = ?', (user.id,))
    row = cursor.fetchone()
    user_coins = row[0] if row else 0
    conn.close()

    account_text = (
        '👤 **[ معلومات العميل ]**\n'
        f'🟢 **الاسم:** {user.first_name}\n'
        f'🆔 **الآيدي:** `{user.id}`\n'
        f'💰 **الكوينز:** `{user_coins}` كوينز\n\n'
        '💳 *لتعبئة رصيد الكوينز تواصل مع مالك البوت أو استخدم الأزرار.*'
    )
    keyboard = [
        [
            InlineKeyboardButton(
                '💬 شحن كوينز',
                url=f'https://t.me/{TARGET_USER.replace("@", "")}',
            )
        ],
        [InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')],
    ]
    await query.edit_message_caption(
        caption=account_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return ConversationHandler.END

  elif query.data == 'bot_info':
    info_text = (
        'ℹ️ **[ النظام الآمن ]**\n'
        'هذا بوت خاص بالهكر، اختر الخدمة وتصفح فقط.\n'
        '⚠️ **ملاحظة:** الخدمات تتطلب الدفع بالكوينز.'
    )
    keyboard = [[InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=info_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return ConversationHandler.END

  elif query.data == 'admin_stats':
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    conn.close()

    stats_text = f'📊 **[ الإحصائيات ]**\n🟢 **المستخدمين:** `{total_users}`'
    keyboard = [[InlineKeyboardButton('🔙 رجوع', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=stats_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return ConversationHandler.END

  elif query.data == 'service_recover_accounts':
    prompt_text = (
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n\n'
        '🔴 **استرجاع حساب**\n'
        '🟢 ارسل عدد المتابعين:'
    )
    keyboard = [[InlineKeyboardButton('🔙 إلغاء', callback_data='main_menu')]]
    await query.edit_message_caption(
        caption=prompt_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return WAITING_FOR_ACCOUNT_FOLLOWERS

  elif query.data == 'service_social':
    platform_text = (
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
        '💰 *السعر بالكوينز سيحدد ويروته لك المالك.*\n\n'
        '🌐 **اختر المنصة المطلوبة:**'
    )
    keyboard = [
        [
            InlineKeyboardButton('🟢 تيك توك', callback_data='plat_tiktok'),
            InlineKeyboardButton('🔴 انستغرام', callback_data='plat_instagram'),
        ],
        [
            InlineKeyboardButton('🟢 فيسبوك', callback_data='plat_facebook'),
            InlineKeyboardButton('🔴 إكس', callback_data='plat_x'),
        ],
        [
            InlineKeyboardButton('🟢 تيليجرام', callback_data='plat_telegram'),
            InlineKeyboardButton('🔙 رجوع', callback_data='main_menu'),
        ],
    ]
    await query.edit_message_caption(
        caption=platform_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown',
    )
    return WAITING_FOR_PLATFORM_CHOICE

  services_map = {
      'service_whatsapp': 'هكر واتساب',
      'service_recover_whatsapp': 'استرجاع رقم',
      'service_email': 'هكر إيميل',
  }

  if query.data in services_map:
    s_name = services_map[query.data]
    context.user_data['pending_service'] = s_name

    input_prompt = (
        f'🟢 **تم اختيار: {s_name}**\n\n'
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
        '🟢 **ارسل الهدف المطلوب للخدمة:**'
    )

    await query.message.reply_text(input_prompt, parse_mode='Markdown')
    return WAITING_FOR_TARGET_INPUT

  return ConversationHandler.END


# =========================
# خطوات استرجاع الحسابات
# =========================


async def receive_account_followers(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  context.user_data['account_followers'] = update.message.text.strip()
  await update.message.reply_text(
      '🟢 **ارسل اليوزر المراد استرجاعه:**', parse_mode='Markdown'
  )
  return WAITING_FOR_ACCOUNT_USERNAME


async def receive_account_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  username_input = update.message.text.strip()
  followers_count = context.user_data.get('account_followers', 'غير محدد')
  user = update.effective_user
  s_name = 'استرجاع حساب'

  if ' ' in username_input or len(username_input) < 2:
    await update.message.reply_text(
        '❌ **اسم اليوزر غير صحيح!**\n🔴 **يرجى إرسال اليوزر الصحيح:**',
        parse_mode='Markdown',
    )
    return WAITING_FOR_ACCOUNT_USERNAME

  target_input_str = f'يوزر: {username_input} (المتابعين: {followers_count})'

  # حفظ الطلب في قاعدة البيانات بدلاً من الذاكرة المؤقتة
  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute(
      'INSERT OR REPLACE INTO pending_requests (user_id, service_name,'
      ' target_input) VALUES (?, ?, ?)',
      (user.id, s_name, target_input_str),
  )
  conn.commit()
  conn.close()

  user_msg = (
      '✅ **تم إرسال الرقم للمالك.**\n\n'
      '🔴 الاختراق وهو فيروس، ورح يرسلك سعر الخدمة.\n'
      '⚠️ الخدمة ليست مجانية وسعرها بالكوينز.\n'
      '💳 الكوينز تقدر تشحنها من المالك من الزر الموجود في الشاشة الرئيسية.'
  )
  keyboard = [
      [
          InlineKeyboardButton(
              '💬 شحن كوينز / التواصل',
              url=f'https://t.me/{TARGET_USER.replace("@", "")}',
          )
      ]
  ]

  await update.message.reply_photo(
      photo=IMAGE_URL,
      caption=user_msg,
      reply_markup=InlineKeyboardMarkup(keyboard),
      parse_mode='Markdown',
  )

  try:
    await context.bot.send_message(
        chat_id=TARGET_USER,
        text=(
            '🚨 **طلب خدمة جديد (استرجاع حساب)!**\n'
            f'👤 اسم العميل: {user.first_name}\n'
            f'🆔 آيدي العميل: `{user.id}`\n'
            f'👥 المتابعين: {followers_count}\n'
            f'🎯 اليوزر: `{username_input}`\n\n'
            '💡 **للرد بالسعر، أرسل الأمر:**\n'
            f'`/price {user.id} <السعر>`'
        ),
        parse_mode='Markdown',
    )
  except Exception:
    pass

  return ConversationHandler.END


# =========================
# اختيار المنصة
# =========================


async def platform_choice_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()

  if query.data == 'main_menu':
    await send_main_menu(update, context, is_callback=True)
    return ConversationHandler.END

  platforms = {
      'plat_tiktok': 'تيك توك',
      'plat_instagram': 'انستغرام',
      'plat_facebook': 'فيسبوك',
      'plat_x': 'إكس',
      'plat_telegram': 'تيليجرام',
  }

  if query.data in platforms:
    p_name = platforms[query.data]
    s_name = f'اختراق {p_name}'
    context.user_data['pending_service'] = s_name

    success_social_text = (
        f'🟢 **تم اختيار منصة {p_name}!**\n\n'
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
        '🔴 **ارسل اليوزر المراد اختراقه:**'
    )
    await query.message.reply_text(success_social_text, parse_mode='Markdown')
    return WAITING_FOR_TARGET_INPUT

  return ConversationHandler.END


# =========================
# استقبال الهدف والتحقق منه وإرساله للمشرف
# =========================


async def receive_target_data(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user_input = update.message.text.strip()
  user = update.effective_user
  s_name = context.user_data.get('pending_service', 'خدمة')

  if s_name == 'هكر إيميل':
    if '@' not in user_input or '.' not in user_input or len(user_input) < 6:
      await update.message.reply_text(
          '❌ **البريد الإلكتروني غير صحيح!**\n🔴 **يرجى إرسال إيميل صحيح:**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  elif 'اختراق' in s_name:
    if ' ' in user_input or len(user_input) < 2:
      await update.message.reply_text(
          '❌ **اسم اليوزر غير صحيح!**\n🔴 **يرجى إرسال يوزر صحيح:**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  elif 'واتساب' in s_name or 'رقم' in s_name:
    digits_only = re.sub(r'\D', '', user_input)
    if len(digits_only) < 7:
      await update.message.reply_text(
          '❌ **رقم الهاتف غير صحيح!**\n🟢 **يرجى إرسال الرقم بشكل صحيح:**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  # حفظ الطلب في قاعدة البيانات بدلاً من الذاكرة المؤقتة
  conn = sqlite3.connect('users.db')
  cursor = conn.cursor()
  cursor.execute(
      'INSERT OR REPLACE INTO pending_requests (user_id, service_name,'
      ' target_input) VALUES (?, ?, ?)',
      (user.id, s_name, user_input),
  )
  conn.commit()
  conn.close()

  user_msg = (
      '✅ **تم إرسال الرقم للمالك.**\n\n'
      '🔴 الاختراق وهو فيروس، ورح يرسلك سعر الخدمة.\n'
      '⚠️ الخدمة ليست مجانية وسعرها بالكوينز.\n'
      '💳 الكوينز تقدر تشحنها من المالك من الزر الموجود في الشاشة الرئيسية.'
  )

  keyboard = [
      [
          InlineKeyboardButton(
              '💬 شحن كوينز / التواصل',
              url=f'https://t.me/{TARGET_USER.replace("@", "")}',
          )
      ]
  ]

  await update.message.reply_photo(
      photo=IMAGE_URL,
      caption=user_msg,
      reply_markup=InlineKeyboardMarkup(keyboard),
      parse_mode='Markdown',
  )

  try:
    await context.bot.send_message(
        chat_id=TARGET_USER,
        text=(
            '🚨 **طلب خدمة جديد (بالكوينز)!**\n'
            f'👤 اسم العميل: {user.first_name}\n'
            f'🆔 آيدي العميل: `{user.id}`\n'
            f'📌 الخدمة: {s_name}\n'
            f'🎯 الهدف المطلوب: `{user_input}`\n\n'
            '💡 **للرد بالسعر، أرسل الأمر:**\n'
            f'`/price {user.id} <السعر>`'
        ),
        parse_mode='Markdown',
    )
  except Exception:
    pass

  return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text('تم الإلغاء.')
  return ConversationHandler.END


# =========================
# التشغيل
# =========================


def main():
  init_db()
  app = (
      ApplicationBuilder()
      .token(TOKEN)
      .connect_timeout(30)
      .read_timeout(30)
      .write_timeout(30)
      .build()
  )

  app.add_handler(CommandHandler('charge', charge_user))
  app.add_handler(CommandHandler('price', admin_set_price))

  conv_handler = ConversationHandler(
      entry_points=[
          CommandHandler('start', start),
          CallbackQueryHandler(button_handler),
      ],
      states={
          WAITING_FOR_PLATFORM_CHOICE: [
              CallbackQueryHandler(platform_choice_handler)
          ],
          WAITING_FOR_TARGET_INPUT: [
              MessageHandler(
                  filters.TEXT & ~filters.COMMAND, receive_target_data
              )
          ],
          WAITING_FOR_ACCOUNT_FOLLOWERS: [
              MessageHandler(
                  filters.TEXT & ~filters.COMMAND, receive_account_followers
              )
          ],
          WAITING_FOR_ACCOUNT_USERNAME: [
              MessageHandler(
                  filters.TEXT & ~filters.COMMAND, receive_account_username
              )
          ],
      },
      fallbacks=[
          CommandHandler('cancel', cancel),
          CommandHandler('start', start),
      ],
  )

  app.add_handler(conv_handler)

  print('🤖 البوت يعمل بكامل التعديلات والربط بقاعدة البيانات...')
  app.run_polling()


if __name__ == '__main__':
  main()
