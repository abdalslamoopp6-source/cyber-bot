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
# إعدادات البوت
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

  # تسجيل المستخدم أو جلب بياناته
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

  # رسالة الترحيب المطلوبة
  welcome_text = (
      '🤖 **أهلاً بك في بوت الفيروس**\n'
      'هذا بوت خاص بالهكر، اختر الخدمة وتصفح فقط.\n\n'
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
# أمر إرسال رسالة خاصة للمستخدم من المالك
# =========================


async def admin_send_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user = update.effective_user
  if not user.username or user.username.lower() != TARGET_USER.replace(
      '@', ''
  ).lower():
    return

  args = context.args
  if len(args) < 2:
    await update.message.reply_text(
        '⚠️ **طريقة الاستخدام الصحيحة للإرسال لمستخدم:**\n'
        '`/send <آيدي_المستخدم> <الرسالة>`\n\n'
        'مثال:\n'
        '`/send 123456789 تم فحص طلبك بنجاح`',
        parse_mode='Markdown',
    )
    return

  target_chat_id = args[0]
  message_text = ' '.join(args[1:])

  try:
    await context.bot.send_message(
        chat_id=int(target_chat_id),
        text=(
            '💬 **رسالة من إدارة البوت:**\n\n'
            f'{message_text}\n\n'
            '💳 *للشحن أو التواصل استخدم الأزرار في القائمة الرئيسية.*'
        ),
        parse_mode='Markdown',
    )
    await update.message.reply_text(
        '✅ تم إرسال الرسالة إلى المستخدم بنجاح!'
    )
  except Exception as e:
    await update.message.reply_text(
        f'❌ فشل إرسال الرسالة للمستخدم. تأكد من صحة الآيدي. الخطأ: {e}'
    )


# =========================
# التعامل مع الأزرار
# =========================


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  user = update.effective_user

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
        '⚠️ **ملاحظة:** الخدمات ليست مجانية وتتطلب الدفع بالكوينز.'
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
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n\n🔴 **استرجاع حساب**\n🟢 ارسل عدد'
        ' المتابعين:'
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
        '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده كوينز.*\n\n'
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

    if s_name == 'هكر واتساب':
      input_prompt = (
          f'🟢 **تم اختيار: {s_name}**\n\n'
          '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
          '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده'
          ' كوينز.*\n\n'
          '🟢 **ارسل الرقم المراد اختراقه:**'
      )
    elif s_name == 'استرجاع رقم':
      input_prompt = (
          f'🟢 **تم اختيار: {s_name}**\n\n'
          '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
          '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده'
          ' كوينز.*\n\n'
          '🟢 **ارسل الرقم المراد استرجاعه:**'
      )
    elif s_name == 'هكر إيميل':
      input_prompt = (
          f'🟢 **تم اختيار: {s_name}**\n\n'
          '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
          '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده'
          ' كوينز.*\n\n'
          '🟢 **ارسل البريد الإلكتروني (الإيميل) المراد اختراقه:**'
      )
    else:
      input_prompt = (
          f'🟢 **تم اختيار: {s_name}**\n\n'
          '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
          '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده'
          ' كوينز.*\n\n'
          '🟢 **ارسل الهدف المطلوب:**'
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
  followers_text = update.message.text.strip()
  context.user_data['account_followers'] = followers_text

  await update.message.reply_text(
      '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده كوينز.*\n\n🟢'
      ' **ارسل اليوزر المراد استرجاعه:**',
      parse_mode='Markdown',
  )
  return WAITING_FOR_ACCOUNT_USERNAME


async def receive_account_username(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  username_input = update.message.text.strip()
  followers_count = context.user_data.get('account_followers', 'غير محدد')
  user = update.effective_user

  if ' ' in username_input or len(username_input) < 2:
    await update.message.reply_text(
        '❌ **اسم اليوزر غير صحيح!**\n'
        'يجب أن يكون يوزراً صحيحاً وخالياً من المسافات.\n'
        '🔴 **يرجى إرسال اليوزر الصحيح:**',
        parse_mode='Markdown',
    )
    return WAITING_FOR_ACCOUNT_USERNAME

  user_msg = (
      'تم اختيار هذه الخدمة وتم إرسال الطلب إلى مالك البوت، راح يتم اكتشاف الحساب'
      ' والسعر المطلوب وراح يتم إرسال لك السعر بالكوينز يرسلها لك البوت في أقرب'
      ' وقت، والكوينز تقدر تشحنها من الأزرار اللي في القائمة الرئيسية.'
  )
  keyboard = [
      [
          InlineKeyboardButton(
              '💬 التواصل مع المالك للشحن',
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
            '🚨 **طلب استرجاع حساب جديد (بالكوينز)!**\n'
            f'👤 العميل: {user.first_name}\n'
            f'🆔 آيدي العميل (انسخه للإرسال له): `{user.id}`\n'
            f'👥 المتابعين: {followers_count}\n'
            f'🎯 اليوزر المراد استرجاعه: `{username_input}`'
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
    context.user_data['pending_service'] = f'اختراق {p_name}'

    success_social_text = (
        f'🟢 **تم اختيار منصة {p_name}!**\n\n'
        '⚠️ **تنبيه: الخدمة ليست مجانية!**\n'
        '💰 *السعر بالكوينز رح يرسله لك مالك البوت وتقدر تشحن من عنده كوينز.*\n\n'
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

  # التحقق من الإيميل
  if s_name == 'هكر إيميل':
    if '@' not in user_input or '.' not in user_input or len(user_input) < 6:
      await update.message.reply_text(
          '❌ **البريد الإلكتروني غير صحيح!**\n'
          'تم رفض الإدخال لعدم مطابقة الشروط.\n'
          '🔴 **يرجى إرسال إيميل صحيح يحتوي على (@) والنطاق (مثل: example@gmail.com):**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  # التحقق من يوزرات منصات التواصل
  elif 'اختراق' in s_name:
    if ' ' in user_input or len(user_input) < 2:
      await update.message.reply_text(
          '❌ **اسم اليوزر أو الحساب غير صحيح!**\n'
          'يجب أن يكون اسم المستخدم صحيحاً وخالياً من المسافات.\n'
          '🔴 **يرجى إرسال يوزر صحيح:**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  # التحقق من أرقام الهواتف
  elif 'واتساب' in s_name or 'رقم' in s_name:
    digits_only = re.sub(r'\D', '', user_input)
    if len(digits_only) < 7:
      await update.message.reply_text(
          '❌ **رقم الهاتف غير صحيح!**\n'
          'الرجاء التأكد من إدخال رقم صحيح يحتوي على أرقام كافية.\n'
          '🟢 **يرجى إعادة إرسال الرقم بشكل صحيح:**',
          parse_mode='Markdown',
      )
      return WAITING_FOR_TARGET_INPUT

  if 'استرجاع' in s_name:
    action_text = (
        'تم إرسال الطلب إلى مالك البوت، راح يتم اكتشاف البيانات والسعر المطلوب'
        ' وراح يتم إرسال لك السعر بالكوينز يرسلها لك البوت في أقرب وقت، والكوينز'
        ' تقدر تشحنها من الأزرار اللي في القائمة الرئيسية.'
    )
  else:
    action_text = (
        'تم إرسال الهدف إلى مالك البوت، راح يتم اكتشاف الهدف والسعر المطلوب وراح'
        ' يتم إرسال لك السعر بالكوينز يرسلها لك البوت في أقرب وقت، والكوينز'
        ' تقدر تشحنها من الأزرار اللي في القائمة الرئيسية.'
    )

  review_text = (
      f'🟢 **تم اختيار هذه الخدمة:** {s_name}\n\n'
      f'{action_text}\n\n'
      f'🎯 المدخل: `{user_input}`'
  )

  keyboard = [
      [
          InlineKeyboardButton(
              '💬 مراسلة المالك للشحن',
              url=f'https://t.me/{TARGET_USER.replace("@", "")}',
          )
      ]
  ]

  await update.message.reply_photo(
      photo=IMAGE_URL,
      caption=review_text,
      reply_markup=InlineKeyboardMarkup(keyboard),
      parse_mode='Markdown',
  )

  try:
    await context.bot.send_message(
        chat_id=TARGET_USER,
        text=(
            '🚨 **طلب خدمة جديد (بالكوينز)!**\n'
            f'👤 اسم العميل: {user.first_name}\n'
            f'🆔 آيدي العميل (انسخه للإرسال له): `{user.id}`\n'
            f'📌 الخدمة: {s_name}\n'
            f'🎯 المدخل المطلوب: `{user_input}`'
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

  # إضافة أمر الإرسال المباشر للمالك
  app.add_handler(CommandHandler('send', admin_send_message))

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

  print('🤖 البوت يعمل بكامل التعديلات والتحكم الخاص بالمالك...')
  app.run_polling()


if __name__ == '__main__':
  main()
