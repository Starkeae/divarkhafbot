from telegram.error import TelegramError
import asyncio
from typing import Dict, List
from datetime import datetime

class Broadcaster:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    async def broadcast_message(
        self, 
        message: str, 
        user_filter: Dict = None,
        parse_mode: str = None
    ) -> Dict[str, int]:
        """Broadcast message to users."""
        results = {
            'success': 0,
            'failed': 0,
            'blocked': 0
        }

        users = await self.db.get_users(user_filter)
        
        for user in users:
            try:
                await self.bot.send_message(
                    chat_id=user['user_id'],
                    text=message,
                    parse_mode=parse_mode
                )
                results['success'] += 1
                await asyncio.sleep(0.05)  # Rate limiting
            except TelegramError as e:
                if 'bot was blocked' in str(e):
                    results['blocked'] += 1
                    await self.db.update_user_status(
                        user['user_id'],
                        {'blocked': True}
                    )
                else:
                    results['failed'] += 1

        return results

    async def broadcast_photo(
        self, 
        photo, 
        caption: str = None,
        user_filter: Dict = None
    ) -> Dict[str, int]:
        """Broadcast photo with optional caption to users."""
        results = {
            'success': 0,
            'failed': 0,
            'blocked': 0
        }

        users = await self.db.get_users(user_filter)
        
        for user in users:
            try:
                await self.bot.send_photo(
                    chat_id=user['user_id'],
                    photo=photo,
                    caption=caption
                )
                results['success'] += 1
                await asyncio.sleep(0.05)  # Rate limiting
            except TelegramError as e:
                if 'bot was blocked' in str(e):
                    results['blocked'] += 1
                    await self.db.update_user_status(
                        user['user_id'],
                        {'blocked': True}
                    )
                else:
                    results['failed'] += 1

        return results

    async def notify_admins(
        self, 
        message: str,
        parse_mode: str = None
    ):
        """Send notification to admin users."""
        admins = await self.db.get_admin_users()
        
        for admin in admins:
            try:
                await self.bot.send_message(
                    chat_id=admin['user_id'],
                    text=message,
                    parse_mode=parse_mode
                )
            except TelegramError as e:
                print(f"Error notifying admin {admin['user_id']}: {e}")
