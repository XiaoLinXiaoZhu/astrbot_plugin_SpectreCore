from typing import Dict

class ImageProcessor:
    """处理图片类消息"""
    
    @classmethod
    def process_image_data(cls, data: Dict) -> Dict:
        """处理图片数据,区分普通图片、QQ表情和普通表情"""
        result = {
            'type': 'image',
            'url': data.get('url', ''),
            'summary': ''
        }
        
        # 判断是否为QQ表情(超级表情/商城表情)
        if 'emoji_id' in data:
            result['type'] = 'mface'
            result['summary'] = data.get('summary', '')
        # 判断是否为普通表情
        elif data.get('sub_type') == 1:
            result['type'] = 'sticker'
            result['summary'] = data.get('summary', '')
        # 普通图片
        else:
            result['file_size'] = data.get('file_size', '')
            result['file'] = data.get('file', '')

        return result
    
    @classmethod
    def format_image_text(cls, data: Dict) -> str:
        """将图片数据格式化为文本表示"""
        image_info = cls.process_image_data(data)
        
        if image_info['type'] == 'mface':
            return f"[QQ表情:{image_info['summary']}]"
        elif image_info['type'] == 'sticker':
            return image_info['summary'] or "[贴纸]"
        else:
            return "[图片]" 