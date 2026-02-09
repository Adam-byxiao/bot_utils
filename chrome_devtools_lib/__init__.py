#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome DevTools Library
通用的Chrome DevTools客户端库，支持多种DevTools协议功能
"""

from .client import ChromeDevToolsClient
from .domains import RuntimeDomain, NetworkDomain, PerformanceDomain, StorageDomain
from .extensions import VoiceAgentMonitor

__version__ = "1.0.0"
__author__ = "Chrome DevTools Library Team"

__all__ = [
    "ChromeDevToolsClient",
    "RuntimeDomain", 
    "NetworkDomain",
    "PerformanceDomain",
    "StorageDomain",
    "VoiceAgentMonitor"
]