from typing import Dict, List

class TextProcessor:
    """处理文本类消息"""
    
    @classmethod
    def process_text(cls, data: Dict) -> str:
        """处理纯文本消息"""
        return data.get('text', '')
    
    @classmethod
    def process_face(cls, data: Dict) -> str:
        """处理表情消息"""
        face_data = data.get('raw', {})
        face_text = face_data.get('faceText', '表情')
        return f"[QQ表情:{face_text}]"
    
    @classmethod
    def process_rps_data(cls, result: str) -> str:
        """处理猜拳消息"""
        rps_map = {
            '1': '布',
            '2': '剪刀',
            '3': '拳头'
        }
        return f"[猜拳:{rps_map.get(result, '未知')}]"

    @classmethod
    def process_dice_data(cls, result: str) -> str:
        """处理骰子消息"""
        return f"[骰子:{result}点]" 