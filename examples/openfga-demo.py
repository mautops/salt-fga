#!/usr/bin/env python3
"""OpenFGA 权限系统功能演示"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from openfga import (
    PermissionRule,
    PermissionStore,
    PermissionChecker,
    PermissionDeniedError,
)
from pathlib import Path
import tempfile


def demo():
    """演示权限系统功能"""
    print("=" * 60)
    print("OpenFGA 权限系统功能演示")
    print("=" * 60)
    print()

    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        store = PermissionStore(Path(tmpdir))
        checker = PermissionChecker(store, enabled=True)

        # 1. 默认拒绝
        print("1. 默认拒绝策略")
        print("-" * 60)
        print("尝试执行命令（没有任何权限规则）:")
        try:
            checker.require("ping", "*", "prod", "alice")
            print("  ✗ 不应该通过")
        except PermissionDeniedError as e:
            print(f"  ✓ 权限被拒绝: {e}")
        print()

        # 2. 添加权限规则
        print("2. 添加权限规则")
        print("-" * 60)
        rules = [
            PermissionRule("alice", "ping", "*", "prod", description="Alice 可以在 prod 环境执行 ping"),
            PermissionRule("bob", "cmd", "web-.*", "dev", description="Bob 可以在 dev 环境对 web 服务器执行 cmd"),
            PermissionRule("charlie", "execute", "db-[0-9]+", "*", description="Charlie 可以在所有环境对数据库执行脚本"),
            PermissionRule("*", "ping", "*", "dev", description="所有用户可以在 dev 环境执行 ping"),
        ]

        for rule in rules:
            store.add_rule(rule)
            print(f"  ✓ 添加规则: {rule.user} -> {rule.command} @ {rule.target_pattern} ({rule.cluster})")
        print()

        # 3. 查看权限规则
        print("3. 查看权限规则")
        print("-" * 60)
        all_rules = store.load_rules()
        print(f"  共 {len(all_rules)} 条规则:")
        for i, rule in enumerate(all_rules, 1):
            print(f"    {i}. {rule.user:10} | {rule.command:8} | {rule.target_pattern:15} | {rule.cluster:8} | {rule.description}")
        print()

        # 4. 权限检查测试
        print("4. 权限检查测试")
        print("-" * 60)

        test_cases = [
            ("alice", "ping", "*", "prod", True, "Alice 在 prod 环境执行 ping"),
            ("alice", "ping", "web-001", "prod", True, "Alice 在 prod 环境对 web-001 执行 ping"),
            ("alice", "cmd", "*", "prod", False, "Alice 在 prod 环境执行 cmd（无权限）"),
            ("bob", "cmd", "web-001", "dev", True, "Bob 在 dev 环境对 web-001 执行 cmd"),
            ("bob", "cmd", "db-001", "dev", False, "Bob 在 dev 环境对 db-001 执行 cmd（目标不匹配）"),
            ("charlie", "execute", "db-001", "prod", True, "Charlie 在 prod 环境对 db-001 执行 execute"),
            ("charlie", "execute", "db-999", "dev", True, "Charlie 在 dev 环境对 db-999 执行 execute"),
            ("charlie", "execute", "web-001", "prod", False, "Charlie 在 prod 环境对 web-001 执行 execute（目标不匹配）"),
            ("anyone", "ping", "*", "dev", True, "任意用户在 dev 环境执行 ping（通配符）"),
            ("anyone", "ping", "*", "prod", False, "任意用户在 prod 环境执行 ping（无权限）"),
        ]

        for user, command, target, cluster, expected, description in test_cases:
            result = checker.check(command, target, cluster, user)
            status = "✓" if result == expected else "✗"
            result_text = "通过" if result else "拒绝"
            print(f"  {status} {description}: {result_text}")

        print()

        # 5. 正则表达式匹配测试
        print("5. 正则表达式匹配测试")
        print("-" * 60)

        regex_tests = [
            ("web-.*", ["web-001", "web-002", "web-999"], ["db-001", "app-001"]),
            ("db-[0-9]+", ["db-001", "db-999"], ["db-abc", "web-001"]),
            ("(web|app)-.*", ["web-001", "app-001"], ["db-001", "api-001"]),
        ]

        for pattern, should_match, should_not_match in regex_tests:
            print(f"  模式: {pattern}")
            rule = PermissionRule("test", "ping", pattern, "test")

            for target in should_match:
                result = rule.matches_target(target)
                status = "✓" if result else "✗"
                print(f"    {status} {target:15} -> 应该匹配: {result}")

            for target in should_not_match:
                result = rule.matches_target(target)
                status = "✓" if not result else "✗"
                print(f"    {status} {target:15} -> 不应该匹配: {not result}")

        print()

        # 6. 删除规则
        print("6. 删除规则")
        print("-" * 60)
        removed = store.remove_rule("alice", "ping", "*", "prod")
        print(f"  {'✓' if removed else '✗'} 删除 alice 的 ping 权限: {removed}")

        # 验证删除
        result = checker.check("ping", "*", "prod", "alice")
        print(f"  {'✓' if not result else '✗'} Alice 现在无法在 prod 环境执行 ping: {not result}")
        print()

        # 7. 统计
        print("7. 统计信息")
        print("-" * 60)
        remaining_rules = store.load_rules()
        print(f"  剩余规则数: {len(remaining_rules)}")
        print()

    print("=" * 60)
    print("演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    demo()
