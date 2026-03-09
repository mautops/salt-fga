"""OpenFGA 权限检查器"""

import getpass
from functools import wraps
from typing import Optional, Callable, Any
import inspect

from .config import OpenFGAConfig, OpenFGAConfigManager
from .client import OpenFGAClientWrapper


class PermissionDeniedError(Exception):
    """权限被拒绝异常。

    Attributes:
        user: 发起请求的用户名。
        command: 被拒绝的命令。
        target: 目标主机。
        cluster: 集群名称。
        reason: 拒绝的详细原因。
    """

    def __init__(self, user: str, command: str, target: str, cluster: str, reason: str = ""):
        self.user = user
        self.command = command
        self.target = target
        self.cluster = cluster
        self.reason = reason
        msg = f"权限被拒绝: user={user}, command={command}, target={target}, cluster={cluster}"
        if reason:
            msg += f" - {reason}"
        super().__init__(msg)


class PermissionChecker:
    """OpenFGA 权限检查器。

    权限检查逻辑:
        1. 用户是否是 cluster 的 member
        2. 用户对 command 是否有 can_execute 权限
        3. target 归属的 target_group
        4. 用户对 target_group 是否有 can_access 权限

    Attributes:
        config: OpenFGA 连接配置。
        enabled: 是否启用权限检查，False 时所有检查直接通过。
        client: OpenFGA 客户端，未初始化时为 None。
    """

    def __init__(self, config: Optional[OpenFGAConfig] = None, enabled: bool = True):
        if config is None:
            config = OpenFGAConfigManager().load()

        self.config = config
        self.enabled = enabled
        self.client = OpenFGAClientWrapper(config) if config.is_initialized() else None

    def get_current_user(self) -> str:
        """获取当前用户名。

        仅使用系统登录用户，不信任环境变量（防止伪造）。

        Returns:
            当前用户名字符串。
        """
        return getpass.getuser()

    def check(self, command: str, target: str, cluster: str, user: Optional[str] = None) -> bool:
        """检查用户是否有权限执行命令。

        Args:
            command: 命令名称，如 "ping"、"cmd"。
            target: 目标主机名。
            cluster: 集群名称。
            user: 用户名，默认读取当前用户。

        Returns:
            True 表示有权限，False 表示无权限或检查失败。
        """
        if not self.enabled:
            return True

        if not self.client:
            return False

        if user is None:
            user = self.get_current_user()

        try:
            # 1. 检查用户是否是 cluster 成员
            if not self.client.check(f"user:{user}", "member", f"cluster:{cluster}"):
                return False

            # 2. 检查用户对 command 是否有执行权限
            if not self.client.check(f"user:{user}", "can_execute", f"command:{command}"):
                return False

            # 3. 查询 target 归属的 target_group（object=target:xxx, relation=group）
            tuples = self.client.read_tuples(object=f"target:{target}", relation="group")
            if not tuples:
                return False

            # 4. 检查用户对 target_group 是否有访问权限
            for t in tuples:
                if self.client.check(f"user:{user}", "can_access", t["user"]):
                    return True

            return False

        except Exception as e:
            print(f"权限检查失败: {e}")
            return False

    def require(self, command: str, target: str, cluster: str, user: Optional[str] = None) -> None:
        """检查权限，无权限时抛出 PermissionDeniedError。

        Args:
            command: 命令名称。
            target: 目标主机名。
            cluster: 集群名称。
            user: 用户名，默认��取当前用户。

        Raises:
            PermissionDeniedError: 用户无权限时抛出，包含详细拒绝原因。
        """
        if user is None:
            user = self.get_current_user()

        if not self.check(command, target, cluster, user):
            reason = self._get_denial_reason(user, command, target, cluster)
            raise PermissionDeniedError(user, command, target, cluster, reason)

    def _get_denial_reason(self, user: str, command: str, target: str, cluster: str) -> str:
        """获取权限拒绝的详细原因，用于提示用户具体缺少哪项权限。

        Args:
            user: 用户名。
            command: 命令名称。
            target: 目标主机名。
            cluster: 集群名称。

        Returns:
            人类可读的拒绝原因字符串。
        """
        if not self.client:
            return "OpenFGA 未初始化，请先运行 'salt permission init'"

        try:
            # 检查是否是 cluster 成员
            if not self.client.check(f"user:{user}", "member", f"cluster:{cluster}"):
                return f"用户 '{user}' 不是环境 '{cluster}' 的成员"

            # 检查命令权限
            if not self.client.check(f"user:{user}", "can_execute", f"command:{command}"):
                return f"用户 '{user}' 没有执行命令 '{command}' 的权限"

            # 检查目标主机权限
            tuples = self.client.read_tuples(object=f"target:{target}", relation="group")
            if not tuples:
                return f"目标主机 '{target}' 不属于任何目标组"

            return f"用户 '{user}' 没有访问目标主机 '{target}' 的权限"

        except Exception as e:
            return f"权限检查失败: {e}"


def require_permission(command: str, target_param: str = "tgt"):
    """权限检查装饰器。

    自动从方法参数中提取 target，从 self.cluster_name 获取 cluster，
    从 self.permission_checker 获取检查器。权限不足时打印错误并提前返回。

    Args:
        command: 命令名称，如 "ping"、"cmd"。
        target_param: 目标主机参数名，默认为 "tgt"。

    Returns:
        方法装饰器。

    Example:
        @require_permission("ping")
        def __call__(self, tgt="*"):
            ...
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs) -> Any:
            checker: Optional[PermissionChecker] = getattr(self, "permission_checker", None)
            if checker and checker.enabled:
                # 从参数中提取 target
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())

                if target_param in kwargs:
                    target = kwargs[target_param]
                elif target_param in params:
                    idx = params.index(target_param) - 1  # 减去 self
                    target = args[idx] if idx < len(args) else sig.parameters[target_param].default
                else:
                    target = "*"

                cluster = getattr(self, "cluster_name", "default")
                formatter = getattr(self, "formatter", None)

                try:
                    checker.require(command, str(target), cluster)
                except PermissionDeniedError as e:
                    if formatter:
                        formatter.print_error(str(e))
                    else:
                        print(f"错误: {e}")
                    return

            return method(self, *args, **kwargs)
        return wrapper
    return decorator
