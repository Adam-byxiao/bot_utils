#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Domain
Chrome DevTools Performance域的实现，用于性能监控和分析
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceDomain:
    """Performance域实现"""
    
    def __init__(self, client):
        """
        初始化Performance域
        
        Args:
            client: ChromeDevToolsClient实例
        """
        self.client = client
        self.domain_name = "Performance"
        self.metrics_handlers = []
    
    async def enable(self, time_domain: Optional[str] = None) -> bool:
        """
        启用Performance域
        
        Args:
            time_domain: 时间域（'timeTicks' 或 'threadTicks'）
        """
        params = {}
        if time_domain is not None:
            params["timeDomain"] = time_domain
        
        result = await self.client.execute_command("Performance.enable", params)
        
        if result["success"]:
            # 注册事件处理器
            self.client.add_event_handler("Performance.metrics", self._handle_metrics)
            
        return result["success"]
    
    async def disable(self) -> bool:
        """禁用Performance域"""
        return await self.client.disable_domain(self.domain_name)
    
    async def _handle_metrics(self, params: Dict):
        """处理性能指标事件"""
        for handler in self.metrics_handlers:
            try:
                await handler(params)
            except Exception as e:
                logger.error(f"性能指标处理器执行失败: {e}")
    
    def add_metrics_handler(self, handler):
        """添加性能指标处理器"""
        self.metrics_handlers.append(handler)
    
    async def get_metrics(self) -> Dict:
        """获取当前性能指标"""
        return await self.client.execute_command("Performance.getMetrics")
    
    async def set_time_domain(self, time_domain: str) -> Dict:
        """
        设置时间域
        
        Args:
            time_domain: 时间域（'timeTicks' 或 'threadTicks'）
        """
        params = {"timeDomain": time_domain}
        return await self.client.execute_command("Performance.setTimeDomain", params)
    
    async def start_precise_coverage(self, call_count: bool = False,
                                   detailed: bool = False,
                                   allow_triggered_updates: bool = False) -> Dict:
        """
        开始精确覆盖率收集
        
        Args:
            call_count: 是否收集调用计数
            detailed: 是否收集详细信息
            allow_triggered_updates: 是否允许触发更新
        """
        params = {
            "callCount": call_count,
            "detailed": detailed,
            "allowTriggeredUpdates": allow_triggered_updates
        }
        return await self.client.execute_command("Profiler.startPreciseCoverage", params)
    
    async def stop_precise_coverage(self) -> Dict:
        """停止精确覆盖率收集"""
        return await self.client.execute_command("Profiler.stopPreciseCoverage")
    
    async def take_precise_coverage(self) -> Dict:
        """获取精确覆盖率数据"""
        return await self.client.execute_command("Profiler.takePreciseCoverage")
    
    async def start_sampling(self, sampling_interval: Optional[int] = None) -> Dict:
        """
        开始CPU采样
        
        Args:
            sampling_interval: 采样间隔（微秒）
        """
        params = {}
        if sampling_interval is not None:
            params["samplingInterval"] = sampling_interval
        
        return await self.client.execute_command("Profiler.start", params)
    
    async def stop_sampling(self) -> Dict:
        """停止CPU采样并获取结果"""
        return await self.client.execute_command("Profiler.stop")
    
    async def get_best_effort_coverage(self) -> Dict:
        """获取最佳努力覆盖率数据"""
        return await self.client.execute_command("Profiler.getBestEffortCoverage")
    
    async def start_heap_sampling(self, sampling_interval: Optional[float] = None,
                                 include_objects_collected_by_major_gc: bool = False,
                                 include_objects_collected_by_minor_gc: bool = False) -> Dict:
        """
        开始堆采样
        
        Args:
            sampling_interval: 采样间隔
            include_objects_collected_by_major_gc: 是否包含主要GC收集的对象
            include_objects_collected_by_minor_gc: 是否包含次要GC收集的对象
        """
        params = {
            "includeObjectsCollectedByMajorGC": include_objects_collected_by_major_gc,
            "includeObjectsCollectedByMinorGC": include_objects_collected_by_minor_gc
        }
        if sampling_interval is not None:
            params["samplingInterval"] = sampling_interval
        
        return await self.client.execute_command("HeapProfiler.startSampling", params)
    
    async def stop_heap_sampling(self) -> Dict:
        """停止堆采样并获取结果"""
        return await self.client.execute_command("HeapProfiler.stopSampling")
    
    async def take_heap_snapshot(self, report_progress: bool = False,
                               treat_global_objects_as_roots: bool = False,
                               capture_numeric_value: bool = False) -> Dict:
        """
        获取堆快照
        
        Args:
            report_progress: 是否报告进度
            treat_global_objects_as_roots: 是否将全局对象视为根
            capture_numeric_value: 是否捕获数值
        """
        params = {
            "reportProgress": report_progress,
            "treatGlobalObjectsAsRoots": treat_global_objects_as_roots,
            "captureNumericValue": capture_numeric_value
        }
        return await self.client.execute_command("HeapProfiler.takeHeapSnapshot", params)
    
    async def collect_garbage(self) -> Dict:
        """强制垃圾回收"""
        return await self.client.execute_command("HeapProfiler.collectGarbage")
    
    async def get_object_by_heap_object_id(self, object_id: str,
                                         object_group: Optional[str] = None) -> Dict:
        """
        通过堆对象ID获取对象
        
        Args:
            object_id: 堆对象ID
            object_group: 对象组
        """
        params = {"objectId": object_id}
        if object_group is not None:
            params["objectGroup"] = object_group
        
        return await self.client.execute_command("HeapProfiler.getObjectByHeapObjectId", params)
    
    async def add_inspected_heap_object(self, heap_object_id: str) -> Dict:
        """
        添加检查的堆对象
        
        Args:
            heap_object_id: 堆对象ID
        """
        params = {"heapObjectId": heap_object_id}
        return await self.client.execute_command("HeapProfiler.addInspectedHeapObject", params)
    
    async def get_heap_object_id(self, object_id: str) -> Dict:
        """
        获取对象的堆对象ID
        
        Args:
            object_id: 对象ID
        """
        params = {"objectId": object_id}
        return await self.client.execute_command("HeapProfiler.getHeapObjectId", params)