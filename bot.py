import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from dotenv import load_dotenv
from config import (
    BOT_TOKEN,
    ADMIN_ID,
    CATEGORIES
)
from database import Database
from handlers.listing_handler import ListingHandler
from handlers.admin_handler import AdminHandler
from handlers.report_handler import ReportHandler
from handlers.urgent_handler import UrgentListingHandler
from utils.cache import Cache
from utils.analytics import Analytics

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
MAIN_MENU, CATEGORY_SELECT = range(2)

class DivarKhafBot:
    def __init__(self):
        # Initialize cache
        self.cache = Cache()
        
        # Initialize database
        self.db = Database(self.cache)
        
        # Initialize analytics
        self.analytics = Analytics(self.db)
        
        # Initialize handlers
        self.listing_handler = ListingHandler(self.db, self.analytics)
        self.admin_handler = AdminHandler(self.db, self.analytics)
        self.report_handler = ReportHandler(self.db)
        self.urgent_handler = UrgentListingHandler(self.db, self.analytics)

    def create_main_menu_keyboard(self, is_admin=False):
        """Create the main menu keyboard."""
        keyboard = [
            ["🔥 آگهی فوری", "➕ افزودن آگهی"],
            ["📢 آگهی ها", "📋 آگهی های من"],
            ["🔍 جستجو", "⭐ نشان شده ها"],
            ["📞 تماس با ما", "❓ راهنما"]
        ]
        if is_admin:
            keyboard.append(["👑 پنل مدیریت"])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def start(self, update: Update, context):
        """Start command handler."""
        user = update.effective_user
        is_admin = str(user.id) == str(ADMIN_ID)
        
        # Track user interaction
        await self.analytics.track_interaction(
            user.id, 
            'start_command'
        )
        
        # Update user data
        await self.db.update_user({
            'user_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'last_active': context.bot.current_timestamp
        })
        
        await update.message.reply_text(
            f"سلام {user.first_name}! 👋\n"
            "به دیوار خواف خوش آمدید!\n\n"
            "از منوی زیر گزینه مورد نظر خود را انتخاب کنید:",
            reply_markup=self.create_main_menu_keyboard(is_admin)
        )
        return MAIN_MENU

    async def help(self, update: Update, context):
        """Help command handler."""
        await self.analytics.track_interaction(
            update.effective_user.id, 
            'help_command'
        )
        
        help_text = (
            "🔰 راهنمای استفاده از ربات دیوار خواف:\n\n"
            "➕ افزودن آگهی جدید:\n"
            "۱. روی دکمه 'افزودن آگهی' کلیک کنید\n"
            "۲. دسته بندی مناسب را انتخاب کنید\n"
            "۳. عنوان و توضیحات آگهی را وارد کنید\n"
            "۴. عکس آگهی را ارسال کنید (اختیاری)\n"
            "۵. قیمت و اطلاعات تماس را وارد کنید\n\n"
            "🔍 جستجوی آگهی:\n"
            "- از دکمه 'جستجو' استفاده کنید\n"
            "- یا دسته بندی مورد نظر را انتخاب کنید\n\n"
            "⭐️ نشان کردن آگهی:\n"
            "- روی دکمه '⭐️' در زیر هر آگهی کلیک کنید\n\n"
            "📞 تماس با فروشنده:\n"
            "- از دکمه 'تماس' در زیر هر آگهی استفاده کنید\n\n"
            "🚫 گزارش تخلف:\n"
            "- از دکمه 'گزارش تخلف' در آگهی استفاده کنید"
        )
        
        await update.message.reply_text(help_text)
        return MAIN_MENU

    async def handle_main_menu(self, update: Update, context):
        """Handle main menu selections."""
        user = update.effective_user
        text = update.message.text
        
        # Track menu selection
        await self.analytics.track_interaction(
            user.id, 
            'menu_selection',
            {'selection': text}
        )
        
        if text == "🔥 آگهی فوری":
            return await self.urgent_handler.show_urgent_menu(update, context)
            
        elif text == "➕ افزودن آگهی":
            return await self.listing_handler.start_listing_creation(update, context)
            
        elif text == "📢 آگهی ها":
            return await self.listing_handler.show_categories(update, context)
            
        elif text == "📋 آگهی های من":
            return await self.listing_handler.show_user_listings(update, context)
            
        elif text == "🔍 جستجو":
            return await self.listing_handler.start_search(update, context)
            
        elif text == "⭐ نشان شده ها":
            return await self.listing_handler.show_bookmarks(update, context)
            
        elif text == "👑 پنل مدیریت" and str(user.id) == str(ADMIN_ID):
            return await self.admin_handler.admin_menu(update, context)

    def run(self):
        """Start the bot."""
        # Create the Application
        application = Application.builder().token(BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help))
        
        # Add main conversation handler
        application.add_handler(ConversationHandler(
            entry_points=[
                CommandHandler('start', self.start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_main_menu)
            ],
            states={
                MAIN_MENU: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_main_menu
                    )
                ]
            },
            fallbacks=[CommandHandler('start', self.start)]
        ))
        
        # Add other handlers
        application.add_handler(self.listing_handler.get_handler())
        application.add_handler(self.admin_handler.get_handler())
        application.add_handler(self.report_handler.get_handler())
        application.add_handler(self.urgent_handler.get_handler())

        # Start the Bot
        application.run_polling()

if __name__ == '__main__':
    bot = DivarKhafBot()
    bot.run()
