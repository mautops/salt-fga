"""OpenFGA SDK 客户端封装"""

from typing import List, Optional, Dict

from openfga_sdk.sync import OpenFgaClient
from openfga_sdk import ClientConfiguration
from openfga_sdk.client.models.tuple import ClientTuple
from openfga_sdk.client.models.write_request import ClientWriteRequest
from openfga_sdk.client.models.check_request import ClientCheckRequest
from openfga_sdk.client.models.list_objects_request import ClientListObjectsRequest
from openfga_sdk.models.read_request_tuple_key import ReadRequestTupleKey

from .config import OpenFGAConfig


class OpenFGAClientWrapper:
    """封装常用的 OpenFGA 读写操作。"""

    def __init__(self, config: OpenFGAConfig):
        if not config.is_initialized():
            raise ValueError("OpenFGA 配置未初始化，请先运行 'salt permission init'")
        self.config = config
        self._client = OpenFgaClient(ClientConfiguration(
            api_url=config.api_url,
            store_id=config.store_id,
            authorization_model_id=config.authorization_model_id,
        ))

    def write_tuples(self, tuples: List[Dict[str, str]]) -> None:
        keys = [ClientTuple(user=t["user"], relation=t["relation"], object=t["object"]) for t in tuples]
        self._client.write(ClientWriteRequest(writes=keys))

    def delete_tuples(self, tuples: List[Dict[str, str]]) -> None:
        keys = [ClientTuple(user=t["user"], relation=t["relation"], object=t["object"]) for t in tuples]
        self._client.write(ClientWriteRequest(deletes=keys))

    def check(self, user: str, relation: str, object: str) -> bool:
        resp = self._client.check(ClientCheckRequest(user=user, relation=relation, object=object))
        return resp.allowed

    def list_objects(self, user: str, relation: str, type: str) -> List[str]:
        resp = self._client.list_objects(ClientListObjectsRequest(user=user, relation=relation, type=type))
        return resp.objects

    def read_tuples(self, user: Optional[str] = None, relation: Optional[str] = None, object: Optional[str] = None) -> List[Dict[str, str]]:
        key = ReadRequestTupleKey(user=user, relation=relation, object=object) if (user or relation or object) else ReadRequestTupleKey()
        resp = self._client.read(key)
        if not resp.tuples:
            return []
        return [
            {"user": t.key.user, "relation": t.key.relation, "object": t.key.object}
            for t in resp.tuples
        ]
