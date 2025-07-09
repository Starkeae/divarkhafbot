import motor.motor_asyncio
from datetime import datetime, timedelta
from config import (
    DATABASE_URL,
    DATABASE_NAME,
    COLLECTIONS,
    LISTING_EXPIRY_DAYS
)
from typing import Optional, List, Dict

class Database:
    def __init__(self, cache=None):
        # Initialize MongoDB connection
        self.client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
        self.db = self.client[DATABASE_NAME]
        
        # Initialize collections
        self.users = self.db[COLLECTIONS['users']]
        self.listings = self.db[COLLECTIONS['listings']]
        self.reports = self.db[COLLECTIONS['reports']]
        self.views = self.db[COLLECTIONS['views']]
        self.interactions = self.db[COLLECTIONS['interactions']]
        self.bookmarks = self.db[COLLECTIONS['bookmarks']]
        self.saved_searches = self.db[COLLECTIONS['saved_searches']]
        
        # Store cache instance
        self.cache = cache
        
        # Create indexes
        self._create_indexes()

    async def _create_indexes(self):
        """Create necessary database indexes."""
        # Users indexes
        await self.users.create_index("user_id", unique=True)
        await self.users.create_index("username")
        await self.users.create_index("last_active")

        # Listings indexes
        await self.listings.create_index("user_id")
        await self.listings.create_index("category")
        await self.listings.create_index("created_at")
        await self.listings.create_index("is_urgent")
        await self.listings.create_index("status")
        await self.listings.create_index([("title", "text"), ("description", "text")])

        # Reports indexes
        await self.reports.create_index("listing_id")
        await self.reports.create_index("reporter_id")
        await self.reports.create_index("status")

        # Views indexes
        await self.views.create_index([("listing_id", 1), ("user_id", 1)])
        await self.views.create_index("timestamp")

        # Bookmarks indexes
        await self.bookmarks.create_index([("user_id", 1), ("listing_id", 1)], unique=True)

    async def update_user(self, user_data: dict) -> bool:
        """Update or create user document."""
        try:
            await self.users.update_one(
                {"user_id": user_data["user_id"]},
                {
                    "$set": user_data,
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    async def create_listing(self, listing_data: dict) -> Optional[str]:
        """Create a new listing."""
        try:
            listing_data["created_at"] = datetime.utcnow()
            listing_data["status"] = "active"
            listing_data["expires_at"] = datetime.utcnow() + timedelta(days=LISTING_EXPIRY_DAYS)
            
            result = await self.listings.insert_one(listing_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating listing: {e}")
            return None

    async def get_listing(self, listing_id: str) -> Optional[dict]:
        """Get listing by ID with cache."""
        if self.cache:
            # Try cache first
            cached_listing = await self.cache.get(f"listing:{listing_id}")
            if cached_listing:
                return cached_listing

        # Get from database
        listing = await self.listings.find_one({"_id": listing_id})
        
        if listing and self.cache:
            # Cache for future requests
            await self.cache.set(f"listing:{listing_id}", listing, 3600)
        
        return listing

    async def update_listing(self, listing_id: str, update_data: dict) -> bool:
        """Update a listing."""
        try:
            result = await self.listings.update_one(
                {"_id": listing_id},
                {"$set": update_data}
            )
            
            # Invalidate cache if exists
            if self.cache:
                await self.cache.delete(f"listing:{listing_id}")
            
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating listing: {e}")
            return False

    async def delete_listing(self, listing_id: str) -> bool:
        """Delete a listing and its associated data."""
        try:
            # Delete listing
            result = await self.listings.delete_one({"_id": listing_id})
            
            if result.deleted_count:
                # Clean up associated data
                await self.reports.delete_many({"listing_id": listing_id})
                await self.views.delete_many({"listing_id": listing_id})
                await self.bookmarks.delete_many({"listing_id": listing_id})
                
                # Invalidate cache if exists
                if self.cache:
                    await self.cache.delete(f"listing:{listing_id}")
                
                return True
            return False
        except Exception as e:
            print(f"Error deleting listing: {e}")
            return False

    async def get_user_listings(self, user_id: int) -> List[dict]:
        """Get all listings for a user."""
        try:
            cursor = self.listings.find({"user_id": user_id}).sort("created_at", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting user listings: {e}")
            return []

    async def add_report(self, report_data: dict) -> bool:
        """Add a new report."""
        try:
            report_data["created_at"] = datetime.utcnow()
            report_data["status"] = "pending"
            await self.reports.insert_one(report_data)
            return True
        except Exception as e:
            print(f"Error adding report: {e}")
            return False

    async def get_reports(self, status: str = None) -> List[dict]:
        """Get reports with optional status filter."""
        try:
            filter_dict = {}
            if status:
                filter_dict["status"] = status
            
            cursor = self.reports.find(filter_dict).sort("created_at", -1)
            return await cursor.to_list(length=None)
        except Exception as e:
            print(f"Error getting reports: {e}")
            return []

    async def track_view(self, listing_id: str, user_id: int) -> bool:
        """Track a listing view."""
        try:
            await self.views.insert_one({
                "listing_id": listing_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow()
            })
            return True
        except Exception as e:
            print(f"Error tracking view: {e}")
            return False

    async def toggle_bookmark(self, user_id: int, listing_id: str) -> bool:
        """Toggle bookmark status for a listing."""
        try:
            # Check if bookmark exists
            existing = await self.bookmarks.find_one({
                "user_id": user_id,
                "listing_id": listing_id
            })
            
            if existing:
                # Remove bookmark
                await self.bookmarks.delete_one({
                    "user_id": user_id,
                    "listing_id": listing_id
                })
            else:
                # Add bookmark
                await self.bookmarks.insert_one({
                    "user_id": user_id,
                    "listing_id": listing_id,
                    "created_at": datetime.utcnow()
                })
            return True
        except Exception as e:
            print(f"Error toggling bookmark: {e}")
            return False

    async def get_bookmarks(self, user_id: int) -> List[dict]:
        """Get user's bookmarked listings."""
        try:
            # Get bookmark records
            cursor = self.bookmarks.find({"user_id": user_id})
            bookmarks = await cursor.to_list(length=None)
            
            # Get actual listings
            listings = []
            for bookmark in bookmarks:
                listing = await self.get_listing(bookmark["listing_id"])
                if listing:
                    listings.append(listing)
            
            return listings
        except Exception as e:
            print(f"Error getting bookmarks: {e}")
            return []

    async def get_statistics(self) -> Dict:
        """Get bot usage statistics."""
        try:
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = {
                "total_users": await self.users.count_documents({}),
                "total_listings": await self.listings.count_documents({}),
                "active_listings": await self.listings.count_documents({"status": "active"}),
                "urgent_listings": await self.listings.count_documents({"is_urgent": True}),
                "today_views": await self.views.count_documents({"timestamp": {"$gte": today}}),
                "today_new_users": await self.users.count_documents({"created_at": {"$gte": today}}),
                "today_new_listings": await self.listings.count_documents({"created_at": {"$gte": today}}),
                "pending_reports": await self.reports.count_documents({"status": "pending"})
            }
            
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
