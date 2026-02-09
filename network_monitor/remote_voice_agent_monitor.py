"""
远程语音代理监控器
整合 Chrome DevTools 连接、JavaScript 执行、数据解析和文件导出功能
用于通过 SSH 端口转发连接远程设备，获取并解析 realtimeManager.getHistory() 数据
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from chrome_console_executor import ChromeConsoleExecutor
from realtime_voice_agent_parser import RealtimeVoiceAgentParser, VoiceMessage, SessionSummary
from voice_data_exporter import VoiceDataExporter


class RemoteVoiceAgentMonitor:
    """远程语音代理监控器"""
    
    def __init__(self, chrome_host: str = "localhost", chrome_port: int = 9222,
                 output_dir: str = "voice_output"):
        """
        初始化监控器
        
        Args:
            chrome_host: Chrome DevTools 主机地址
            chrome_port: Chrome DevTools 端口
            output_dir: 输出目录
        """
        self.chrome_host = chrome_host
        self.chrome_port = chrome_port
        self.output_dir = output_dir
        
        # 初始化组件
        self.console_executor = ChromeConsoleExecutor(chrome_port, chrome_host)
        self.parser = RealtimeVoiceAgentParser()
        self.exporter = VoiceDataExporter(output_dir)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
    
    async def connect_to_remote_device(self) -> bool:
        """
        连接到远程设备的 Chrome DevTools
        
        Returns:
            连接是否成功
        """
        try:
            self.logger.info(f"正在连接到远程设备 {self.chrome_host}:{self.chrome_port}")
            success = await self.console_executor.connect(tab_url_pattern="bot_controller")
            
            if success:
                self.logger.info("成功连接到远程设备")
                return True
            else:
                self.logger.error("连接远程设备失败")
                return False
                
        except Exception as e:
            self.logger.error(f"连接远程设备时发生错误: {e}")
            return False
    
    async def check_realtime_voice_agent(self) -> bool:
        """
        检查 realtimeVoiceAgent 是否可用
        
        Returns:
            realtimeVoiceAgent 是否可用
        """
        try:
            self.logger.info("检查 realtimeVoiceAgent 可用性")
            result = await self.console_executor.check_realtime_voice_agent_availability()
            
            if result:
                self.logger.info("realtimeVoiceAgent 可用")
                return True
            else:
                self.logger.warning("realtimeVoiceAgent 不可用")
                return False
                
        except Exception as e:
            self.logger.error(f"检查 realtimeVoiceAgent 时发生错误: {e}")
            return False
    
    async def get_session_history(self) -> Optional[List[Dict]]:
        """
        获取 realtimeManager.getHistory() 数据
        
        Returns:
            会话历史数据，如果获取失败则返回 None
        """
        try:
            self.logger.info("调用 realtimeManager.getHistory() 获取数据")
            result = await self.console_executor.get_realtime_voice_agent_history()
            
            if result.get("success", False):
                # 从 result.result.value 中获取实际的数组数据
                result_data = result.get("result", {})
                if result_data.get("type") == "object" and "value" in result_data:
                    history_data = result_data["value"]
                else:
                    history_data = []
                self.logger.info(f"成功获取 {len(history_data)} 条历史记录")
                return history_data
            else:
                error_msg = result.get("error", "未知错误")
                self.logger.error(f"获取会话历史失败: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取会话历史时发生错误: {e}")
            return None
    
    def parse_and_classify_data(self, history_data: List[Dict]) -> Tuple[List[VoiceMessage], List[VoiceMessage], SessionSummary]:
        """
        解析并分类历史数据
        
        Args:
            history_data: 原始历史数据
            
        Returns:
            (用户输入消息, 助手输出消息, 会话摘要)
        """
        try:
            self.logger.info("解析和分类历史数据")
            
            # 解析数据
            parse_success = self.parser.parse_history_data(history_data)
            if not parse_success:
                self.logger.error("解析历史数据失败")
                return [], [], None
            
            # 获取所有解析的消息
            all_messages = self.parser.get_all_messages()
            self.logger.info(f"解析得到 {len(all_messages)} 条消息")
            
            # 分类消息
            input_messages = self.parser.get_input_messages()
            output_messages = self.parser.get_output_messages()
            
            self.logger.info(f"分类结果: {len(input_messages)} 条输入, {len(output_messages)} 条输出")
            
            # 生成会话摘要
            session_summary = self.parser.get_session_summary()
            
            return input_messages, output_messages, session_summary
            
        except Exception as e:
            self.logger.error(f"解析和分类数据时发生错误: {e}")
            return [], [], None
    
    def export_classified_data(self, input_messages: List[VoiceMessage], 
                              output_messages: List[VoiceMessage],
                              session_summary: SessionSummary) -> Dict[str, str]:
        """
        导出分类后的数据到本地文件
        
        Args:
            input_messages: 用户输入消息
            output_messages: 助手输出消息
            session_summary: 会话摘要
            
        Returns:
            导出文件路径字典
        """
        try:
            self.logger.info("导出分类后的数据到本地文件")
            
            # 导出分类文件
            file_paths = self.exporter.export_input_output_files(
                input_messages, output_messages, session_summary
            )
            
            # 导出合并对话文件
            combined_file = self.exporter.export_combined_file(
                input_messages, output_messages, session_summary
            )
            file_paths["combined_file"] = combined_file
            
            self.logger.info("数据导出完成")
            for file_type, file_path in file_paths.items():
                if file_path:
                    self.logger.info(f"  {file_type}: {file_path}")
            
            return file_paths
            
        except Exception as e:
            self.logger.error(f"导出数据时发生错误: {e}")
            return {}
    
    async def run_complete_monitoring_cycle(self) -> Dict[str, any]:
        """
        运行完整的监控周期
        
        Returns:
            监控结果字典
        """
        result = {
            "success": False,
            "timestamp": datetime.now().isoformat(),
            "steps_completed": [],
            "errors": [],
            "file_paths": {},
            "statistics": {}
        }
        
        try:
            # 步骤 1: 连接远程设备
            self.logger.info("=== 开始完整监控周期 ===")
            if not await self.connect_to_remote_device():
                result["errors"].append("连接远程设备失败")
                return result
            result["steps_completed"].append("连接远程设备")
            
            # 步骤 2: 检查 realtimeVoiceAgent（仅记录状态，不阻止继续执行）
            agent_available = await self.check_realtime_voice_agent()
            if agent_available:
                result["steps_completed"].append("检查 realtimeVoiceAgent - 可用")
            else:
                result["steps_completed"].append("检查 realtimeVoiceAgent - 不可用，但继续尝试获取数据")
            
            # 步骤 3: 获取会话历史
            history_data = await self.get_session_history()
            if history_data is None:
                result["errors"].append("获取会话历史失败")
                return result
            elif len(history_data) == 0:
                result["steps_completed"].append("获取会话历史 - 无历史记录")
            else:
                result["steps_completed"].append(f"获取会话历史 - {len(history_data)} 条记录")
            
            # 步骤 4: 解析和分类数据
            input_messages, output_messages, session_summary = self.parse_and_classify_data(history_data)
            total_messages = len(input_messages) + len(output_messages)
            if total_messages == 0:
                result["steps_completed"].append("解析和分类数据 - 无有效消息")
            else:
                result["steps_completed"].append(f"解析和分类数据 - {total_messages} 条消息")
            
            # 步骤 5: 导出数据
            file_paths = self.export_classified_data(input_messages, output_messages, session_summary)
            if not file_paths:
                result["errors"].append("导出数据失败")
                return result
            result["steps_completed"].append("导出数据")
            result["file_paths"] = file_paths
            
            # 生成统计信息
            result["statistics"] = {
                "total_messages": len(input_messages) + len(output_messages),
                "input_messages": len(input_messages),
                "output_messages": len(output_messages),
                "session_summary": session_summary.to_dict() if session_summary else None
            }
            
            result["success"] = True
            self.logger.info("=== 监控周期完成 ===")
            
        except Exception as e:
            error_msg = f"监控周期执行错误: {e}"
            self.logger.error(error_msg)
            result["errors"].append(error_msg)
        
        finally:
            # 断开连接
            try:
                await self.console_executor.disconnect()
                self.logger.info("已断开与远程设备的连接")
            except Exception as e:
                self.logger.warning(f"断开连接时发生错误: {e}")
        
        return result
    
    async def get_session_info(self) -> Optional[Dict]:
        """
        获取会话信息
        
        Returns:
            会话信息字典
        """
        try:
            self.logger.info("获取会话信息")
            result = await self.console_executor.get_session_info()
            
            if result.get("success", False):
                session_info = result.get("data", {})
                self.logger.info("成功获取会话信息")
                return session_info
            else:
                error_msg = result.get("error", "未知错误")
                self.logger.error(f"获取会话信息失败: {error_msg}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取会话信息时发生错误: {e}")
            return None


async def main():
    """主函数示例"""
    # 创建监控器实例（使用 SSH 端口转发的默认配置）
    monitor = RemoteVoiceAgentMonitor(
        chrome_host="localhost",  # SSH 端口转发后的本地地址
        chrome_port=9222,        # SSH 端口转发的端口
        output_dir="voice_output"
    )
    
    # 运行完整监控周期
    result = await monitor.run_complete_monitoring_cycle()
    
    # 输出结果
    print("\n=== 监控结果 ===")
    print(f"成功: {result['success']}")
    print(f"完成步骤: {', '.join(result['steps_completed'])}")
    
    if result['errors']:
        print(f"错误: {', '.join(result['errors'])}")
    
    if result['file_paths']:
        print("\n导出文件:")
        for file_type, file_path in result['file_paths'].items():
            if file_path:
                print(f"  {file_type}: {file_path}")
    
    if result['statistics']:
        stats = result['statistics']
        print(f"\n统计信息:")
        print(f"  总消息数: {stats['total_messages']}")
        print(f"  用户输入: {stats['input_messages']}")
        print(f"  助手输出: {stats['output_messages']}")


if __name__ == "__main__":
    asyncio.run(main())