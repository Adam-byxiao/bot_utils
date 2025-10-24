#!/usr/bin/env python3
"""
检查 realtimeVoiceAgent.session 的完整结构
"""

import asyncio
import json
import logging
from chrome_console_executor import ChromeConsoleExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def inspect_session_structure():
    """检查session对象的完整结构"""
    console_executor = ChromeConsoleExecutor(9222, "localhost")
    
    # 连接到Chrome DevTools
    success = await console_executor.connect(tab_url_pattern="bot_controller")
    if not success:
        logger.error("无法连接到Chrome DevTools")
        return
    
    logger.info("检查 realtimeVoiceAgent.session 的完整结构...")
    
    # 获取session对象的所有属性
    result = await console_executor.execute_javascript("""
    (function() {
        try {
            if (typeof realtimeVoiceAgent === 'undefined' || !realtimeVoiceAgent.session) {
                return { error: 'realtimeVoiceAgent.session 不存在' };
            }
            
            const session = realtimeVoiceAgent.session;
            const result = {
                sessionExists: true,
                sessionType: typeof session,
                sessionConstructor: session.constructor.name,
                ownProperties: Object.getOwnPropertyNames(session),
                allProperties: [],
                methods: [],
                values: {}
            };
            
            // 获取所有属性（包括原型链上的）
            let obj = session;
            while (obj && obj !== Object.prototype) {
                Object.getOwnPropertyNames(obj).forEach(prop => {
                    if (!result.allProperties.includes(prop)) {
                        result.allProperties.push(prop);
                    }
                });
                obj = Object.getPrototypeOf(obj);
            }
            
            // 检查每个属性的类型和值
            result.ownProperties.forEach(prop => {
                try {
                    const value = session[prop];
                    const type = typeof value;
                    
                    if (type === 'function') {
                        result.methods.push(prop);
                    } else {
                        result.values[prop] = {
                            type: type,
                            value: type === 'object' && value !== null ? 
                                   (Array.isArray(value) ? `Array(${value.length})` : 'Object') : 
                                   value
                        };
                    }
                } catch (e) {
                    result.values[prop] = { error: e.message };
                }
            });
            
            return result;
        } catch (e) {
            return { error: e.message };
        }
    })()
    """)
    
    if result["success"]:
        session_info = result["result"].get("value", {})
        logger.info("Session 结构信息:")
        print(json.dumps(session_info, indent=2, ensure_ascii=False))
        
        # 如果有类似history的属性，进一步检查
        if 'values' in session_info:
            for prop, info in session_info['values'].items():
                if 'history' in prop.lower() or 'message' in prop.lower() or 'conversation' in prop.lower():
                    logger.info(f"发现可能相关的属性: {prop} = {info}")
    
    # 检查是否有其他可能的历史记录存储位置
    logger.info("检查其他可能的历史记录位置...")
    
    result = await console_executor.execute_javascript("""
    (function() {
        try {
            const agent = realtimeVoiceAgent;
            const locations = {};
            
            // 检查常见的历史记录属性名
            const historyProps = ['history', 'messages', 'conversation', 'chat', 'log', 'events', 'transcript'];
            
            historyProps.forEach(prop => {
                // 检查agent级别
                if (agent[prop] !== undefined) {
                    locations[`agent.${prop}`] = {
                        type: typeof agent[prop],
                        isArray: Array.isArray(agent[prop]),
                        length: Array.isArray(agent[prop]) ? agent[prop].length : 'N/A'
                    };
                }
                
                // 检查session级别
                if (agent.session && agent.session[prop] !== undefined) {
                    locations[`session.${prop}`] = {
                        type: typeof agent.session[prop],
                        isArray: Array.isArray(agent.session[prop]),
                        length: Array.isArray(agent.session[prop]) ? agent.session[prop].length : 'N/A'
                    };
                }
            });
            
            return locations;
        } catch (e) {
            return { error: e.message };
        }
    })()
    """)
    
    if result["success"]:
        locations = result["result"].get("value", {})
        if locations:
            logger.info("找到的可能历史记录位置:")
            print(json.dumps(locations, indent=2, ensure_ascii=False))
        else:
            logger.warning("未找到任何历史记录相关的属性")
    
    await console_executor.disconnect()

if __name__ == "__main__":
    asyncio.run(inspect_session_structure())