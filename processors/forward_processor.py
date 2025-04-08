from typing import Dict, List
import time as time_module
from astrbot.api.all import logger

class ForwardProcessor:
    """处理合并转发类消息"""
    
    @classmethod
    async def process_forward_message(cls, forward_data: Dict, sender_info: Dict = None, msg_time: int = None) -> Dict:
        """处理合并转发消息,保持嵌套结构
        
        Args:
            forward_data: 合并转发消息数据
            sender_info: 发送者信息，如果为None则尝试从forward_data中获取
            msg_time: 消息时间戳，如果为None则使用当前时间
        """
        # 设置默认的发送者和时间
        sender_info = cls._get_sender_info(forward_data, sender_info)
        msg_time = msg_time or int(time_module.time())
        
        # 格式化发送者和时间信息
        sender_text = f"{sender_info.get('nickname', '未知用户')}(id:{sender_info.get('user_id', '未知')})"
        time_text = time_module.strftime('%Y-%m-%d %H:%M:%S', time_module.localtime(msg_time))
        
        # 处理合并转发中的子消息
        forward_messages = []
        if 'content' in forward_data:
            for msg in forward_data['content']:
                processed_msg = await cls._process_sub_message(msg)
                forward_messages.append(processed_msg)

        logger.debug(f"处理合并转发消息，发送者: {sender_text}, 包含 {len(forward_messages)} 条子消息")
        
        return {
            'time': time_text,
            'sender': sender_text,
            'content': '[合并转发消息]',
            'resources': [],
            'forward_messages': forward_messages
        }
    
    @classmethod
    def _get_sender_info(cls, forward_data: Dict, sender_info: Dict = None) -> Dict:
        """获取发送者信息"""
        if sender_info is not None:
            return sender_info
            
        if 'sender' in forward_data:
            return forward_data.get('sender', {})
            
        return {'nickname': '未知用户', 'user_id': '未知'}
    
    @classmethod
    async def _process_sub_message(cls, msg: Dict) -> Dict:
        """处理合并转发消息中的子消息"""
        sender = msg.get('sender', {})
        processed_msg = {
            'time': time_module.strftime('%Y-%m-%d %H:%M:%S', 
                              time_module.localtime(msg.get('time', 0))),
            'sender': f"{sender.get('nickname', '未知用户')}(id:{sender.get('user_id', '未知')})",
            'content': '',
            'resources': []
        }

        # 处理消息内容
        content_segments = []
        for seg in msg.get('message', []):
            segment_text = await cls._process_message_segment(seg, sender, msg.get('time', 0), processed_msg)
            content_segments.append(segment_text)

        processed_msg['content'] = ''.join(content_segments)
        return processed_msg
    
    @classmethod
    async def _process_message_segment(cls, seg: Dict, sender: Dict, msg_time: int, processed_msg: Dict) -> str:
        """处理消息段"""
        if seg['type'] == 'forward':
            # 递归处理嵌套的合并转发
            nested_forward = await cls.process_forward_message(
                seg['data'],
                sender,
                msg_time
            )
            processed_msg['forward_messages'] = nested_forward['forward_messages']
            return '[合并转发消息]'
            
        elif seg['type'] == 'text':
            return seg['data']['text']
            
        elif seg['type'] == 'image':
            return '[图片]'
            
        elif seg['type'] == 'face':
            face_text = seg['data'].get('raw', {}).get('faceText', '表情')
            return f"[QQ表情:{face_text}]"
            
        elif seg['type'] == 'at':
            qq = seg['data']['qq']
            return "[@全体成员]" if qq == 'all' else f"[@{qq}]"
        
        # 默认未知类型
        return f"[未知类型:{seg['type']}]"
    
    @classmethod
    async def format_forward_message(cls, forward_data: Dict) -> str:
        """将合并转发消息格式化为文本展示"""
        content = await cls.process_forward_message(forward_data)
        if not content or 'forward_messages' not in content:
            return "[空的合并转发消息]"
            
        # 格式化展示合并转发消息
        formatted_msgs = []
        for msg in content.get('forward_messages', []):
            sender = msg.get('sender', '')
            msg_content = msg.get('content', '')
            formatted_msgs.append(f"{sender}: {msg_content}")
                
        if formatted_msgs:
            return "[合并转发消息]\n" + '\n'.join(formatted_msgs)
        return "[空的合并转发消息]" 