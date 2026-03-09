"""OpenFGA 权限系统测试

测试说明:
- 单元测试（mock）: 不依赖 OpenFGA 服务器，使用 unittest.mock
- 集成测试: 需要 OpenFGA 服务器（docker-compose up -d），标记为 @pytest.mark.integration
"""

import os
import pytest
from unittest.mock import MagicMock

from openfga import (
    OpenFGAConfig,
    OpenFGAConfigManager,
    OpenFGAClientWrapper,
    PermissionChecker,
    PermissionDeniedError,
)


# ========== 配置管理测试 ==========

class TestOpenFGAConfig:
    """测试 OpenFGA 配置"""

    def test_default_config(self):
        """默认配置应该有正确的默认值"""
        config = OpenFGAConfig()
        assert config.api_url == "http://localhost:8080"
        assert config.store_id is None
        assert config.authorization_model_id is None

    def test_is_initialized_false(self):
        """未设置 store_id 和 model_id 时应该未初始化"""
        config = OpenFGAConfig()
        assert not config.is_initialized()

    def test_is_initialized_true(self):
        """设置了 store_id 和 model_id 时应该已初始化"""
        config = OpenFGAConfig(
            store_id="store-123",
            authorization_model_id="model-456",
        )
        assert config.is_initialized()

    def test_is_initialized_partial(self):
        """只设置了其中一个时应该未初始化"""
        config1 = OpenFGAConfig(store_id="store-123")
        assert not config1.is_initialized()

        config2 = OpenFGAConfig(authorization_model_id="model-456")
        assert not config2.is_initialized()

    def test_to_dict(self):
        """转换为字典应该包含所有字段"""
        config = OpenFGAConfig(
            api_url="http://example.com",
            store_id="store-123",
            authorization_model_id="model-456",
        )
        d = config.to_dict()
        assert d["api_url"] == "http://example.com"
        assert d["store_id"] == "store-123"
        assert d["authorization_model_id"] == "model-456"


class TestOpenFGAConfigManager:
    """测试配置文件管理器"""

    def test_load_nonexistent_file(self, tmp_path):
        """加载不存在的配置文件应该返回默认配置"""
        manager = OpenFGAConfigManager(tmp_path / "nonexistent.json")
        config = manager.load()
        assert config.api_url == "http://localhost:8080"
        assert not config.is_initialized()

    def test_save_and_load(self, tmp_path):
        """保存后加载应该得到相同的配置"""
        config_path = tmp_path / "openfga.json"
        manager = OpenFGAConfigManager(config_path)

        config = OpenFGAConfig(
            api_url="http://test:8080",
            store_id="store-abc",
            authorization_model_id="model-xyz",
        )
        manager.save(config)

        loaded = manager.load()
        assert loaded.api_url == "http://test:8080"
        assert loaded.store_id == "store-abc"
        assert loaded.authorization_model_id == "model-xyz"

    def test_update_store_id(self, tmp_path):
        """更新 store_id 应该只修改该字段"""
        config_path = tmp_path / "openfga.json"
        manager = OpenFGAConfigManager(config_path)

        # 先保存初始配置
        initial = OpenFGAConfig(api_url="http://test:8080")
        manager.save(initial)

        # 更新 store_id
        updated = manager.update(store_id="new-store-id")
        assert updated.store_id == "new-store-id"
        assert updated.api_url == "http://test:8080"  # 其他字段不变


# ========== 权限检查器测试（Mock）==========

class TestPermissionCheckerDisabled:
    """测试禁用权限检查"""

    def test_disabled_allows_all(self):
        """禁用权限检查时所有操作都应该允许"""
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        checker = PermissionChecker(config=config, enabled=False)

        assert checker.check("ping", "*", "prod", "anyone")
        assert checker.check("cmd", "web-001", "prod", "anyone")


class TestPermissionCheckerUninitialized:
    """测试未初始化的权限检查器"""

    def test_uninitialized_denies_all(self):
        """未初始化 OpenFGA 时所有检查应该拒绝"""
        config = OpenFGAConfig()  # 未初始化
        checker = PermissionChecker(config=config, enabled=True)

        assert not checker.check("ping", "*", "prod", "alice")

    def test_require_raises_permission_denied(self):
        """未初始化时 require 应该抛出 PermissionDeniedError"""
        config = OpenFGAConfig()  # 未初始化
        checker = PermissionChecker(config=config, enabled=True)

        with pytest.raises(PermissionDeniedError) as exc_info:
            checker.require("ping", "*", "prod", "alice")

        assert "alice" in str(exc_info.value)
        assert "ping" in str(exc_info.value)


class TestPermissionCheckerMocked:
    """测试带 Mock 的权限检查器"""

    def _make_checker_with_mock_client(self, cluster_member: bool, can_execute: bool, target_groups: list, can_access_group: bool):
        """
        创建一个使用 mock client 的权限检查器

        Args:
            cluster_member: 用户是否是 cluster 成员
            can_execute: 用户是否有命令执行权限
            target_groups: target 所属的组列表（字典列表）
            can_access_group: 用户是否有目标组访问权限
        """
        config = OpenFGAConfig(store_id="s", authorization_model_id="m")
        checker = PermissionChecker(config=config, enabled=True)

        # 创建 mock 客户端
        mock_client = MagicMock()

        # check 方法的不同调用返回不同结果
        def mock_check(user, relation, object, contextual_tuples=None):
            if relation == "member":
                return cluster_member
            elif relation == "can_execute":
                return can_execute
            elif relation == "can_access":
                return can_access_group
            return False

        mock_client.check = mock_check
        mock_client.read_tuples = MagicMock(return_value=target_groups)

        # 替换 checker 的 client
        checker.client = mock_client

        return checker

    def test_all_permissions_granted(self):
        """所有权限都满足时应该允许"""
        checker = self._make_checker_with_mock_client(
            cluster_member=True,
            can_execute=True,
            target_groups=[{"user": "target:web-001", "relation": "group", "object": "target_group:web-servers"}],
            can_access_group=True,
        )

        assert checker.check("ping", "web-001", "prod", "alice")

    def test_not_cluster_member(self):
        """用户不是 cluster 成员时应该拒绝"""
        checker = self._make_checker_with_mock_client(
            cluster_member=False,
            can_execute=True,
            target_groups=[{"user": "target:web-001", "relation": "group", "object": "target_group:web-servers"}],
            can_access_group=True,
        )

        assert not checker.check("ping", "web-001", "prod", "alice")

    def test_cannot_execute_command(self):
        """用户没有命令执行权限时应该拒绝"""
        checker = self._make_checker_with_mock_client(
            cluster_member=True,
            can_execute=False,
            target_groups=[{"user": "target:web-001", "relation": "group", "object": "target_group:web-servers"}],
            can_access_group=True,
        )

        assert not checker.check("cmd", "web-001", "prod", "alice")

    def test_target_not_in_group(self):
        """目标主机不属于任何组时应该拒绝"""
        checker = self._make_checker_with_mock_client(
            cluster_member=True,
            can_execute=True,
            target_groups=[],  # 没有组
            can_access_group=True,
        )

        assert not checker.check("ping", "unknown-host", "prod", "alice")

    def test_cannot_access_target_group(self):
        """用户没有目标组访问权限时应该拒绝"""
        checker = self._make_checker_with_mock_client(
            cluster_member=True,
            can_execute=True,
            target_groups=[{"user": "target:web-001", "relation": "group", "object": "target_group:web-servers"}],
            can_access_group=False,
        )

        assert not checker.check("ping", "web-001", "prod", "alice")

    def test_require_raises_on_denied(self):
        """权限被拒绝时 require 应该抛出 PermissionDeniedError"""
        checker = self._make_checker_with_mock_client(
            cluster_member=False,
            can_execute=True,
            target_groups=[],
            can_access_group=False,
        )

        with pytest.raises(PermissionDeniedError) as exc_info:
            checker.require("ping", "web-001", "prod", "alice")

        error = exc_info.value
        assert error.user == "alice"
        assert error.command == "ping"
        assert error.target == "web-001"
        assert error.cluster == "prod"


# ========== PermissionDeniedError 测试 ==========

class TestPermissionDeniedError:
    """测试 PermissionDeniedError 异常"""

    def test_error_message(self):
        """异常消息应该包含相关信息"""
        error = PermissionDeniedError("alice", "ping", "web-001", "prod")
        assert "alice" in str(error)
        assert "ping" in str(error)
        assert "web-001" in str(error)
        assert "prod" in str(error)

    def test_error_message_with_reason(self):
        """附带原因的异常消息"""
        error = PermissionDeniedError("alice", "ping", "web-001", "prod", reason="测试原因")
        assert "测试原因" in str(error)

    def test_error_attributes(self):
        """异常对象应该有正确的属性"""
        error = PermissionDeniedError("alice", "ping", "web-001", "prod", reason="权限不足")
        assert error.user == "alice"
        assert error.command == "ping"
        assert error.target == "web-001"
        assert error.cluster == "prod"
        assert error.reason == "权限不足"


# ========== 集成测试（需要 OpenFGA 服务器）==========

@pytest.mark.integration
class TestIntegration:
    """集成测试 - 需要 OpenFGA 服务器

    运行方式:
        docker-compose up -d
        pytest tests/test_openfga.py -m integration
    """

    @pytest.fixture(autouse=True)
    def setup_config(self):
        """设置集成测试配置"""
        # 集成测试使用专用的测试配置
        self.config = OpenFGAConfig(
            api_url=os.environ.get("OPENFGA_API_URL", "http://localhost:8080")
        )
        # 注意：集成测试需要先通过 `salt permission init` 初始化 store

    def test_connection(self):
        """测试能否连接到 OpenFGA 服务器"""
        from openfga_sdk.sync import OpenFgaClient
        from openfga_sdk import ClientConfiguration

        config = ClientConfiguration(api_url=self.config.api_url)
        client = OpenFgaClient(config)

        # 尝试列出 stores
        response = client.list_stores()
        assert response is not None

    def test_full_permission_flow(self):
        """测试完整的权限授予和检查流程

        需要 OpenFGA 已初始化（有 store_id 和 model_id）
        """
        config_manager = OpenFGAConfigManager()
        config = config_manager.load()

        if not config.is_initialized():
            pytest.skip("OpenFGA 未初始化，跳过集成测试")

        client = OpenFGAClientWrapper(config)

        # 授予权限
        client.write_tuples([
            {"user": "user:test_alice", "relation": "member", "object": "cluster:test_env"},
            {"user": "cluster:test_env#member", "relation": "can_execute", "object": "command:test_ping"},
            {"user": "cluster:test_env#member", "relation": "can_access", "object": "target_group:test_group"},
            {"user": "target:test_host", "relation": "group", "object": "target_group:test_group"},
        ])

        try:
            # 权限检查
            checker = PermissionChecker(config=config, enabled=True)
            assert checker.check("test_ping", "test_host", "test_env", "test_alice")

            # 非成员应该被拒绝
            assert not checker.check("test_ping", "test_host", "test_env", "unknown_user")

        finally:
            # 清理测试数据
            try:
                client.delete_tuples([
                    {"user": "user:test_alice", "relation": "member", "object": "cluster:test_env"},
                    {"user": "cluster:test_env#member", "relation": "can_execute", "object": "command:test_ping"},
                    {"user": "cluster:test_env#member", "relation": "can_access", "object": "target_group:test_group"},
                    {"user": "target:test_host", "relation": "group", "object": "target_group:test_group"},
                ])
            except Exception:
                pass  # 清理失败不影响测试结果报告
