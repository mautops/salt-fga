"""keys 命令 - 管理 minion keys"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from openfga import require_permission

from typing import Optional
from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class KeysCommand:
    """Keys 命令 - 管理 minion keys。

    Attributes:
        client: Salt API 客户端。
        formatter: 输出格式化器。
        permission_checker: 权限检查器（可选）。
        cluster_name: 集群名称。
    """

    def __init__(self, client: SaltAPIClient, formatter: OutputFormatter, permission_checker=None, cluster_name: str = "default"):
        self.client = client
        self.formatter = formatter
        self.permission_checker = permission_checker
        self.cluster_name = cluster_name

    @require_permission("keys", target_param="mid")
    def list(self, mid: Optional[str] = None):
        """列出 minion keys。

        Args:
            mid: Minion ID，不指定时返回所有 keys。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.get_keys(mid)
            self.formatter.print_result(result)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise

    @require_permission("keys", target_param="mid")
    def accept(self, mid: str):
        """接受 minion key。

        Args:
            mid: Minion ID。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.execute_wheel(fun="key.accept", kwarg={"match": mid})
            self.formatter.print_result(result)
            self.formatter.print_success(f"已接受 minion key: {mid}")
        except Exception as e:
            self.formatter.print_error(str(e))
            raise

    @require_permission("keys", target_param="mid")
    def reject(self, mid: str):
        """拒绝 minion key。

        Args:
            mid: Minion ID。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.execute_wheel(fun="key.reject", kwarg={"match": mid})
            self.formatter.print_result(result)
            self.formatter.print_success(f"已拒绝 minion key: {mid}")
        except Exception as e:
            self.formatter.print_error(str(e))
            raise

    @require_permission("keys", target_param="mid")
    def delete(self, mid: str):
        """删除 minion key。

        Args:
            mid: Minion ID。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.execute_wheel(fun="key.delete", kwarg={"match": mid})
            self.formatter.print_result(result)
            self.formatter.print_success(f"已删除 minion key: {mid}")
        except Exception as e:
            self.formatter.print_error(str(e))
            raise

    def __call__(self, mid: Optional[str] = None):
        """默认行为：列出所有 keys。

        Args:
            mid: Minion ID，不指定时返回所有 keys。
        """
        self.list(mid)
