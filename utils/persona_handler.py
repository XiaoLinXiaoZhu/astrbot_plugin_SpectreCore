from astrbot.api.all import logger

async def get_persona_info(persona_name, context):
    """从AstrBot系统中获取人格信息
    
    Args:
        persona_name: 人格名称
        context: AstrBot上下文
        
    Returns:
        dict: 人格信息，包含系统提示词和对话上下文等
    """
    try:
        if not persona_name:
            logger.debug("未指定人格名称,将不使用人格")
            return None
            
        # 获取所有可用的人格
        personas = context.provider_manager.personas
        if not personas:
            logger.warning("系统中没有可用的人格")
            return None
            
        # 查找指定名称的人格
        persona = None
        for p in personas:
            if p.get('name') == persona_name:
                persona = p
                break
                
        if not persona:
            logger.warning(f"找不到名为 '{persona_name}' 的人格")
            return None
            
        logger.info(f"找到人格 '{persona_name}'")
        return persona
        
    except Exception as e:
        logger.error(f"获取人格信息时出错: {str(e)}", exc_info=True)
        return None 