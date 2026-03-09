import inspect
from functools import wraps
from typing import Callable, Any

from openfga_sdk.sync import OpenFgaClient
from openfga_sdk import ClientConfiguration
from openfga_sdk.client.models.check_request import ClientCheckRequest

from .config import load_config, OpenFGAConfig


def _client(config: OpenFGAConfig) -> OpenFgaClient:
    return OpenFgaClient(
        ClientConfiguration(
            api_url=config.api_url,
            store_id=config.store_id,
            authorization_model_id=config.authorization_model_id,
        )
    )


def require_permission(command: str, target_param: str = "tgt"):
    """权限检查装饰器。

    从 self.no_auth 读取是否跳过检查，从 self.cluster_name 获取集群名。
    OpenFGA 未初始化时自动跳过（降级放行）。

    Example:
        @require_permission("ping")
        def __call__(self, tgt="*"):
            ...
    """

    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs) -> Any:
            if getattr(self, "no_auth", False):
                return method(self, *args, **kwargs)

            config = load_config()
            if not config.is_initialized():
                return method(self, *args, **kwargs)

            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            if target_param in kwargs:
                target = kwargs[target_param]
            elif target_param in params:
                idx = params.index(target_param) - 1
                target = (
                    args[idx]
                    if idx < len(args)
                    else sig.parameters[target_param].default
                )
            else:
                target = "*"

            cluster = getattr(self, "cluster_name", "default")
            user = getattr(self, "username", None)
            formatter = getattr(self, "formatter", None)

            if not user:
                msg = "权限检查失败: 未指定用户名，请使用 --user 参数"
                formatter.print_error(msg) if formatter else print(f"错误: {msg}")
                return

            try:
                fga = _client(config)
                checks = [
                    fga.check(
                        ClientCheckRequest(
                            user=f"user:{user}",
                            relation="member",
                            object=f"cluster:{cluster}",
                        )
                    ).allowed,
                    fga.check(
                        ClientCheckRequest(
                            user=f"user:{user}",
                            relation="can_execute",
                            object=f"command:{command}",
                        )
                    ).allowed,
                ]
                # 通配符 target 跳过 can_access 检查
                if "*" not in str(target) and "?" not in str(target):
                    checks.append(
                        fga.check(
                            ClientCheckRequest(
                                user=f"user:{user}",
                                relation="can_access",
                                object=f"target:{target}",
                            )
                        ).allowed
                    )
                allowed = all(checks)
            except Exception as e:
                msg = f"权限检查失败: {e}"
                formatter.print_error(msg) if formatter else print(f"错误: {msg}")
                return

            if not allowed:
                msg = f"权限被拒绝: user={user}, command={command}, target={target}, cluster={cluster}"
                formatter.print_error(msg) if formatter else print(f"错误: {msg}")
                return

            return method(self, *args, **kwargs)

        return wrapper

    return decorator
