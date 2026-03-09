"""配置管理模块 - 读取和管理 Salt 环境配置"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class ClusterConfig:
    """环境配置类"""

    def __init__(self, data: Dict):
        self.name = data["name"]
        self.description = data.get("description", "")
        self.base_url = data["base_url"]
        self.username = data["username"]
        self.password = data["password"]
        self.eauth = data.get("eauth", "file")
        self.token_expire = data.get("token_expire", "10h")

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "base_url": self.base_url,
            "username": self.username,
            "password": self.password,
            "eauth": self.eauth,
            "token_expire": self.token_expire,
        }


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_dir = Path.home() / ".config" / "salt"
        self.config_file = self.config_dir / "credentials.json"
        self._clusters: Optional[List[ClusterConfig]] = None

    def ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        token_dir = self.config_dir / "tokens"
        token_dir.mkdir(exist_ok=True)

    def load_clusters(self) -> List[ClusterConfig]:
        """加载环境配置"""
        if self._clusters is not None:
            return self._clusters

        if not self.config_file.exists():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_file}\n"
                f"请创建配置文件，格式参考 CLAUDE.md"
            )

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("配置文件格式错误：应为 JSON 数组")

            self._clusters = [ClusterConfig(item) for item in data]

            if not self._clusters:
                raise ValueError("配置文件中没有定义任何环境")

            return self._clusters

        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件 JSON 格式错误: {e}")

    def get_cluster(self, name: Optional[str] = None) -> ClusterConfig:
        """获取指定环境配置，如果未指定则返回默认环境（第一个）"""
        clusters = self.load_clusters()

        if name is None:
            return clusters[0]

        for cluster in clusters:
            if cluster.name == name:
                return cluster

        available = ", ".join(c.name for c in clusters)
        raise ValueError(f"环境 '{name}' 不存在。可用环境: {available}")

    def list_clusters(self) -> List[ClusterConfig]:
        """列出所有环境"""
        return self.load_clusters()
