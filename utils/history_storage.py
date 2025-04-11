import os
import pickle
from typing import List
from astrbot.api.all import *
import time

class HistoryStorage:
    """
    历史消息存储工具类
    
    按照平台->聊天类型->ID的层级结构存储消息
    使用pickle序列化AstrBotMessage对象
    """
    
    # 保存配置对象的静态变量
    config = None
    # 基础存储路径
    base_storage_path = None
    
    @staticmethod
    def init(config: AstrBotConfig):
        """初始化配置对象"""
        HistoryStorage.config = config
        # 初始化基础存储路径
        HistoryStorage.base_storage_path = os.path.join(os.getcwd(), "data", "chat_history")
        HistoryStorage._ensure_dir(HistoryStorage.base_storage_path)
        logger.info(f"消息存储路径初始化: {HistoryStorage.base_storage_path}")
    
    @staticmethod
    def _ensure_dir(directory: str) -> None:
        """确保目录存在，不存在则创建"""
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def _get_storage_path(platform_name: str, is_private_chat: bool, chat_id: str) -> str:
        """获取存储路径"""
        if not HistoryStorage.base_storage_path:
            # 确保基础路径已初始化，未初始化则初始化一次
            HistoryStorage.base_storage_path = os.path.join(os.getcwd(), "data", "chat_history")
            HistoryStorage._ensure_dir(HistoryStorage.base_storage_path)
            logger.info(f"消息存储路径初始化: {HistoryStorage.base_storage_path}")
            
        chat_type = "private" if is_private_chat else "group"
        directory = os.path.join(HistoryStorage.base_storage_path, platform_name, chat_type)
        
        HistoryStorage._ensure_dir(directory)
        return os.path.join(directory, f"{chat_id}.pkl")
    
    @staticmethod
    def save_message(message: AstrBotMessage) -> bool:
        """
        保存消息到历史记录
        
        Args:
            message: AstrBot消息对象
            
        Returns:
            是否保存成功
        """
        try:
            # 判断是群聊还是私聊
            is_private_chat = not bool(message.group_id)
            platform_name = message.platform_name if hasattr(message, "platform_name") else "unknown"
            
            if is_private_chat:
                if message.private_id:
                    chat_id = message.private_id
                else:
                    chat_id = message.sender.user_id
            else:
                chat_id = message.group_id
                
            # 获取存储路径
            file_path = HistoryStorage._get_storage_path(platform_name, is_private_chat, chat_id)
            
            # 读取现有历史记录
            history = HistoryStorage.get_history(platform_name, is_private_chat, chat_id)
            if not history:
                history = []
                
            # 添加新消息并保存
            history.append(message)
            
            # 限制历史记录数量
            if len(history) > 200:
                history = history[-200:]
            
            # 确保父目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
            with open(file_path, "wb") as f:
                pickle.dump(history, f)
                
            return True
        except Exception as e:
            logger.error(f"保存消息历史记录失败: {e}")
            return False
    
    @staticmethod
    def is_chat_enabled(event: AstrMessageEvent) -> bool:
        """
        判断当前聊天是否启用保存功能
        
        Args:
            event: 消息事件
            
        Returns:
            是否启用
        """
        if not HistoryStorage.config:
            logger.warning("HistoryStorage配置未初始化，默认不启用保存功能")
            return False
            
        is_private = event.is_private_chat()
        if is_private:
            return HistoryStorage.config.get("enabled_private", False)
        else:
            group_id = event.get_group_id()
            return group_id in HistoryStorage.config.get("enabled_groups", [])
    
    @staticmethod
    def process_and_save_user_message(event: AstrMessageEvent) -> None:
        """
        处理用户消息并保存到历史记录
        
        Args:
            event: 消息事件
        """
        # 检查是否启用
        is_enabled = HistoryStorage.is_chat_enabled(event)
        if not is_enabled:
            chat_type = "私聊" if event.is_private_chat() else f"群聊{event.get_group_id()}"
            logger.debug(f"{chat_type}未开启回复功能")
            return
            
        # 创建消息对象
        message_obj = event.message_obj
        message_obj.platform_name = event.get_platform_name()
                
        # 保存消息
        HistoryStorage.save_message(message_obj)
        
        chat_type = "私聊" if event.is_private_chat() else "群聊"
        logger.debug(f"已保存{chat_type}消息到历史记录")
    
    @staticmethod
    def create_bot_message(chain: List[BaseMessageComponent], event: AstrMessageEvent) -> AstrBotMessage:
        """
        从消息链和事件对象创建一个机器人消息对象
        
        Args:
            chain: 消息链
            event: 触发消息的事件
            
        Returns:
            创建的AstrBotMessage对象
        """
        # 创建消息对象
        msg = AstrBotMessage()
        
        # 设置基本属性
        msg.message = chain
        msg.platform_name = event.get_platform_name()
        msg.timestamp = int(time.time())
        
        # 设置消息类型和会话信息
        is_private = event.is_private_chat()
        msg.type = MessageType.FRIEND_MESSAGE if is_private else MessageType.GROUP_MESSAGE
        if not is_private:
            msg.group_id = event.get_group_id()
        
        # 设置发送者信息        
        msg.sender = MessageMember(user_id=event.get_self_id(), nickname="AstrBot")

        # 设置对方的id
        msg.private_id = event.get_sender_id()
        
        # 生成纯文本消息
        msg.message_str = ""
        for comp in chain:
            if isinstance(comp, Plain):
                msg.message_str += comp.text
        
        # 设置其他必要字段
        msg.self_id = event.message_obj.self_id if hasattr(event.message_obj, "self_id") else "bot"
        msg.session_id = event.session_id
        msg.message_id = f"bot_{int(time.time())}"  # 创建一个唯一的消息ID
        
        return msg
    
    @staticmethod
    def save_bot_message_from_chain(chain: List[BaseMessageComponent], event: AstrMessageEvent) -> bool:
        """
        从消息链和事件对象创建并保存机器人消息
        
        Args:
            chain: 消息链
            event: 触发消息的事件
            
        Returns:
            是否保存成功
        """
        try:
            # 检查是否启用
            is_enabled = HistoryStorage.is_chat_enabled(event)
            if not is_enabled:
                return False
                
            # 创建机器人消息对象
            bot_msg = HistoryStorage.create_bot_message(chain, event)
            
            # 保存消息
            return HistoryStorage.save_message(bot_msg)
        except Exception as e:
            logger.error(f"保存机器人消息失败: {e}")
            return False
    
    @staticmethod
    def get_history(platform_name: str, is_private_chat: bool, chat_id: str) -> List[AstrBotMessage]:
        """
        获取历史消息记录
        
        Args:
            platform_name: 平台名称
            is_private_chat: 是否为私聊
            chat_id: 聊天ID
            
        Returns:
            历史消息列表
        """
        try:
            file_path = HistoryStorage._get_storage_path(platform_name, is_private_chat, chat_id)
            
            if not os.path.exists(file_path):
                return []
                
            with open(file_path, "rb") as f:
                history = pickle.load(f)
                
            return history
        except Exception as e:
            logger.error(f"读取消息历史记录失败: {e}")
            return []
    
    @staticmethod
    def clear_history(platform_name: str, is_private_chat: bool, chat_id: str) -> bool:
        """
        清空历史消息记录
        
        Args:
            platform_name: 平台名称
            is_private_chat: 是否为私聊
            chat_id: 聊天ID
            
        Returns:
            是否清空成功
        """
        try:
            file_path = HistoryStorage._get_storage_path(platform_name, is_private_chat, chat_id)
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
            return True
        except Exception as e:
            logger.error(f"清空消息历史记录失败: {e}")
            return False 