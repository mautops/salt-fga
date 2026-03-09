"""jobs 命令 - 查看任务执行历史"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from openfga import require_permission

from typing import Optional
from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class JobsCommand:
    """Jobs 命令 - 查看任务执行历史。

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

    @require_permission("jobs", target_param="jid")
    def __call__(self, jid: Optional[str] = None):
        """查看任务信息。

        Args:
            jid: Job ID，不指定时返回所有任务历史。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.get_jobs(jid)
            self.formatter.print_result(result)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise
