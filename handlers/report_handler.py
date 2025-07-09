from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from datetime import datetime

REPORT_REASON = range(1)

class ReportHandler:
    def __init__(self, db):
        self.db = db

    async def start_report(self, update: Update, context):
        """Start the reporting process."""
        query = update.callback_query
        listing_id = query.data.split('_')[1]
        context.user_data['reporting_listing'] = listing_id
        
        keyboard = [
            [InlineKeyboardButton("محتوای نامناسب", callback_data="reason_inappropriate")],
            [InlineKeyboardButton("کلاهبرداری", callback_data="reason_scam")],
            [InlineKeyboardButton("اطلاعات نادرست", callback_data="reason_false_info")],
            [InlineKeyboardButton("تکراری", callback_data="reason_duplicate")],
            [InlineKeyboardButton("لغو ⛔️", callback_data="cancel_report")]
        ]
        
        await query.edit_message_text(
            "🚫 گزارش تخلف\n\n"
            "لطفا دلیل گزارش را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return REPORT_REASON

    async def handle_report_reason(self, update: Update, context):
        """Handle the selected report reason."""
        query = update.callback_query
        if query.data == "cancel_report":
            await query.edit_message_text("❌ گزارش لغو شد.")
            return ConversationHandler.END

        reason = query.data.split('_')[1]
        listing_id = context.user_data.get('reporting_listing')
        
        # Get listing details
        listing = await self.db.get_listing(listing_id)
        if not listing:
            await query.edit_message_text("❌ آگهی مورد نظر یافت نشد.")
            return ConversationHandler.END
        
        report_data = {
            'listing_id': listing_id,
            'listing_title': listing.get('title', 'نامشخص'),
            'reporter_id': update.effective_user.id,
            'reporter_name': update.effective_user.full_name,
            'reason': reason,
            'reported_at': datetime.utcnow(),
            'status': 'pending'
        }
        
        success = await self.db.add_report(report_data)
        
        if success:
            await query.edit_message_text(
                "✅ گزارش شما با موفقیت ثبت شد و توسط مدیران بررسی خواهد شد."
            )
        else:
            await query.edit_message_text(
                "❌ متأسفانه مشکلی در ثبت گزارش پیش آمد. لطفاً دوباره تلاش کنید."
            )
        
        return ConversationHandler.END

    def get_handler(self):
        """Return the ConversationHandler for reports."""
        return ConversationHandler(
            entry_points=[
                CallbackQueryHandler(
                    self.start_report,
                    pattern=r'^report_\d+'
                )
            ],
            states={
                REPORT_REASON: [
                    CallbackQueryHandler(
                        self.handle_report_reason,
                        pattern=r'^(reason_|cancel_report)'
                    )
                ]
            },
            fallbacks=[
                CallbackQueryHandler(
                    lambda u, c: ConversationHandler.END,
                    pattern=r'^cancel_'
                )
            ]
        )
