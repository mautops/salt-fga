"""OpenFGA SDK 客户端封装"""

from contextlib import contextmanager
from typing import List, Optional, Dict

import openfga_sdk
from openfga_sdk.sync import OpenFgaClient
from openfga_sdk import ClientConfiguration

from .config import OpenFGAConfig


@contextmanager
def get_client(config: OpenFGAConfig):
    """返回已配置的 OpenFgaClient 上下文管理器。

    Args:
        config: OpenFGA 连接配置。

    Yields:
        已配置的 OpenFgaClient 实例。

    Raises:
        ValueError: 配置未初始化（缺少 store_id 或 model_id）时抛出。
    """
    if not config.is_initialized():
        raise ValueError("OpenFGA 配置未初始化，请先运行 'salt permission init'")

    configuration = ClientConfiguration(
        api_url=config.api_url,
        store_id=config.store_id,
        authorization_model_id=config.authorization_model_id,
    )
    yield OpenFgaClient(configuration)


class OpenFGAClientWrapper:
    """封装常用的 OpenFGA 读写操作。

    提供写入/删除关系元组、权限检查、对象列表查询等方法。

    Attributes:
        config: OpenFGA 连接配置。
    """

    def __init__(self, config: OpenFGAConfig):
        self.config = config

    def write_tuples(self, tuples: List[Dict[str, str]]) -> None:
        """写入关系元组。

        Args:
            tuples: 元组列表，每项格式为 {"user": ..., "relation": ..., "object": ...}。
        """
        with get_client(self.config) as client:
            keys = [openfga_sdk.TupleKey(user=t["user"], relation=t["relation"], object=t["object"]) for t in tuples]
            client.write(openfga_sdk.WriteRequest(writes=openfga_sdk.WriteRequestWrites(tuple_keys=keys)))

    def delete_tuples(self, tuples: List[Dict[str, str]]) -> None:
        """删除关系元组。

        Args:
            tuples: 元组列表，每项格式为 {"user": ..., "relation": ..., "object": ...}。
        """
        with get_client(self.config) as client:
            # 删除接口要求使用 TupleKeyWithoutCondition
            keys = [openfga_sdk.TupleKeyWithoutCondition(user=t["user"], relation=t["relation"], object=t["object"]) for t in tuples]
            client.write(openfga_sdk.WriteRequest(deletes=openfga_sdk.WriteRequestDeletes(tuple_keys=keys)))

    def check(self, user: str, relation: str, object: str) -> bool:
        """检查 user 对 object 是否具有指定 relation。

        Args:
            user: 用户标识，如 "user:alice"。
            relation: 关系名称，如 "can_execute"。
            object: 对象标识，如 "command:ping"。

        Returns:
            True 表示具有该关系权限。
        """
        with get_client(self.config) as client:
            resp = client.check(openfga_sdk.CheckRequest(user=user, relation=relation, object=object))
            return resp.allowed

    def list_objects(self, user: str, relation: str, type: str) -> List[str]:
        """列出 user 具有指定 relation 的所有对象。

        Args:
            user: 用户标识，如 "user:alice"。
            relation: 关系名称，如 "can_access"。
            type: 对象类型，如 "target_group"。

        Returns:
            满足条件的对象标识列表，如 ["target_group:web-servers"]。
        """
        with get_client(self.config) as client:
            resp = client.list_objects(openfga_sdk.ListObjectsRequest(user=user, relation=relation, type=type))
            return resp.objects

    def read_tuples(self, user: Optional[str] = None, relation: Optional[str] = None, object: Optional[str] = None) -> List[Dict[str, str]]:
        """读取关系元组，支持按 user/relation/object 过滤。

        Args:
            user: 按用户过滤（可选）。
            relation: 按关系过滤（可选）。
            object: 按对象过滤（可选）。

        Returns:
            元组列表，每项包含 user、relation、object 字段。
        """
        with get_client(self.config) as client:
            body = openfga_sdk.ReadRequest()
            if user or relation or object:
                body.tuple_key = openfga_sdk.ReadRequestTupleKey(user=user, relation=relation, object=object)

            resp = client.read(body)
            if not resp.tuples:
                return []

            return [
                {"user": t.key.user, "relation": t.key.relation, "object": t.key.object}
                for t in resp.tuples
            ]
