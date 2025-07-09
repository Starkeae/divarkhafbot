from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from config import CATEGORIES, MAX_IMAGES_PER_LISTING
from datetime import datetime

# States
(CATEGORY, TITLE, DESCRIPTION, PRICE, CONTACT, 
 LOCATION, PHOTO, CONFIRM) = range(8)

class ListingHandler:
    def __init__(self, db, analytics):
        self.db = db
        self.analytics = analytics

    def create_categories_keyboard(self):
        """Create keyboard with all categories."""
        keyboard = []
        row = []
        for category in CATEGORIES.keys():
            row.append(category)
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append(["🔙 بازگشت به منوی اصلی"])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def start_listing_creation(self, update: Update, context):
        """Start the listing creation process."""
        # Initialize listing data in context
        context.user_data['listing'] = {}
        
        await update.message.reply_text(
            "📝 ثبت آگهی جدید\n\n"
            "لطفاً دسته‌بندی آگهی خود را انتخاب کنید:",
            reply_markup=self.create_categories_keyboard()
        )
        return CATEGORY

    async def handle_category(self, update: Update, context):
        """Handle category selection."""
        category = update.message.text
        
        if category == "🔙 بازگشت به منوی اصلی":
            await update.message.reply_text("عملیات لغو شد.")
            return ConversationHandler.END
            
        if category not in CATEGORIES:
            await update.message.reply_text(
                "❌ لطفاً یک دسته‌بندی معتبر انتخاب کنید."
            )
            return CATEGORY
            
        context.user_data['listing']['category'] = CATEGORIES[category]
        
        await update.message.reply_text(
            "عنوان آگهی خود را وارد کنید:\n"
            "(حداقل ۱۰ و حداکثر ۱۰۰ کاراکتر)"
        )
        return TITLE

    async def handle_title(self, update: Update, context):
        """Handle listing title."""
        title = update.message.text
        
        if len(title) < 10 or len(title) > 100:
            await update.message.reply_text(
                "❌ عنوان باید بین ۱۰ تا ۱۰۰ کاراکتر باشد.\n"
                "لطفاً دوباره وارد کنید:"
            )
            return TITLE
            
        context.user_data['listing']['title'] = title
        
        await update.message.reply_text(
            "توضیحات آگهی را وارد کنید:\n"
            "(حداقل ۳۰ و حداکثر ۱۰۰۰ کاراکتر)"
        )
        return DESCRIPTION

    async def handle_description(self, update: Update, context):
        """Handle listing description."""
        description = update.message.text
        
        if len(description) < 30 or len(description) > 1000:
            await update.message.reply_text(
                "❌ توضیحات باید بین ۳۰ تا ۱۰۰۰ کاراکتر باشد.\n"
                "لطفاً دوباره وارد کنید:"
            )
            return DESCRIPTION
            
        context.user_data['listing']['description'] = description
        
        await update.message.reply_text(
            "قیمت را وارد کنید:\n"
            "برای توافقی بودن عدد 0 را وارد کنید"
        )
        return PRICE

    async def handle_price(self, update: Update, context):
        """Handle listing price."""
        try:
            price = int(update.message.text)
            if price < 0:
                raise ValueError
                
            context.user_data['listing']['price'] = price
            
            await update.message.reply_text(
                "شماره تماس خود را وارد کنید:\n"
                "(می‌توانید از دکمه شماره تماس استفاده کنید)"
            )
            return CONTACT
            
        except ValueError:
            await update.message.reply_text(
                "❌ لطفاً یک عدد معتبر وارد کنید:"
            )
            return PRICE

    async def handle_contact(self, update: Update, context):
        """Handle contact information."""
        contact = update.message.text
        
        # Basic phone number validation
        if not contact.isdigit() or len(contact) < 10:
            await update.message.reply_text(
                "❌ لطفاً یک شماره تماس معتبر وارد کنید:"
            )
            return CONTACT
            
        context.user_data['listing']['contact'] = contact
        
        await update.message.reply_text(
            "موقعیت مکانی را وارد کنید:\n"
            "مثال: خواف - خیابان امام رضا"
        )
        return LOCATION

    async def handle_location(self, update: Update, context):
        """Handle location information."""
        location = update.message.text
        context.user_data['listing']['location'] = location
        
        # Initialize photos list
        context.user_data['listing']['photos'] = []
        
        await update.message.reply_text(
            "عکس آگهی را ارسال کنید:\n"
            "(حداکثر ۱۰ عکس، برای رد کردن /skip را بزنید)"
        )
        return PHOTO

    async def handle_photo(self, update: Update, context):
        """Handle photo uploads."""
        if update.message.text == "/skip":
            return await self.show_confirmation(update, context)
            
        if not update.message.photo:
            await update.message.reply_text(
                "❌ لطفاً یک عکس ارسال کنید یا /skip را بزنید."
            )
            return PHOTO
            
        photos = context.user_data['listing'].get('photos', [])
        if len(photos) >= MAX_IMAGES_PER_LISTING:
            await update.message.reply_text(
                "❌ حداکثر تعداد عکس‌های مجاز ارسال شده است."
            )
            return await self.show_confirmation(update, context)
            
        # Get the largest photo
        photo = update.message.photo[-1]
        photos.append(photo.file_id)
        context.user_data['listing']['photos'] = photos
        
        keyboard = [["✅ پایان", "📸 عکس بیشتر"]]
        await update.message.reply_text(
            f"عکس {len(photos)} از {MAX_IMAGES_PER_LISTING} ذخیره شد.\n"
            "می‌خواهید عکس دیگری اضافه کنید؟",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return PHOTO

    async def show_confirmation(self, update: Update, context):
        """Show listing confirmation."""
        listing = context.user_data['listing']
        
        message = (
            "📝 پیش‌نمایش آگهی:\n\n"
            f"🏷 عنوان: {listing['title']}\n"
            f"📝 توضیحات: {listing['description']}\n"
            f"💰 قیمت: {listing['price']:,} تومان\n"
            f"📞 تماس: {listing['contact']}\n"
            f"📍 موقعیت: {listing['location']}\n"
            f"🖼 تعداد عکس: {len(listing.get('photos', []))}\n\n"
            "آیا از ثبت آگهی مطمئن هستید؟"
        )
        
        keyboard = [["✅ ثبت آگهی", "❌ انصراف"]]
        await update.message.reply_text(
            message,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CONFIRM

    async def handle_confirmation(self, update: Update, context):
        """Handle listing confirmation."""
        response = update.message.text
        
        if response == "❌ انصراف":
            await update.message.reply_text("عملیات لغو شد.")
            return ConversationHandler.END
            
        listing = context.user_data['listing']
        listing['user_id'] = update.effective_user.id
        listing['status'] = 'active'
        listing['created_at'] = datetime.utcnow()
        
        # Save listing to database
        listing_id = await self.db.create_listing(listing)
        
        if listing_id:
            # Track the new listing creation
            await self.analytics.track_interaction(
                update.effective_user.id,
                'create_listing',
                {'listing_id': listing_id}
            )
            
            await update.message.reply_text(
                "✅ آگهی شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد."
            )
        else:
            await update.message.reply_text(
                "❌ متأسفانه مشکلی در ثبت آگهی پیش آمد. لطفاً دوباره تلاش کنید."
            )
            
        return ConversationHandler.END

    async def show_categories(self, update: Update, context):
        """Show categories for browsing."""
        await update.message.reply_text(
            "لطفاً دسته‌بندی مورد نظر را انتخاب کنید:",
            reply_markup=self.create_categories_keyboard()
        )

    async def show_category_listings(self, update: Update, context):
        """Show listings in a category."""
        category = update.message.text
        if category not in CATEGORIES:
            return
            
        listings = await self.db.get_category_listings(CATEGORIES[category])
        if not listings:
            await update.message.reply_text(
                "📭 هیچ آگهی در این دسته‌بندی وجود ندارد."
            )
            return
            
        for listing in listings:
            await self.send_listing(update, context, listing)

    async def send_listing(self, update: Update, context, listing: dict):
        """Send a listing message."""
        message = (
            f"📌 {listing['title']}\n\n"
            f"📝 {listing['description']}\n\n"
            f"💰 قیمت: {listing['price']:,} تومان\n"
            f"📍 موقعیت: {listing['location']}\n"
            f"⏰ ثبت شده در: {listing['created_at'].strftime('%Y-%m-%d %H:%M')}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📞 تماس", callback_data=f"contact_{listing['_id']}"),
                InlineKeyboardButton("⭐️ نشان کردن", callback_data=f"bookmark_{listing['_id']}")
            ],
            [
                InlineKeyboardButton("🚫 گزارش", callback_data=f"report_{listing['_id']}")
            ]
        ]
        
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

    def get_handler(self):
        """Return the ConversationHandler for listings."""
        return ConversationHandler(
            entry_points=[
                MessageHandler(
                    filters.Regex("^➕ افزودن آگهی$"),
                    self.start_listing_creation
                )
            ],
            states={
                CATEGORY: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_category
                    )
                ],
                TITLE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_title
                    )
                ],
                DESCRIPTION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_description
                    )
                ],
                PRICE: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_price
                    )
                ],
                CONTACT: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_contact
                    )
                ],
                LOCATION: [
                    MessageHandler(
                        filters.TEXT & ~filters.COMMAND,
                        self.handle_location
                    )
                ],
                PHOTO: [
                    MessageHandler(
                        filters.PHOTO | filters.Regex("^✅ پایان$") | 
                        filters.Regex("^📸 عکس بیشتر$") | filters.Command("skip"),
                        self.handle_photo
                    )
                ],
                CONFIRM: [
                    MessageHandler(
                        filters.Regex("^(✅ ثبت آگهی|❌ انصراف)$"),
                        self.handle_confirmation
                    )
                ]
            },
            fallbacks=[
                CommandHandler('cancel', lambda u, c: ConversationHandler.END)
            ]
        )
