from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import ADMIN_ID
from datetime import datetime

# Admin panel states
(ADMIN_MENU, HANDLE_REPORTS, MANAGE_URGENT, BROADCAST_MESSAGE,
 REMOVE_AD, ADD_URGENT, VIEW_STATS, HANDLE_USER) = range(8)

class AdminHandler:
    def __init__(self, db, analytics):
        self.db = db
        self.analytics = analytics

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return str(user_id) == str(ADMIN_ID)

    def create_admin_keyboard(self):
        """Create admin panel keyboard."""
        keyboard = [
            ["📊 آمار کلی", "🚫 گزارش های تخلف"],
            ["✨ مدیریت آگهی های فوری", "❌ حذف آگهی"],
            ["📢 ارسال پیام همگانی", "👥 کاربران آنلاین"],
            ["🔙 بازگشت به منوی اصلی"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def admin_menu(self, update: Update, context):
        """Display admin panel menu."""
        if not self.is_admin(update.effective_user.id):
            await update.message.reply_text("⛔️ شما دسترسی به این بخش را ندارید.")
            return ConversationHandler.END

        await update.message.reply_text(
            "🎛 پنل مدیریت دیوار خواف\n"
            "لطفا یکی از گزینه های زیر را انتخاب کنید:",
            reply_markup=self.create_admin_keyboard()
        )
        return ADMIN_MENU

    async def handle_admin_menu(self, update: Update, context):
        """Handle admin menu selections."""
        text = update.message.text

        if text == "📊 آمار کلی":
            return await self.show_statistics(update, context)
        elif text == "🚫 گزارش های تخلف":
            return await self.show_reports(update, context)
        elif text == "✨ مدیریت آگهی های فوری":
            return await self.manage_urgent_ads(update, context)
        elif text == "❌ حذف آگهی":
            return await self.remove_ad_start(update, context)
        elif text == "📢 ارسال پیام همگانی":
            return await self.broadcast_start(update, context)
        elif text == "👥 کاربران آنلاین":
            return await self.show_online_users(update, context)
        elif text == "🔙 بازگشت به منوی اصلی":
            return ConversationHandler.END

    async def show_statistics(self, update: Update, context):
        """Show bot statistics."""
        stats = await self.db.get_statistics()
        
        message = (
            "📊 آمار کلی دیوار خواف:\n\n"
            f"👥 تعداد کل کاربران: {stats.get('total_users', 0)}\n"
            f"📢 تعداد کل آگهی ها: {stats.get('total_listings', 0)}\n"
            f"✅ آگهی های فعال: {stats.get('active_listings', 0)}\n"
            f"🔥 آگهی های فوری: {stats.get('urgent_listings', 0)}\n"
            f"👁 بازدید امروز: {stats.get('today_views', 0)}\n"
            f"👥 کاربران جدید امروز: {stats.get('today_new_users', 0)}\n"
            f"📝 آگهی های جدید امروز: {stats.get('today_new_listings', 0)}\n"
            f"🚫 گزارش های در انتظار: {stats.get('pending_reports', 0)}\n\n"
            f"آخرین بروزرسانی: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await update.message.reply_text(message)
        return ADMIN_MENU

    async def show_reports(self, update: Update, context):
        """Show reported listings."""
        reports = await self.db.get_reports(status="pending")
        
        if not reports:
            await update.message.reply_text("🎉 هیچ گزارش تخلفی وجود ندارد!")
            return ADMIN_MENU

        for report in reports:
            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ تایید و حذف آگهی",
                        callback_data=f"approve_report_{report['_id']}"
                    ),
                    InlineKeyboardButton(
                        "❌ رد گزارش",
                        callback_data=f"reject_report_{report['_id']}"
                    )
                ]
            ]
            
            message = (
                f"🚫 گزارش تخلف:\n\n"
                f"📢 آگهی: {report.get('listing_title', 'نامشخص')}\n"
                f"👤 گزارش دهنده: {report.get('reporter_name', 'نامشخص')}\n"
                f"📝 دلیل: {report.get('reason', 'نامشخص')}\n"
                f"⏰ زمان گزارش: {report['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            await update.message.reply_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        return HANDLE_REPORTS

    async def handle_report_action(self, update: Update, context):
        """Handle report approval or rejection."""
        query = update.callback_query
        action, report_id = query.data.split('_')[1:]
        
        success = await self.db.handle_report(report_id, action)
        
        if success:
            await query.edit_message_text(
                f"✅ گزارش با موفقیت {'تایید و آگهی حذف شد' if action == 'approve' else 'رد شد'}."
            )
        else:
            await query.edit_message_text("❌ خطا در پردازش گزارش.")
        
        return ADMIN_MENU

    async def manage_urgent_ads(self, update: Update, context):
        """Manage urgent ads section."""
        keyboard = [
            ["➕ افزودن آگهی فوری جدید"],
            ["📋 لیست آگهی های فوری"],
            ["🔙 بازگشت به پنل مدیریت"]
        ]
        
        await update.message.reply_text(
            "✨ مدیریت آگهی های فوری\n"
            "لطفا یک گزینه را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return MANAGE_URGENT

    async def broadcast_start(self, update: Update, context):
        """Start broadcast message process."""
        await update.message.reply_text(
            "📢 ارسال پیام همگانی\n"
            "لطفا پیام خود را وارد کنید:"
        )
        return BROADCAST_MESSAGE

    async def broadcast_message(self, update: Update, context):
        """Send broadcast message to all users."""
        message = update.message.text
        users = await self.db.get_all_users()
        success = 0
        failed = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 پیام مدیریت دیوار خواف:\n\n{message}"
                )
                success += 1
            except:
                failed += 1

        await update.message.reply_text(
            f"✅ پیام با موفقیت ارسال شد!\n\n"
            f"📊 نتیجه ارسال:\n"
            f"✅ موفق: {success}\n"
            f"❌ ناموفق: {failed}"
        )
        return ADMIN_MENU

    async def remove_ad_start(self, update: Update, context):
        """Start process of removing an ad."""
        await update.message.reply_text(
            "❌ حذف آگهی\n"
            "لطفا شناسه آگهی مورد نظر را وارد کنید:"
        )
        return REMOVE_AD

    async def remove_ad(self, update: Update, context):
        """Remove specified ad."""
        listing_id = update.message.text
        result = await self.db.remove_listing(listing_id)
        
        if result:
            await update.message.reply_text("✅ آگهی با موفقیت حذف شد.")
        else:
            await update.message.reply_text("❌ آگهی مورد نظر یافت نشد.")
        
        return ADMIN_MENU

    def get_handler(self):
        """Return the ConversationHandler for admin panel."""
        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Regex("^👑 پنل مدیریت$"), 
                    self.admin_menu
                )
            ],
            states={
                ADMIN_MENU: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_admin_menu
                    )
                ],
                HANDLE_REPORTS: [
                    CallbackQueryHandler(
                        self.handle_report_action,
                        pattern=r'^(approve|reject)_report_\d+'
                    )
                ],
                MANAGE_URGENT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.manage_urgent_ads
                    )
                ],
                BROADCAST_MESSAGE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.broadcast_message
                    )
                ],
                REMOVE_AD: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.remove_ad
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
