#!/usr/bin/env python3
"""
实时监控 realtimeVoiceAgent 状态变化
"""

import asyncio
import json
import logging
from datetime import datetime
from chrome_console_executor import ChromeConsoleExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealtimeVoiceAgentMonitor:
    def __init__(self):
        self.console_executor = ChromeConsoleExecutor(9222, "localhost")
        self.last_state = None
    
    async def get_current_state(self):
        """获取当前状态"""
        result = await self.console_executor.execute_javascript("""
        (function() {
            try {
                const agent = realtimeVoiceAgent;
                if (typeof agent === 'undefined') {
                    return { exists: false };
                }
                
                return {
                    exists: true,
                    type: typeof agent,
                    hasSession: typeof agent.session !== 'undefined',
                    sessionType: typeof agent.session,
                    sessionState: agent.session ? {
                        hasHistory: typeof agent.session.history !== 'undefined',
                        historyType: typeof agent.session.history,
                        historyLength: Array.isArray(agent.session.history) ? agent.session.history.length : 'N/A',
                        sessionProps: Object.getOwnPropertyNames(agent.session || {})
                    } : null,
                    agentProps: Object.getOwnPropertyNames(agent),
                    timestamp: new Date().toISOString()
                };
            } catch (e) {
                return { error: e.message, timestamp: new Date().toISOString() };
            }
        })()
        """)
        
        if result["success"]:
            return result["result"].get("value", {})
        else:
            return {"error": "JavaScript执行失败"}
    
    async def monitor_loop(self, duration_seconds=60, check_interval=2):
        """监控循环"""
        logger.info(f"开始监控 realtimeVoiceAgent，持续 {duration_seconds} 秒，每 {check_interval} 秒检查一次")
        
        # 连接到Chrome DevTools
        success = await self.console_executor.connect(tab_url_pattern="bot_controller")
        if not success:
            logger.error("无法连接到Chrome DevTools")
            return
        
        start_time = datetime.now()
        check_count = 0
        
        try:
            while (datetime.now() - start_time).total_seconds() < duration_seconds:
                check_count += 1
                current_state = await self.get_current_state()
                
                # 检查状态是否发生变化
                if current_state != self.last_state:
                    logger.info(f"检查 #{check_count} - 状态发生变化:")
                    print(json.dumps(current_state, indent=2, ensure_ascii=False))
                    
                    # 如果发现history存在，立即获取内容
                    if (current_state.get('sessionState', {}) and 
                        current_state['sessionState'].get('hasHistory', False)):
                        await self.capture_history()
                    
                    self.last_state = current_state
                else:
                    logger.info(f"检查 #{check_count} - 状态无变化")
                
                await asyncio.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("监控被用户中断")
        
        finally:
            await self.console_executor.disconnect()
            logger.info("监控结束")
    
    async def capture_history(self):
        """捕获历史记录内容"""
        logger.info("发现history存在，正在捕获内容...")
        
        result = await self.console_executor.execute_javascript("""
        (function() {
            try {
                if (realtimeVoiceAgent.session && realtimeVoiceAgent.session.history) {
                    return {
                        success: true,
                        history: realtimeVoiceAgent.session.history,
                        length: realtimeVoiceAgent.session.history.length
                    };
                }
                return { success: false, reason: 'history不存在' };
            } catch (e) {
                return { success: false, error: e.message };
            }
        })()
        """)
        
        if result["success"]:
            history_data = result["result"].get("value", {})
            if history_data.get("success"):
                logger.info(f"成功捕获历史记录，长度: {history_data.get('length', 0)}")
                
                # 保存到文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"captured_history_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(history_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"历史记录已保存到: {filename}")
            else:
                logger.warning(f"捕获历史记录失败: {history_data}")

async def main():
    """主函数"""
    monitor = RealtimeVoiceAgentMonitor()
    
    print("开始监控 realtimeVoiceAgent 状态变化...")
    print("请在Bot Controller页面中进行语音对话以触发状态变化")
    print("按 Ctrl+C 停止监控")
    
    await monitor.monitor_loop(duration_seconds=300, check_interval=2)  # 监控5分钟

if __name__ == "__main__":
    asyncio.run(main())