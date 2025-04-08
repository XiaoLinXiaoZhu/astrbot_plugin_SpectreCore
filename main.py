import os
import traceback
import time
import asyncio
from astrbot.api.all import *
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from .message_processor import MessageProcessor
from .utils.chat_formatter import format_chat_history
from .utils.reply_decision import should_reply
from .utils.persona_handler import get_persona_info
from .utils.text_filter import process_model_text
from astrbot.api.provider import LLMResponse
from astrbot.api.event import filter, AstrMessageEvent
from .api_client import APIClient

@register(
    "spectrecore",
    "23q3", 
    "使大模型更好的主动回复群聊中的消息，带来生动和沉浸的群聊对话体验",
    "1.0.4",
    "https://github.com/23q3/astrbot_plugin_SpectreCore"
)
class SpectreCore(Star):
    """
    使大模型更好的主动回复群聊中的消息，带来生动和沉浸的群聊对话体验
    """
    
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.base_path = os.path.join("data", "group_messages")
        os.makedirs(self.base_path, exist_ok=True)
        logger.info(f"SpectreCore插件初始化完成，消息存储路径: {self.base_path}")
        # 为每个群组创建锁字典，防止并发调用大模型
        self.group_locks = {}

    def get_group_lock(self, group_id):
        """获取群组锁，如果不存在则创建"""
        if group_id not in self.group_locks:
            self.group_locks[group_id] = asyncio.Lock()
        return self.group_locks[group_id]

    async def collect_image_urls(self, messages, latest_message_index, img_count):
        """收集图片URL"""
        if img_count <= 0:
            return []
            
        image_urls = []
        latest_message = messages[latest_message_index]
        
        # 从最新消息中收集图片
        for seg in latest_message.get('message', []):
            if seg.get('type') == 'image':
                url = seg.get('data', {}).get('url')
                if url:
                    image_urls.append(url)
        
        # 如果需要更多图片，从其他消息中收集
        if len(image_urls) < img_count:
            for msg in messages[:latest_message_index]:
                if len(image_urls) >= img_count:
                    break
                for seg in msg.get('message', []):
                    if seg.get('type') == 'image':
                        url = seg.get('data', {}).get('url')
                        if url and url not in image_urls:
                            image_urls.append(url)
                            if len(image_urls) >= img_count:
                                break
        
        return image_urls[:img_count]

    async def prepare_model_prompt(self, persona_info):
        """准备模型系统提示词和上下文"""
        system_prompt = f"当前时间:{time.strftime('%Y-%m-%d %H:%M:%S')}"
        contexts = []
        
        if persona_info:
            # 添加人格提示词
            if persona_info.get('prompt'):
                system_prompt += f"\n\n{persona_info.get('prompt')}"
            
            # 添加对话风格模仿提示
            mood_imitation = persona_info.get('_mood_imitation_dialogs_processed')
            if mood_imitation:
                system_prompt += f"\n\n请模仿以下对话风格进行回复：\n{mood_imitation}"
            
            # 添加预设对话上下文
            begin_dialogs = persona_info.get('_begin_dialogs_processed', [])
            if begin_dialogs:
                contexts.extend(begin_dialogs)
        
        return system_prompt, contexts
        
    async def process_and_save_group_message(self, event):
        """处理并保存群消息"""
        try:
            # 检查事件类型
            if not isinstance(event, AiocqhttpMessageEvent):
                logger.debug("非AiocqhttpMessageEvent类型的消息，跳过处理")
                return None
                
            client = event.bot
            group_id = event.get_group_id()
            
            # 检查是否为启用回复功能的群聊
            enabled_groups = self.config.get('enabled_groups', [])
            if enabled_groups and str(group_id) not in [str(g) for g in enabled_groups]:
                logger.debug(f"群 {group_id} 未启用回复功能，跳过保存消息")
                return None
                
            # 获取群消息历史
            response = await APIClient.get_group_message_history(client, group_id, 2)
            if not response or 'messages' not in response or not response['messages']:
                return None
                
            messages = response['messages']

            logger.debug(f"群 {group_id} 的消息历史: {messages}")
            
            # 处理并保存消息
            save_result = await MessageProcessor.save_messages(
                group_id, messages, self.base_path, client, self.config.get('group_msg_history', 100)
            )
            
            if not save_result:
                logger.warning(f"群 {group_id} 的消息保存失败")
                return None
                
            return messages
        except Exception as e:
            logger.error(f"处理群消息时出错: {str(e)}")
            return None
    
    async def get_local_message_history(self, group_id):
        """获取本地保存的消息历史"""
        try:
            file_path = os.path.join(self.base_path, f"{group_id}.json")
            if not os.path.exists(file_path):
                logger.debug(f"群 {group_id} 的历史消息文件不存在")
                return None
                
            import aiofiles
            import json
            
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                if 'messages' in data and data['messages']:
                    logger.debug(f"成功读取群 {group_id} 的本地历史消息，共 {len(data['messages'])} 条")
                    return data['messages']
                else:
                    logger.debug(f"群 {group_id} 的本地历史消息为空")
                    return None
        except Exception as e:
            logger.error(f"读取本地历史消息出错: {str(e)}")
            return None
    
    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def on_group_message(self, event: AstrMessageEvent):
        """处理群消息事件"""
        try:
            group_id = event.get_group_id()

            enabled_groups = self.config.get('enabled_groups', [])
            if enabled_groups and str(group_id) not in [str(g) for g in enabled_groups]:
                logger.debug(f"群 {group_id} 未启用回复功能")
                return
            
            # 获取并保存最新的群消息，但不使用它来决定是否回复
            await self.process_and_save_group_message(event)
            
            # 从本地获取历史消息
            local_messages = await self.get_local_message_history(group_id)
            if not local_messages:
                logger.debug(f"群 {group_id} 没有本地历史消息，无法处理")
                return
            
            # 获取最新消息内容，决定是否回复
            latest_message = local_messages[-1]  # 使用本地历史中的最新消息
            
            # 分析最新消息是否需要回复
            content = latest_message.get('content', '')
            if not content:
                logger.debug(f"最新消息内容为空，跳过回复")
                return
                
            # 判断是否需要回复
            if not should_reply(content, self.config, group_id):
                return
                
            # 获取群组锁，确保同一群组的大模型调用是串行的
            group_lock = self.get_group_lock(group_id)
            
            # 尝试获取锁，如果锁被占用，表示已经有一个请求在处理中
            if not group_lock.locked():
                async with group_lock:
                    logger.debug(f"群 {group_id} 获取锁成功，开始处理大模型调用")
                    # 准备调用大模型
                    login_info = await APIClient.get_login_info(event.bot)
                    botname = login_info.get('nickname')
                    botqq = login_info.get('user_id')
                    chat_history = await format_chat_history(group_id, self.base_path, self.config)
                    prompt = f"你在一个qq群聊中，你是qq号为{botqq}，昵称为{botname}的一名用户，以下是经过格式化后的聊天记录（所有消息均被格式化成文本，如图片被转换为[图片]，表情被转换为[动画表情]）:\n{chat_history}\n\n你输出的内容将作为群聊中的消息发送。" + \
                        "你只应该发送文字消息，不要发送[图片]、[qq表情]、[@某人(id:xxx)]等你在聊天记录中看到的特殊内容。"
                    
                    # 收集图片URL（从本地历史消息中获取）
                    img_count = self.config.get('image_count', 0)
                    image_urls = []
                    
                    if img_count > 0:
                        # 从最新消息中收集图片URL
                        latest_message_data = latest_message.get('raw_message', {})
                        if isinstance(latest_message_data, dict) and 'message' in latest_message_data:
                            for seg in latest_message_data.get('message', []):
                                if seg.get('type') == 'image':
                                    url = seg.get('data', {}).get('url')
                                    if url:
                                        image_urls.append(url)
                                        if len(image_urls) >= img_count:
                                            break
                        
                        # 如果需要更多图片，从其他消息中收集
                        if len(image_urls) < img_count:
                            for msg in reversed(local_messages[:-1]):  # 除了最新消息外的消息，从新到旧
                                if len(image_urls) >= img_count:
                                    break
                                msg_data = msg.get('raw_message', {})
                                if isinstance(msg_data, dict) and 'message' in msg_data:
                                    for seg in msg_data.get('message', []):
                                        if seg.get('type') == 'image':
                                            url = seg.get('data', {}).get('url')
                                            if url and url not in image_urls:
                                                image_urls.append(url)
                                                if len(image_urls) >= img_count:
                                                    break
                    
                    # 获取人格信息
                    persona_name = self.config.get('persona', '')
                    persona_info = await get_persona_info(persona_name, self.context)
                    
                    # 准备系统提示词和上下文
                    system_prompt, contexts = await self.prepare_model_prompt(persona_info)
                    logger.debug(f"提示词: {prompt}")
                    
                    # 调用大模型
                    if self.config.get('use_func_tool', False):
                        func_tools_mgr = self.context.get_llm_tool_manager()
                    else:
                        func_tools_mgr = None
                    yield event.request_llm(
                        prompt=prompt,
                        contexts=contexts,
                        image_urls=image_urls,
                        func_tool_manager=func_tools_mgr,
                        system_prompt=system_prompt
                    )
                    logger.debug(f"群 {group_id} 大模型调用完成，释放锁")
            else:
                logger.debug(f"群 {group_id} 已有一个大模型调用在进行中，跳过此次请求")
         
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"处理群消息时出错: {str(e)}\n{error_details}")

    @filter.after_message_sent()
    async def after_message_sent(self, event: AstrMessageEvent):
        """发送消息给消息平台适配器后"""
        # 获取并保存机器人发送的消息
        await self.process_and_save_group_message(event)

    @filter.on_llm_response()
    async def on_llm_resp(self, event: AstrMessageEvent, resp: LLMResponse): 
        """处理大模型回复"""
        try:
           if (self.config.get('filter_thinking', False) or self.config.get('read_air', False)) and resp.role == "assistant":
                resp.completion_text = process_model_text(resp.completion_text, self.config)
                if resp.completion_text == "":
                    event.stop_event()
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"处理大模型回复时出错: {str(e)}\n{error_details}")
    
    @command_group("spectrecore",alias=['sc'])
    def spectrecore(self):
        """指令前缀spectrecore或sc"""

    @spectrecore.command("help", alias=['帮助', 'helpme'])
    async def help(self, event: AstrMessageEvent):
        """查看帮助文档"""
        yield event.plain_result(
            "SpectreCore插件帮助文档\n"
            "1.用spectrecore或sc作为指令前缀 如/sc help\n"
            "2.使用reset重置聊天记录 如/sc reset\n"
            "你也可以在私聊中重置群聊天记录 如/sc reset 群号\n"
            "更多信息请查看https://github.com/23q3/astrbot_plugin_SpectreCore"
        )
    
    @spectrecore.command("reset")
    async def reset(self, event: AstrMessageEvent, group_id: int = None):
        """重置聊天记录
        
        Args:
            event: 消息事件
            group_id: 群号，可选参数
        """
        try:
            # 判断消息类型和参数情况
            if group_id is None:
                # 如果没有提供群号
                if event.get_group_id():
                    # 群聊消息，使用当前群号
                    group_id = event.get_group_id()
                    logger.info(f"使用当前群 {group_id} 进行重置")
                else:
                    # 私聊消息且没有提供群号，返回提示
                    yield event.plain_result("请提供要重置聊天记录的群号，例如：/sc reset 123456789")
                    return
            
            # 检查群号是否有效
            if not group_id or not str(group_id).isdigit():
                yield event.plain_result("请提供有效的群号")
                return
                
            # 执行重置操作
            file_path = os.path.join(self.base_path, f"{group_id}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"已重置群 {group_id} 的聊天记录")
                yield event.plain_result(f"已重置群 {group_id} 的聊天记录")
            else:
                logger.info(f"群 {group_id} 没有聊天记录文件")
                yield event.plain_result(f"群 {group_id} 没有聊天记录文件，可能已经被重置")
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"重置聊天记录时出错: {str(e)}\n{error_details}")
            yield event.plain_result(f"重置聊天记录失败: {str(e)}")
