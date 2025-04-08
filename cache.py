from collections import OrderedDict
from typing import Any

class LRUCache:
    """实现LRU缓存，防止内存无限增长"""
    def __init__(self, capacity: int = 500):
        self.cache: OrderedDict = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str) -> Any:
        """获取缓存项，如果存在则移到最近使用位置"""
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)  # 移动到最后（最近使用）
        return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """添加或更新缓存项"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        # 超出容量时移除最久未使用的项
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否在缓存中"""
        return key in self.cache
    
    def __len__(self) -> int:
        """返回缓存大小"""
        return len(self.cache)

# 全局缓存实例
name_cache = LRUCache(200)  # 用户名缓存
message_cache = LRUCache(100)  # 消息缓存 