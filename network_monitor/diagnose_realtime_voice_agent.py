#!/usr/bin/env python3
"""
realtimeVoiceAgent 诊断工具
用于检查和诊断 realtimeVoiceAgent 的可用性问题
"""

import asyncio
import json
import logging
from chrome_console_executor import ChromeConsoleExecutor

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealtimeVoiceAgentDiagnostic:
    """realtimeVoiceAgent 诊断工具"""
    
    def __init__(self, chrome_host: str = "localhost", chrome_port: int = 9222):
        self.console_executor = ChromeConsoleExecutor(chrome_port, chrome_host)
    
    async def run_diagnostic(self):
        """运行完整的诊断流程"""
        logger.info("开始 realtimeVoiceAgent 诊断...")
        
        # 1. 连接到Chrome DevTools
        logger.info("步骤1: 连接到Chrome DevTools")
        success = await self.console_executor.connect(tab_url_pattern="bot_controller")
        if not success:
            logger.error("无法连接到Chrome DevTools")
            return
        
        # 2. 检查页面基本信息
        await self.check_page_info()
        
        # 3. 检查全局对象
        await self.check_global_objects()
        
        # 4. 检查realtimeVoiceAgent
        await self.check_realtime_voice_agent_detailed()
        
        # 5. 检查可能的替代对象
        await self.check_alternative_objects()
        
        # 6. 检查页面加载状态
        await self.check_page_load_status()
        
        await self.console_executor.disconnect()
        logger.info("诊断完成")
    
    async def check_page_info(self):
        """检查页面基本信息"""
        logger.info("检查页面基本信息...")
        
        # 检查页面URL
        result = await self.console_executor.execute_javascript("window.location.href")
        if result["success"]:
            url = result["result"].get("value", "未知")
            logger.info(f"当前页面URL: {url}")
        
        # 检查页面标题
        result = await self.console_executor.execute_javascript("document.title")
        if result["success"]:
            title = result["result"].get("value", "未知")
            logger.info(f"页面标题: {title}")
    
    async def check_global_objects(self):
        """检查全局对象"""
        logger.info("检查全局对象...")
        
        # 检查window对象上的属性
        result = await self.console_executor.execute_javascript("""
        Object.getOwnPropertyNames(window).filter(name => 
            name.toLowerCase().includes('voice') || 
            name.toLowerCase().includes('agent') ||
            name.toLowerCase().includes('realtime')
        )
        """)
        
        if result["success"]:
            properties = result["result"].get("value", [])
            if properties:
                logger.info(f"找到相关的全局属性: {properties}")
            else:
                logger.warning("未找到相关的全局属性")
    
    async def check_realtime_voice_agent_detailed(self):
        """详细检查realtimeVoiceAgent"""
        logger.info("详细检查 realtimeVoiceAgent...")
        
        # 检查是否存在
        result = await self.console_executor.execute_javascript("typeof realtimeVoiceAgent")
        if result["success"]:
            type_result = result["result"].get("value", "undefined")
            logger.info(f"realtimeVoiceAgent 类型: {type_result}")
            
            if type_result != "undefined":
                # 检查属性
                result = await self.console_executor.execute_javascript("""
                (function() {
                    try {
                        return {
                            hasManager: typeof realtimeManager !== 'undefined',
                            hasGetHistory: typeof realtimeManager?.getHistory !== 'undefined',
                            managerType: typeof realtimeManager,
                            getHistoryType: typeof realtimeManager?.getHistory,
                            getHistoryResult: typeof realtimeManager?.getHistory()
                        };
                    } catch (e) {
                        return { error: e.message };
                    }
                })()
                """)
                
                if result["success"]:
                    details = result["result"].get("value", {})
                    logger.info(f"realtimeVoiceAgent 详细信息: {json.dumps(details, indent=2)}")
            else:
                logger.warning("realtimeVoiceAgent 不存在")
    
    async def check_alternative_objects(self):
        """检查可能的替代对象"""
        logger.info("检查可能的替代对象...")
        
        alternatives = [
            "voiceAgent",
            "realtimeAgent", 
            "speechAgent",
            "conversationAgent",
            "chatAgent"
        ]
        
        for alt in alternatives:
            result = await self.console_executor.execute_javascript(f"typeof {alt}")
            if result["success"]:
                type_result = result["result"].get("value", "undefined")
                if type_result != "undefined":
                    logger.info(f"找到替代对象: {alt} (类型: {type_result})")
    
    async def check_page_load_status(self):
        """检查页面加载状态"""
        logger.info("检查页面加载状态...")
        
        result = await self.console_executor.execute_javascript("""
        ({
            readyState: document.readyState,
            hasJQuery: typeof $ !== 'undefined',
            hasReact: typeof React !== 'undefined',
            hasVue: typeof Vue !== 'undefined',
            scriptsCount: document.scripts.length,
            domContentLoaded: document.readyState === 'complete'
        })
        """)
        
        if result["success"]:
            status = result["result"].get("value", {})
            logger.info(f"页面加载状态: {json.dumps(status, indent=2)}")

async def main():
    """主函数"""
    diagnostic = RealtimeVoiceAgentDiagnostic()
    await diagnostic.run_diagnostic()

if __name__ == "__main__":
    asyncio.run(main())