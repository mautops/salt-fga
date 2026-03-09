"""OpenFGA 权限管理命令 - CLI 命令实现"""

import getpass
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .config import OpenFGAConfig, OpenFGAConfigManager
from .client import OpenFGAClientWrapper
from .store_manager import StoreManager
from .checker import PermissionChecker


class PermissionCommand:
    """权限管理命令 - 管理 OpenFGA 权限。

    所有写操作（grant/revoke/add/remove）均需要管理员权限。
    管理员列表配置在 ~/.config/salt/openfga.json 的 admins 字段中。

    Attributes:
        config_manager: 配置文件管理器。
        config: 当前加载的配置。
        console: Rich 控制台输出。
    """

    def __init__(self, config: Optional[OpenFGAConfig] = None):
        self.config_manager = OpenFGAConfigManager()
        self.config = config or self.config_manager.load()
        self.console = Console()

    def _current_user(self) -> str:
        """获取当前用户名。

        仅使用系统登录用户，不信任环境变量（防止伪造）。

        Returns:
            当前用户名字符串。
        """
        return getpass.getuser()

    def _require_admin(self) -> None:
        """检查当前用户是否是管理员，否则抛出异常。

        Raises:
            PermissionError: 当 admins 列表未配置或当前用户不在列表中时抛出。
        """
        self.config = self.config_manager.load()
        user = self._current_user()

        # 如果 admins 列表为空，任何用户都不能管理（防止误配置）
        if not self.config.admins:
            raise PermissionError(
                "权限系统未配置管理员，请在 ~/.config/salt/openfga.json 中添��� admins 字段"
            )

        if not self.config.is_admin(user):
            raise PermissionError(
                f"用户 '{user}' 没有权限管理 OpenFGA 授权规则，需要管理员权限"
            )

    def _get_client(self) -> OpenFGAClientWrapper:
        """获取已初始化的 OpenFGA 客户端。

        Returns:
            OpenFGAClientWrapper 实例。

        Raises:
            RuntimeError: OpenFGA 未初始化时抛出，提示运行 init 命令。
        """
        self.config = self.config_manager.load()
        if not self.config.is_initialized():
            raise RuntimeError("OpenFGA 未初始化，请先运行 'salt permission init'")
        return OpenFGAClientWrapper(self.config)

    def init(self, name: str = "salt-cli"):
        """初始化 OpenFGA Store 和授权模型（需要管理员权限）。

        Args:
            name: Store 名称，默认为 "salt-cli"。
        """
        try:
            self._require_admin()
            self.console.print("[bold]初始化 OpenFGA Store...[/bold]")
            config = StoreManager(self.config_manager).init_store(name=name)
            self.console.print(f"[green]✓ 初始化完成[/green]")
            self.console.print(f"  Store ID: {config.store_id}")
            self.console.print(f"  Model ID: {config.authorization_model_id}")
            self.console.print(f"  API URL: {config.api_url}")
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_command(self, user: str, command: str, user_type: str = "user"):
        """授予命令执行权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识（如 alice 或 cluster:prod#member）。
            command: 命令名称，如 "ping"、"cmd"。
            user_type: 用户类型，"user" 或 "cluster_member"，影响 user 标识构建方式。
        """
        try:
            self._require_admin()
            client = self._get_client()

            # 构建 user 标识
            if user_type == "cluster_member" or "#member" in user:
                user_id = user if ":" in user else f"cluster:{user}#member"
            else:
                user_id = f"user:{user}"

            client.write_tuples([{
                "user": user_id,
                "relation": "can_execute",
                "object": f"command:{command}",
            }])

            self.console.print(
                f"[green]✓ 已授权[/green]: {user_id} 可以执行命令 '{command}'"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_command(self, user: str, command: str, user_type: str = "user"):
        """撤销命令执行权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            command: 命令名称。
            user_type: 用户类型，"user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            client = self._get_client()

            # 构建 user 标识
            if user_type == "cluster_member" or "#member" in user:
                user_id = user if ":" in user else f"cluster:{user}#member"
            else:
                user_id = f"user:{user}"

            client.delete_tuples([{
                "user": user_id,
                "relation": "can_execute",
                "object": f"command:{command}",
            }])

            self.console.print(
                f"[green]✓ 已撤销[/green]: {user_id} 执行命令 '{command}' 的权限"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_target_group(self, user: str, group: str, user_type: str = "user"):
        """授予目标主机组的访问权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识（如 alice 或 cluster:prod#member）。
            group: 目标组名称，如 "web-servers"。
            user_type: 用户类型，"user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            client = self._get_client()

            # 构建 user 标识
            if user_type == "cluster_member" or "#member" in user:
                user_id = user if ":" in user else f"cluster:{user}#member"
            else:
                user_id = f"user:{user}"

            client.write_tuples([{
                "user": user_id,
                "relation": "can_access",
                "object": f"target_group:{group}",
            }])

            self.console.print(
                f"[green]✓ 已授权[/green]: {user_id} 可以访问目标组 '{group}'"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_target_group(self, user: str, group: str, user_type: str = "user"):
        """撤销目标主机组的访问权限（需要管理员权限）。

        Args:
            user: 用户名或集群标识。
            group: 目标组名称。
            user_type: 用户类型，"user" 或 "cluster_member"。
        """
        try:
            self._require_admin()
            client = self._get_client()

            # 构建 user 标识
            if user_type == "cluster_member" or "#member" in user:
                user_id = user if ":" in user else f"cluster:{user}#member"
            else:
                user_id = f"user:{user}"

            client.delete_tuples([{
                "user": user_id,
                "relation": "can_access",
                "object": f"target_group:{group}",
            }])

            self.console.print(
                f"[green]✓ 已撤销[/green]: {user_id} 对目标组 '{group}' 的访问权限"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def add_cluster_member(self, user: str, cluster: str, as_admin: bool = False):
        """将用户加入集群（需要管理员权限）。

        Args:
            user: 用户名。
            cluster: 集群名称，如 "prod"、"dev"。
            as_admin: True 表示以管理员角色加入，False 表示普通成员。
        """
        try:
            self._require_admin()
            client = self._get_client()

            relation = "admin" if as_admin else "member"

            client.write_tuples([{
                "user": f"user:{user}",
                "relation": relation,
                "object": f"cluster:{cluster}",
            }])

            role = "管理员" if as_admin else "成员"
            self.console.print(
                f"[green]✓ 已将用户 '{user}' 加入集群 '{cluster}'（{role}）[/green]"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def remove_cluster_member(self, user: str, cluster: str, as_admin: bool = False):
        """从集群移除用户（需要管理员权限）。

        Args:
            user: 用户名。
            cluster: 集群名称。
            as_admin: True 表示移除管理员角色，False 表示移除普通成员角色。
        """
        try:
            self._require_admin()
            client = self._get_client()

            relation = "admin" if as_admin else "member"

            client.delete_tuples([{
                "user": f"user:{user}",
                "relation": relation,
                "object": f"cluster:{cluster}",
            }])

            role = "管理员" if as_admin else "成员"
            self.console.print(
                f"[green]✓ 已从集群 '{cluster}' 移除用户 '{user}'（{role}）[/green]"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def create_target_group(self, name: str, admin: Optional[str] = None):
        """创建目标主机组（需要管理员权限）。

        目标组在 OpenFGA 中不需要显式创建，写入关联 tuple 即可。

        Args:
            name: 目标组名称，如 "web-servers"。
            admin: 组管理员用户名（可选），设置后该用户对该组有 admin 关系。
        """
        try:
            self._require_admin()
            client = self._get_client()

            tuples = []
            if admin:
                tuples.append({
                    "user": f"user:{admin}",
                    "relation": "admin",
                    "object": f"target_group:{name}",
                })

            if tuples:
                client.write_tuples(tuples)

            # 目标组在 OpenFGA 中不需要显式创建，只需要有关联的 tuple 即可
            self.console.print(
                f"[green]✓ 目标组 '{name}' 已创建[/green]"
            )
            if admin:
                self.console.print(f"  管理员: {admin}")
            self.console.print(f"  使用 add_target 命令添加主机到该组")

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def add_target(self, target: str, group: str):
        """将主机加入目标组（需要管理员权限）。

        Args:
            target: 主机名，如 "web-001"。
            group: 目标组名称，如 "web-servers"。
        """
        try:
            self._require_admin()
            client = self._get_client()

            client.write_tuples([{
                "user": f"target_group:{group}",
                "relation": "group",
                "object": f"target:{target}",
            }])

            self.console.print(
                f"[green]✓ 主机 '{target}' 已加入目标组 '{group}'[/green]"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def remove_target(self, target: str, group: str):
        """从目标组移除主机（需要管理员权限）。

        Args:
            target: 主机名。
            group: 目标组名称。
        """
        try:
            self._require_admin()
            client = self._get_client()

            client.delete_tuples([{
                "user": f"target_group:{group}",
                "relation": "group",
                "object": f"target:{target}",
            }])

            self.console.print(
                f"[green]✓ 主机 '{target}' 已从目标组 '{group}' 移除[/green]"
            )

        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def check(self, user: str, command: str, target: str, cluster: str):
        """测试权限检查（调试用）。

        Args:
            user: 用户名。
            command: 命令名称，如 "ping"、"cmd"。
            target: 目标主机名。
            cluster: 集群名称。
        """
        # 重新加载配置
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
            type_filter: 按对象类型过滤，如 "cluster"、"command"、"target_group"（可选）。
        """
        try:
            client = self._get_client()
            tuples = client.read_tuples()

            if not tuples:
                self.console.print("[yellow]没有找到关系元组[/yellow]")
                return

            # 过滤
            if type_filter:
                tuples = [t for t in tuples if t["object"].startswith(f"{type_filter}:")]

            # 创建表格
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
        # 重新加载配置
        self.config = self.config_manager.load()

        table = Table(title="OpenFGA 配置状态", show_header=True, header_style="bold magenta")
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")

        table.add_row("API URL", self.config.api_url)
        table.add_row("Store ID", self.config.store_id or "[yellow]未设置[/yellow]")
        table.add_row("Model ID", self.config.authorization_model_id or "[yellow]未设置[/yellow]")
        table.add_row("已初始化", "✓ 是" if self.config.is_initialized() else "✗ 否")
        table.add_row("配置文件", str(self.config_manager.config_path))

        self.console.print(table)

    def __call__(self):
        """默认行为：查看配置状态。"""
        self.status()
