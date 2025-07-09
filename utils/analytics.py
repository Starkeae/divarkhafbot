from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class Analytics:
    def __init__(self, db):
        self.db = db

    async def track_interaction(
        self, 
        user_id: int, 
        action_type: str, 
        data: Dict[str, Any] = None
    ):
        """Track user interaction."""
        interaction = {
            'user_id': user_id,
            'action_type': action_type,
            'timestamp': datetime.utcnow(),
            'data': data or {}
        }
        await self.db.add_interaction(interaction)

    async def track_listing_view(self, listing_id: str, user_id: int):
        """Track listing view."""
        view_data = {
            'listing_id': listing_id,
            'user_id': user_id,
            'timestamp': datetime.utcnow()
        }
        await self.db.add_listing_view(view_data)

    async def get_user_stats(self, user_id: int) -> dict:
        """Get statistics for a specific user."""
        stats = await self.db.get_user_stats(user_id)
        return {
            'total_listings': stats.get('total_listings', 0),
            'active_listings': stats.get('active_listings', 0),
            'total_views': stats.get('total_views', 0),
            'interactions_today': await self.get_user_interactions_today(user_id)
        }

    async def get_user_interactions_today(self, user_id: int) -> int:
        """Get number of user interactions today."""
        today = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return await self.db.count_user_interactions(user_id, today)

    async def get_listing_stats(self, listing_id: str) -> dict:
        """Get statistics for a specific listing."""
        stats = await self.db.get_listing_stats(listing_id)
        return {
            'total_views': stats.get('total_views', 0),
            'unique_views': stats.get('unique_views', 0),
            'bookmarks': stats.get('bookmarks', 0),
            'reports': stats.get('reports', 0)
        }

    async def get_daily_stats(self) -> dict:
        """Get daily statistics."""
        today = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return {
            'new_users': await self.db.count_new_users(today),
            'new_listings': await self.db.count_new_listings(today),
            'total_views': await self.db.count_views(today),
            'total_interactions': await self.db.count_interactions(today)
  }
