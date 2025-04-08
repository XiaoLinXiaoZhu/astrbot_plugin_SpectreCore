from typing import Dict, List, Optional, Tuple
import json
import os
import aiofiles
import asyncio
import time
import traceback
from astrbot.api.all import logger

from .message_formatter import MessageFormatter

class MessageProcessor:
    """
    消息处理器：负责处理和保存QQ群消息
    
    主要功能:
    1. 读取现有消息历史
    2. 格式化和存储新消息
    3. 去重和控制历史记录大小
    4. 持久化存储消息到文件
    """
    
    @classmethod
    async def save_messages(cls, group_id: int, messages: List[Dict], base_path: str, 
                           client = None, max_history: int = 100) -> bool:
        """
        保存消息到本地并控制历史记录数量
        
        Args:
            group_id: 群ID
            messages: 新消息列表
            base_path: 消息存储基础路径
            client: 消息客户端
            max_history: 最大历史消息数量
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建消息存储文件路径
            file_path = os.path.join(base_path, f"{group_id}.json")
            
            # 步骤1: 读取现有消息历史
            existing_messages = await cls._read_existing_messages(file_path)
            
            # 步骤2: 处理和添加新消息
            existing_messages = await cls._process_and_add_new_messages(
                existing_messages, messages, group_id, client
            )
            
            # 步骤3: 控制历史记录数量
            if len(existing_messages) > max_history:
                logger.debug(f"消息数量超过上限({max_history})，截取最新的{max_history}条")
                existing_messages = existing_messages[-max_history:]
                
            # 步骤4: 保存到文件
            return await cls._save_messages_to_file(file_path, group_id, existing_messages)
                
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"保存消息时出错: {str(e)}\n{error_details}")
            return False
    
    @classmethod
    async def _read_existing_messages(cls, file_path: str) -> List[Dict]:
        """
        读取现有消息历史
        
        Args:
            file_path: 消息文件路径
            
        Returns:
            List[Dict]: 现有消息列表
        """
        existing_messages = []
        
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    if content.strip():  # 确保文件不为空
                        data = json.loads(content)
                        if 'messages' in data:
                            existing_messages = data['messages']
                            logger.debug(f"从文件读取了 {len(existing_messages)} 条现有消息")
            except json.JSONDecodeError:
                logger.error(f"JSON解析错误，文件可能损坏: {file_path}")
                # 备份损坏的文件
                backup_path = f"{file_path}.backup.{int(time.time())}"
                try:
                    os.rename(file_path, backup_path)
                    logger.info(f"已将损坏的文件备份为: {backup_path}")
                except Exception as be:
                    logger.error(f"备份损坏文件失败: {str(be)}")
            except Exception as e:
                logger.error(f"读取消息文件时出错: {str(e)}")
        
        return existing_messages
    
    @classmethod
    async def _process_and_add_new_messages(cls, existing_messages: List[Dict], 
                                         new_messages: List[Dict], group_id: int,
                                         client) -> List[Dict]:
        """
        处理并添加新消息到现有消息列表
        
        Args:
            existing_messages: 现有消息列表
            new_messages: 新消息列表
            group_id: 群ID
            client: 消息客户端
            
        Returns:
            List[Dict]: 更新后的消息列表
        """
        # 获取现有消息ID集合，用于快速查找
        existing_message_ids = {
            msg.get('message_id') for msg in existing_messages 
            if msg.get('message_id') is not None
        }
        
        # 处理新消息
        for message in new_messages:
            try:
                # 格式化消息
                processed_message = await MessageFormatter.process_group_message(
                    message, new_messages, client, group_id
                )
                
                if processed_message:
                    message_id = processed_message.get('message_id')
                    
                    # 检查是否为重复消息
                    if message_id is not None and message_id in existing_message_ids:
                        logger.debug(f"消息已存在(ID:{message_id})，跳过")
                        continue
                    
                    # 添加新消息并更新ID集合
                    existing_messages.append(processed_message)
                    if message_id is not None:
                        existing_message_ids.add(message_id)
                    
                    # 记录日志
                    content_preview = processed_message.get('content', '')[:20]
                    logger.debug(f"添加新消息(ID:{message_id}): {content_preview}...")
            
            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}", exc_info=True)
        
        return existing_messages
    
    @classmethod
    async def _save_messages_to_file(cls, file_path: str, group_id: int, 
                                   messages: List[Dict]) -> bool:
        """
        保存消息到文件
        
        Args:
            file_path: 文件路径
            group_id: 群ID
            messages: 消息列表
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建保存数据
            data = {
                'group_id': group_id,
                'messages': messages
            }
            
            # 写入文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2))
            
            logger.debug(f"成功保存群 {group_id} 的消息，总共 {len(messages)} 条")
            return True
        
        except Exception as e:
            logger.error(f"写入文件时出错: {str(e)}", exc_info=True)
            return False
