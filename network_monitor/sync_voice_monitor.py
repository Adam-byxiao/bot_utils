#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步语音代理监控器
为GUI应用程序提供完全同步的接口，避免异步事件循环冲突
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime

from remote_voice_agent_monitor import RemoteVoiceAgentMonitor
from realtime_voice_agent_parser import VoiceMessage, SessionSummary

logger = logging.getLogger(__name__)

class SyncVoiceMonitor:
    """同步语音代理监控器
    
    这个类提供了RemoteVoiceAgentMonitor的同步接口，
    通过在独立线程中运行异步操作来避免事件循环冲突。
    """
    
    def __init__(self, chrome_host: str = "localhost", chrome_port: int = 9222,
                 output_dir: str = "voice_output"):
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        self.output_dir = output_dir
        self.monitor = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.loop = None
        self.loop_thread = None
        self.is_connected = False
        
    def _run_async_in_thread(self, coro):
        """在独立线程中运行异步协程"""
        if self.loop is None or self.loop.is_closed():
            self._start_event_loop()
        
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=30)  # 30秒超时
        except Exception as e:
            logger.error(f"异步操作失败: {e}")
            return None
    
    def _start_event_loop(self):
        """启动独立的事件循环线程"""
        if self.loop_thread and self.loop_thread.is_alive():
            return
            
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.loop.run_forever()
            finally:
                self.loop.close()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
        
        # 等待事件循环启动
        while self.loop is None:
            time.sleep(0.01)
    
    def connect_to_device(self) -> bool:
        """连接到远程设备（同步）"""
        try:
            logger.info("正在连接到远程设备")
            
            # 创建监控器实例
            self.monitor = RemoteVoiceAgentMonitor(
                chrome_host=self.chrome_host,
                chrome_port=self.chrome_port,
                output_dir=self.output_dir
            )
            
            # 在独立线程中运行连接操作
            async def connect_async():
                success = await self.monitor.connect_to_remote_device()
                if success:
                    # 检查语音代理可用性
                    agent_available = await self.monitor.check_realtime_voice_agent()
                    return agent_available
                return False
            
            result = self._run_async_in_thread(connect_async())
            self.is_connected = result if result is not None else False
            
            if self.is_connected:
                logger.info("成功连接到远程设备")
            else:
                logger.error("连接到远程设备失败")
                
            return self.is_connected
            
        except Exception as e:
            logger.error(f"连接过程中发生错误: {e}")
            self.is_connected = False
            return False
    
    def get_session_history(self) -> Optional[List[Dict]]:
        """获取会话历史（同步）"""
        if not self.is_connected or not self.monitor:
            logger.warning("未连接到设备，无法获取会话历史")
            return None
        
        try:
            result = self._run_async_in_thread(self.monitor.get_session_history())
            return result
        except Exception as e:
            logger.error(f"获取会话历史失败: {e}")
            return None
    
    def parse_and_classify_data(self, history_data: List[Dict]) -> Tuple[List[VoiceMessage], List[VoiceMessage], SessionSummary]:
        """解析和分类数据（同步）"""
        if not self.monitor:
            return [], [], SessionSummary()
        
        try:
            return self.monitor.parse_and_classify_data(history_data)
        except Exception as e:
            logger.error(f"解析数据失败: {e}")
            return [], [], SessionSummary()
    
    def export_classified_data(self, input_messages: List[VoiceMessage], 
                              output_messages: List[VoiceMessage],
                              session_summary: SessionSummary) -> Dict[str, str]:
        """导出分类数据（同步）"""
        if not self.monitor:
            return {}
        
        try:
            return self.monitor.export_classified_data(input_messages, output_messages, session_summary)
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return {}
    
    def run_complete_monitoring_cycle(self) -> Dict[str, any]:
        """运行完整的监控周期（同步）"""
        if not self.is_connected or not self.monitor:
            return {"success": False, "error": "未连接到设备"}
        
        try:
            result = self._run_async_in_thread(self.monitor.run_complete_monitoring_cycle())
            return result if result is not None else {"success": False, "error": "监控周期执行失败"}
        except Exception as e:
            logger.error(f"监控周期执行失败: {e}")
            return {"success": False, "error": str(e)}
    
    def get_session_info(self) -> Optional[Dict]:
        """获取会话信息（同步）"""
        if not self.is_connected or not self.monitor:
            return None
        
        try:
            result = self._run_async_in_thread(self.monitor.get_session_info())
            return result
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return None
    
    def disconnect(self):
        """断开连接并清理资源"""
        try:
            if self.monitor and self.is_connected:
                # 在独立线程中运行断开连接操作
                async def disconnect_async():
                    if hasattr(self.monitor, 'console_executor') and self.monitor.console_executor:
                        await self.monitor.console_executor.disconnect()
                
                self._run_async_in_thread(disconnect_async())
            
            self.is_connected = False
            self.monitor = None
            
            # 停止事件循环
            if self.loop and not self.loop.is_closed():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            # 关闭线程池
            if self.executor:
                self.executor.shutdown(wait=False)
                
            logger.info("已断开连接并清理资源")
            
        except Exception as e:
            logger.error(f"断开连接时发生错误: {e}")
    
    def __del__(self):
        """析构函数，确保资源被正确清理"""
        try:
            self.disconnect()
        except:
            pass

def main():
    """测试同步监控器"""
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = SyncVoiceMonitor()
    
    try:
        # 连接到设备
        if monitor.connect_to_device():
            print("成功连接到设备")
            
            # 获取会话历史
            history = monitor.get_session_history()
            if history:
                print(f"获取到 {len(history)} 条历史记录")
            else:
                print("未获取到历史记录")
        else:
            print("连接到设备失败")
    
    except KeyboardInterrupt:
        print("\n用户中断")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()