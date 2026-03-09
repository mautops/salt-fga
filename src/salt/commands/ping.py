"""ping 命令 - 测试 minion 连接"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from openfga import require_permission

from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class PingCommand:
    """Ping 命令 - 执行 test.ping 测试 minion 连接。

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

    @require_permission("ping")
    def __call__(self, tgt: str = "*"):
        """执行 test.ping 命令测试 minion 连接。

        Args:
            tgt: 目标主机，支持通配符，默认为 "*"（所有主机）。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.execute(client="local", tgt=tgt, fun="test.ping")
            self.formatter.print_result(result)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise
