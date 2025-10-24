#!/usr/bin/env python3
"""
测试 realtimeVoiceAgent.session 的访问
"""

import asyncio
import json
import logging
from chrome_console_executor import ChromeConsoleExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_session_access():
    """测试session访问"""
    console_executor = ChromeConsoleExecutor(9222, "localhost")
    
    # 连接到Chrome DevTools
    success = await console_executor.connect(tab_url_pattern="bot_controller")
    if not success:
        logger.error("无法连接到Chrome DevTools")
        return
    
    # 测试1: 基本存在性检查
    logger.info("测试1: 基本存在性检查")
    result = await console_executor.execute_javascript("""
    ({
        agentExists: typeof realtimeVoiceAgent !== 'undefined',
        agentType: typeof realtimeVoiceAgent,
        sessionExists: typeof realtimeVoiceAgent !== 'undefined' && typeof realtimeVoiceAgent.session !== 'undefined',
        sessionType: typeof realtimeVoiceAgent !== 'undefined' ? typeof realtimeVoiceAgent.session : 'N/A'
    })
    """)
    
    if result["success"]:
        print("基本检查结果:", json.dumps(result["result"].get("value", {}), indent=2))
    
    # 测试2: 尝试访问session属性
    logger.info("测试2: 尝试访问session属性")
    result = await console_executor.execute_javascript("""
    (function() {
        try {
            if (typeof realtimeVoiceAgent === 'undefined') {
                return { error: 'realtimeVoiceAgent不存在' };
            }
            
            const agent = realtimeVoiceAgent;
            const session = agent.session;
            
            if (!session) {
                return { error: 'session为null或undefined' };
            }
            
            return {
                success: true,
                sessionConstructor: session.constructor.name,
                sessionProps: Object.getOwnPropertyNames(session),
                sessionKeys: Object.keys(session)
            };
        } catch (e) {
            return { error: e.message, stack: e.stack };
        }
    })()
    """)
    
    if result["success"]:
        print("Session访问结果:", json.dumps(result["result"].get("value", {}), indent=2))
    
    # 测试3: 检查具体的history属性
    logger.info("测试3: 检查history属性")
    result = await console_executor.execute_javascript("""
    (function() {
        try {
            const agent = realtimeVoiceAgent;
            if (!agent || !agent.session) {
                return { error: 'agent或session不存在' };
            }
            
            const session = agent.session;
            
            return {
                hasHistory: 'history' in session,
                historyValue: session.history,
                historyType: typeof session.history,
                historyDescriptor: Object.getOwnPropertyDescriptor(session, 'history'),
                allProps: Object.getOwnPropertyNames(session).filter(p => p.toLowerCase().includes('hist') || p.toLowerCase().includes('message') || p.toLowerCase().includes('log'))
            };
        } catch (e) {
            return { error: e.message };
        }
    })()
    """)
    
    if result["success"]:
        print("History检查结果:", json.dumps(result["result"].get("value", {}), indent=2))
    
    # 测试4: 检查原型链上的属性
    logger.info("测试4: 检查原型链属性")
    result = await console_executor.execute_javascript("""
    (function() {
        try {
            const session = realtimeVoiceAgent.session;
            if (!session) return { error: 'session不存在' };
            
            const protoProps = [];
            let obj = session;
            let level = 0;
            
            while (obj && level < 5) {
                const props = Object.getOwnPropertyNames(obj);
                protoProps.push({
                    level: level,
                    constructor: obj.constructor.name,
                    properties: props.filter(p => p.toLowerCase().includes('hist') || p.toLowerCase().includes('message'))
                });
                obj = Object.getPrototypeOf(obj);
                level++;
            }
            
            return { prototypeChain: protoProps };
        } catch (e) {
            return { error: e.message };
        }
    })()
    """)
    
    if result["success"]:
        print("原型链检查结果:", json.dumps(result["result"].get("value", {}), indent=2))
    
    await console_executor.disconnect()

if __name__ == "__main__":
    asyncio.run(test_session_access())