"""OpenFGA 权限管理命令 - CLI 命令实现"""

import getpass
from typing import Optional

from rich.console import Console
from rich.table import Table

from .config import OpenFGAConfig, OpenFGAConfigManager
from .client import OpenFGAClientWrapper
from .store_manager import StoreManager
from .checker import PermissionChecker


class PermissionCommand:
    """权限管理命令 - 管理 OpenFGA 权限。

    所有写操作均需要管理员权限。
    管理员列表配置在 ~/.config/salt/openfga.json 的 admins 字段中。
    """

    def __init__(self, config: Optional[OpenFGAConfig] = None):
        self.config_manager = OpenFGAConfigManager()
        self.config = config or self.config_manager.load()
        self.console = Console()

    def _current_user(self) -> str:
        return getpass.getuser()

    def _require_admin(self) -> None:
        self.config = self.config_manager.load()
        user = self._current_user()
        if not self.config.admins:
            raise PermissionError(
                "权限系统未配置管理员，请在 ~/.config/salt/openfga.json 中添加 admins 字段"
            )
        if not self.config.is_admin(user):
            raise PermissionError(
                f"用户 '{user}' 没有权限管理 OpenFGA 授权规则，需要管理员权限"
            )

    def _get_client(self) -> OpenFGAClientWrapper:
        self.config = self.config_manager.load()
        if not self.config.is_initialized():
            raise RuntimeError("OpenFGA 未初始化，请先运行 'salt permission init'")
        return OpenFGAClientWrapper(self.config)

    def _build_user_id(self, user: str, user_type: str = "user") -> str:
        if user_type == "cluster_member" or "#member" in user:
            return user if ":" in user else f"cluster:{user}#member"
        return f"user:{user}"

    def init(self, name: str = "salt-cli"):
        """初始化 OpenFGA Store 和授权模型（需要管理员权限）。"""
        try:
            self._require_admin()
            self.console.print("[bold]初始化 OpenFGA Store...[/bold]")
            config = StoreManager(self.config_manager).init_store(name=name)
            self.console.print("[green]✓ 初始化完成[/green]")
            self.console.print(f"  Store ID: {config.store_id}")
            self.console.print(f"  Model ID: {config.authorization_model_id}")
            self.console.print(f"  API URL: {config.api_url}")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_command(self, user: str, command: str, user_type: str = "user"):
        """授予命令执行权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            command: 命令名称，如 "ping"、"cmd"。
            user_type: "user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            user_id = self._build_user_id(user, user_type)
            self._get_client().write_tuples([{
                "user": user_id,
                "relation": "can_execute",
                "object": f"command:{command}",
            }])
            self.console.print(f"[green]✓ 已授权[/green]: {user_id} 可以执行命令 '{command}'")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_command(self, user: str, command: str, user_type: str = "user"):
        """撤销命令执行权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            command: 命令名称。
            user_type: "user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            user_id = self._build_user_id(user, user_type)
            self._get_client().delete_tuples([{
                "user": user_id,
                "relation": "can_execute",
                "object": f"command:{command}",
            }])
            self.console.print(f"[green]✓ 已撤销[/green]: {user_id} 执行命令 '{command}' 的权限")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_target(self, user: str, target: str, user_type: str = "user"):
        """授予访问主机的权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            target: 主机名，如 "web-001"。
            user_type: "user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            user_id = self._build_user_id(user, user_type)
            self._get_client().write_tuples([{
                "user": user_id,
                "relation": "can_access",
                "object": f"target:{target}",
            }])
            self.console.print(f"[green]✓ 已授权[/green]: {user_id} 可以访问主机 '{target}'")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_target(self, user: str, target: str, user_type: str = "user"):
        """撤销访问主机的权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            target: 主机名。
            user_type: "user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            user_id = self._build_user_id(user, user_type)
            self._get_client().delete_tuples([{
                "user": user_id,
                "relation": "can_access",
                "object": f"target:{target}",
            }])
            self.console.print(f"[green]✓ 已撤销[/green]: {user_id} 访问主机 '{target}' 的权限")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def add_cluster_member(self, user: str, cluster: str, as_admin: bool = False):
        """将用户加入集群（需要管理员权限）。

        Args:
            user: 用户名。
            cluster: 集群名称。
            as_admin: True 表示以管理员角色加入。
        """
        try:
            self._require_admin()
            relation = "admin" if as_admin else "member"
            self._get_client().write_tuples([{
                "user": f"user:{user}",
                "relation": relation,
                "object": f"cluster:{cluster}",
            }])
            role = "管理员" if as_admin else "成员"
            self.console.print(f"[green]✓ 已将用户 '{user}' 加入集群 '{cluster}'（{role}）[/green]")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def remove_cluster_member(self, user: str, cluster: str, as_admin: bool = False):
        """从集群移除用户（需要管理员权限）。

        Args:
            user: 用户名。
            cluster: 集群名称。
            as_admin: True 表示移除管理员角色。
        """
        try:
            self._require_admin()
            relation = "admin" if as_admin else "member"
            self._get_client().delete_tuples([{
                "user": f"user:{user}",
                "relation": relation,
                "object": f"cluster:{cluster}",
            }])
            role = "管理员" if as_admin else "成员"
            self.console.print(f"[green]✓ 已从集群 '{cluster}' 移除用户 '{user}'（{role}）[/green]")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def check(self, user: str, command: str, target: str, cluster: str):
        """测试权限检查（调试用）。

        Args:
            user: 用户名。
            command: 命令名称。
            target: 目标主机名。
            cluster: 集群名称。
        """
        self.config = self.config_manager.load()
        checker = PermissionChecker(config=self.config, enabled=True)
        self.console.print(
            f"检查权限: user={user}, command={command}, target={target}, cluster={cluster}"
        )
        try:
            checker.require(command, target, cluster, user)
            self.console.print("[green]✓ 权限检查通过[/green]")
        except Exception as e:
            self.console.print(f"[red]✗ 权限检查失败: {e}[/red]")

    def list_tuples(self, type_filter: Optional[str] = None):
        """列出所有关系元组。

        Args:
            type_filter: 按对象类型过滤，如 "cluster"、"command"、"target"（可选）。
        """
        try:
            tuples = self._get_client().read_tuples()
            if not tuples:
                self.console.print("[yellow]没有找到关系元组[/yellow]")
                return

            if type_filter:
                tuples = [t for t in tuples if t["object"].startswith(f"{type_filter}:")]

            table = Table(title="关系元组列表", show_header=True, header_style="bold magenta")
            table.add_column("用户/对象", style="cyan")
            table.add_column("关系", style="green")
            table.add_column("对象", style="yellow")

            for t in tuples:
                table.add_row(t["user"], t["relation"], t["object"])

            self.console.print(table)
            self.console.print(f"\n共 {len(tuples)} 个元组")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def status(self):
        """查看 OpenFGA 配置状态。"""
        self.config = self.config_manager.load()

        table = Table(title="OpenFGA 配置状态", show_header=True, header_style="bold magenta")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("API URL", self.config.api_url)
        table.add_row("Store ID", self.config.store_id or "[yellow]未设置[/yellow]")
        table.add_row(
            "Model ID", self.config.authorization_model_id or "[yellow]未设置[/yellow]"
        )
        table.add_row("已初始化", "✓ 是" if self.config.is_initialized() else "✗ 否")
        table.add_row("配置文件", str(self.config_manager.config_path))

        self.console.print(table)

    def __call__(self):
        """默认行为：查看配置状态。"""
        self.status()
