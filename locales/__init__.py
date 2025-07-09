from .fa import FA_MESSAGES

MESSAGES = {
    'fa': FA_MESSAGES
}

def get_message(lang: str, key: str, **kwargs) -> str:
    """Get localized message."""
    messages = MESSAGES.get(lang, MESSAGES['fa'])
    message = messages.get(key, MESSAGES['fa'].get(key, ''))
    return message.format(**kwargs) if kwargs else message
