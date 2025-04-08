import random
from astrbot.api.all import logger

def should_reply(content, config, group_id=None):
    """决定是否应该回复消息
    
    Args:
        content: 消息内容
        config: 插件配置
        group_id: 群聊ID，如果为None则不检查群聊是否启用
        
    Returns:
        bool: 是否应该回复
    """
    try:
        # 首先检查是否包含命令关键词，避免回复命令
        command_keywords = ["reset", "help",  "spectrecore", "sc "]
        for keyword in command_keywords:
            if keyword in content.lower():
                logger.debug(f"消息包含命令关键词 '{keyword}'，不回复")
                return False
                
        # 检查群聊是否在启用列表中
        if group_id is not None:
            enabled_groups = config.get('enabled_groups', [])
            # 如果启用列表为空或当前群聊不在列表中，则不回复
            if not enabled_groups or str(group_id) not in [str(g) for g in enabled_groups]:
                logger.debug(f"群聊 {group_id} 未启用回复功能")
                return False
        
        # 检查模型频率设置
        freq_config = config.get('model_frequency', {})
        
        # 检查关键词触发
        keywords = freq_config.get('keywords', [])
        if keywords:
            for keyword in keywords:
                if keyword in content:
                    logger.debug(f"关键词 '{keyword}' 触发了回复")
                    return True
        
        # 概率触发
        method = freq_config.get('method', '')
        if method == "概率回复":
            # 直接使用配置中的概率值（0-1之间的小数）
            prob_config = freq_config.get('probability', {})
            probability = prob_config.get('probability', 0)
            
            # 确保概率值是浮点数类型
            try:
                probability = float(probability)
            except (ValueError, TypeError):
                logger.warning(f"概率值 '{probability}' 不是有效的数值，使用默认值0")
                probability = 0.0
            
            # 确保概率值在有效范围内
            if probability < 0:
                probability = 0
            elif probability > 1:
                probability = 1
                
            random_value = random.random()  # 生成0-1之间的随机小数
            if random_value <= probability:
                logger.debug(f"概率触发回复: {random_value:.4f} <= {probability:.4f}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"检查是否回复时出错: {str(e)}", exc_info=True)
        return False 