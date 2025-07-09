from locales import get_message
from typing import Optional

class LanguageHandler:
    def __init__(self, default_lang: str = 'fa'):
        self.default_lang = default_lang

    def get_user_language(self, user_id: int) -> str:
        """Get user's preferred language."""
        # For now, always return Persian
        return 'fa'

    def get_message(
        self, 
        key: str, 
        user_id: Optional[int] = None, 
        **kwargs
    ) -> str:
        """Get localized message for user."""
        lang = self.get_user_language(user_id) if user_id else self.default_lang
        return get_message(lang, key, **kwargs)

    def get_category_name(
        self, 
        category_key: str, 
        user_id: Optional[int] = None
    ) -> str:
        """Get localized category name."""
        lang = self.get_user_language(user_id) if user_id else self.default_lang
        categories = get_message(lang, 'categories')
        return categories.get(category_key, category_key)
