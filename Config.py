import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'divarkhaf')

# Redis Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Collection Names
COLLECTIONS = {
    'users': 'users',
    'listings': 'listings',
    'reports': 'reports',
    'views': 'views',
    'interactions': 'interactions',
    'bookmarks': 'bookmarks',
    'saved_searches': 'saved_searches'
}

# Categories
CATEGORIES = {
    '🏠 املاک': 'real_estate',
    '📱 دیجیتال': 'digital',
    '👕 لباس': 'clothing',
    '🚗 وسایل نقلیه': 'vehicles',
    '🏠 لوازم خانگی': 'home_appliances',
    '💼 خدمات': 'services',
    '💼 استخدام و کاریابی': 'jobs',
    '🎮 سرگرمی و فراغت': 'entertainment',
    '👶 کودک و نوزاد': 'baby',
    '🐱 حیوانات': 'pets'
}

# Image Settings
MAX_IMAGES_PER_LISTING = 10
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png']

# Listing Settings
LISTING_EXPIRY_DAYS = 30
MAX_LISTINGS_PER_USER = 10
MIN_TITLE_LENGTH = 10
MAX_TITLE_LENGTH = 100
MIN_DESCRIPTION_LENGTH = 30
MAX_DESCRIPTION_LENGTH = 1000
