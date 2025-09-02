#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进的意图识别功能
"""

import requests
import json
from typing import Dict, Any

API_BASE = "http://localhost:8000"

def test_chat(message: str, session_id: str = None) -> Dict[str, Any]:
    """
    测试聊天API
    """
    url = f"{API_BASE}/api/chat/"
    payload = {
        "message": message,
        "session_id": session_id,
        "user_id": 1
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return {}

def print_response(response: Dict[str, Any], test_name: str):
    """
    打印响应结果
    """
    print(f"\n=== {test_name} ===")
    print(f"用户消息: {response.get('original_message', 'N/A')}")
    print(f"AI回复: {response.get('response', 'N/A')}")
    print(f"识别意图: {response.get('intent', 'N/A')}")
    print(f"提取实体: {json.dumps(response.get('entities', {}), ensure_ascii=False, indent=2)}")
    print(f"建议操作: {response.get('suggestions', [])}")
    print(f"会话ID: {response.get('session_id', 'N/A')}")
    if response.get('reservation_created'):
        print("✅ 预约已创建")
    print("-" * 50)

def main():
    print("🚀 开始测试改进的意图识别功能")
    
    # 测试场景1：不完整的预约信息 - 只有意图，没有时间
    response1 = test_chat("我想预约会议室")
    print_response(response1, "测试1: 不完整预约信息 - 缺少时间")
    
    session_id = response1.get('session_id')
    
    # 测试场景2：补充时间信息
    if session_id:
        response2 = test_chat("明天下午2点", session_id)
        print_response(response2, "测试2: 补充时间信息")
    
    # 测试场景3：访客预约 - 不完整信息
    response3 = test_chat("我要安排访客来访")
    print_response(response3, "测试3: 访客预约 - 缺少访客信息")
    
    session_id2 = response3.get('session_id')
    
    # 测试场景4：补充访客信息
    if session_id2:
        response4 = test_chat("张先生明天上午10点来访", session_id2)
        print_response(response4, "测试4: 补充访客信息")
    
    # 测试场景5：车位预约 - 不完整信息
    response5 = test_chat("需要预约停车位")
    print_response(response5, "测试5: 车位预约 - 缺少车牌信息")
    
    session_id3 = response5.get('session_id')
    
    # 测试场景6：补充车牌信息
    if session_id3:
        response6 = test_chat("京A12345，明天上午9点", session_id3)
        print_response(response6, "测试6: 补充车牌信息")
    
    # 测试场景7：智能意图推断 - 包含时间但没有明确预约关键词
    response7 = test_chat("明天下午3点有空吗")
    print_response(response7, "测试7: 智能意图推断")
    
    # 测试场景8：完整的预约信息
    response8 = test_chat("我要预约明天下午2点到4点的会议室")
    print_response(response8, "测试8: 完整预约信息")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    main()