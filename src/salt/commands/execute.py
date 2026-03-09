"""execute 命令 - 执行脚本"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
from openfga import require_permission

from ..client import SaltAPIClient
from ..formatter import OutputFormatter


class ExecuteCommand:
    """Execute 命令 - 在目标主机上执行脚本。

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

    @require_permission("execute")
    def __call__(self, tgt: str, script_content: str, shell: str = "bash"):
        """在目标主机上执行脚本。

        Args:
            tgt: 目标主机，支持通配符。
            script_content: 脚本内容字符串。
            shell: 脚本解释器，默认为 "bash"。

        Raises:
            Exception: API 调用失败时抛出。
        """
        try:
            result = self.client.execute(
                client="local",
                tgt=tgt,
                fun="run_execute.run",
                arg=[shell],
                kwarg={"script_content": script_content},
            )
            self.formatter.print_result(result)
        except Exception as e:
            self.formatter.print_error(str(e))
            raise
