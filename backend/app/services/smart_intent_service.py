import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from .ai_service import AIService
from .intent_service import IntentService
import logging

logger = logging.getLogger(__name__)

class SmartIntentService:
    """智能意图识别服务，结合大模型和规则引擎"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.intent_service = IntentService()
        
    async def analyze_smart_intent(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """智能意图分析，结合大模型和规则引擎"""
        
        try:
            # 1. 使用大模型进行深度意图理解
            ai_analysis = await self._ai_intent_analysis(message, context)
            
            # 2. 使用规则引擎进行实体提取
            rule_analysis = self.intent_service.analyze_intent(message)
            
            # 3. 融合分析结果
            merged_result = self._merge_analysis_results(ai_analysis, rule_analysis)
            
            # 4. 验证和补全信息
            validated_result = self._validate_and_complete(merged_result, context)
            
            return validated_result
            
        except Exception as e:
            logger.error(f"智能意图分析失败: {e}")
            # 降级到规则引擎
            return self.intent_service.analyze_intent(message)
    
    async def _ai_intent_analysis(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """使用大模型进行意图分析"""
        
        # 构建对话历史
        conversation_history = ""
        if context and context.get("conversation_history"):
            history = context["conversation_history"][-5:]  # 最近5轮对话
            for msg in history:
                conversation_history += f"{msg['type']}: {msg['text']}\n"
        
        # 构建提示词
        prompt = f"""你是一个智能会议预约助手，需要分析用户的预约意图并提取关键信息。

对话历史：
{conversation_history}

当前用户输入：{message}

请分析用户意图并提取以下信息（如果有的话）：
1. 预约意图类型（reservation/query/cancel/modify/help）
2. 时间信息（具体日期时间、持续时间）
3. 会议室类型（小型/大型/多媒体等）
4. 访客信息（姓名、公司、人数、联系方式）
5. 车辆信息（车牌号、车辆类型）
6. 其他特殊需求

请以JSON格式返回分析结果：
{{
  "intent": "预约意图类型",
  "confidence": 0.0-1.0,
  "entities": {{
    "time": {{
      "start_time": "YYYY-MM-DD HH:MM",
      "end_time": "YYYY-MM-DD HH:MM",
      "duration": "持续时间（分钟）"
    }},
    "room_type": "会议室类型",
    "visitor_info": {{
      "names": ["访客姓名列表"],
      "company": "公司名称",
      "count": 访客人数,
      "contact": "联系方式"
    }},
    "vehicle_info": {{
      "license_plate": "车牌号",
      "vehicle_type": "车辆类型"
    }},
    "special_requirements": "特殊需求"
  }},
  "missing_information": ["缺失的关键信息列表"],
  "suggestions": ["建议用户提供的信息"],
  "natural_response": "自然语言回复"
}}

注意：
- 时间解析要考虑相对时间（如"明天"、"下周"、"下午2点"）
- 如果信息不完整，在missing_information中列出
- 提供友好的自然语言回复
- 置信度要根据信息完整性和明确性评估
"""
        
        try:
            # 使用现有AI服务生成响应
            ai_response = await self.ai_service.generate_response(
                message=prompt,
                context=context
            )
            
            # 尝试提取JSON
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                logger.warning(f"无法从AI响应中提取JSON: {ai_response}")
                return {"intent": "unknown", "confidence": 0.0}
                
        except Exception as e:
            logger.error(f"AI意图分析失败: {e}")
            # 检查是否是API密钥相关错误
            if "API密钥" in str(e) or "InvalidApiKey" in str(e) or "401" in str(e):
                logger.warning("检测到API密钥无效，使用本地规则引擎")
            return {"intent": "unknown", "confidence": 0.0}
    
    def _merge_analysis_results(
        self, 
        ai_result: Dict[str, Any], 
        rule_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """融合AI分析和规则分析结果"""
        
        # 智能选择意图：优先使用非unknown的结果
        ai_intent = ai_result.get("intent", "unknown")
        rule_intent = rule_result.get("intent", "unknown")
        
        if ai_intent != "unknown":
            final_intent = ai_intent
        elif rule_intent != "unknown":
            final_intent = rule_intent
        else:
            final_intent = "unknown"
        
        merged = {
            "intent": final_intent,
            "confidence": max(
                ai_result.get("confidence", 0.0),
                rule_result.get("confidence", 0.0)
            ),
            "entities": {},
            "missing_information": [],
            "suggestions": [],
            "natural_response": ai_result.get("natural_response", "")
        }
        
        # 融合实体信息
        ai_entities = ai_result.get("entities", {})
        rule_entities = rule_result.get("entities", {})
        
        # 时间信息优先使用AI结果，因为AI更擅长自然语言时间解析
        if ai_entities.get("time"):
            merged["entities"]["time"] = ai_entities["time"]
        elif rule_entities.get("time"):
            merged["entities"]["time"] = rule_entities["time"]
        
        # 其他实体信息取并集
        for key in ["room_type", "visitor_info", "vehicle_info", "special_requirements"]:
            if ai_entities.get(key):
                merged["entities"][key] = ai_entities[key]
            elif rule_entities.get(key):
                merged["entities"][key] = rule_entities[key]
        
        # 合并缺失信息和建议
        merged["missing_information"] = list(set(
            ai_result.get("missing_information", []) + 
            rule_result.get("missing_information", [])
        ))
        
        merged["suggestions"] = list(set(
            ai_result.get("suggestions", []) + 
            rule_result.get("suggestions", [])
        ))
        
        return merged
    
    def _validate_and_complete(
        self, 
        analysis_result: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证和补全分析结果"""
        
        # 检查是否可以创建预约
        entities = analysis_result.get("entities", {})
        missing_info = analysis_result.get("missing_information", [])
        
        # 必需信息检查
        required_fields = ["time", "visitor_info"]
        
        for field in required_fields:
            if not entities.get(field):
                if field not in missing_info:
                    missing_info.append(field)
        
        # 时间验证
        if entities.get("time"):
            time_info = entities["time"]
            if not time_info.get("start_time") or not time_info.get("end_time"):
                if "time" not in missing_info:
                    missing_info.append("time")
        
        # 访客信息验证
        if entities.get("visitor_info"):
            visitor_info = entities["visitor_info"]
            if not visitor_info.get("names") and not visitor_info.get("count"):
                if "visitor_info" not in missing_info:
                    missing_info.append("visitor_info")
        
        # 更新结果
        analysis_result["missing_information"] = missing_info
        analysis_result["can_create_reservation"] = len(missing_info) == 0
        
        # 如果可以创建预约，构建预约数据
        if analysis_result["can_create_reservation"]:
            analysis_result["reservation_data"] = self._build_reservation_data(entities)
        
        return analysis_result
    
    def _build_reservation_data(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """构建预约数据"""
        
        reservation_data = {}
        
        # 时间信息
        if entities.get("time"):
            time_info = entities["time"]
            reservation_data.update({
                "start_time": time_info.get("start_time"),
                "end_time": time_info.get("end_time"),
                "duration": time_info.get("duration")
            })
        
        # 访客信息
        if entities.get("visitor_info"):
            visitor_info = entities["visitor_info"]
            reservation_data.update({
                "visitor_name": ", ".join(visitor_info.get("names", [])),
                "visitor_company": visitor_info.get("company", ""),
                "visitor_count": visitor_info.get("count", 1),
                "visitor_contact": visitor_info.get("contact", "")
            })
        
        # 会议室类型
        if entities.get("room_type"):
            reservation_data["room_type"] = entities["room_type"]
        
        # 车辆信息
        if entities.get("vehicle_info"):
            vehicle_info = entities["vehicle_info"]
            reservation_data.update({
                "license_plate": vehicle_info.get("license_plate", ""),
                "vehicle_type": vehicle_info.get("vehicle_type", "")
            })
        
        # 特殊需求
        if entities.get("special_requirements"):
            reservation_data["special_requirements"] = entities["special_requirements"]
        
        return reservation_data