import os
import json
import re
from astrbot.api.all import logger

async def format_chat_history(group_id, base_path, config):
    """格式化聊天记录为大模型输入格式
    
    Args:
        group_id: 群组ID
        base_path: 消息存储的基础路径
        config: 插件配置
        
    Returns:
        str: 格式化后的聊天记录
    """
    try:
        file_path = os.path.join(base_path, f"{group_id}.json")
        if not os.path.exists(file_path):
            logger.warning(f"群 {group_id} 的消息历史文件不存在")
            return ""
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data or 'messages' not in data:
            return ""
            
        formatted_messages = []
        messages = data['messages']
        
        logger.debug(f"开始格式化群 {group_id} 的聊天记录，共 {len(messages)} 条消息")
        
        # 全局图片计数器和可用图片上限
        img_count = config.get('image_count', 0)
        
        # 添加图片指引提示
        if img_count > 0:
            image_guide = f"【注意：当前最多输入{img_count}张图片(如果有)，标记为[图片1]到[图片{img_count}]，按照消息发送时间从早到晚排序,标记为[图片]的为超出限制的图片】"
            formatted_messages.append(image_guide)
        
        # 收集所有图片资源
        all_images = []
        for msg in messages:
            resources = msg.get('resources', [])
            # 过滤出图片类型的资源
            img_resources = [r for r in resources if r.get('type') == 'image']
            
            if img_resources:
                # 为每条消息的每张图片创建一个记录，包含消息索引和资源索引
                for res_idx, _ in enumerate(img_resources):
                    all_images.append({
                        'msg_idx': messages.index(msg),
                        'res_idx': res_idx,
                        'msg': msg
                    })
                
        # 按照消息从早到晚排序（如果消息时间相同，则按照资源索引排序）
        all_images.sort(key=lambda x: (x['msg_idx'], x['res_idx']))
        
        # 如果图片数量超过限制，只保留前img_count张
        if 0 < img_count < len(all_images):
            all_images = all_images[:img_count]
            
        logger.debug(f"群 {group_id} 的聊天记录中共有 {len(all_images)} 张图片被处理")
        
        # 为每张图片分配全局编号（从1开始）
        for i, img_data in enumerate(all_images):
            img_idx = i + 1  # 从1开始编号
            msg_idx = img_data['msg_idx']
            res_idx = img_data['res_idx']
            
            # 如果消息还没有_img_map字段，初始化一个空字典
            if '_img_map' not in messages[msg_idx]:
                messages[msg_idx]['_img_map'] = {}
            
            # 记录这张图片的全局编号
            messages[msg_idx]['_img_map'][res_idx] = img_idx
            
        # 添加读空气相关提示词
        if config.get('read_air', False):
            formatted_messages.append("【如果你觉得现在不适合发消息，请直接输出<NO_RESPONSE>】")
            
        # 从前向后正常处理消息
        for i, msg in enumerate(messages):
            sender = msg.get('sender', '未知用户')
            msg_time = msg.get('time', '未知时间')
            content = msg.get('content', '')
            img_map = msg.get('_img_map', {})
            
            # 检查是否是合并转发消息
            if "转发消息" in content:
                # 如果有forward_messages字段，用新格式处理合并转发消息
                if 'forward_messages' in msg and msg['forward_messages']:
                    # 格式化合并转发消息的开始部分
                    formatted_content = f"[{sender}/{msg_time}]:[发送了一条合并转发消息 内容如下\n{{"
                    formatted_messages.append(formatted_content)
                    
                    # 格式化内部的子消息
                    forward_contents = []
                    for forward_msg in msg['forward_messages']:
                        f_sender = forward_msg.get('sender', '未知用户')
                        f_time = forward_msg.get('time', '未知时间')
                        f_content = forward_msg.get('content', '')
                        
                        # 检查是否是嵌套的合并转发消息
                        if "转发消息" in f_content and 'forward_messages' in forward_msg:
                            # 处理嵌套的合并转发消息
                            nested_contents = []
                            for nested_msg in forward_msg.get('forward_messages', []):
                                n_sender = nested_msg.get('sender', '未知用户')
                                n_time = nested_msg.get('time', '未知时间')
                                n_content = nested_msg.get('content', '')
                                nested_contents.append(f"[{n_sender}/{n_time}]:{n_content}")
                            
                            # 格式化嵌套的合并转发消息
                            nested_formatted = f"[{f_sender}/{f_time}]:[发送了一条合并转发消息 内容如下\n{{\n"
                            nested_formatted += "\n---\n".join(nested_contents)
                            nested_formatted += "\n}}]"
                            forward_contents.append(nested_formatted)
                        else:
                            # 普通消息
                            forward_contents.append(f"[{f_sender}/{f_time}]:{f_content}")
                    
                    # 将子消息添加到格式化消息中
                    formatted_messages.append("\n---\n".join(forward_contents))
                    
                    # 添加合并转发消息的结束部分
                    formatted_messages.append("}]")
                    
                    logger.debug(f"处理第 {i+1}/{len(messages)} 条消息: 合并转发消息，包含 {len(msg['forward_messages'])} 条子消息")
                else:
                    # 如果没有子消息，简单显示合并转发消息
                    formatted_content = f"[{sender}/{msg_time}]:{content}"
                    formatted_messages.append(formatted_content)
                    logger.debug(f"处理第 {i+1}/{len(messages)} 条消息: 空的合并转发消息")
            else:
                # 处理普通消息和图片消息
                if img_map:
                    # 从消息内容中删除所有[图片]标记
                    clean_content = re.sub(r'\[图片\]', '', content).strip()
                    
                    # 生成图片标记，确保按照资源索引顺序添加
                    img_markers = ""
                    for res_idx in sorted(img_map.keys()):
                        img_id = img_map[res_idx]
                        img_markers += f"[图片{img_id}]"
                    
                    # 合并图片标记和清理后的内容
                    if clean_content:
                        formatted_content = f"[{sender}/{msg_time}]:{img_markers}{clean_content}"
                    else:
                        formatted_content = f"[{sender}/{msg_time}]:{img_markers}"
                        
                    formatted_messages.append(formatted_content)
                    logger.debug(f"处理第 {i+1}/{len(messages)} 条消息: 图片消息，包含 {len(img_map)} 张图片")
                else:
                    # 处理普通文本消息
                    formatted_content = f"[{sender}/{msg_time}]:{content}"
                    formatted_messages.append(formatted_content)
                    logger.debug(f"处理第 {i+1}/{len(messages)} 条消息: 普通消息")
        
        # 消息已经按从早到晚排序，最后一条是最新消息
        result = "\n---\n".join(formatted_messages)
        logger.debug(f"格式化完成，共处理 {len(formatted_messages)} 条格式化消息")
        return result
        
    except Exception as e:
        logger.error(f"格式化聊天记录出错: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        return "" 