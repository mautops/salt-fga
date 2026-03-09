"""CLI 入口 - 使用 fire 管理命令行"""

import getpass
import sys
import fire

from .auth import TokenManager
from .client import SaltAPIClient
from .config import ConfigManager
from .formatter import OutputFormatter
from .commands.clusters import ClustersCommand
from .commands.ping import PingCommand
from .commands.execute import ExecuteCommand
from .commands.minions import MinionsCommand
from .commands.jobs import JobsCommand
from .commands.keys import KeysCommand
from .commands.cmd import CmdCommand

# 导入权限模块
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from openfga import PermissionChecker, PermissionCommand
from openfga.config import OpenFGAConfigManager


class SaltCLI:
    """Salt CLI 主类"""

    def __init__(self, cluster: str = None, raw: bool = False, no_auth: bool = False):
        """初始化 CLI。

        Args:
            cluster: 环境名称（-c/--cluster）。
            raw: 是否使用原始输出（--raw）。
            no_auth: 是否禁用权限检查（--no-auth，需要管理员权限）。
        """
        # 验证 no_auth 参数的使用权限（仅管理员可用）
        if no_auth:
            self._verify_no_auth_permission()

        self.config_manager = ConfigManager()
        self.config_manager.ensure_config_dir()

        # 获取环境配置
        try:
            self.cluster_config = self.config_manager.get_cluster(cluster)
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

        # 获取环境名称
        cluster_name = self.cluster_config.name

        # 初始化组件
        self.token_manager = TokenManager(self.config_manager.config_dir)
        self.client = SaltAPIClient(self.cluster_config, self.token_manager)
        self.formatter = OutputFormatter(raw=raw)

        # 初始化权限检查器（从 OpenFGA 配置加载，默认启用）
        perm_checker = PermissionChecker(enabled=not no_auth)

        # 注册子命令，传入权限检查器
        self.clusters = ClustersCommand(self.config_manager, self.formatter)
        self.ping = PingCommand(self.client, self.formatter, perm_checker, cluster_name)
        self.execute = ExecuteCommand(
            self.client, self.formatter, perm_checker, cluster_name
        )
        self.minions = MinionsCommand(
            self.client, self.formatter, perm_checker, cluster_name
        )
        self.jobs = JobsCommand(self.client, self.formatter, perm_checker, cluster_name)
        self.keys = KeysCommand(self.client, self.formatter, perm_checker, cluster_name)
        self.cmd = CmdCommand(self.client, self.formatter, perm_checker, cluster_name)

        # 权限管理命令
        self.permission = PermissionCommand()

    @staticmethod
    def _verify_no_auth_permission() -> None:
        """验证当前用户是否有权限使用 --no-auth 参数。

        从 OpenFGA 配置文件读取管理员列表，只有管理员才能禁用权限检查。

        Raises:
            SystemExit: 当用户不是管理员或配置未设置时，打印错误并退出。
        """
        openfga_config = OpenFGAConfigManager().load()
        current_user = getpass.getuser()

        if not openfga_config.admins:
            print(
                "错误: --no-auth 需要管理员权限，但权限系统未配置管理员列表。\n"
                "请在 ~/.config/salt/openfga.json 中添加 admins 字段。",
                file=sys.stderr,
            )
            sys.exit(1)

        if not openfga_config.is_admin(current_user):
            print(
                f"错误: 用户 '{current_user}' 没有使用 --no-auth 的权限，需要管理员身份。",
                file=sys.stderr,
            )
            sys.exit(1)


def main():
    """CLI 入口函数"""
    try:
        fire.Fire(SaltCLI)
    except KeyboardInterrupt:
        print("\n操作已取消", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
