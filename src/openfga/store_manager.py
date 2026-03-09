"""OpenFGA Store 和 Model 管理器"""

import json
from pathlib import Path
from typing import Optional

import openfga_sdk
from openfga_sdk.sync import OpenFgaClient
from openfga_sdk import ClientConfiguration

from .config import OpenFGAConfig, OpenFGAConfigManager


# 授权模型文件路径
AUTHORIZATION_MODEL_FILE = Path(__file__).parent / "authorization_model.fga"


class StoreManager:
    """OpenFGA Store 和授权模型管理器。

    负责创建 Store、写入授权模型、保存配置等初始化操作。

    Attributes:
        config_manager: 配置管理器实例。
    """

    def __init__(self, config_manager: Optional[OpenFGAConfigManager] = None):
        """初始化 Store 管理器。

        Args:
            config_manager: 配置管理器实例，默认创建新实例。
        """
        self.config_manager = config_manager or OpenFGAConfigManager()

    def init_store(self, name: str = "salt-cli") -> OpenFGAConfig:
        """初始化 OpenFGA Store 和授权模型。

        执行步骤:
            1. 创建 Store
            2. 读取 .fga 文件
            3. 写入授权模型
            4. 保存 store_id 和 model_id 到配置文件

        Args:
            name: Store 名称，默认为 "salt-cli"。

        Returns:
            更新后的配置对象。

        Raises:
            Exception: 初始化失败时抛出，包含详细错误信息。
        """
        # 加载当前配置
        config = self.config_manager.load()

        # 创建临时客户端（不需要 store_id 和 model_id）
        configuration = ClientConfiguration(api_url=config.api_url)
        client = OpenFgaClient(configuration)

        try:
            # 1. 创建 Store
            store_request = openfga_sdk.CreateStoreRequest(name=name)
            store_response = client.create_store(store_request)
            store_id = store_response.id

            print(f"✓ 创建 Store 成功: {store_id}")

            # 2. 读取授权模型文件
            if not AUTHORIZATION_MODEL_FILE.exists():
                raise FileNotFoundError(f"授权模型文件不存在: {AUTHORIZATION_MODEL_FILE}")

            with open(AUTHORIZATION_MODEL_FILE, "r", encoding="utf-8") as f:
                model_dsl = f.read()

            # 3. 写入授权模型
            # 更新客户端配置，添加 store_id
            configuration.store_id = store_id
            client = OpenFgaClient(configuration)

            # 解析 DSL 并写入模型
            model_request = openfga_sdk.WriteAuthorizationModelRequest(
                schema_version="1.1",
                type_definitions=self._parse_fga_dsl(model_dsl),
            )
            model_response = client.write_authorization_model(model_request)
            model_id = model_response.authorization_model_id

            print(f"✓ 写入授权模型成功: {model_id}")

            # 4. 保存配置
            config.store_id = store_id
            config.authorization_model_id = model_id
            self.config_manager.save(config)

            print(f"✓ 配置已保存到: {self.config_manager.config_path}")

            return config

        except Exception as e:
            raise Exception(f"初始化 Store 失败: {e}")

    def get_model_id(self) -> Optional[str]:
        """获取当前授权模型 ID。

        Returns:
            授权模型 ID，如果未初始化则返回 None。
        """
        config = self.config_manager.load()
        return config.authorization_model_id

    def _parse_fga_dsl(self, dsl: str) -> list:
        """解析 OpenFGA DSL 为 TypeDefinition 列表。

        注意: 这是一个简化的解析器，仅支持基本的 DSL 语法。
        对于复杂的模型，建议使用 OpenFGA CLI 工具生成 JSON。

        Args:
            dsl: OpenFGA DSL 字符串。

        Returns:
            TypeDefinition 列表。

        Raises:
            NotImplementedError: DSL 解析功能尚未实现，提示使用 fga CLI 工具。
        """
        # 简化实现：使用 OpenFGA 的 transformer 来解析 DSL
        # 这里我们需要手动构建 TypeDefinition
        # 由于 SDK 没有提供 DSL 解析器，我们需要手动解析或使用 CLI 工具

        # 临时方案：返回空列表，让用户使用 fga CLI 工具
        # 或者我们可以调用 fga CLI 来转换 DSL 到 JSON
        raise NotImplementedError(
            "DSL 解析功能尚未实现。请使用以下命令手动初始化:\n"
            "1. fga model transform --file src/openfga/authorization_model.fga > model.json\n"
            "2. 使用 model.json 内容调用 API"
        )

    def init_store_from_json(self, name: str = "salt-cli", model_json_path: Optional[Path] = None) -> OpenFGAConfig:
        """从 JSON 文件初始化 Store 和授权模型。

        Args:
            name: Store 名称，默认为 "salt-cli"。
            model_json_path: 授权模型 JSON 文件路径，默认为 authorization_model.json。

        Returns:
            更新后的配置对象。

        Raises:
            Exception: 初始化失败时抛出，包含详细错误信息。
            FileNotFoundError: JSON 文件不存在时抛出，提示使用 fga CLI 转换。
        """
        # 加载当前配置
        config = self.config_manager.load()

        # 创建临时客户端
        configuration = ClientConfiguration(api_url=config.api_url)
        client = OpenFgaClient(configuration)

        try:
            # 1. 创建 Store
            store_request = openfga_sdk.CreateStoreRequest(name=name)
            store_response = client.create_store(store_request)
            store_id = store_response.id

            print(f"✓ 创建 Store 成功: {store_id}")

            # 2. 读取授权模型 JSON
            if model_json_path is None:
                model_json_path = AUTHORIZATION_MODEL_FILE.with_suffix(".json")

            if not model_json_path.exists():
                raise FileNotFoundError(
                    f"授权模型 JSON 文件不存在: {model_json_path}\n"
                    f"请先运行: fga model transform --file {AUTHORIZATION_MODEL_FILE} > {model_json_path}"
                )

            with open(model_json_path, "r", encoding="utf-8") as f:
                model_data = json.load(f)

            # 3. 写入授权模型
            configuration.store_id = store_id
            client = OpenFgaClient(configuration)

            # 构建请求
            type_definitions = []
            for type_def in model_data.get("type_definitions", []):
                type_definitions.append(openfga_sdk.TypeDefinition(**type_def))

            model_request = openfga_sdk.WriteAuthorizationModelRequest(
                schema_version=model_data.get("schema_version", "1.1"),
                type_definitions=type_definitions,
            )
            model_response = client.write_authorization_model(model_request)
            model_id = model_response.authorization_model_id

            print(f"✓ 写入授权模型成功: {model_id}")

            # 4. 保存配置
            config.store_id = store_id
            config.authorization_model_id = model_id
            self.config_manager.save(config)

            print(f"✓ 配置已保存到: {self.config_manager.config_path}")

            return config

        except Exception as e:
            raise Exception(f"初始化 Store 失败: {e}")
