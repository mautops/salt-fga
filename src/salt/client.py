"""Salt API 客户端 - 封装 Salt Cherry API 调用"""

import requests
from typing import Any, Dict, List, Optional

from .auth import TokenManager
from .config import ClusterConfig


class SaltAPIError(Exception):
    """Salt API 错误"""

    pass


class SaltAPIClient:
    """Salt API 客户端"""

    def __init__(self, cluster: ClusterConfig, token_manager: TokenManager):
        self.cluster = cluster
        self.token_manager = token_manager
        self._token: Optional[str] = None

    def _get_token(self) -> str:
        """获取有效的 Token（从缓存或重新登录）"""
        # 尝试从缓存加载
        if self._token is None:
            self._token = self.token_manager.load_token(self.cluster)

        # 如果缓存中没有或已过期，重新登录
        if self._token is None:
            self._token = self._login()

        return self._token

    def _login(self) -> str:
        """登录获取 Token"""
        url = f"{self.cluster.base_url}/login"

        payload = {
            "username": self.cluster.username,
            "password": self.cluster.password,
            "eauth": self.cluster.eauth,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Salt API 登录返回格式：
            # {"return": {"token": "...", "expire": 1234567890.0, ...}}
            # 部分版本可能返回列表格式：{"return": [{"token": "..."}]}
            if "return" not in data or not data["return"]:
                raise SaltAPIError("登录响应格式错误")

            ret = data["return"]
            if isinstance(ret, list):
                ret = ret[0] if ret else {}

            token = ret.get("token")
            if not token:
                raise SaltAPIError("登录失败：未返回 token")

            # 保存到缓存，同时传入 API 返回的精确过期时间
            expire = ret.get("expire")
            self.token_manager.save_token(self.cluster, token, expire=expire)

            return token

        except requests.RequestException as e:
            raise SaltAPIError(f"登录请求失败: {e}")
        except (KeyError, IndexError, ValueError) as e:
            raise SaltAPIError(f"解析登录响应失败: {e}")

    def execute(
        self,
        client: str,
        tgt: str,
        fun: str,
        arg: Optional[List[Any]] = None,
        kwarg: Optional[Dict[str, Any]] = None,
        full_return: bool = False,
    ) -> Dict:
        """执行 Salt 命令"""
        token = self._get_token()
        url = f"{self.cluster.base_url}/"

        payload = {
            "client": client,
            "tgt": tgt,
            "fun": fun,
        }

        if arg:
            payload["arg"] = arg
        if kwarg:
            payload["kwarg"] = kwarg
        if full_return:
            payload["full_return"] = True

        headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=[payload], headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            # Salt API 返回格式: {"return": [{...}]}
            if "return" not in data:
                raise SaltAPIError("响应格式错误：缺少 return 字段")

            return data

        except requests.RequestException as e:
            # Token 可能过期，清除缓存并重试一次
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                self.token_manager.clear_token(self.cluster)
                self._token = None
                # 递归重试一次
                return self.execute(client, tgt, fun, arg, kwarg, full_return)

            raise SaltAPIError(f"API 请求失败: {e}")
        except (KeyError, ValueError) as e:
            raise SaltAPIError(f"解析响应失败: {e}")

    def get_minions(self, mid: Optional[str] = None) -> Dict:
        """
        获取 minion 信息

        Args:
            mid: minion ID，如果为 None 则返回所有 minions
        """
        token = self._get_token()

        if mid:
            url = f"{self.cluster.base_url}/minions/{mid}"
        else:
            url = f"{self.cluster.base_url}/minions"

        headers = {"X-Auth-Token": token}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise SaltAPIError(f"获取 minion 信息失败: {e}")

    def get_jobs(self, jid: Optional[str] = None) -> Dict:
        """
        获取任务信息

        Args:
            jid: job ID，如果为 None 则返回所有任务
        """
        token = self._get_token()

        if jid:
            url = f"{self.cluster.base_url}/jobs/{jid}"
        else:
            url = f"{self.cluster.base_url}/jobs"

        headers = {"X-Auth-Token": token}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise SaltAPIError(f"获取任务信息失败: {e}")

    def get_keys(self, mid: Optional[str] = None) -> Dict:
        """
        获取 minion keys

        Args:
            mid: minion ID，如果指定则只返回该 minion 的 key 信息
        """
        token = self._get_token()

        if mid:
            url = f"{self.cluster.base_url}/keys/{mid}"
        else:
            url = f"{self.cluster.base_url}/keys"

        headers = {"X-Auth-Token": token}

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise SaltAPIError(f"获取 keys 失败: {e}")

    def execute_wheel(
        self,
        fun: str,
        kwarg: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        执行 wheel 客户端命令（用于 master 端操作，如 key 管理）

        Args:
            fun: 要执行的函数（如 key.accept, key.reject, key.delete）
            kwarg: 关键字参数
        """
        token = self._get_token()
        url = f"{self.cluster.base_url}/"

        payload = {
            "client": "wheel",
            "fun": fun,
        }

        if kwarg:
            payload["kwarg"] = kwarg

        headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(url, json=[payload], headers=headers, timeout=60)
            response.raise_for_status()

            data = response.json()

            if "return" not in data:
                raise SaltAPIError("响应格式错误：缺少 return 字段")

            return data

        except requests.RequestException as e:
            # Token 可能过期，清除缓存并重试一次
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                self.token_manager.clear_token(self.cluster)
                self._token = None
                # 递归重试一次
                return self.execute_wheel(fun, kwarg)

            raise SaltAPIError(f"API 请求失败: {e}")
        except (KeyError, ValueError) as e:
            raise SaltAPIError(f"解析响应失败: {e}")

    def run_command(
        self,
        tgt: str,
        fun: str,
        arg: Optional[List[Any]] = None,
        kwarg: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        使用 /run 端点直接执行命令（绕过 session）

        Args:
            tgt: 目标主机
            fun: 要执行的函数
            arg: 位置参数
            kwarg: 关键字参数
        """
        url = f"{self.cluster.base_url}/run"

        payload = {
            "client": "local",
            "tgt": tgt,
            "fun": fun,
            "eauth": self.cluster.eauth,
            "username": self.cluster.username,
            "password": self.cluster.password,
        }

        if arg:
            payload["arg"] = arg
        if kwarg:
            payload["kwarg"] = kwarg

        try:
            response = requests.post(url, json=[payload], timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise SaltAPIError(f"执行命令失败: {e}")

