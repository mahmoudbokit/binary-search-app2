from app.database import RedisDatabase
import random
from typing import Dict, List, Optional
from datetime import datetime, date
import time

class BinarySearchService:
    def __init__(self, db: RedisDatabase):
        self.db = db
        self.array_size = 100
        self.min_value = 1
        self.max_value = 1000
        self.seed = 42
        self.stats_key = "search_stats"
        
        # In-memory statistics (in production, store in Redis)
        self._search_stats = {
            "total_searches": 0,
            "successful_searches": 0,
            "failed_searches": 0,
            "search_times": [],
            "value_counts": {},
            "daily_counts": {}
        }

    async def initialize_array(self):
        """Initialize or load array from Redis"""
        array = await self.db.load_array()
        
        if not array:
            array = self._generate_array()
            await self.db.save_array(array)
            await self.db.save_array_metadata({
                "size": len(array),
                "min_value": self.min_value,
                "max_value": self.max_value,
                "seed": self.seed,
                "generated_at": datetime.now().isoformat(),
                "source": "generated"
            })
            print(f"Generated new array of size {len(array)}")
        else:
            print(f"Loaded array from Redis of size {len(array)}")
        
        return array

    def _generate_array(self, size: int = None, min_val: int = None, 
                       max_val: int = None, seed: int = None) -> List[int]:
        """Generate sorted random array"""
        size = size or self.array_size
        min_val = min_val or self.min_value
        max_val = max_val or self.max_value
        seed = seed or self.seed
        
        if min_val >= max_val:
            raise ValueError("min_value must be less than max_value")
        
        random.seed(seed)
        array = [random.randint(min_val, max_val) for _ in range(size)]
        return sorted(array)

    def _binary_search(self, arr: List[int], target: int) -> int:
        """Binary search implementation"""
        left, right = 0, len(arr) - 1
        
        while left <= right:
            mid = (left + right) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1

    async def search(self, value: int) -> Dict:
        """Search for value in array"""
        array = await self.get_array()
        
        if value < array[0] or value > array[-1]:
            # Early exit if value is outside array bounds
            return {
                "found": False,
                "index": -1,
                "value": value,
                "array_size": len(array),
                "array_min": array[0],
                "array_max": array[-1]
            }
        
        index = self._binary_search(array, value)
        
        return {
            "found": index != -1,
            "index": index,
            "value": value,
            "array_size": len(array),
            "array_min": array[0],
            "array_max": array[-1]
        }

    async def get_array(self) -> List[int]:
        """Get current array"""
        array = await self.db.load_array()
        if not array:
            array = await self.initialize_array()
        return array

    async def get_array_source(self) -> str:
        """Get array source information"""
        metadata = await self.db.load_array_metadata()
        return metadata.get("source", "unknown") if metadata else "generated"

    async def reset_array(self, size: int = None, min_value: int = None,
                         max_value: int = None, seed: int = None):
        """Reset array with new parameters"""
        if size:
            self.array_size = size
        if min_value:
            self.min_value = min_value
        if max_value:
            self.max_value = max_value
        if seed:
            self.seed = seed
        
        array = self._generate_array(size, min_value, max_value, seed)
        await self.db.save_array(array)
        await self.db.save_array_metadata({
            "size": len(array),
            "min_value": min_value or self.min_value,
            "max_value": max_value or self.max_value,
            "seed": seed or self.seed,
            "generated_at": datetime.now().isoformat(),
            "source": "regenerated"
        })

    def track_search(self, value: int, found: bool, search_time: float):
        """Track search statistics"""
        today = date.today().isoformat()
        
        # Update in-memory stats
        self._search_stats["total_searches"] += 1
        if found:
            self._search_stats["successful_searches"] += 1
        else:
            self._search_stats["failed_searches"] += 1
        
        self._search_stats["search_times"].append(search_time)
        
        # Track value frequency
        self._search_stats["value_counts"][value] = \
            self._search_stats["value_counts"].get(value, 0) + 1
        
        # Track daily counts
        self._search_stats["daily_counts"][today] = \
            self._search_stats["daily_counts"].get(today, 0) + 1
        
        # Keep only last 1000 search times for average calculation
        if len(self._search_stats["search_times"]) > 1000:
            self._search_stats["search_times"].pop(0)

    def get_statistics(self) -> Dict:
        """Get search statistics"""
        stats = self._search_stats.copy()
        
        # Calculate averages
        if stats["search_times"]:
            stats["average_search_time_ms"] = sum(stats["search_times"]) / len(stats["search_times"])
        else:
            stats["average_search_time_ms"] = 0
        
        # Find most searched value
        if stats["value_counts"]:
            stats["most_searched_value"] = max(
                stats["value_counts"].items(), 
                key=lambda x: x[1]
            )[0]
        else:
            stats["most_searched_value"] = None
        
        # Get today's count
        today = date.today().isoformat()
        stats["searches_today"] = stats["daily_counts"].get(today, 0)
        
        return stats