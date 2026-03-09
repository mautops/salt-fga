"""CLI 入口 - 使用 fire 管理命令行"""

import getpass
import os
import sys
import requests
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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
from openfga import PermissionCommand, load_config
from openfga.commands import is_superadmin


def _resolve_user() -> str:
    """通过 COPAW_AUTH_TOKEN 调用 API 获取当前用户 ID。

    Returns:
        user_id 字符串，未设置 token 时返回 None。
    """
    token = os.environ.get("COPAW_AUTH_TOKEN")
    if not token:
        return None
    api_base = os.environ.get("COPAW_API_BASE_URL", "http://localhost:8088")
    resp = requests.get(
        f"{api_base}/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()["user_id"]


class SaltCLI:
    """Salt CLI 主类"""

    def __init__(self, cluster: str = None, raw: bool = False, no_auth: bool = False):
        """初始化 CLI。

        Args:
            cluster: 环境名称（-c/--cluster）。
            raw: 是否使用原始输出（--raw）。
            no_auth: 是否禁用权限检查（--no-auth，需要管理员权限）。
        """
        if no_auth:
            self._verify_no_auth_permission()

        try:
            user = _resolve_user() if not no_auth else None
        except Exception as e:
            print(f"错误: 获取用户身份失败: {e}", file=sys.stderr)
            sys.exit(1)

        self.config_manager = ConfigManager()
        self.config_manager.ensure_config_dir()

        try:
            self.cluster_config = self.config_manager.get_cluster(cluster)
        except Exception as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

        cluster_name = self.cluster_config.name

        self.token_manager = TokenManager(self.config_manager.config_dir)
        self.client = SaltAPIClient(self.cluster_config, self.token_manager)
        self.formatter = OutputFormatter(raw=raw)

        self.clusters = ClustersCommand(self.config_manager, self.formatter)
        self.ping = PingCommand(
            self.client, self.formatter, no_auth, cluster_name, user
        )
        self.execute = ExecuteCommand(
            self.client, self.formatter, no_auth, cluster_name, user
        )
        self.minions = MinionsCommand(
            self.client, self.formatter, no_auth, cluster_name, user
        )
        self.jobs = JobsCommand(
            self.client, self.formatter, no_auth, cluster_name, user
        )
        self.keys = KeysCommand(
            self.client, self.formatter, no_auth, cluster_name, user
        )
        self.cmd = CmdCommand(self.client, self.formatter, no_auth, cluster_name, user)

        self.permission = PermissionCommand()

    @staticmethod
    def _verify_no_auth_permission() -> None:
        config = load_config()
        if not config.is_initialized():
            return
        user = getpass.getuser()
        try:
            allowed = is_superadmin(config, user)
        except Exception as e:
            print(f"错误: 超级管理员权限检查失败: {e}", file=sys.stderr)
            sys.exit(1)
        if not allowed:
            print(
                f"错误: 用户 '{user}' 不是超级管理员，无法使用 --no-auth 参数。\n"
                f"请让现有超管通过 fga CLI 授权:\n"
                f"  fga tuple write --store-id {config.store_id} "
                f'\'[{{"user":"user:{user}","relation":"admin","object":"cluster:system"}}]\'',
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
