from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import ADMIN_ID
from datetime import datetime

class UrgentListingHandler:
    def __init__(self, db, analytics):
        self.db = db
        self.analytics = analytics

    async def show_urgent_menu(self, update: Update, context):
        """Display urgent listings menu."""
        keyboard = [
            ["📢 همه آگهی های فوری"],
            ["✨ درخواست آگهی فوری"],
            ["🔙 بازگشت به منوی اصلی"]
        ]
        
        await update.message.reply_text(
            "🔥 آگهی های فوری\n"
            "لطفاً یک گزینه را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return "URGENT_MENU"

    async def show_urgent_listings(self, update: Update, context):
        """Display all urgent listings."""
        listings = await self.db.get_urgent_listings()
        
        if not listings:
            await update.message.reply_text(
                "📭 در حال حاضر هیچ آگهی فوری ثبت نشده است."
            )
            return

        # Track interaction
        await self.analytics.track_interaction(
            update.effective_user.id,
            'view_urgent_listings'
        )

        for listing in listings:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "👁 مشاهده جزئیات",
                        callback_data=f"view_{listing['_id']}"
                    ),
                    InlineKeyboardButton(
                        "📞 تماس",
                        callback_data=f"contact_{listing['_id']}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "⭐️ نشان کردن",
                        callback_data=f"bookmark_{listing['_id']}"
                    ),
                    InlineKeyboardButton(
                        "🚫 گزارش",
                        callback_data=f"report_{listing['_id']}"
                    )
                ]
            ]
            
            message = (
                f"🔥 آگهی فوری\n\n"
                f"📌 {listing['title']}\n"
                f"💰 قیمت: {listing['price']:,} تومان\n"
                f"📍 موقعیت: {listing['location']}\n"
                f"⏰ ثبت شده در: {listing['created_at'].strftime('%Y-%m-%d %H:%M')}"
            )
            
            if listing.get('photos'):
                await update.message.reply_photo(
                    photo=listing['photos'][0],
                    caption=message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )

    async def request_urgent_listing(self, update: Update, context):
        """Handle urgent listing request."""
        await update.message.reply_text(
            "✨ درخواست آگهی فوری\n\n"
            "برای ثبت آگهی فوری با ادمین دیوار خواف تماس بگیرید:\n"
            "@divarkhafadmin\n\n"
            "مزایای آگهی فوری:\n"
            "🔸 نمایش در بخش ویژه\n"
            "🔸 اولویت در جستجو\n"
            "🔸 بازدید بیشتر\n"
            "🔸 فروش سریعتر"
        )

    async def handle_urgent_menu(self, update: Update, context):
        """Handle urgent menu selections."""
        text = update.message.text
        
        if text == "📢 همه آگهی های فوری":
            await self.show_urgent_listings(update, context)
        elif text == "✨ درخواست آگهی فوری":
            await self.request_urgent_listing(update, context)
        elif text == "🔙 بازگشت به منوی اصلی":
            return ConversationHandler.END

    def get_handler(self):
        """Return the ConversationHandler for urgent listings."""
        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Regex("^🔥 آگهی فوری$"),
                    self.show_urgent_menu
                )
            ],
            states={
                "URGENT_MENU": [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_urgent_menu
                    )
                ]
            },
            fallbacks=[
                MessageHandler(
                    filters.Regex("^🔙 بازگشت به منوی اصلی$"),
                    lambda u, c: ConversationHandler.END
                )
            ]
        )
