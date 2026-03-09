"""OpenFGA 权限模块单元测试"""

import json
from unittest.mock import MagicMock

from openfga.config import OpenFGAConfig, load_config, save_config
from openfga.checker import require_permission


# ========== OpenFGAConfig ==========


class TestOpenFGAConfig:
    def test_default_values(self):
        config = OpenFGAConfig()
        assert config.api_url == "http://localhost:8080"
        assert config.store_id is None
        assert config.authorization_model_id is None

    def test_is_initialized_false_when_empty(self):
        assert not OpenFGAConfig().is_initialized()

    def test_is_initialized_false_when_partial(self):
        assert not OpenFGAConfig(store_id="s").is_initialized()
        assert not OpenFGAConfig(authorization_model_id="m").is_initialized()

    def test_is_initialized_true(self):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        assert config.is_initialized()


# ========== load_config / save_config ==========


class TestConfigIO:
    def test_load_returns_default_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr("openfga.config.CONFIG_PATH", tmp_path / "openfga.json")
        config = load_config()
        assert config.api_url == "http://localhost:8080"
        assert not config.is_initialized()

    def test_save_and_load_roundtrip(self, tmp_path, monkeypatch):
        path = tmp_path / "openfga.json"
        monkeypatch.setattr("openfga.config.CONFIG_PATH", path)

        original = OpenFGAConfig(
            api_url="http://test:8080",
            store_id="store-abc",
            authorization_model_id="model-xyz",
        )
        save_config(original)
        loaded = load_config()

        assert loaded.api_url == "http://test:8080"
        assert loaded.store_id == "store-abc"
        assert loaded.authorization_model_id == "model-xyz"

    def test_saved_file_has_no_admins_field(self, tmp_path, monkeypatch):
        path = tmp_path / "openfga.json"
        monkeypatch.setattr("openfga.config.CONFIG_PATH", path)
        save_config(OpenFGAConfig(store_id="s", authorization_model_id="m"))

        with open(path) as f:
            data = json.load(f)
        assert "admins" not in data

    def test_load_ignores_unknown_fields(self, tmp_path, monkeypatch):
        path = tmp_path / "openfga.json"
        monkeypatch.setattr("openfga.config.CONFIG_PATH", path)
        path.write_text(
            json.dumps(
                {
                    "api_url": "http://test:8080",
                    "store_id": "s",
                    "authorization_model_id": "m",
                    "admins": ["alice"],  # 旧字段，应被忽略
                }
            )
        )
        config = load_config()
        assert config.api_url == "http://test:8080"
        assert not hasattr(config, "admins")


# ========== require_permission 装饰器 ==========


def _make_cmd(no_auth=False, cluster_name="prod", username="alice"):
    """构造带 require_permission 装饰器的最小命令对象。"""

    class FakeCmd:
        def __init__(self):
            self.no_auth = no_auth
            self.cluster_name = cluster_name
            self.username = username
            self.formatter = None
            self.called = False

        @require_permission("ping")
        def __call__(self, tgt="*"):
            self.called = True

    return FakeCmd()


class TestRequirePermission:
    def test_no_auth_bypasses_openfga(self):
        cmd = _make_cmd(no_auth=True)
        cmd()
        assert cmd.called

    def test_uninitialized_openfga_allows_all(self, monkeypatch):
        monkeypatch.setattr("openfga.checker.load_config", lambda: OpenFGAConfig())
        cmd = _make_cmd(no_auth=False)
        cmd()
        assert cmd.called

    def test_missing_username_blocks_execution(self, monkeypatch):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        monkeypatch.setattr("openfga.checker.load_config", lambda: config)

        cmd = _make_cmd(no_auth=False, username=None)
        cmd()
        assert not cmd.called

    def test_all_checks_pass_allows_execution(self, monkeypatch):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        monkeypatch.setattr("openfga.checker.load_config", lambda: config)

        mock_fga = MagicMock()
        mock_fga.check.return_value = MagicMock(allowed=True)
        monkeypatch.setattr("openfga.checker._client", lambda cfg: mock_fga)

        cmd = _make_cmd(no_auth=False, username="alice")
        cmd()
        assert cmd.called

    def test_any_check_fails_blocks_execution(self, monkeypatch):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        monkeypatch.setattr("openfga.checker.load_config", lambda: config)

        mock_fga = MagicMock()
        # 第一个 check（cluster member）返回 False
        mock_fga.check.return_value = MagicMock(allowed=False)
        monkeypatch.setattr("openfga.checker._client", lambda cfg: mock_fga)

        cmd = _make_cmd(no_auth=False, username="alice")
        cmd()
        assert not cmd.called

    def test_wildcard_target_skips_access_check(self, monkeypatch):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        monkeypatch.setattr("openfga.checker.load_config", lambda: config)

        call_log = []

        def mock_check(req):
            call_log.append(req.object)
            return MagicMock(allowed=True)

        mock_fga = MagicMock()
        mock_fga.check.side_effect = mock_check
        monkeypatch.setattr("openfga.checker._client", lambda cfg: mock_fga)

        cmd = _make_cmd(no_auth=False, username="alice")
        cmd(tgt="*")

        # 通配符目标不应发起 target:* 的 can_access 检查
        assert not any("target:" in obj for obj in call_log)

    def test_specific_target_triggers_access_check(self, monkeypatch):
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        monkeypatch.setattr("openfga.checker.load_config", lambda: config)

        call_log = []

        def mock_check(req):
            call_log.append(req.object)
            return MagicMock(allowed=True)

        mock_fga = MagicMock()
        mock_fga.check.side_effect = mock_check
        monkeypatch.setattr("openfga.checker._client", lambda cfg: mock_fga)

        cmd = _make_cmd(no_auth=False, username="alice")
        cmd(tgt="web-01")

        assert any("target:web-01" in obj for obj in call_log)
