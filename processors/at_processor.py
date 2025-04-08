from typing import Dict, List
from astrbot.api.all import logger
from ..cache import name_cache
from ..api_client import APIClient

class AtProcessor:
    """处理@类型消息"""
    
    @classmethod
    def find_username_in_messages(cls, user_id: str, messages: List[Dict]) -> str:
        """从历史消息中查找用户名"""
        for msg in messages:
            sender = msg.get('sender', {})
            if str(sender.get('user_id')) == user_id:
                return sender.get('nickname', '')
        return ''
    
    @classmethod
    async def process_at_segment(cls, segment: Dict, messages: List[Dict], client, group_id: int) -> str:
        """处理@类型消息段"""
        qq = segment['data']['qq']
        if qq == 'all':
            return "[@全体成员]"
        
        # 多级查找用户名
        # 1. 检查缓存
        username = name_cache.get(qq)
        if username:
            return f"[@{username}(id:{qq})]"
        
        # 2. 检查历史消息
        if messages:
            username = cls.find_username_in_messages(qq, messages)
            if username:
                name_cache.put(qq, username)
                return f"[@{username}(id:{qq})]"
        
        # 3. 尝试API获取
        if client and group_id:
            username = await APIClient.get_group_member_info(client, group_id, qq)
            if username:
                return f"[@{username}(id:{qq})]"
        
        # 都失败了才返回ID
        return f"[@未获取到用户名(id:{qq})]" 