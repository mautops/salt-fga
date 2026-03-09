"""minions 命令 - 查看和管理 minions"""

from openfga import require_permission

from typing import Optional
from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class MinionsCommand:
    """Minions 命令 - 查看 minion 信息。

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
