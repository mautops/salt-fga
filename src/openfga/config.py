import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path.home() / ".config" / "salt" / "openfga.json"


@dataclass
class OpenFGAConfig:
    api_url: str = "http://localhost:8080"
    store_id: Optional[str] = None
    authorization_model_id: Optional[str] = None

    def is_initialized(self) -> bool:
        return bool(self.store_id and self.authorization_model_id)


def load_config() -> OpenFGAConfig:
    if not CONFIG_PATH.exists():
        return OpenFGAConfig()
    with open(CONFIG_PATH) as f:
        data = json.load(f)
    return OpenFGAConfig(
        api_url=data.get("api_url", "http://localhost:8080"),
        store_id=data.get("store_id"),
        authorization_model_id=data.get("authorization_model_id"),
    )


def save_config(config: OpenFGAConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(
            {
                "api_url": config.api_url,
                "store_id": config.store_id,
                "authorization_model_id": config.authorization_model_id,
            },
            f,
            indent=2,
        )
