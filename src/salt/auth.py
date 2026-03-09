"""认证和 Token 管理模块"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import ClusterConfig


class TokenManager:
    """Token 管理器"""

    def __init__(self, config_dir: Path):
        self.token_dir = config_dir / "tokens"
        self.token_dir.mkdir(parents=True, exist_ok=True)

    def _parse_expire_time(self, expire_str: str) -> int:
        """解析过期时间字符串（如 '10h'）为秒数"""
        expire_str = expire_str.strip().lower()

        if expire_str.endswith("h"):
            hours = int(expire_str[:-1])
            return hours * 3600
        elif expire_str.endswith("m"):
            minutes = int(expire_str[:-1])
            return minutes * 60
        elif expire_str.endswith("s"):
            seconds = int(expire_str[:-1])
            return seconds
        else:
            # 默认按小时处理
            return int(expire_str) * 3600

    def get_token_file(self, cluster_name: str) -> Path:
        """获取 Token 文件路径"""
        return self.token_dir / f"{cluster_name}.json"

    def load_token(self, cluster: ClusterConfig) -> Optional[str]:
        """加载缓存的 Token，如果过期则返回 None"""
        token_file = self.get_token_file(cluster.name)

        if not token_file.exists():
            return None

        try:
            with open(token_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            token = data.get("token")
            timestamp = data.get("timestamp")

            if not token or not timestamp:
                return None

            # 优先使用 API 返回的精确过期时间戳
            if "expire" in data:
                if time.time() >= data["expire"]:
                    return None
            else:
                # 回退到基于配置的过期时间计算
                expire_seconds = self._parse_expire_time(cluster.token_expire)
                elapsed = time.time() - timestamp
                if elapsed >= expire_seconds:
                    return None

            return token

        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def save_token(self, cluster: ClusterConfig, token: str, expire: Optional[float] = None):
        """
        保存 Token 到缓存

        Args:
            cluster: 集群配置
            token: Token 字符串
            expire: API 返回的过期 Unix 时间戳（优先使用，没有则基于配置计算）
        """
        token_file = self.get_token_file(cluster.name)

        data = {
            "token": token,
            "timestamp": time.time(),
            "cluster": cluster.name,
        }

        # 如果 API 返回了精确的过期时间，直接存储
        if expire is not None:
            data["expire"] = expire

        with open(token_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def clear_token(self, cluster: ClusterConfig):
        """清除缓存的 Token"""
        token_file = self.get_token_file(cluster.name)
        if token_file.exists():
            token_file.unlink()
