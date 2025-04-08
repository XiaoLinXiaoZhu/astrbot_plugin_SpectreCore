from typing import Dict, List, Tuple
import asyncio
from astrbot.api.all import logger
from ..cache import name_cache, message_cache
from ..api_client import APIClient

class ReplyProcessor:
    """处理回复引用类消息"""
    
    @classmethod
    def format_quoted_message(cls, msg_data: Dict) -> Tuple[str, str]:
        """格式化引用消息,返回(发送者信息, 消息内容)"""
        from .segment_processor import SegmentProcessor  # 避免循环导入
        
        if not msg_data:
            return "未知用户", "未知消息"
            
        sender = msg_data.get('sender', {})
        sender_text = f"{sender.get('nickname', '未知用户')}(id:{sender.get('user_id', '未知')})"

        # 处理每个消息段
        message_segments = []
        for seg in msg_data.get('message', []):
            if seg['type'] == 'text':
                message_segments.append(seg['data']['text'])
            elif seg['type'] == 'image':
                data = seg['data']
                if 'summary' in data and data['summary']:
                    message_segments.append(f"[QQ表情:{data['summary']}]")
                else:
                    message_segments.append("[图片]")
            elif seg['type'] == 'face':
                face_data = seg['data'].get('raw', {})
                face_text = face_data.get('faceText', '表情')
                message_segments.append(f"[QQ表情:{face_text}]")
            elif seg['type'] == 'at':
                qq = seg['data']['qq']
                if qq == 'all':
                    message_segments.append("[@全体成员]")
                else:
                    name = name_cache.get(qq) or f"用户(id:{qq})"
                    message_segments.append(f"[@{name}]")
        
        return sender_text, ''.join(message_segments) or "非文本消息"

    @classmethod
    async def process_quoted_message(cls, msg_data: Dict, messages: List[Dict] = None, client = None, group_id: int = None) -> str:
        """递归处理引用消息"""
        if not msg_data:
            return "未知消息"

        # 直接处理当前消息的内容
        segments = []
        has_reply = False
        reply_content = None

        # 先处理引用部分
        for seg in msg_data.get('message', []):
            if seg['type'] == 'reply':
                has_reply = True
                reply_id = str(seg['data']['id'])
                quoted_msg = None
                logger.debug(f"递归处理引用消息, ID: {reply_id}")
                
                # 获取被引用的消息
                quoted_msg = message_cache.get(reply_id)
                
                if not quoted_msg and messages:
                    quoted_msg = cls.find_message_in_history(reply_id, messages)
                    if quoted_msg:
                        message_cache.put(reply_id, quoted_msg)
                
                if not quoted_msg and client:
                    quoted_msg = await APIClient.get_message_by_id(client, reply_id)
                    if quoted_msg:
                        message_cache.put(reply_id, quoted_msg)
                
                if quoted_msg:
                    reply_content = await cls.process_quoted_message(
                        quoted_msg, messages, client, group_id
                    )
            else:
                # 处理当前消息的其他部分
                if seg['type'] == 'text':
                    segments.append(seg['data']['text'])
                elif seg['type'] == 'image':
                    data = seg['data']
                    if 'summary' in data and data['summary']:
                        segments.append(f"[QQ表情:{data['summary']}]")
                    else:
                        segments.append("[图片]")
                elif seg['type'] == 'face':
                    face_data = seg['data'].get('raw', {})
                    face_text = face_data.get('faceText', '表情')
                    segments.append(f"[QQ表情:{face_text}]")

        # 组装消息内容
        current_content = ''.join(segments)
        sender = msg_data.get('sender', {})
        sender_text = f"{sender.get('nickname', '未知用户')}(id:{sender.get('user_id', '未知')})"
        
        # 如果有引用，拼接引用和当前消息
        if has_reply and reply_content:
            return f"{reply_content} -> {sender_text}的消息:{current_content}"
        else:
            # 如果是最底层消息，只返回当前内容
            return f"{sender_text}的消息:{current_content}"
    
    @classmethod
    def find_message_in_history(cls, message_id: str, messages: List[Dict]) -> Dict:
        """从历史消息中查找并格式化指定ID的消息"""
        message_id = str(message_id)  # 确保ID是字符串格式
        logger.debug(f"查找消息ID: {message_id}, 历史消息列表大小: {len(messages)}")
        
        for msg in messages:
            curr_id = str(msg.get('message_id', ''))
            if curr_id == message_id:
                logger.debug(f"在历史消息中找到匹配ID: {curr_id}")
                return {
                    'sender': msg.get('sender', {}),
                    'message': msg.get('message', []),
                    'raw_message': msg.get('raw_message', ''),
                    'message_id': curr_id,
                    'time': msg.get('time', 0)
                }
        logger.debug(f"未找到消息ID: {message_id}")
        return {}
    
    @classmethod
    async def process_reply_segment(cls, segment: Dict, messages: List[Dict], client, group_id: int) -> str:
        """处理回复类型消息段"""
        reply_id = str(segment['data']['id'])
        quoted_msg = None
        logger.debug(f"开始处理引用消息, ID: {reply_id}")
        
        # 多级查找消息
        # 1. 检查缓存
        quoted_msg = message_cache.get(reply_id)
        
        # 2. 检查历史消息
        if not quoted_msg and messages:
            quoted_msg = cls.find_message_in_history(reply_id, messages)
            if quoted_msg:
                message_cache.put(reply_id, quoted_msg)
            
        # 3. 尝试API获取
        if not quoted_msg and client:
            quoted_msg = await APIClient.get_message_by_id(client, reply_id)
            if quoted_msg:
                message_cache.put(reply_id, quoted_msg)

        if quoted_msg:
            return f"[引用{await cls.process_quoted_message(quoted_msg, messages, client, group_id)}]"
        
        logger.warning(f"所有方法都未能获取到消息ID:{reply_id}的内容")
        return f"[引用消息:未找到消息内容(id:{reply_id})]" 