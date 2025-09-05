import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)

class EnhancedIntentService:
    """增强的意图识别服务，具备智能对话能力"""
    
    def __init__(self):
        # 预约意图的强指示器
        self.strong_reservation_indicators = [
            r'预约|预定|订|约|申请.*会议室',
            r'会议室.*预约|预定|订|约',
            r'明天.*会议|今天.*会议|下周.*会议',
            r'\d+点.*会议室|\d+:\d+.*会议室',
            r'需要.*会议室|要.*会议室',
            r'安排.*会议|组织.*会议'
        ]
        
        # 预约意图的中等指示器
        self.medium_reservation_indicators = [
            r'会议室|会议|开会',
            r'明天|今天|下周|下午|上午|晚上',
            r'\d+点|\d+:\d+|\d+小时',
            r'房间|场地|地方'
        ]
        
        # 预约意图的弱指示器
        self.weak_reservation_indicators = [
            r'时间|安排|计划',
            r'可以|能否|是否',
            r'空闲|有空|可用'
        ]
        
        # 闲聊意图的强指示器
        self.strong_chat_indicators = [
            r'你好|您好|hi|hello',
            r'天气|温度|下雨|晴天|阴天',
            r'怎么样|如何|什么样',
            r'谢谢|感谢|再见|拜拜',
            r'你是谁|你叫什么|介绍.*自己'
        ]
        
        # 闲聊意图的上下文指示器
        self.context_chat_indicators = [
            r'.*吗\?$|.*呢\?$|.*啊\?$',
            r'^为什么|^怎么|^什么时候',
            r'告诉我|说说|聊聊'
        ]
        
        # 查询动作指示器
        self.query_indicators = [
            r'查询|查看|看看|显示',
            r'有哪些|什么.*预约|我的.*预约',
            r'状态|情况|列表'
        ]
        
        # 取消动作指示器
        self.cancel_indicators = [
            r'取消|删除|撤销',
            r'不要了|不需要了|算了'
        ]
        
        # 修改动作指示器
        self.modify_indicators = [
            r'修改|更改|调整|改成',
            r'换.*时间|改.*时间|延期'
        ]
        
        # 帮助动作指示器
        self.help_indicators = [
            r'帮助|help|怎么用|如何使用',
            r'功能|能做什么|可以.*什么',
            r'使用说明|操作指南'
        ]
        
        # 实体提取模式
        self.entity_patterns = {
            'time': [
                r'(\d{1,2})点(\d{1,2}分?)?',
                r'(\d{1,2}):(\d{2})',
                r'(明天|今天|后天|下周\w*|下个?月)',
                r'(上午|下午|晚上|中午)',
                r'(\d{4}-\d{1,2}-\d{1,2})',
                r'(\d{1,2}月\d{1,2}日?)'
            ],
            'duration': [
                r'(\d+)小时',
                r'(\d+)分钟',
                r'(半小时|一小时|两小时|三小时)'
            ],
            'attendee_count': [
                r'(\d+)人',
                r'(\d+)个人',
                r'(一|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九|二十)人',
                r'(\d+)位',
                r'我们(\d+)个',
                r'共(\d+)人'
            ],
            'equipment_requirements': [
                r'(投影仪|投影|projector)',
                r'(电视|TV|tv|屏幕)',
                r'(白板|whiteboard)',
                r'(音响|音箱|sound)',
                r'(视频会议|video|conference)',
                r'(空调|air)',
                r'(WiFi|wifi|网络)',
                r'(麦克风|microphone|mic)'
            ],
            'room_type': [
                r'(大|小|中).*会议室',
                r'会议室.*(\d+)',
                r'(多媒体|投影|视频).*会议室',
                r'(培训室|讨论室|会议室)'
            ],
            'visitor_info': [
                r'(\d+)人',
                r'(\w+部门?|\w+组)',
                r'联系.*?(\d{11}|\d{3}-\d{8})'
            ]
        }
    
    def analyze_intent(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """分析用户意图和提取实体"""
        try:
            message = message.strip()
            logger.info(f"分析意图: {message}")
            
            # 计算各种意图的置信度
            reservation_score = self._calculate_reservation_score(message)
            chat_score = self._calculate_chat_score(message)
            
            # 检查特定动作
            action_scores = {
                'query': self._calculate_action_score(message, self.query_indicators),
                'cancel': self._calculate_action_score(message, self.cancel_indicators),
                'modify': self._calculate_action_score(message, self.modify_indicators),
                'help': self._calculate_action_score(message, self.help_indicators)
            }
            
            # 确定主要意图
            intent, confidence = self._determine_primary_intent(
                reservation_score, chat_score, action_scores
            )
            
            # 提取实体
            entities = self._extract_entities(message)
            
            # 构建结果
            result = {
                'intent': intent,
                'confidence': confidence,
                'entities': entities,
                'scores': {
                    'reservation': reservation_score,
                    'chat': chat_score,
                    **action_scores
                },
                'message': message
            }
            
            logger.info(f"意图识别结果: {json.dumps(result, ensure_ascii=False)}")
            return result
            
        except Exception as e:
            logger.error(f"意图分析失败: {str(e)}")
            return {
                'intent': 'chat',
                'confidence': 0.5,
                'entities': {},
                'scores': {},
                'message': message,
                'error': str(e)
            }
    
    def _calculate_reservation_score(self, message: str) -> float:
        """计算预约意图得分"""
        score = 0.0
        
        # 强指示器权重: 0.4
        for pattern in self.strong_reservation_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                score += 0.4
                break
        
        # 中等指示器权重: 0.2 (可累加)
        medium_matches = 0
        for pattern in self.medium_reservation_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                medium_matches += 1
        score += min(medium_matches * 0.2, 0.4)
        
        # 弱指示器权重: 0.1 (可累加)
        weak_matches = 0
        for pattern in self.weak_reservation_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                weak_matches += 1
        score += min(weak_matches * 0.1, 0.2)
        
        return min(score, 1.0)
    
    def _calculate_chat_score(self, message: str) -> float:
        """计算闲聊意图得分"""
        score = 0.0
        
        # 强指示器权重: 0.6
        for pattern in self.strong_chat_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                score += 0.6
                break
        
        # 上下文指示器权重: 0.4
        for pattern in self.context_chat_indicators:
            if re.search(pattern, message, re.IGNORECASE):
                score += 0.4
                break
        
        return min(score, 1.0)
    
    def _calculate_action_score(self, message: str, indicators: List[str]) -> float:
        """计算特定动作的得分"""
        for pattern in indicators:
            if re.search(pattern, message, re.IGNORECASE):
                return 0.8
        return 0.0
    
    def _determine_primary_intent(self, reservation_score: float, chat_score: float, 
                                action_scores: Dict[str, float]) -> Tuple[str, float]:
        """确定主要意图"""
        # 检查特定动作
        max_action = max(action_scores.items(), key=lambda x: x[1])
        if max_action[1] > 0.7:
            return max_action[0], max_action[1]
        
        # 比较预约和闲聊得分
        if reservation_score > chat_score and reservation_score > 0.3:
            return 'reservation', reservation_score
        elif chat_score > reservation_score and chat_score > 0.3:
            return 'chat', chat_score
        elif reservation_score > 0.1:  # 有一定预约倾向
            return 'reservation', reservation_score
        else:
            return 'chat', max(chat_score, 0.5)  # 默认为闲聊
    
    def _extract_entities(self, message: str) -> Dict[str, List[str]]:
        """提取实体信息"""
        entities = {}
        
        for entity_type, patterns in self.entity_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, message, re.IGNORECASE)
                if found:
                    if isinstance(found[0], tuple):
                        matches.extend([''.join(match) for match in found])
                    else:
                        matches.extend(found)
            
            if matches:
                entities[entity_type] = list(set(matches))  # 去重
        
        return entities
    
    def get_intent_explanation(self, result: Dict[str, Any]) -> str:
        """获取意图识别的解释"""
        intent = result.get('intent', 'unknown')
        confidence = result.get('confidence', 0)
        scores = result.get('scores', {})
        
        explanations = {
            'reservation': f"识别为预约意图 (置信度: {confidence:.2f})，检测到预约相关关键词",
            'chat': f"识别为闲聊意图 (置信度: {confidence:.2f})，未检测到明确的预约需求",
            'query': f"识别为查询意图 (置信度: {confidence:.2f})，检测到查询相关关键词",
            'cancel': f"识别为取消意图 (置信度: {confidence:.2f})，检测到取消相关关键词",
            'modify': f"识别为修改意图 (置信度: {confidence:.2f})，检测到修改相关关键词",
            'help': f"识别为帮助意图 (置信度: {confidence:.2f})，检测到帮助相关关键词"
        }
        
        return explanations.get(intent, f"未知意图: {intent}")

# 保持向后兼容
class IntentService(EnhancedIntentService):
    """向后兼容的意图识别服务"""
    pass