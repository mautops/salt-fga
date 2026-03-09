"""OpenFGA 权限模块 - 基于真实 OpenFGA SDK 的权限管理"""

from .config import OpenFGAConfig, OpenFGAConfigManager
from .client import OpenFGAClientWrapper
from .store_manager import StoreManager
from .checker import PermissionChecker, PermissionDeniedError, require_permission
from .commands import PermissionCommand

__all__ = [
    "OpenFGAConfig",
    "OpenFGAConfigManager",
    "OpenFGAClientWrapper",
    "StoreManager",
    "PermissionChecker",
    "PermissionDeniedError",
    "require_permission",
    "PermissionCommand",
]
