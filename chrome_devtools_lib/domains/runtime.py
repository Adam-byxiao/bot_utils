#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Runtime Domain
Chrome DevTools Runtime域的实现，用于JavaScript执行和调试
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RuntimeDomain:
    """Runtime域实现"""
    
    def __init__(self, client):
        """
        初始化Runtime域
        
        Args:
            client: ChromeDevToolsClient实例
        """
        self.client = client
        self.domain_name = "Runtime"
    
    async def enable(self) -> bool:
        """启用Runtime域"""
        return await self.client.enable_domain(self.domain_name)
    
    async def disable(self) -> bool:
        """禁用Runtime域"""
        return await self.client.disable_domain(self.domain_name)
    
    async def evaluate(self, expression: str, 
                      return_by_value: bool = True,
                      generate_preview: bool = True,
                      user_gesture: bool = True,
                      await_promise: bool = True,
                      execution_context_id: Optional[int] = None,
                      object_group: Optional[str] = None,
                      include_command_line_api: bool = False,
                      silent: bool = False,
                      context_id: Optional[int] = None,
                      throw_on_side_effect: bool = False,
                      timeout: Optional[int] = None) -> Dict:
        """
        在Runtime中执行JavaScript表达式
        
        Args:
            expression: 要执行的JavaScript表达式
            return_by_value: 是否返回值而不是对象引用
            generate_preview: 是否生成预览
            user_gesture: 是否作为用户手势执行
            await_promise: 是否等待Promise解析
            execution_context_id: 执行上下文ID
            object_group: 对象组名
            include_command_line_api: 是否包含命令行API
            silent: 是否静默执行（不触发异常事件）
            context_id: 上下文ID（已弃用，使用execution_context_id）
            throw_on_side_effect: 是否在副作用时抛出异常
            timeout: 超时时间（毫秒）
            
        Returns:
            执行结果字典
        """
        params = {
            "expression": expression,
            "returnByValue": return_by_value,
            "generatePreview": generate_preview,
            "userGesture": user_gesture,
            "awaitPromise": await_promise,
            "includeCommandLineAPI": include_command_line_api,
            "silent": silent,
            "throwOnSideEffect": throw_on_side_effect
        }
        
        # 添加可选参数
        if execution_context_id is not None:
            params["executionContextId"] = execution_context_id
        if object_group is not None:
            params["objectGroup"] = object_group
        if context_id is not None:
            params["contextId"] = context_id
        if timeout is not None:
            params["timeout"] = timeout
        
        try:
            response = await self.client.execute_command("Runtime.evaluate", params)
            
            if not response["success"]:
                return response
            
            result = response["result"]
            
            # 检查是否有异常
            if result.get('exceptionDetails'):
                logger.error(f"JavaScript执行异常: {result['exceptionDetails']}")
                return {
                    "success": False,
                    "error": "JavaScript执行异常",
                    "exception": result['exceptionDetails'],
                    "timestamp": datetime.now().isoformat()
                }
            
            return {
                "success": True,
                "result": result.get('result', {}),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"执行JavaScript失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def call_function_on(self, function_declaration: str,
                              object_id: Optional[str] = None,
                              arguments: Optional[list] = None,
                              silent: bool = False,
                              return_by_value: bool = True,
                              generate_preview: bool = False,
                              user_gesture: bool = False,
                              await_promise: bool = False,
                              execution_context_id: Optional[int] = None,
                              object_group: Optional[str] = None) -> Dict:
        """
        在指定对象上调用函数
        
        Args:
            function_declaration: 函数声明
            object_id: 目标对象ID
            arguments: 函数参数
            silent: 是否静默执行
            return_by_value: 是否返回值
            generate_preview: 是否生成预览
            user_gesture: 是否作为用户手势
            await_promise: 是否等待Promise
            execution_context_id: 执行上下文ID
            object_group: 对象组
            
        Returns:
            调用结果
        """
        params = {
            "functionDeclaration": function_declaration,
            "silent": silent,
            "returnByValue": return_by_value,
            "generatePreview": generate_preview,
            "userGesture": user_gesture,
            "awaitPromise": await_promise
        }
        
        if object_id is not None:
            params["objectId"] = object_id
        if arguments is not None:
            params["arguments"] = arguments
        if execution_context_id is not None:
            params["executionContextId"] = execution_context_id
        if object_group is not None:
            params["objectGroup"] = object_group
        
        return await self.client.execute_command("Runtime.callFunctionOn", params)
    
    async def get_properties(self, object_id: str,
                           own_properties: bool = False,
                           accessor_properties_only: bool = False,
                           generate_preview: bool = False,
                           non_indexed_properties_only: bool = False) -> Dict:
        """
        获取对象属性
        
        Args:
            object_id: 对象ID
            own_properties: 是否只获取自有属性
            accessor_properties_only: 是否只获取访问器属性
            generate_preview: 是否生成预览
            non_indexed_properties_only: 是否只获取非索引属性
            
        Returns:
            属性列表
        """
        params = {
            "objectId": object_id,
            "ownProperties": own_properties,
            "accessorPropertiesOnly": accessor_properties_only,
            "generatePreview": generate_preview,
            "nonIndexedPropertiesOnly": non_indexed_properties_only
        }
        
        return await self.client.execute_command("Runtime.getProperties", params)
    
    async def release_object(self, object_id: str) -> Dict:
        """释放对象引用"""
        params = {"objectId": object_id}
        return await self.client.execute_command("Runtime.releaseObject", params)
    
    async def release_object_group(self, object_group: str) -> Dict:
        """释放对象组"""
        params = {"objectGroup": object_group}
        return await self.client.execute_command("Runtime.releaseObjectGroup", params)
    
    async def compile_script(self, expression: str,
                           source_url: str,
                           persist_script: bool = False,
                           execution_context_id: Optional[int] = None) -> Dict:
        """
        编译脚本
        
        Args:
            expression: 脚本表达式
            source_url: 源URL
            persist_script: 是否持久化脚本
            execution_context_id: 执行上下文ID
            
        Returns:
            编译结果
        """
        params = {
            "expression": expression,
            "sourceURL": source_url,
            "persistScript": persist_script
        }
        
        if execution_context_id is not None:
            params["executionContextId"] = execution_context_id
        
        return await self.client.execute_command("Runtime.compileScript", params)
    
    async def run_script(self, script_id: str,
                        execution_context_id: Optional[int] = None,
                        object_group: Optional[str] = None,
                        silent: bool = False,
                        include_command_line_api: bool = False,
                        return_by_value: bool = False,
                        generate_preview: bool = False,
                        await_promise: bool = False) -> Dict:
        """运行已编译的脚本"""
        params = {
            "scriptId": script_id,
            "silent": silent,
            "includeCommandLineAPI": include_command_line_api,
            "returnByValue": return_by_value,
            "generatePreview": generate_preview,
            "awaitPromise": await_promise
        }
        
        if execution_context_id is not None:
            params["executionContextId"] = execution_context_id
        if object_group is not None:
            params["objectGroup"] = object_group
        
        return await self.client.execute_command("Runtime.runScript", params)