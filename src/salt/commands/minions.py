"""minions 命令 - 查看和管理 minions"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from openfga import require_permission

from typing import Optional
from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class MinionsCommand:
    """Minions 命令 - 查看 minion 信息。

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

    @require_permission("minions", target_param="mid")
    def __call__(self, mid: Optional[str] = None):
        """查看 minion 信息。

        Args:
            mid: Minion ID，不指定时返回所有 minion 信息。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.get_minions(mid)
            self.formatter.print_result(result)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise
