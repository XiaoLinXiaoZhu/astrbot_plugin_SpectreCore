from typing import Dict, List, Optional
import time
import asyncio
import json
from astrbot.api.all import logger
from .processors.segment_processor import SegmentProcessor
from .processors.image_processor import ImageProcessor
from .cache import name_cache

class MessageFormatter:
    """
    消息格式化类：负责将原始消息处理成结构化数据
    
    主要功能:
    1. 处理普通文本消息
    2. 处理合并转发消息
    3. 处理伪合并转发消息(json格式)
    4. 处理图片等资源
    """
    
    @classmethod
    async def process_group_message(cls, message_data: Dict, messages: List[Dict] = None, 
                                   client = None, group_id: Optional[int] = None) -> Dict:
        """
        处理群消息，返回格式化后的消息字典
        
        Args:
            message_data: 原始消息数据
            messages: 消息列表上下文
            client: 消息客户端
            group_id: 群ID
            
        Returns:
            Dict: 格式化后的消息字典
        """
        # 提取基本信息
        message = message_data['message']
        sender = message_data['sender']
        message_time = message_data['time']
        message_id = message_data.get('message_id')
        
        # 缓存用户信息，方便后续使用
        name_cache.put(str(sender['user_id']), sender['nickname'])
        
        # 首先检查是否为特殊消息类型(如合并转发)
        special_message = await cls._check_special_message_types(message, sender, message_time, message_id)
        if special_message:
            return special_message

        # 处理普通消息
        return await cls._process_normal_message(message_data, messages, client, group_id)
        
    @classmethod
    async def _check_special_message_types(cls, message: List[Dict], sender: Dict, 
                                         message_time: int, message_id: Optional[int] = None) -> Optional[Dict]:
        """
        检查是否为特殊类型的消息，如合并转发消息
        
        Args:
            message: 消息内容
            sender: 发送者信息
            message_time: 消息时间戳
            message_id: 消息ID
            
        Returns:
            Optional[Dict]: 处理后的特殊消息，如果不是特殊消息则返回None
        """
        for seg in message:
            # 处理常规合并转发消息
            if seg['type'] == 'forward':
                from .processors.forward_processor import ForwardProcessor
                logger.debug(f"检测到合并转发消息，发送者：{sender['nickname']}，时间：{message_time}")
                
                processed_msg = await ForwardProcessor.process_forward_message(
                    seg['data'], 
                    sender_info=sender,
                    msg_time=message_time
                )
                
                # 确保添加消息ID以便去重
                if processed_msg and message_id is not None:
                    processed_msg['message_id'] = message_id
                return processed_msg
            
            # 处理伪合并转发消息(通过json传递的)
            if seg['type'] == 'json':
                processed_message = await cls._process_pseudo_forward(seg, sender, message_time, message_id)
                if processed_message:
                    return processed_message
                    
        return None
        
    @classmethod
    async def _process_pseudo_forward(cls, segment: Dict, sender: Dict, 
                                     message_time: int, message_id: Optional[int] = None) -> Optional[Dict]:
        """
        处理伪合并转发消息(腾讯多消息合并格式)
        
        Args:
            segment: json消息段
            sender: 发送者信息
            message_time: 消息时间戳
            message_id: 消息ID
            
        Returns:
            Optional[Dict]: 处理后的伪合并转发消息，处理失败则返回None
        """
        try:
            # 解析json数据
            json_data = json.loads(segment['data']['data'])
            
            # 检查是否为腾讯多消息类型
            if json_data.get('app') == 'com.tencent.multimsg':
                logger.debug(f"检测到伪合并转发消息，发送者：{sender['nickname']}，时间：{message_time}")
                from .processors.forward_processor import ForwardProcessor
                
                # 构建伪合并转发消息数据结构
                pseudo_forward_data = {'content': []}
                
                # 提取消息内容项
                news_items = json_data.get('meta', {}).get('detail', {}).get('news', [])
                for item in news_items:
                    if 'text' in item:
                        pseudo_forward_data['content'].append({
                            'time': message_time,
                            'sender': sender,
                            'message': [{'type': 'text', 'data': {'text': item['text']}}]
                        })
                
                # 使用转发处理器处理
                processed_msg = await ForwardProcessor.process_forward_message(
                    pseudo_forward_data,
                    sender_info=sender,
                    msg_time=message_time
                )
                
                # 确保添加消息ID以便去重
                if processed_msg and message_id is not None:
                    processed_msg['message_id'] = message_id
                return processed_msg
                
        except Exception as e:
            logger.error(f"处理伪合并转发消息时出错: {str(e)}", exc_info=True)
            
        return None
        
    @classmethod
    async def _process_normal_message(cls, message_data: Dict, messages: List[Dict] = None, 
                                     client = None, group_id: Optional[int] = None) -> Dict:
        """
        处理普通消息(非特殊类型)
        
        Args:
            message_data: 原始消息数据
            messages: 消息列表上下文
            client: 消息客户端
            group_id: 群ID
            
        Returns:
            Dict: 格式化后的普通消息
        """
        message = message_data['message']
        sender = message_data['sender']
        
        # 并发处理所有消息段落
        tasks = [SegmentProcessor.process_message_segment(seg, messages, client, group_id) for seg in message]
        processed_segments = await asyncio.gather(*tasks)
        
        # 构建结构化的消息结果
        result = {
            'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message_data['time'])),
            'sender': f"{sender['nickname']}(id:{sender['user_id']})",
            'content': ''.join(processed_segments),
            'resources': [],
            'message_id': message_data.get('message_id', None)
        }

        # 收集图片等资源信息
        for seg in message:
            if seg['type'] == 'image':
                image_info = ImageProcessor.process_image_data(seg['data'])
                result['resources'].append(image_info)

        return result 