"""OpenFGA 连接配置管理"""

import json
from pathlib import Path
from typing import Optional, List

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "salt" / "openfga.json"


class OpenFGAConfig:
    """OpenFGA 连接配置。

    存储连接 OpenFGA 服务所需的参数，以及管理员列表。

    Attributes:
        api_url: OpenFGA 服务 API 地址。
        store_id: OpenFGA Store ID。
        authorization_model_id: 授权模型 ID。
        admins: 有权管理权限规则的用户列表。
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8080",
        store_id: Optional[str] = None,
        authorization_model_id: Optional[str] = None,
        admins: Optional[List[str]] = None,
    ):
        self.api_url = api_url
        self.store_id = store_id
        self.authorization_model_id = authorization_model_id
        self.admins = admins or []

    def is_initialized(self) -> bool:
        """检查 Store 和授权模型是否已初始化。

        Returns:
            True 表示 store_id 和 authorization_model_id 均已设置。
        """
        return bool(self.store_id and self.authorization_model_id)

    def is_admin(self, user: str) -> bool:
        """检查用户是否在管理员列表中。

        Args:
            user: 用户名。

        Returns:
            True 表示该用户是管理员。
        """
        return user in self.admins

    def to_dict(self) -> dict:
        """将配置序列化为字典。

        Returns:
            包含所有配置字段的字典。
        """
        return {
            "api_url": self.api_url,
            "store_id": self.store_id,
            "authorization_model_id": self.authorization_model_id,
            "admins": self.admins,
        }


class OpenFGAConfigManager:
    """OpenFGA 配置文件管理器。

    负责从 JSON 文件加载和保存 OpenFGAConfig 配置。

    Attributes:
        config_path: 配置文件路径，默认为 ~/.config/salt/openfga.json。
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH

    def load(self) -> OpenFGAConfig:
        """从文件加载配置，文件不存在时返回默认配置。

        Returns:
            从文件加载的 OpenFGAConfig，或带有默认值的空配置。
        """
        if not self.config_path.exists():
            return OpenFGAConfig()

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return OpenFGAConfig(
            api_url=data.get("api_url", "http://localhost:8080"),
            store_id=data.get("store_id"),
            authorization_model_id=data.get("authorization_model_id"),
            admins=data.get("admins", []),
        )

    def save(self, config: OpenFGAConfig) -> None:
        """将配置保存到文件，父目录不存在时自动创建。

        Args:
            config: 要保存的配置对象。
        """
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

    def update(self, store_id: str = None, authorization_model_id: str = None) -> OpenFGAConfig:
        """更新部分配置字段并保存。

        Args:
            store_id: 新的 Store ID（可选）。
            authorization_model_id: 新的授权模型 ID（可选）。

        Returns:
            更新后的配置对象。
        """
        config = self.load()
        if store_id is not None:
            config.store_id = store_id
        if authorization_model_id is not None:
            config.authorization_model_id = authorization_model_id
        self.save(config)
        return config
