import logging
import sqlite3
import random
import datetime
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تعریف آداپتور برای datetime
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(s):
    return datetime.datetime.fromisoformat(s)

sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("DATETIME", convert_datetime)

# ایموجی‌ها و نام‌ها
EMOJIS = {
    '🔥': 'Fire',
    '💧': 'Water',
    '☁️': 'Cloud',
    '☀️': 'Sun',
    '❄️': 'Snow',
    '🌍': 'Earth',
    '⛰️': 'Mountain'
}

# لیست NFTها
NFT_LIST = [
    {'name': 'LOL Pop', 'price': 1.6},
    {'name': 'Holiday Drink', 'price': 1.8},
    {'name': 'Ginger Cookie', 'price': 1.8},
    {'name': 'Snoop Dogg', 'price': 2.0},
    {'name': 'Tama Gadget', 'price': 2.2},
    {'name': 'Swag Bag', 'price': 2.5},
    {'name': 'Snow Mittens', 'price': 3.0},
    {'name': 'Spy Agaric', 'price': 3.2},
    {'name': 'Pet Snake', 'price': 5.0},
    {'name': 'Snoop Cigar', 'price': 7.2}
]

# دیکشنری ترجمه‌ها
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome to @PlushNFTbot! 🎉',
        'captcha_prompt': 'Type the name of this emoji in English: {name}',
        'incorrect_captcha': 'Incorrect! Try /start again. ❌',
        'main_menu': 'Main Menu:',
        'profile': 'Profile 👤',
        'referral_link': 'Referral Link 🔗',
        'your_referral_link': 'Your referral link: {link}',
        'daily_bonus': 'Daily Bonus 🎁',
        'claimed_bonus': 'You claimed 0.1 TON daily bonus! 💰',
        'already_claimed_bonus': 'You already claimed today\'s bonus! ⏳',
        'withdrawal': 'Withdrawal 📤',
        'withdrawal_prompt': 'Depending on your account balance, select one of the following NFTs from the list and submit your withdrawal request using the glass button👇',
        'option': 'Option {number}:\n``` {name} ```: *{price} TON*',
        'user_info': 'User ID: {user_id}\nReferrals: {referrals}\nJoin Date: {join_date}\nWithdrawals: {withdrawals}',
        'referral_joined': 'User {username} joined via your referral link and 0.1 TON added to your balance. 👏',
        'request_account_id': 'Please enter your account ID to proceed with the withdrawal.',
        'confirm_purchase': 'Are you sure you want to purchase this NFT with the required balance deducted?',
        'confirm': '✅ Confirm',
        'cancel': '❌ Cancel',
        'withdrawal_success': 'Your NFT will be deposited into your account within the next 2 business days. 📩',
        'withdrawal_canceled': 'Operation canceled. 🚫',
        'insufficient_balance': 'Insufficient balance! ⚠️',
        'invalid_nft': 'Invalid NFT selection! ⚠️',
        'language': 'Language 🌐',
        'admin_menu': 'Admin Menu:',
        'list_users': 'List Users 👥',
        'list_requests': 'List Withdrawal Requests 📋',
        'broadcast': 'Broadcast Message 📢',
        'users_list': 'Users List:\n{users}',
        'requests_list': 'Withdrawal Requests:\n{requests}',
        'enter_broadcast': 'Enter the message to broadcast to all users.',
        'broadcast_sent': 'Message sent to all users. 📤',
        'approve': 'Approve ✅',
        'reject': 'Reject ❌',
        'request_approved': 'Request approved. ✅',
        'request_rejected': 'Request rejected. ❌',
        'not_admin': 'You are not the admin! ⚠️',
        'back': 'Back 🔙'
    },
    'fa': {
        'welcome': 'خوش آمدید به @PlushNFTbot! 🎉',
        'captcha_prompt': 'نام این ایموجی را به انگلیسی بنویسید: {name}',
        'incorrect_captcha': 'نادرست! دوباره /start را امتحان کنید. ❌',
        'main_menu': 'منوی اصلی:',
        'profile': 'پروفایل 👤',
        'referral_link': 'لینک رفرال 🔗',
        'your_referral_link': 'لینک رفرال شما: {link}',
        'daily_bonus': 'پاداش روزانه 🎁',
        'claimed_bonus': 'شما 0.1 TON پاداش روزانه دریافت کردید! 💰',
        'already_claimed_bonus': 'شما امروز پاداش را دریافت کرده‌اید! ⏳',
        'withdrawal': 'برداشت 📤',
        'withdrawal_prompt': 'با توجه به موجودی حسابتان، یکی از NFTهای زیر را از لیست انتخاب کنید و درخواست برداشت خود را با دکمه شیشه‌ای ارسال کنید👇',
        'option': 'گزینه {number}:\n``` {name} ```: *{price} TON*',
        'user_info': 'شناسه کاربر: {user_id}\nرفرال‌ها: {referrals}\nتاریخ عضویت: {join_date}\nبرداشت‌ها: {withdrawals}',
        'referral_joined': 'کاربر {username} از طریق لینک رفرال شما پیوست و 0.1 TON به موجودی شما اضافه شد. 👏',
        'request_account_id': 'لطفاً شناسه حساب خود را برای ادامه برداشت وارد کنید.',
        'confirm_purchase': 'آیا از خرید این NFT با کسر موجودی مورد نیاز مطمئن هستید؟',
        'confirm': '✅ تأیید',
        'cancel': '❌ لغو',
        'withdrawal_success': 'NFT شما طی 2 روز کاری آینده به حسابتان واریز خواهد شد. 📩',
        'withdrawal_canceled': 'عملیات لغو شد. 🚫',
        'insufficient_balance': 'موجودی کافی نیست! ⚠️',
        'invalid_nft': 'انتخاب NFT نامعتبر! ⚠️',
        'language': 'زبان 🌐',
        'admin_menu': 'منوی ادمین:',
        'list_users': 'لیست کاربران 👥',
        'list_requests': 'لیست درخواست‌های برداشت 📋',
        'broadcast': 'ارسال پیام گروهی 📢',
        'users_list': 'لیست کاربران:\n{users}',
        'requests_list': 'لیست درخواست‌های برداشت:\n{requests}',
        'enter_broadcast': 'پیام برای ارسال به همه کاربران را وارد کنید.',
        'broadcast_sent': 'پیام به همه کاربران ارسال شد. 📤',
        'approve': 'تأیید ✅',
        'reject': 'رد ❌',
        'request_approved': 'درخواست تأیید شد. ✅',
        'request_rejected': 'درخواست رد شد. ❌',
        'not_admin': 'شما ادمین نیستید! ⚠️',
        'back': 'بازگشت 🔙'
    },
    'ru': {  # روسی
        'welcome': 'Добро пожаловать в @PlushNFTbot! 🎉',
        'captcha_prompt': 'Введите название этого эмодзи на английском: {name}',
        'incorrect_captcha': 'Неверно! Попробуйте /start снова. ❌',
        'main_menu': 'Главное меню:',
        'profile': 'Профиль 👤',
        'referral_link': 'Реферальная ссылка 🔗',
        'your_referral_link': 'Ваша реферальная ссылка: {link}',
        'daily_bonus': 'Ежедневный бонус 🎁',
        'claimed_bonus': 'Вы получили 0.1 TON ежедневного бонуса! 💰',
        'already_claimed_bonus': 'Вы уже получили бонус за сегодня! ⏳',
        'withdrawal': 'Вывод 📤',
        'withdrawal_prompt': 'В зависимости от баланса вашего аккаунта, выберите один из следующих NFT из списка и отправьте запрос на вывод с помощью стеклянной кнопки👇',
        'option': 'Опция {number}:\n``` {name} ```: *{price} TON*',
        'user_info': 'ID пользователя: {user_id}\nРефералы: {referrals}\nДата присоединения: {join_date}\nВыводы: {withdrawals}',
        'referral_joined': 'Пользователь {username} присоединился по вашей реферальной ссылке, и 0.1 TON добавлено к вашему балансу. 👏',
        'request_account_id': 'Пожалуйста, введите ваш ID аккаунта для продолжения вывода.',
        'confirm_purchase': 'Вы уверены, что хотите купить этот NFT с вычетом требуемого баланса?',
        'confirm': '✅ Подтвердить',
        'cancel': '❌ Отмена',
        'withdrawal_success': 'Ваш NFT будет зачислен на ваш аккаунт в течение следующих 2 рабочих дней. 📩',
        'withdrawal_canceled': 'Операция отменена. 🚫',
        'insufficient_balance': 'Недостаточно баланса! ⚠️',
        'invalid_nft': 'Неверный выбор NFT! ⚠️',
        'language': 'Язык 🌐',
        'admin_menu': 'Меню администратора:',
        'list_users': 'Список пользователей 👥',
        'list_requests': 'Список запросов на вывод 📋',
        'broadcast': 'Рассылка сообщений 📢',
        'users_list': 'Список пользователей:\n{users}',
        'requests_list': 'Запросы на вывод:\n{requests}',
        'enter_broadcast': 'Введите сообщение для рассылки всем пользователям.',
        'broadcast_sent': 'Сообщение отправлено всем пользователям. 📤',
        'approve': 'Одобрить ✅',
        'reject': 'Отклонить ❌',
        'request_approved': 'Запрос одобрен. ✅',
        'request_rejected': 'Запрос отклонен. ❌',
        'not_admin': 'Вы не администратор! ⚠️',
        'back': 'Назад 🔙'
    },
    'fr': {  # فرانسوی
        'welcome': 'Bienvenue sur @PlushNFTbot ! 🎉',
        'captcha_prompt': 'Tapez le nom de cet emoji en anglais : {name}',
        'incorrect_captcha': 'Incorrect ! Réessayez avec /start. ❌',
        'main_menu': 'Menu Principal :',
        'profile': 'Profil 👤',
        'referral_link': 'Lien de Référence 🔗',
        'your_referral_link': 'Votre lien de référence : {link}',
        'daily_bonus': 'Bonus Quotidien 🎁',
        'claimed_bonus': 'Vous avez réclamé 0.1 TON de bonus quotidien ! 💰',
        'already_claimed_bonus': 'Vous avez déjà réclamé le bonus d\'aujourd\'hui ! ⏳',
        'withdrawal': 'Retrait 📤',
        'withdrawal_prompt': 'Selon votre solde, sélectionnez un des NFT suivants dans la liste et soumettez votre demande de retrait avec le bouton en verre👇',
        'option': 'Option {number}:\n``` {name} ```: *{price} TON*',
        'user_info': 'ID Utilisateur : {user_id}\nRéférences : {referrals}\nDate d\'inscription : {join_date}\nRetraits : {withdrawals}',
        'referral_joined': 'L\'utilisateur {username} s\'est inscrit via votre lien de référence et 0.1 TON a été ajouté à votre solde. 👏',
        'request_account_id': 'Veuillez entrer votre ID de compte pour continuer le retrait.',
        'confirm_purchase': 'Êtes-vous sûr de vouloir acheter ce NFT avec le solde requis déduit ?',
        'confirm': '✅ Confirmer',
        'cancel': '❌ Annuler',
        'withdrawal_success': 'Votre NFT sera déposé sur votre compte dans les 2 prochains jours ouvrables. 📩',
        'withdrawal_canceled': 'Opération annulée. 🚫',
        'insufficient_balance': 'Solde insuffisant ! ⚠️',
        'invalid_nft': 'Sélection NFT invalide ! ⚠️',
        'language': 'Langue 🌐',
        'admin_menu': 'Menu Administrateur :',
        'list_users': 'Liste des Utilisateurs 👥',
        'list_requests': 'Liste des Demandes de Retrait 📋',
        'broadcast': 'Message de Diffusion 📢',
        'users_list': 'Liste des Utilisateurs :\n{users}',
        'requests_list': 'Demandes de Retrait :\n{requests}',
        'enter_broadcast': 'Entrez le message à diffuser à tous les utilisateurs.',
        'broadcast_sent': 'Message envoyé à tous les utilisateurs. 📤',
        'approve': 'Approuver ✅',
        'reject': 'Rejeter ❌',
        'request_approved': 'Demande approuvée. ✅',
        'request_rejected': 'Demande rejetée. ❌',
        'not_admin': 'Vous n\'êtes pas administrateur ! ⚠️',
        'back': 'Retour 🔙'
    },
    'ar': {  # عربی
        'welcome': 'مرحبا بك في @PlushNFTbot! 🎉',
        'captcha_prompt': 'اكتب اسم هذا الإيموجي بالإنجليزية: {name}',
        'incorrect_captcha': 'خطأ! حاول /start مرة أخرى. ❌',
        'main_menu': 'القائمة الرئيسية:',
        'profile': 'الملف الشخصي 👤',
        'referral_link': 'رابط الإحالة 🔗',
        'your_referral_link': 'رابط الإحالة الخاص بك: {link}',
        'daily_bonus': 'المكافأة اليومية 🎁',
        'claimed_bonus': 'لقد حصلت على 0.1 TON مكافأة يومية! 💰',
        'already_claimed_bonus': 'لقد حصلت بالفعل على مكافأة اليوم! ⏳',
        'withdrawal': 'السحب 📤',
        'withdrawal_prompt': 'بناءً على رصيد حسابك، اختر أحد NFT التالية من القائمة وأرسل طلب السحب باستخدام زر الزجاج👇',
        'option': 'الخيار {number}:\n``` {name} ```: *{price} TON*',
        'user_info': 'معرف المستخدم: {user_id}\nالإحالات: {referrals}\nتاريخ الانضمام: {join_date}\nالسحوبات: {withdrawals}',
        'referral_joined': 'المستخدم {username} انضم عبر رابط الإحالة الخاص بك وتمت إضافة 0.1 TON إلى رصيدك. 👏',
        'request_account_id': 'يرجى إدخال معرف حسابك للمتابعة في السحب.',
        'confirm_purchase': 'هل أنت متأكد من شراء هذا NFT مع خصم الرصيد المطلوب؟',
        'confirm': '✅ تأكيد',
        'cancel': '❌ إلغاء',
        'withdrawal_success': 'سيتم إيداع NFT الخاص بك في حسابك خلال اليومين العاملين التاليين. 📩',
        'withdrawal_canceled': 'تم إلغاء العملية. 🚫',
        'insufficient_balance': 'رصيد غير كافٍ! ⚠️',
        'invalid_nft': 'اختيار NFT غير صالح! ⚠️',
        'language': 'اللغة 🌐',
        'admin_menu': 'قائمة المشرف:',
        'list_users': 'قائمة المستخدمين 👥',
        'list_requests': 'قائمة طلبات السحب 📋',
        'broadcast': 'رسالة الإذاعة 📢',
        'users_list': 'قائمة المستخدمين:\n{users}',
        'requests_list': 'طلبات السحب:\n{requests}',
        'enter_broadcast': 'أدخل الرسالة لإرسالها لجميع المستخدمين.',
        'broadcast_sent': 'تم إرسال الرسالة إلى جميع المستخدمين. 📤',
        'approve': 'موافقة ✅',
        'reject': 'رفض ❌',
        'request_approved': 'تمت الموافقة على الطلب. ✅',
        'request_rejected': 'تم رفض الطلب. ❌',
        'not_admin': 'أنت لست مشرفًا! ⚠️',
        'back': 'عودة 🔙'
    }
}

# آیدی ادمین (جایگزین با آیدی عددی تلگرام خودت)
ADMIN_ID = 5095867558 # جایگزین با آیدی واقعی تلگرامت

# اتصال دیتابیس
conn = sqlite3.connect('users.db', check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, referrer_id INTEGER, join_date DATETIME, referrals INTEGER DEFAULT 0, 
                   balance REAL DEFAULT 0.0, withdrawals INTEGER DEFAULT 0, last_bonus DATETIME, language TEXT DEFAULT 'en')''')
cursor.execute('''CREATE TABLE IF NOT EXISTS requests 
                  (request_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, nft_name TEXT, account_id TEXT, status TEXT DEFAULT 'pending')''')
conn.commit()

# تابع برای گرفتن ترجمه
def get_text(user_id, key, **kwargs):
    cursor.execute("SELECT language FROM users WHERE user_id=?", (user_id,))
    lang = cursor.fetchone()
    lang = lang[0] if lang else 'en'
    text = TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    return text.format(**kwargs)

# تابع برای تولید لینک رفرال
def get_referral_link(user_id):
    return f"https://t.me/PlushNFTbot?start={user_id}"  # جایگزین your_bot_username

# هندلر /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    args = context.args
    referrer_id = int(args[0]) if args else None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        await show_menu(update, context)
        return

    emoji = random.choice(list(EMOJIS.keys()))
    name = EMOJIS[emoji]
    options = random.sample(list(EMOJIS.keys()), 4)
    if emoji not in options:
        options[random.randint(0, 3)] = emoji

    keyboard = [[InlineKeyboardButton(opt, callback_data=f"captcha_{opt}_{emoji}") for opt in options]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(get_text(user_id, 'captcha_prompt', name=name), reply_markup=reply_markup)
    context.user_data['referrer_id'] = referrer_id
    context.user_data['captcha_emoji'] = emoji

# هندلر callback برای کپچا
async def captcha_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')
    selected = data[1]
    correct = data[2]

    await query.answer()
    if selected == correct:
        user_id = query.from_user.id
        referrer_id = context.user_data.get('referrer_id')

        join_date = datetime.datetime.now()
        cursor.execute("INSERT INTO users (user_id, referrer_id, join_date, language) VALUES (?, ?, ?, ?)", 
                       (user_id, referrer_id, join_date, 'en'))
        conn.commit()

        if referrer_id:
            cursor.execute("UPDATE users SET referrals = referrals + 1, balance = balance + 0.1 WHERE user_id=?", (referrer_id,))
            conn.commit()
            username = query.from_user.username or "Anonymous"
            await context.bot.send_message(referrer_id, get_text(referrer_id, 'referral_joined', username=username))

        await query.edit_message_text(get_text(user_id, 'welcome'))
        await show_menu(update, context)
    else:
        await query.edit_message_text(get_text(query.from_user.id, 'incorrect_captcha'))

# نمایش منو
async def show_menu(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'profile'), callback_data="profile")],
        [InlineKeyboardButton(get_text(user_id, 'referral_link'), callback_data="referral")],
        [InlineKeyboardButton(get_text(user_id, 'daily_bonus'), callback_data="daily_bonus")],
        [InlineKeyboardButton(get_text(user_id, 'withdrawal'), callback_data="withdrawal")],
        [InlineKeyboardButton(get_text(user_id, 'language'), callback_data="language")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = get_text(user_id, 'main_menu')
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# هندلر callback برای منو
async def menu_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    await query.answer()

    if data == "profile":
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cursor.fetchone()
        if user:
            user_info = get_text(user_id, 'user_info', referrals=user[3], join_date=user[2], withdrawals=user[5])
            keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(user_info, reply_markup=reply_markup)
        else:
            await query.edit_message_text("User data not found! ⚠️")
            await show_menu(update, context)

    elif data == "referral":
        link = get_referral_link(user_id)
        keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(get_text(user_id, 'your_referral_link', link=link), reply_markup=reply_markup)

    elif data == "daily_bonus":
        cursor.execute("SELECT last_bonus, balance FROM users WHERE user_id=?", (user_id,))
        last_bonus, balance = cursor.fetchone()
        now = datetime.datetime.now()
        if not last_bonus or (now - last_bonus) >= datetime.timedelta(days=1):
            new_balance = balance + 0.1
            cursor.execute("UPDATE users SET balance = ?, last_bonus = ? WHERE user_id=?", (new_balance, now, user_id))
            conn.commit()
            msg = get_text(user_id, 'claimed_bonus')
        else:
            msg = get_text(user_id, 'already_claimed_bonus')
        await context.bot.send_message(user_id, msg)
        keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Check your message! 📩", reply_markup=reply_markup)

    elif data == "withdrawal":
        msg = get_text(user_id, 'withdrawal_prompt') + "\n\n"
        for i, nft in enumerate(NFT_LIST, 1):
            msg += get_text(user_id, 'option', number=i, name=nft['name'], price=nft['price']) + "\n"
        keyboard = []
        for i, nft in enumerate(NFT_LIST, 1):
            keyboard.append([InlineKeyboardButton(f"``` {nft['name']} ``` 📦", callback_data=f"select_nft_{i-1}")])
        keyboard.append([InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
        context.user_data['withdrawal_mode'] = True

    elif data == "language":
        keyboard = [
            [InlineKeyboardButton("English 🇬🇧", callback_data="lang_en")],
            [InlineKeyboardButton("فارسی 🇮🇷", callback_data="lang_fa")],
            [InlineKeyboardButton("Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton("Français 🇫🇷", callback_data="lang_fr")],
            [InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")],
            [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Select language 🌐:", reply_markup=reply_markup)

    elif data == "main_menu":
        await show_menu(update, context)

# هندلر برای تغییر زبان
async def change_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    lang = data.split('_')[1]

    cursor.execute("UPDATE users SET language = ? WHERE user_id=?", (lang, user_id))
    conn.commit()

    await query.answer("Language changed! ✅")
    await show_menu(update, context)

# هندلر برای انتخاب NFT
async def select_nft(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data.split('_')
    if data[0] == "select" and data[1] == "nft":
        index = int(data[2])
        nft = NFT_LIST[index]
        user_id = query.from_user.id

        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]

        if balance >= nft['price']:
            context.user_data['selected_nft'] = nft
            await query.edit_message_text(get_text(user_id, 'request_account_id'))
            context.user_data['awaiting_account_id'] = True
        else:
            await query.edit_message_text(get_text(user_id, 'insufficient_balance'))
            await show_menu(update, context)

# هندلر پیام برای دریافت آیدی حساب و پیام‌های دیگر
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if context.user_data.get('awaiting_account_id'):
        nft = context.user_data.get('selected_nft')
        if nft:
            keyboard = [
                [InlineKeyboardButton(get_text(user_id, 'confirm'), callback_data="confirm_purchase")],
                [InlineKeyboardButton(get_text(user_id, 'cancel'), callback_data="cancel_purchase")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(get_text(user_id, 'confirm_purchase'), reply_markup=reply_markup)
            context.user_data['account_id'] = text
            context.user_data['awaiting_account_id'] = False
        else:
            await update.message.reply_text(get_text(user_id, 'invalid_nft'))
            context.user_data['awaiting_account_id'] = False
            await show_menu(update, context)
    elif context.user_data.get('awaiting_broadcast') and user_id == ADMIN_ID:
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        for u in users:
            try:
                await context.bot.send_message(u[0], text)
            except Exception as e:
                logger.error(f"Error sending broadcast to {u[0]}: {e}")
        await update.message.reply_text(get_text(user_id, 'broadcast_sent'))
        context.user_data['awaiting_broadcast'] = False
        await show_admin_menu(update, context)

# هندلر برای تأیید یا لغو خرید
async def handle_purchase(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    nft = context.user_data.get('selected_nft')
    account_id = context.user_data.get('account_id')

    if data == "confirm_purchase" and nft:
        cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = cursor.fetchone()[0]
        if balance >= nft['price']:
            new_balance = balance - nft['price']
            cursor.execute("UPDATE users SET balance = ?, withdrawals = withdrawals + 1 WHERE user_id=?", (new_balance, user_id))
            conn.commit()
            cursor.execute("INSERT INTO requests (user_id, nft_name, account_id) VALUES (?, ?, ?)", (user_id, nft['name'], account_id))
            conn.commit()
            await context.bot.send_message(ADMIN_ID, f"New withdrawal request from user {user_id}: NFT {nft['name']}, Account ID: {account_id}")
            await query.edit_message_text(get_text(user_id, 'withdrawal_success'))
        else:
            await query.edit_message_text(get_text(user_id, 'insufficient_balance'))
        context.user_data['selected_nft'] = None
        context.user_data['account_id'] = None
        await show_menu(update, context)
    elif data == "cancel_purchase":
        await query.edit_message_text(get_text(user_id, 'withdrawal_canceled'))
        context.user_data['selected_nft'] = None
        context.user_data['account_id'] = None
        await show_menu(update, context)

# هندلر /admin برای ادمین
async def admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id == ADMIN_ID:
        await show_admin_menu(update, context)
    else:
        await update.message.reply_text(get_text(user_id, 'not_admin'))

# نمایش منو ادمین
async def show_admin_menu(update: Update, context: CallbackContext) -> None:
    user_id = update.callback_query.from_user.id if update.callback_query else update.message.from_user.id
    keyboard = [
        [InlineKeyboardButton(get_text(user_id, 'list_users'), callback_data="admin_list_users")],
        [InlineKeyboardButton(get_text(user_id, 'list_requests'), callback_data="admin_list_requests")],
        [InlineKeyboardButton(get_text(user_id, 'broadcast'), callback_data="admin_broadcast")],
        [InlineKeyboardButton(get_text(user_id, 'back'), callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = get_text(user_id, 'admin_menu')
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# هندلر callback برای ادمین
async def admin_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id

    if user_id != ADMIN_ID:
        await query.answer(get_text(user_id, 'not_admin'))
        return

    await query.answer()

    if data == "admin_list_users":
        cursor.execute("SELECT user_id, balance FROM users")
        users = cursor.fetchall()
        msg = get_text(user_id, 'users_list', users='\n'.join([f"User {u[0]}: Balance {u[1]} TON" for u in users]))
        keyboard = [[InlineKeyboardButton(get_text(user_id, 'back'), callback_data="admin_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup)

    elif data == "admin_list_requests":
        cursor.execute("SELECT request_id, user_id, nft_name, account_id, status FROM requests")
        requests = cursor.fetchall()
        msg = get_text(user_id, 'requests_list', requests='\n'.join([f"ID {r[0]}: User {r[1]}, NFT {r[2]}, Account {r[3]}, Status {r[4]}" for r in requests]))
        keyboard = []
        if requests:
            for r in requests:
                keyboard.append([InlineKeyboardButton(f"{get_text(user_id, 'approve')} {r[0]} ✅", callback_data=f"admin_approve_{r[0]}"),
                               InlineKeyboardButton(f"{get_text(user_id, 'reject')} {r[0]} ❌", callback_data=f"admin_reject_{r[0]}")])
        keyboard.append([InlineKeyboardButton(get_text(user_id, 'back'), callback_data="admin_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(msg, reply_markup=reply_markup)

    elif data == "admin_broadcast":
        await query.edit_message_text(get_text(user_id, 'enter_broadcast'))
        context.user_data['awaiting_broadcast'] = True

    elif data.startswith("admin_approve_"):
        request_id = int(data.split('_')[2])
        cursor.execute("UPDATE requests SET status = 'approved' WHERE request_id=?", (request_id,))
        conn.commit()
        await query.edit_message_text(get_text(user_id, 'request_approved'))
        await show_admin_menu(update, context)

    elif data.startswith("admin_reject_"):
        request_id = int(data.split('_')[2])
        cursor.execute("UPDATE requests SET status = 'rejected' WHERE request_id=?", (request_id,))
        conn.commit()
        await query.edit_message_text(get_text(user_id, 'request_rejected'))
        await show_admin_menu(update, context)

    elif data == "admin_menu":
        await show_admin_menu(update, context)

    elif data == "main_menu":
        await show_menu(update, context)

# تابع برای تنظیم خودکار webhook
async def set_webhook(application):
    token = application.token
    port = int(os.getenv('PORT', 8443))
    webhook_url = f"https://plushnft.onrender.com/{token}"
    logger.info(f"Setting webhook to {webhook_url} on port {port}...")
    set_webhook_url = f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
    response = requests.get(set_webhook_url)
    if response.json().get('ok'):
        logger.info("Webhook set successfully!")
    else:
        logger.error(f"Failed to set webhook: {response.text}")

def main():
    token = "7593433447:AAF9Bnx0xzlDvJhz_DPCU02lQ70t2BBgSew"  # جایگزین با توکن واقعی
    logger.info(f"Initializing application with token: {token[:10]}...")
    application = Application.builder().token(token).build()

    # تنظیم خودکار webhook
    import asyncio
    asyncio.run(set_webhook(application))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CallbackQueryHandler(captcha_callback, pattern="^captcha_"))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(CallbackQueryHandler(change_language, pattern="^lang_"))
    application.add_handler(CallbackQueryHandler(select_nft, pattern="^select_nft_"))
    application.add_handler(CallbackQueryHandler(handle_purchase, pattern="^confirm_purchase|^cancel_purchase"))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_|^admin_menu|^main_menu"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # اجرای برنامه با webhook
    port = int(os.getenv('PORT', 8443))
    webhook_url = f"https://plushnft.onrender.com/{token}"
    logger.info(f"Running webhook on {webhook_url} with port {port}...")
    application.run_webhook(
        listen='0.0.0.0',
        port=port,
        url_path=token,
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    main() 
