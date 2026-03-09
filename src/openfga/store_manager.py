"""OpenFGA Store 和 Model 管理器"""

import json
import subprocess
from pathlib import Path
from typing import Optional

import openfga_sdk
from openfga_sdk.sync import OpenFgaClient
from openfga_sdk import ClientConfiguration

from .config import OpenFGAConfig, OpenFGAConfigManager


AUTHORIZATION_MODEL_FILE = Path(__file__).parent / "authorization_model.fga"


class StoreManager:
    """OpenFGA Store 和授权模型管理器。"""

    def __init__(self, config_manager: Optional[OpenFGAConfigManager] = None):
        self.config_manager = config_manager or OpenFGAConfigManager()

    def init_store(self, name: str = "salt-cli") -> OpenFGAConfig:
        """初始化 OpenFGA Store 和授权模型。

        直接读取 .fga 文件，通过 fga CLI 在内存中转换，无需中间 JSON 文件。
        """
        if not AUTHORIZATION_MODEL_FILE.exists():
            raise FileNotFoundError(f"授权模型文件不存在: {AUTHORIZATION_MODEL_FILE}")

        # 将 .fga DSL 转换为 JSON（内存中完成，无需写入文件）
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

        config = self.config_manager.load()
        configuration = ClientConfiguration(api_url=config.api_url)
        client = OpenFgaClient(configuration)

        try:
            store_response = client.create_store(openfga_sdk.CreateStoreRequest(name=name))
            store_id = store_response.id
            print(f"✓ 创建 Store 成功: {store_id}")

            configuration.store_id = store_id
            client = OpenFgaClient(configuration)

            type_definitions = [
                openfga_sdk.TypeDefinition(**td)
                for td in model_data.get("type_definitions", [])
            ]
            model_request = openfga_sdk.WriteAuthorizationModelRequest(
                schema_version=model_data.get("schema_version", "1.1"),
                type_definitions=type_definitions,
            )
            model_response = client.write_authorization_model(model_request)
            model_id = model_response.authorization_model_id
            print(f"✓ 写入授权模型成功: {model_id}")

            config.store_id = store_id
            config.authorization_model_id = model_id
            self.config_manager.save(config)
            print(f"✓ 配置已保存到: {self.config_manager.config_path}")

            return config

        except Exception as e:
            raise Exception(f"初始化 Store 失败: {e}")

    def get_model_id(self) -> Optional[str]:
        config = self.config_manager.load()
        return config.authorization_model_id
