import getpass
import json
import subprocess
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table

from openfga_sdk import (
    ClientConfiguration,
    CreateStoreRequest,
    TypeDefinition,
    WriteAuthorizationModelRequest,
)
from openfga_sdk.client.models.check_request import ClientCheckRequest
from openfga_sdk.client.models.tuple import ClientTuple
from openfga_sdk.client.models.write_request import ClientWriteRequest
from openfga_sdk.models.read_request_tuple_key import ReadRequestTupleKey
from openfga_sdk.sync import OpenFgaClient

from .config import OpenFGAConfig, load_config, save_config

AUTHORIZATION_MODEL_FILE = Path(__file__).parent / "authorization_model.fga"

# 超级管理员在 OpenFGA 中的标识对象
# 用 fga tuple write 添加: user:<username> admin cluster:system
SUPERADMIN_OBJECT = "cluster:system"


def _client(config: OpenFGAConfig) -> OpenFgaClient:
    return OpenFgaClient(
        ClientConfiguration(
            api_url=config.api_url,
            store_id=config.store_id,
            authorization_model_id=config.authorization_model_id,
        )
    )


def is_superadmin(config: OpenFGAConfig, user: str) -> bool:
    """检查用户是否是超级管理员（admin of cluster:system）。"""
    fga = _client(config)
    return fga.check(
        ClientCheckRequest(
            user=f"user:{user}",
            relation="admin",
            object=SUPERADMIN_OBJECT,
        )
    ).allowed


class PermissionCommand:
    """权限管理命令。超级管理员通过 fga tuple write 直接在 OpenFGA 中配置。"""

    def __init__(self):
        self.console = Console()

    def _require_admin(self) -> OpenFGAConfig:
        """检查当前用户是否是超级管理员，不是则抛出异常。"""
        config = load_config()
        if not config.is_initialized():
            raise RuntimeError("OpenFGA 未初始化，请先运行 'salt permission init'")
        user = getpass.getuser()
        try:
            allowed = is_superadmin(config, user)
        except Exception as e:
            raise RuntimeError(f"超级管理员权限检查失败: {e}")
        if not allowed:
            store_id = config.store_id
            raise PermissionError(
                f"用户 '{user}' 不是超级管理员。\n"
                f"请让现有超管执行:\n"
                f"  fga tuple write --store-id {store_id} "
                f'\'[{{"user":"user:{user}","relation":"admin","object":"{SUPERADMIN_OBJECT}"}}]\''
            )
        return config

    def _get_client(self) -> OpenFgaClient:
        config = load_config()
        if not config.is_initialized():
            raise RuntimeError("OpenFGA 未初始化，请先运行 'salt permission init'")
        return _client(config)

    def _write(self, user: str, relation: str, object: str) -> None:
        self._get_client().write(
            ClientWriteRequest(
                writes=[ClientTuple(user=user, relation=relation, object=object)]
            )
        )

    def _delete(self, user: str, relation: str, object: str) -> None:
        self._get_client().write(
            ClientWriteRequest(
                deletes=[ClientTuple(user=user, relation=relation, object=object)]
            )
        )

    def init(self, name: str = "salt-fga"):
        """初始化 OpenFGA Store 和授权模型，并将当前用户设为超级管理员。"""
        try:
            config = load_config()
            self.console.print("[bold]初始化 OpenFGA Store...[/bold]")

            result = subprocess.run(
                ["fga", "model", "transform", "--file", str(AUTHORIZATION_MODEL_FILE)],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"fga model transform 失败，请确认已安装 fga CLI\n{result.stderr}"
                )

            model_data = json.loads(result.stdout)

            fga = OpenFgaClient(ClientConfiguration(api_url=config.api_url))
            store_id = fga.create_store(CreateStoreRequest(name=name)).id
            self.console.print(f"  ✓ 创建 Store: {store_id}")

            fga = OpenFgaClient(
                ClientConfiguration(api_url=config.api_url, store_id=store_id)
            )
            model_id = fga.write_authorization_model(
                WriteAuthorizationModelRequest(
                    schema_version=model_data.get("schema_version", "1.1"),
                    type_definitions=[
                        TypeDefinition(**td)
                        for td in model_data.get("type_definitions", [])
                    ],
                )
            ).authorization_model_id
            self.console.print(f"  ✓ 写入授权模型: {model_id}")

            config.store_id = store_id
            config.authorization_model_id = model_id
            save_config(config)

            # 将当前用户设为第一个超级管理员
            current_user = getpass.getuser()
            fga_with_model = OpenFgaClient(
                ClientConfiguration(
                    api_url=config.api_url,
                    store_id=store_id,
                    authorization_model_id=model_id,
                )
            )
            fga_with_model.write(
                ClientWriteRequest(
                    writes=[
                        ClientTuple(
                            user=f"user:{current_user}",
                            relation="admin",
                            object=SUPERADMIN_OBJECT,
                        )
                    ]
                )
            )
            self.console.print(f"  ✓ 设置超级管理员: {current_user}")

            self.console.print(
                f"[green]✓ 初始化完成[/green]  Store ID: {store_id}  Model ID: {model_id}\n"
                f"\n后续可通过 fga CLI 手动添加其他超级管理员:\n"
                f"  fga tuple write --store-id {store_id} "
                f'\'[{{"user":"user:<username>","relation":"admin","object":"{SUPERADMIN_OBJECT}"}}]\''
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_cmd(self, user: str, command: str):
        """授予用户执行命令的权限（需要超级管理员权限）。"""
        try:
            self._require_admin()
            self._write(f"user:{user}", "can_execute", f"command:{command}")
            self.console.print(
                f"[green]✓ 已授权[/green]: user:{user} 可以执行命令 '{command}'"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_cmd(self, user: str, command: str):
        """撤销用户执行命令的权限（需要超级管理员权限）。"""
        try:
            self._require_admin()
            self._delete(f"user:{user}", "can_execute", f"command:{command}")
            self.console.print(
                f"[green]✓ 已撤销[/green]: user:{user} 执行命令 '{command}' 的权限"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def grant_target(self, user: str, target: str):
        """授予用户访问主机的权限（需要超级管理员权限）。"""
        try:
            self._require_admin()
            self._write(f"user:{user}", "can_access", f"target:{target}")
            self.console.print(
                f"[green]✓ 已授权[/green]: user:{user} 可以访问主机 '{target}'"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def revoke_target(self, user: str, target: str):
        """撤销用户访问主机的权限（需要超级管理员权限）。"""
        try:
            self._require_admin()
            self._delete(f"user:{user}", "can_access", f"target:{target}")
            self.console.print(
                f"[green]✓ 已撤销[/green]: user:{user} 访问主机 '{target}' 的权限"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def add_member(self, user: str, cluster: str, as_admin: bool = False):
        """将用户加入集群（需要超级管理员权限）。"""
        try:
            self._require_admin()
            relation = "admin" if as_admin else "member"
            self._write(f"user:{user}", relation, f"cluster:{cluster}")
            role = "管理员" if as_admin else "成员"
            self.console.print(
                f"[green]✓ 已将用户 '{user}' 加入集群 '{cluster}'（{role}）[/green]"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def remove_member(self, user: str, cluster: str, as_admin: bool = False):
        """从集群移除用户（需要超级管理员权限）。"""
        try:
            self._require_admin()
            relation = "admin" if as_admin else "member"
            self._delete(f"user:{user}", relation, f"cluster:{cluster}")
            role = "管理员" if as_admin else "成员"
            self.console.print(
                f"[green]✓ 已从集群 '{cluster}' 移除用户 '{user}'（{role}）[/green]"
            )
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")

    def check(self, user: str, command: str, target: str, cluster: str):
        """测试权限检查（调试用，需要超级管理员权限）。"""
        try:
            self._require_admin()
        except Exception as e:
            self.console.print(f"[red]错误: {e}[/red]")
            return

        self.console.print(
            f"检查权限: user={user}, command={command}, target={target}, cluster={cluster}"
        )
        try:
            fga = self._get_client()
            allowed = (
                fga.check(
                    ClientCheckRequest(
                        user=f"user:{user}",
                        relation="member",
                        object=f"cluster:{cluster}",
                    )
                ).allowed
                and fga.check(
                    ClientCheckRequest(
                        user=f"user:{user}",
                        relation="can_execute",
                        object=f"command:{command}",
                    )
                ).allowed
                and fga.check(
                    ClientCheckRequest(
                        user=f"user:{user}",
                        relation="can_access",
                        object=f"target:{target}",
                    )
                ).allowed
            )
            self.console.print(
                "[green]✓ 权限检查通过[/green]"
                if allowed
                else "[red]✗ 权限被拒绝[/red]"
            )
        except Exception as e:
            self.console.print(f"[red]✗ 权限检查失败: {e}[/red]")

    def list(self, type_filter: Optional[str] = None):
        """列出所有权限规则（需要超级管理员权限）。"""
        try:
            self._require_admin()
            resp = self._get_client().read(ReadRequestTupleKey())
            tuples = [
                {"user": t.key.user, "relation": t.key.relation, "object": t.key.object}
                for t in (resp.tuples or [])
            ]
            if type_filter:
                tuples = [
                    t for t in tuples if t["object"].startswith(f"{type_filter}:")
                ]
            if not tuples:
                self.console.print("[yellow]没有找到关系元组[/yellow]")
                return

            table = Table(
                title="关系元组列表", show_header=True, header_style="bold magenta"
            )
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
        """查看 OpenFGA 配置状态（无需管理员权限）。"""
        config = load_config()
        table = Table(
            title="OpenFGA 配置状态", show_header=True, header_style="bold magenta"
        )
        table.add_column("配置项", style="cyan")
        table.add_column("值", style="green")
        table.add_row("API URL", config.api_url)
        table.add_row("Store ID", config.store_id or "[yellow]未设置[/yellow]")
        table.add_row(
            "Model ID", config.authorization_model_id or "[yellow]未设置[/yellow]"
        )
        table.add_row("已初始化", "✓ 是" if config.is_initialized() else "✗ 否")
        self.console.print(table)

    def __call__(self):
        self.status()
