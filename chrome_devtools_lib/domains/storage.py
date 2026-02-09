#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage Domain
Chrome DevTools Storage域的实现，用于存储管理和分析
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class StorageDomain:
    """Storage域实现"""
    
    def __init__(self, client):
        """
        初始化Storage域
        
        Args:
            client: ChromeDevToolsClient实例
        """
        self.client = client
        self.domain_name = "Storage"
    
    async def enable(self) -> bool:
        """启用Storage域"""
        return await self.client.enable_domain(self.domain_name)
    
    async def disable(self) -> bool:
        """禁用Storage域"""
        return await self.client.disable_domain(self.domain_name)
    
    async def clear_data_for_origin(self, origin: str,
                                   storage_types: str) -> Dict:
        """
        清除指定源的数据
        
        Args:
            origin: 源地址
            storage_types: 存储类型（逗号分隔）
        """
        params = {
            "origin": origin,
            "storageTypes": storage_types
        }
        return await self.client.execute_command("Storage.clearDataForOrigin", params)
    
    async def get_cookies(self, browser_context_id: Optional[str] = None) -> Dict:
        """
        获取Cookie
        
        Args:
            browser_context_id: 浏览器上下文ID
        """
        params = {}
        if browser_context_id is not None:
            params["browserContextId"] = browser_context_id
        
        return await self.client.execute_command("Storage.getCookies", params)
    
    async def set_cookies(self, cookies: List[Dict],
                         browser_context_id: Optional[str] = None) -> Dict:
        """
        设置Cookie
        
        Args:
            cookies: Cookie列表
            browser_context_id: 浏览器上下文ID
        """
        params = {"cookies": cookies}
        if browser_context_id is not None:
            params["browserContextId"] = browser_context_id
        
        return await self.client.execute_command("Storage.setCookies", params)
    
    async def clear_cookies(self, browser_context_id: Optional[str] = None) -> Dict:
        """
        清除Cookie
        
        Args:
            browser_context_id: 浏览器上下文ID
        """
        params = {}
        if browser_context_id is not None:
            params["browserContextId"] = browser_context_id
        
        return await self.client.execute_command("Storage.clearCookies", params)
    
    async def get_usage_and_quota(self, origin: str) -> Dict:
        """
        获取存储使用情况和配额
        
        Args:
            origin: 源地址
        """
        params = {"origin": origin}
        return await self.client.execute_command("Storage.getUsageAndQuota", params)
    
    async def override_quota_for_origin(self, origin: str,
                                      quota_size: Optional[float] = None) -> Dict:
        """
        覆盖源的配额
        
        Args:
            origin: 源地址
            quota_size: 配额大小
        """
        params = {"origin": origin}
        if quota_size is not None:
            params["quotaSize"] = quota_size
        
        return await self.client.execute_command("Storage.overrideQuotaForOrigin", params)
    
    async def track_cache_storage_for_origin(self, origin: str) -> Dict:
        """
        跟踪源的缓存存储
        
        Args:
            origin: 源地址
        """
        params = {"origin": origin}
        return await self.client.execute_command("Storage.trackCacheStorageForOrigin", params)
    
    async def track_indexed_db_for_origin(self, origin: str) -> Dict:
        """
        跟踪源的IndexedDB
        
        Args:
            origin: 源地址
        """
        params = {"origin": origin}
        return await self.client.execute_command("Storage.trackIndexedDBForOrigin", params)
    
    async def untrack_cache_storage_for_origin(self, origin: str) -> Dict:
        """
        停止跟踪源的缓存存储
        
        Args:
            origin: 源地址
        """
        params = {"origin": origin}
        return await self.client.execute_command("Storage.untrackCacheStorageForOrigin", params)
    
    async def untrack_indexed_db_for_origin(self, origin: str) -> Dict:
        """
        停止跟踪源的IndexedDB
        
        Args:
            origin: 源地址
        """
        params = {"origin": origin}
        return await self.client.execute_command("Storage.untrackIndexedDBForOrigin", params)
    
    async def get_trust_tokens(self) -> Dict:
        """获取信任令牌"""
        return await self.client.execute_command("Storage.getTrustTokens")
    
    async def clear_trust_tokens(self, issuer_origin: str) -> Dict:
        """
        清除信任令牌
        
        Args:
            issuer_origin: 发行者源
        """
        params = {"issuerOrigin": issuer_origin}
        return await self.client.execute_command("Storage.clearTrustTokens", params)
    
    async def get_interest_group_details(self, owner_origin: str,
                                       name: str) -> Dict:
        """
        获取兴趣组详情
        
        Args:
            owner_origin: 所有者源
            name: 名称
        """
        params = {
            "ownerOrigin": owner_origin,
            "name": name
        }
        return await self.client.execute_command("Storage.getInterestGroupDetails", params)
    
    async def set_interest_group_tracking(self, enable: bool) -> Dict:
        """
        设置兴趣组跟踪
        
        Args:
            enable: 是否启用
        """
        params = {"enable": enable}
        return await self.client.execute_command("Storage.setInterestGroupTracking", params)
    
    async def get_shared_storage_metadata(self, owner_origin: str) -> Dict:
        """
        获取共享存储元数据
        
        Args:
            owner_origin: 所有者源
        """
        params = {"ownerOrigin": owner_origin}
        return await self.client.execute_command("Storage.getSharedStorageMetadata", params)
    
    async def get_shared_storage_entries(self, owner_origin: str) -> Dict:
        """
        获取共享存储条目
        
        Args:
            owner_origin: 所有者源
        """
        params = {"ownerOrigin": owner_origin}
        return await self.client.execute_command("Storage.getSharedStorageEntries", params)
    
    async def set_shared_storage_entry(self, owner_origin: str,
                                     key: str,
                                     value: str,
                                     ignore_if_present: Optional[bool] = None) -> Dict:
        """
        设置共享存储条目
        
        Args:
            owner_origin: 所有者源
            key: 键
            value: 值
            ignore_if_present: 如果存在是否忽略
        """
        params = {
            "ownerOrigin": owner_origin,
            "key": key,
            "value": value
        }
        if ignore_if_present is not None:
            params["ignoreIfPresent"] = ignore_if_present
        
        return await self.client.execute_command("Storage.setSharedStorageEntry", params)
    
    async def delete_shared_storage_entry(self, owner_origin: str,
                                        key: str) -> Dict:
        """
        删除共享存储条目
        
        Args:
            owner_origin: 所有者源
            key: 键
        """
        params = {
            "ownerOrigin": owner_origin,
            "key": key
        }
        return await self.client.execute_command("Storage.deleteSharedStorageEntry", params)
    
    async def clear_shared_storage_entries(self, owner_origin: str) -> Dict:
        """
        清除共享存储条目
        
        Args:
            owner_origin: 所有者源
        """
        params = {"ownerOrigin": owner_origin}
        return await self.client.execute_command("Storage.clearSharedStorageEntries", params)
    
    async def reset_shared_storage_budget(self, owner_origin: str) -> Dict:
        """
        重置共享存储预算
        
        Args:
            owner_origin: 所有者源
        """
        params = {"ownerOrigin": owner_origin}
        return await self.client.execute_command("Storage.resetSharedStorageBudget", params)
    
    async def set_shared_storage_tracking(self, enable: bool) -> Dict:
        """
        设置共享存储跟踪
        
        Args:
            enable: 是否启用
        """
        params = {"enable": enable}
        return await self.client.execute_command("Storage.setSharedStorageTracking", params)