"""ping 命令 - 测试 minion 连接"""

from openfga import require_permission

from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class PingCommand:
    """Ping 命令 - 执行 test.ping 测试 minion 连接。

    Attributes:
        client: Salt API 客户端。
        formatter: 输出格式化器。
        no_auth: 是否跳过权限检查。
        cluster_name: 集群名称。
    """

    def __init__(self, client: SaltAPIClient, formatter: OutputFormatter, no_auth: bool = False, cluster_name: str = "default", username: str = None):
        self.client = client
        self.formatter = formatter
        self.no_auth = no_auth
        self.cluster_name = cluster_name
        self.username = username

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
