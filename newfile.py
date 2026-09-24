import sqlite3
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# =========================
# إعدادات البوت
# =========================

TOKEN = "8506228695:AAE3Sy2VXlbgPijeWgF-YmdVpDOakvHpCfM"
TARGET_USER = "@BoTmz66"  # يوزر حسابك للمسؤول
IMAGE_URL = "https://cdn.phototourl.com/member/2026-09-23-f246863f-e6e8-440d-844d-03cd92960e4d.jpg"

# حالات المحادثة
WAITING_FOR_CONFIRMATION = 1
WAITING_FOR_PLATFORM_CHOICE = 2
WAITING_FOR_TARGET_INPUT = 3
WAITING_FOR_ACCOUNT_FOLLOWERS = 4
WAITING_FOR_ACCOUNT_USERNAME = 5


# =========================
# التحقق من صحة المدخلات
# =========================

def is_valid_target(text):
    text = text.strip()
    if len(text) < 3:
        return False
    
    phone_pattern = r'^\+?[0-9]{7,15}$'
    if re.match(phone_pattern, text):
        return True
    
    if text.isdigit():
        return False
    
    if any(domain in text.lower() for domain in ["t.me/", "instagram.com/", "tiktok.com/", "facebook.com/", "x.com/", "twitter.com/"]):
        return True
    
    pattern = r'^@?[a-zA-Z0-9_.-]{3,35}$'
    return bool(re.match(pattern, text))


# =========================
# إعداد قاعدة البيانات
# =========================

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TEXT
        )
    """)
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if "coins" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0")
    conn.commit()
    conn.close()


# =========================
# القائمة الرئيسية (نصوص مختصرة)
# =========================

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, is_callback=False):
    user = update.effective_user
    
    init_db()
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    
    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, coins, joined_at) VALUES (?, ?, ?, 0, ?)",
            (user.id, user.username or "", user.first_name or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        current_coins = 0
    else:
        current_coins = row[0] if row[0] is not None else 0
        
    conn.close()

    welcome_text = (
        "💻 **[ CYBER ROOT ]** 💻\n"
        f"🔴 **الرصيد:** `{current_coins}` كوينز\n\n"
        "⚡ **اختر الخدمة المطلوبة:**"
    )

    keyboard = [
        [
            InlineKeyboardButton("💻 معلومات المالك", callback_data="service_virus"),
            InlineKeyboardButton("🔴 هكر واتساب (10)", callback_data="service_whatsapp")
        ],
        [
            InlineKeyboardButton("🟢 استرجاع رقم (10)", callback_data="service_recover_whatsapp"),
            InlineKeyboardButton("🔴 استرجاع حساب", callback_data="service_recover_accounts")
        ],
        [
            InlineKeyboardButton("🟢 هكر إيميل (15)", callback_data="service_email"),
            InlineKeyboardButton("🔴 منصات (40)", callback_data="service_social")
        ],
        [
            InlineKeyboardButton("👤 حسابي", callback_data="my_account"),
            InlineKeyboardButton("ℹ️ معلومات", callback_data="bot_info")
        ],
        [
            InlineKeyboardButton("📊 السجل", callback_data="admin_stats"),
            InlineKeyboardButton("💳 شحن", url=f"https://t.me/{TARGET_USER.replace('@', '')}")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if is_callback:
        query = update.callback_query
        if query.message.photo:
            await query.edit_message_caption(caption=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.edit_message_text(text=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_photo(photo=IMAGE_URL, caption=welcome_text, reply_markup=reply_markup, parse_mode="Markdown")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_main_menu(update, context, is_callback=False)
    return ConversationHandler.END


# =========================
# التعامل مع الأزرار
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    user_coins = row[0] if (row and row[0] is not None) else 0
    conn.close()

    if query.data == "verify" or query.data == "main_menu":
        await send_main_menu(update, context, is_callback=True)
        return ConversationHandler.END

    # صفحة معلومات المالك (مجانية بالكامل وبدون خصم)
    elif query.data == "service_virus":
        owner_text = (
            "💻 **[ معلومات مالك البوت ]**\n"
            "👤 **الاسم:** فيروز | هكر سعودي\n"
            "⭐ **الخبرة:** متعلم منذ 10 سنوات\n"
            "🔒 **الأمان:** أمين مليون بالمئة\n"
            "📞 **الهاتف:** رقم مجهول (سعودي)"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        await query.edit_message_caption(caption=owner_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif query.data == "my_account":
        account_text = (
            "👤 **[ معلومات العميل ]**\n"
            f"🟢 **الاسم:** {user.first_name}\n"
            f"🆔 **الآيدي:** `{user.id}` | 🔴 **الرصيد:** `{user_coins}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        await query.edit_message_caption(caption=account_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif query.data == "bot_info":
        info_text = (
            "ℹ️ **[ النظام الآمن ]**\n"
            "نظام مخصص للخدمات الرقمية.\n"
            "🔴 **الضمان:** استرجاع الكوينز عند الفشل."
        )
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        await query.edit_message_caption(caption=info_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif query.data == "admin_stats":
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        conn.close()

        stats_text = f"📊 **[ الإحصائيات ]**\n🟢 **المستخدمين:** `{total_users}`"
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
        await query.edit_message_caption(caption=stats_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return ConversationHandler.END

    elif query.data == "service_recover_accounts":
        prompt_text = "🔴 **استرجاع حساب**\n🟢 ارسل عدد المتابعين:"
        keyboard = [[InlineKeyboardButton("🔙 إلغاء", callback_data="main_menu")]]
        await query.edit_message_caption(caption=prompt_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return WAITING_FOR_ACCOUNT_FOLLOWERS

    if query.data == "service_social":
        platform_text = f"🌐 **اختر المنصة** (رصيدك: `{user_coins}`)"
        keyboard = [
            [
                InlineKeyboardButton("🟢 تيك توك", callback_data="plat_tiktok"),
                InlineKeyboardButton("🔴 انستغرام", callback_data="plat_instagram")
            ],
            [
                InlineKeyboardButton("🟢 فيسبوك", callback_data="plat_facebook"),
                InlineKeyboardButton("🔴 إكس", callback_data="plat_x")
            ],
            [
                InlineKeyboardButton("🟢 تيليجرام", callback_data="plat_telegram"),
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]
        ]
        await query.edit_message_caption(caption=platform_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return WAITING_FOR_PLATFORM_CHOICE

    costs = {
        "service_whatsapp": (10, "هكر واتساب"),
        "service_recover_whatsapp": (10, "استرجاع رقم"),
        "service_email": (15, "هكر إيميل")
    }

    if query.data in costs:
        cost, s_name = costs[query.data]
        
        if user_coins < cost:
            no_balance_text = f"❌ **رصيدك غير كافي!**\n🟢 رصيدك: `{user_coins}` | المطلوبة: `{cost}`"
            keyboard = [
                [InlineKeyboardButton("💳 شحن", url=f"https://t.me/{TARGET_USER.replace('@', '')}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
            ]
            await query.edit_message_caption(caption=no_balance_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return ConversationHandler.END

        context.user_data['pending_service'] = s_name
        context.user_data['pending_cost'] = cost

        confirm_text = f"⚠️ **تأكيد الطلب**\n🟢 الخدمة: {s_name}\n🔴 التكلفة: `{cost}` كوينز"
        keyboard = [
            [
                InlineKeyboardButton("🟢 تأكيد", callback_data="confirm_buy_yes"),
                InlineKeyboardButton("🔴 إلغاء", callback_data="main_menu")
            ]
        ]
        await query.edit_message_caption(caption=confirm_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return WAITING_FOR_CONFIRMATION

    return ConversationHandler.END


# =========================
# خطوات الحسابات
# =========================

async def receive_account_followers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    followers_text = update.message.text.strip()
    context.user_data['account_followers'] = followers_text
    
    await update.message.reply_text("🟢 ارسل يوزر الحساب:", parse_mode="Markdown")
    return WAITING_FOR_ACCOUNT_USERNAME


async def receive_account_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username_input = update.message.text.strip()
    followers_count = context.user_data.get('account_followers', 'غير محدد')
    user = update.effective_user
    
    user_msg = "🟢 تم إرسال الحساب للمراجعة وتحديد التكلفة."
    keyboard = [[InlineKeyboardButton("💬 مراسلة المسؤول", url=f"https://t.me/{TARGET_USER.replace('@', '')}")]]
    
    await update.message.reply_photo(photo=IMAGE_URL, caption=user_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    
    try:
        await context.bot.send_message(
            chat_id=TARGET_USER,
            text=f"🚨 **طلب استرجاع جديد!**\n👤 العميل: {user.first_name} (`{user.id}`)\n👥 المتابعين: {followers_count}\n🎯 اليوزر: `{username_input}`",
            parse_mode="Markdown"
        )
    except Exception:
        pass
        
    return ConversationHandler.END


# =========================
# تأكيد الشراء
# =========================

async def confirm_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        await send_main_menu(update, context, is_callback=True)
        return ConversationHandler.END

    if query.data == "confirm_buy_yes":
        user = update.effective_user
        cost = context.user_data.get('pending_cost', 0)
        s_name = context.user_data.get('pending_service', 'خدمة')

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        current_coins = row[0] if (row and row[0] is not None) else 0

        if current_coins < cost:
            conn.close()
            await query.edit_message_caption(caption="❌ الرصيد أصبح غير كافي!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 الرئيسية", callback_data="main_menu")]]))
            return ConversationHandler.END

        new_balance = current_coins - cost
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, user.id))
        conn.commit()
        conn.close()

        # طلب رقم الهاتف مباشرة بدون ذكر يوزر أو رابط عند اختيار واتساب أو استرجاع أرقام
        if "واتساب" in s_name or "رقم" in s_name:
            input_prompt = "🟢 ارسل رقم الهاتف المستهدف:"
        elif "الإيميل" in s_name:
            input_prompt = "🟢 ارسل البريد الإلكتروني:"
        else:
            input_prompt = "🟢 ارسل الهدف المطلوب:"

        success_buy_text = f"🟢 **تم الخصم بنجاح!**\n المتبقي: `{new_balance}` كوينز\n\n{input_prompt}"
        await query.message.reply_text(success_buy_text, parse_mode="Markdown")
        return WAITING_FOR_TARGET_INPUT

    return ConversationHandler.END


# =========================
# اختيار المنصة
# =========================

async def platform_choice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "main_menu":
        await send_main_menu(update, context, is_callback=True)
        return ConversationHandler.END

    platforms = {
        "plat_tiktok": "تيك توك",
        "plat_instagram": "انستغرام",
        "plat_facebook": "فيسبوك",
        "plat_x": "إكس",
        "plat_telegram": "تيليجرام"
    }

    if query.data in platforms:
        p_name = platforms[query.data]
        cost = 40
        user = update.effective_user

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
        row = cursor.fetchone()
        user_coins = row[0] if (row and row[0] is not None) else 0

        if user_coins < cost:
            conn.close()
            no_balance_text = f"❌ رصيدك غير كافي! (`{user_coins}`/`{cost}`)"
            keyboard = [
                [InlineKeyboardButton("💳 شحن", url=f"https://t.me/{TARGET_USER.replace('@', '')}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
            ]
            await query.edit_message_caption(caption=no_balance_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
            return ConversationHandler.END

        new_balance = user_coins - cost
        cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_balance, user.id))
        conn.commit()
        conn.close()

        context.user_data['pending_service'] = f"اختراق {p_name}"

        success_social_text = f"🟢 **تم الشراء!** المتبقي: `{new_balance}`\n\n🔴 ارسل يوزر الحساب المستهدف:"
        await query.message.reply_text(success_social_text, parse_mode="Markdown")
        return WAITING_FOR_TARGET_INPUT

    return ConversationHandler.END


# =========================
# استقبال الهدف
# =========================

async def receive_target_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user = update.effective_user
    s_name = context.user_data.get('pending_service', 'خدمة')

    review_text = f"⏳ **قيد المعالجة**\n🟢 الخدمة: {s_name}\n🔴 الهدف: `{user_input}`"
    keyboard = [[InlineKeyboardButton("💬 مراسلة المسؤول", url=f"https://t.me/{TARGET_USER.replace('@', '')}")]]
    
    await update.message.reply_photo(photo=IMAGE_URL, caption=review_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    try:
        await context.bot.send_message(
            chat_id=TARGET_USER,
            text=f"🚨 **طلب مدفوع جديد!**\n👤 العميل: {user.first_name} (`{user.id}`)\n📌 الخدمة: {s_name}\n🎯 الهدف: `{user_input}`",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.")
    return ConversationHandler.END


# =========================
# شحن الكوينز للمشرف
# =========================

async def add_coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ الصيغة: `/addcoins [ID] [العدد]`", parse_mode="Markdown")
        return

    try:
        target_id = int(args[0])
        coins_to_add = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ تأكد أن الآيدي والعدد أرقام صحيحة.")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, coins FROM users WHERE user_id = ?", (target_id,))
    user_row = cursor.fetchone()

    if not user_row:
        await update.message.reply_text("❌ المستخدم غير مسجل.")
        conn.close()
        return

    current_coins = user_row[1] if user_row[1] is not None else 0
    new_total = current_coins + coins_to_add

    cursor.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_total, target_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(f"🟢 **تم الشحن بنجاح!**\n🆔 الآيدي: `{target_id}`\n💰 الجديد: `{new_total}`", parse_mode="Markdown")

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"🎁 **تم شحن رصيدك!**\n➕ أُضيف: `{coins_to_add}`\n💰 رصيدك: `{new_total}`",
            parse_mode="Markdown"
        )
    except Exception:
        pass


# =========================
# التشغيل
# =========================

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_handler)
        ],
        states={
            WAITING_FOR_CONFIRMATION: [CallbackQueryHandler(confirm_purchase_handler)],
            WAITING_FOR_PLATFORM_CHOICE: [CallbackQueryHandler(platform_choice_handler)],
            WAITING_FOR_TARGET_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_data)],
            WAITING_FOR_ACCOUNT_FOLLOWERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_followers)],
            WAITING_FOR_ACCOUNT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_account_username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("addcoins", add_coins_command))

    print("🤖 البوت يعمل بكامل التعديلات وجاهز...")
    app.run_polling()


if __name__ == "__main__":
    main()
