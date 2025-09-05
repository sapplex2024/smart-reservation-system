import re
import logging
from datetime import datetime, timedelta, date, time
from typing import Dict, List, Optional, Tuple, Any
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)

class SmartTimeParser:
    """智能时间解析器，处理复杂的中文时间表达"""
    
    def __init__(self):
        # 时间关键词映射
        self.time_keywords = {
            # 相对时间
            "今天": 0, "今日": 0, "当天": 0,
            "明天": 1, "明日": 1,
            "后天": 2,
            "大后天": 3,
            "昨天": -1, "昨日": -1,
            "前天": -2,
            
            # 星期
            "这周": 0, "本周": 0,
            "下周": 1, "下个星期": 1,
            "上周": -1, "上个星期": -1,
            
            # 月份
            "这个月": 0, "本月": 0,
            "下个月": 1, "下月": 1,
            "上个月": -1, "上月": -1,
        }
        
        # 星期映射
        self.weekday_map = {
            "周一": 0, "星期一": 0, "礼拜一": 0, "周1": 0,
            "周二": 1, "星期二": 1, "礼拜二": 1, "周2": 1,
            "周三": 2, "星期三": 2, "礼拜三": 2, "周3": 2,
            "周四": 3, "星期四": 3, "礼拜四": 3, "周4": 3,
             "周五": 4, "星期五": 4, "礼拜五": 4, "周5": 4,
            "周六": 5, "星期六": 5, "礼拜六": 5, "周6": 5,
            "周日": 6, "星期日": 6, "礼拜日": 6, "周7": 6, "星期天": 6
        }
        
        # 时间段映射
        self.time_period_map = {
            "早上": (8, 0), "早晨": (8, 0), "上午": (9, 0),
            "中午": (12, 0), "午间": (12, 0),
            "下午": (14, 0), "午后": (14, 0),
            "晚上": (19, 0), "傍晚": (18, 0), "夜里": (20, 0), "夜间": (20, 0)
        }
        
        # 数字映射
        self.number_map = {
            "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
            "十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15,
            "十六": 16, "十七": 17, "十八": 18, "十九": 19, "二十": 20,
            "二十一": 21, "二十二": 22, "二十三": 23, "二十四": 24,
            "二十五": 25, "二十六": 26, "二十七": 27, "二十八": 28,
            "二十九": 29, "三十": 30, "三十一": 31
        }
        
        # 时长单位映射
        self.duration_units = {
            "分钟": 1, "分": 1,
            "小时": 60, "时": 60, "个小时": 60,
            "半小时": 30, "半个小时": 30,
            "一刻钟": 15, "刻钟": 15
        }
    
    def parse_time_expression(self, text: str, base_time: Optional[datetime] = None) -> Dict[str, Any]:
        """解析时间表达式"""
        if base_time is None:
            base_time = datetime.now()
        
        result = {
            "success": False,
            "date": None,
            "time": None,
            "duration": None,
            "end_time": None,
            "parsed_expressions": [],
            "confidence": 0.0
        }
        
        try:
            # 预处理文本
            text = self._preprocess_text(text)
            
            # 解析日期
            date_result = self._parse_date(text, base_time)
            if date_result["success"]:
                result["date"] = date_result["date"]
                result["parsed_expressions"].append(date_result["expression"])
                result["confidence"] += 0.3
            
            # 解析时间
            time_result = self._parse_time(text, base_time)
            if time_result["success"]:
                result["time"] = time_result["time"]
                result["parsed_expressions"].append(time_result["expression"])
                result["confidence"] += 0.4
            
            # 解析时长
            duration_result = self._parse_duration(text)
            if duration_result["success"]:
                result["duration"] = duration_result["duration"]
                result["parsed_expressions"].append(duration_result["expression"])
                result["confidence"] += 0.2
            
            # 计算结束时间
            if result["time"] and result["duration"]:
                start_datetime = datetime.combine(
                    result["date"] or base_time.date(),
                    result["time"]
                )
                end_datetime = start_datetime + timedelta(minutes=result["duration"])
                result["end_time"] = end_datetime.time()
                result["confidence"] += 0.1
            
            # 设置成功标志
            result["success"] = result["confidence"] > 0.3
            
            return result
            
        except Exception as e:
            logger.error(f"时间解析失败: {e}")
            return result
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 标准化数字表达
        for chinese_num, arabic_num in self.number_map.items():
            text = text.replace(chinese_num, str(arabic_num))
        
        return text
    
    def _parse_date(self, text: str, base_time: datetime) -> Dict[str, Any]:
        """解析日期表达式"""
        result = {"success": False, "date": None, "expression": ""}
        
        try:
            # 1. 绝对日期格式 (YYYY-MM-DD, MM-DD, MM/DD等)
            date_patterns = [
                r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日号]?',
                r'(\d{1,2})[-/月](\d{1,2})[日号]',
                r'(\d{1,2})[月](\d{1,2})[日号]'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:  # YYYY-MM-DD
                        year, month, day = map(int, groups)
                    else:  # MM-DD
                        year = base_time.year
                        month, day = map(int, groups)
                    
                    try:
                        parsed_date = date(year, month, day)
                        # 如果日期在过去且没有指定年份，可能是指明年
                        if len(groups) == 2 and parsed_date < base_time.date():
                            parsed_date = date(year + 1, month, day)
                        
                        result["success"] = True
                        result["date"] = parsed_date
                        result["expression"] = match.group()
                        return result
                    except ValueError:
                        continue
            
            # 2. 相对日期 (今天、明天、后天等)
            for keyword, offset in self.time_keywords.items():
                if keyword in text:
                    if "周" in keyword or "星期" in keyword:
                        # 处理周相关的表达
                        target_date = base_time.date() + timedelta(weeks=offset)
                    elif "月" in keyword:
                        # 处理月相关的表达
                        target_date = (base_time + relativedelta(months=offset)).date()
                    else:
                        # 处理天相关的表达
                        target_date = base_time.date() + timedelta(days=offset)
                    
                    result["success"] = True
                    result["date"] = target_date
                    result["expression"] = keyword
                    return result
            
            # 3. 星期表达 (下周三、这周五等)
            week_pattern = r'(下周|下个星期|上周|上个星期|这周|本周)?(周[一二三四五六日]|星期[一二三四五六日天]|礼拜[一二三四五六日天])'
            match = re.search(week_pattern, text)
            if match:
                week_prefix = match.group(1) or "这周"
                weekday_str = match.group(2)
                
                # 获取目标星期几
                target_weekday = self.weekday_map.get(weekday_str)
                if target_weekday is not None:
                    # 计算周偏移
                    week_offset = 0
                    if "下周" in week_prefix or "下个星期" in week_prefix:
                        week_offset = 1
                    elif "上周" in week_prefix or "上个星期" in week_prefix:
                        week_offset = -1
                    
                    # 计算目标日期
                    current_weekday = base_time.weekday()
                    days_ahead = target_weekday - current_weekday
                    if week_offset == 0 and days_ahead <= 0:
                        days_ahead += 7  # 如果是本周但已过去，指向下周
                    
                    target_date = base_time.date() + timedelta(
                        days=days_ahead + (week_offset * 7)
                    )
                    
                    result["success"] = True
                    result["date"] = target_date
                    result["expression"] = match.group()
                    return result
            
            # 4. 尝试使用dateutil解析
            try:
                parsed_date = date_parser.parse(text, default=base_time, fuzzy=True).date()
                if parsed_date != base_time.date():  # 确实解析出了不同的日期
                    result["success"] = True
                    result["date"] = parsed_date
                    result["expression"] = "dateutil_parsed"
                    return result
            except:
                pass
            
        except Exception as e:
            logger.error(f"日期解析失败: {e}")
        
        return result
    
    def _parse_time(self, text: str, base_time: datetime) -> Dict[str, Any]:
        """解析时间表达式"""
        result = {"success": False, "time": None, "expression": ""}
        
        try:
            # 1. 标准时间格式 (HH:MM, HH点MM分等)
            time_patterns = [
                r'(\d{1,2}):(\d{2})',
                r'(\d{1,2})[点时](\d{1,2})[分]?',
                r'(\d{1,2})[点时]',
                r'(\d{1,2})[分]'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    if len(groups) == 2:
                        hour, minute = map(int, groups)
                    elif len(groups) == 1:
                        if "分" in match.group():
                            hour = base_time.hour
                            minute = int(groups[0])
                        else:
                            hour = int(groups[0])
                            minute = 0
                    
                    # 验证时间有效性
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        result["success"] = True
                        result["time"] = time(hour, minute)
                        result["expression"] = match.group()
                        return result
            
            # 2. 时间段表达 (上午、下午、晚上等)
            for period, (default_hour, default_minute) in self.time_period_map.items():
                if period in text:
                    # 检查是否有具体时间跟随
                    period_pattern = f'{period}(\\d{{1,2}})[点时]?(\\d{{1,2}})?[分]?'
                    match = re.search(period_pattern, text)
                    
                    if match:
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                        
                        # 调整小时（12小时制转24小时制）
                        if period in ["下午", "午后"] and hour < 12:
                            hour += 12
                        elif period in ["晚上", "夜里", "夜间"] and hour < 12:
                            hour += 12
                        elif period in ["上午", "早上", "早晨"] and hour == 12:
                            hour = 0
                    else:
                        hour, minute = default_hour, default_minute
                    
                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        result["success"] = True
                        result["time"] = time(hour, minute)
                        result["expression"] = period
                        return result
            
            # 3. 特殊时间表达
            special_times = {
                "现在": base_time.time(),
                "此时": base_time.time(),
                "马上": base_time.time(),
                "立即": base_time.time(),
                "中午": time(12, 0),
                "正午": time(12, 0),
                "午夜": time(0, 0),
                "半夜": time(0, 0)
            }
            
            for expr, time_obj in special_times.items():
                if expr in text:
                    result["success"] = True
                    result["time"] = time_obj
                    result["expression"] = expr
                    return result
            
        except Exception as e:
            logger.error(f"时间解析失败: {e}")
        
        return result
    
    def _parse_duration(self, text: str) -> Dict[str, Any]:
        """解析时长表达式"""
        result = {"success": False, "duration": None, "expression": ""}
        
        try:
            # 1. 数字+单位格式
            for unit, minutes in self.duration_units.items():
                pattern = rf'(\d+(?:\.\d+)?){unit}'
                match = re.search(pattern, text)
                if match:
                    number = float(match.group(1))
                    duration = int(number * minutes)
                    
                    result["success"] = True
                    result["duration"] = duration
                    result["expression"] = match.group()
                    return result
            
            # 2. 特殊时长表达
            special_durations = {
                "半小时": 30,
                "半个小时": 30,
                "一小时": 60,
                "一个小时": 60,
                "两小时": 120,
                "两个小时": 120,
                "一刻钟": 15,
                "三刻钟": 45,
                "整个上午": 240,  # 4小时
                "整个下午": 240,  # 4小时
                "全天": 480,     # 8小时
                "一整天": 480
            }
            
            for expr, minutes in special_durations.items():
                if expr in text:
                    result["success"] = True
                    result["duration"] = minutes
                    result["expression"] = expr
                    return result
            
            # 3. 时间范围格式 (从X到Y)
            range_pattern = r'从?\s*(\d{1,2})[点时:](\d{0,2})\s*[分]?\s*[到至-]\s*(\d{1,2})[点时:](\d{0,2})\s*[分]?'
            match = re.search(range_pattern, text)
            if match:
                start_hour = int(match.group(1))
                start_minute = int(match.group(2)) if match.group(2) else 0
                end_hour = int(match.group(3))
                end_minute = int(match.group(4)) if match.group(4) else 0
                
                start_time = time(start_hour, start_minute)
                end_time = time(end_hour, end_minute)
                
                # 计算时长
                start_minutes = start_hour * 60 + start_minute
                end_minutes = end_hour * 60 + end_minute
                
                if end_minutes > start_minutes:
                    duration = end_minutes - start_minutes
                    result["success"] = True
                    result["duration"] = duration
                    result["expression"] = match.group()
                    return result
            
        except Exception as e:
            logger.error(f"时长解析失败: {e}")
        
        return result
    
    def format_parsed_result(self, parsed_result: Dict[str, Any]) -> str:
        """格式化解析结果为可读字符串"""
        if not parsed_result["success"]:
            return "未能解析时间信息"
        
        parts = []
        
        if parsed_result["date"]:
            parts.append(f"日期: {parsed_result['date'].strftime('%Y年%m月%d日')}")
        
        if parsed_result["time"]:
            parts.append(f"时间: {parsed_result['time'].strftime('%H:%M')}")
        
        if parsed_result["duration"]:
            hours = parsed_result["duration"] // 60
            minutes = parsed_result["duration"] % 60
            if hours > 0:
                parts.append(f"时长: {hours}小时{minutes}分钟")
            else:
                parts.append(f"时长: {minutes}分钟")
        
        if parsed_result["end_time"]:
            parts.append(f"结束时间: {parsed_result['end_time'].strftime('%H:%M')}")
        
        return ", ".join(parts)
    
    def validate_business_hours(self, parsed_time: time, parsed_date: date = None) -> Dict[str, Any]:
        """验证是否在营业时间内"""
        if parsed_date is None:
            parsed_date = date.today()
        
        # 营业时间规则
        weekday = parsed_date.weekday()  # 0=Monday, 6=Sunday
        
        if weekday < 5:  # 周一到周五
            start_time = time(9, 0)
            end_time = time(18, 0)
        elif weekday == 5:  # 周六
            start_time = time(9, 0)
            end_time = time(12, 0)
        else:  # 周日
            return {
                "valid": False,
                "message": "周日不营业",
                "suggested_times": ["周一至周五 9:00-18:00", "周六 9:00-12:00"]
            }
        
        if start_time <= parsed_time <= end_time:
            return {"valid": True, "message": "时间有效"}
        else:
            return {
                "valid": False,
                "message": f"不在营业时间内，营业时间: {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}",
                "suggested_times": [f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"]
            }