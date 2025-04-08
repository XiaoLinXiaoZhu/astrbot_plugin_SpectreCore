from typing import Dict, List
import asyncio
import json
from astrbot.api.all import logger

class SegmentProcessor:
    """处理消息段"""
    
    @classmethod
    async def process_message_segment(cls, segment: Dict, messages: List[Dict] = None, client = None, group_id: int = None) -> str:
        """处理单个消息段"""
        from .text_processor import TextProcessor
        from .image_processor import ImageProcessor
        from .reply_processor import ReplyProcessor
        from .forward_processor import ForwardProcessor
        from .at_processor import AtProcessor
        
        seg_type = segment['type']
        
        # 分派不同类型的消息处理
        if seg_type == 'rps':
            return TextProcessor.process_rps_data(segment['data']['result'])
            
        elif seg_type == 'dice':
            return TextProcessor.process_dice_data(segment['data']['result'])
            
        elif seg_type == 'forward':
            content = await ForwardProcessor.process_forward_message(segment['data'])
            if content:
                return await ForwardProcessor.format_forward_message(segment['data'])
            return "[空的合并转发消息]"
            
        elif seg_type == 'json':
            return await cls._process_json_segment(segment)
            
        elif seg_type == 'reply':
            return await ReplyProcessor.process_reply_segment(segment, messages, client, group_id)
            
        elif seg_type == 'at':
            return await AtProcessor.process_at_segment(segment, messages, client, group_id)
            
        elif seg_type == 'text':
            return TextProcessor.process_text(segment['data'])
            
        elif seg_type == 'image':
            return ImageProcessor.format_image_text(segment['data'])
            
        elif seg_type == 'face':
            return TextProcessor.process_face(segment['data'])
            
        return f"[未知类型消息:{seg_type}]"
        
    @classmethod
    async def _process_json_segment(cls, segment: Dict) -> str:
        """处理JSON类型的消息段，包括伪合并转发消息"""
        from .forward_processor import ForwardProcessor
        
        try:
            json_data = json.loads(segment['data']['data'])
            
            # 处理伪合并转发消息
            if json_data.get('app') == 'com.tencent.multimsg':
                logger.debug("处理伪合并转发消息")
                return await cls._process_pseudo_forward(json_data)
                
            # 处理其他类型的JSON消息
            return f"[json消息: {json_data.get('desc', '未知内容')}]"
            
        except Exception as e:
            logger.error(f"处理JSON段落时出错: {str(e)}", exc_info=True)
            return "[处理失败的JSON消息]"
            
    @classmethod
    async def _process_pseudo_forward(cls, json_data: Dict) -> str:
        """处理伪合并转发消息"""
        from .forward_processor import ForwardProcessor
        
        # 构建伪合并转发消息数据
        pseudo_forward_data = {'content': []}
        
        # 提取消息内容
        news_items = json_data.get('meta', {}).get('detail', {}).get('news', [])
        for item in news_items:
            if 'text' in item:
                pseudo_message = {
                    'time': 0,  # 无法获取确切时间，使用默认值
                    'sender': {'nickname': '未知', 'user_id': '0'},  # 默认发送者
                    'message': [{'type': 'text', 'data': {'text': item['text']}}]
                }
                pseudo_forward_data['content'].append(pseudo_message)
        
        # 使用转发处理器处理
        content = await ForwardProcessor.process_forward_message(pseudo_forward_data)
        
        # 格式化展示
        formatted_msgs = []
        for msg in content.get('forward_messages', []):
            sender = msg.get('sender', '')
            msg_content = msg.get('content', '')
            formatted_msgs.append(f"{sender}: {msg_content}")
            
        if formatted_msgs:
            return "[伪合并转发消息]\n" + '\n'.join(formatted_msgs)
        return "[空的伪合并转发消息]" 