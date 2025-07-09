import re
from typing import Optional
from datetime import datetime
from PIL import Image
import io

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    phone_pattern = re.compile(r'^(\+98|0)?9\d{9}$')
    return bool(phone_pattern.match(phone))

def format_price(price: int) -> str:
    """Format price with proper separators."""
    if price == 0:
        return "توافقی"
    return f"{price:,} تومان"

def format_datetime(dt: datetime) -> str:
    """Format datetime to Persian style string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

async def process_image(image_data: bytes, max_size: tuple = (800, 800)) -> Optional[bytes]:
    """Process and optimize image."""
    try:
        # Open image
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if needed
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize if larger than max_size
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)
        
        # Save optimized image
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def validate_listing_data(data: dict) -> tuple[bool, str]:
    """Validate listing data."""
    if len(data.get('title', '')) < 10:
        return False, "عنوان آگهی باید حداقل ۱۰ کاراکتر باشد."
    
    if len(data.get('description', '')) < 30:
        return False, "توضیحات آگهی باید حداقل ۳۰ کاراکتر باشد."
    
    if not validate_phone_number(data.get('contact', '')):
        return False, "شماره تماس نامعتبر است."
    
    if data.get('price', -1) < 0:
        return False, "قیمت نامعتبر است."
    
    return True, ""

def create_keyboard_markup(buttons: list, row_width: int = 2) -> list:
    """Create keyboard markup with specified row width."""
    keyboard = []
    row = []
    for button in buttons:
        row.append(button)
        if len(row) == row_width:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return keyboard
