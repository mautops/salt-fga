#!/bin/bash
# OpenFGA 权限系统快速开始示例

echo "=== OpenFGA 权限系统快速开始 ==="
echo ""

# 设置当前用户
export SALT_USER="demo-user"
echo "1. 设置当前用户: $SALT_USER"
echo ""

# 查看当前权限规则（应该为空）
echo "2. 查看当前权限规则:"
uv run python -m salt.cli permission list
echo ""

# 尝试执行命令（应该被拒绝）
echo "3. 尝试执行 ping 命令（应该被拒绝）:"
uv run python -m salt.cli -c prod ping --tgt="*" 2>&1 || echo "✓ 权限被拒绝（符合预期）"
echo ""

# 添加权限规则
echo "4. 添加权限规则: 允许 demo-user 在 prod 环境执行 ping 命令"
uv run python -m salt.cli permission add \
  --user="demo-user" \
  --command=ping \
  --target_pattern="*" \
  --cluster=prod \
  --description="Demo: 允许 demo-user 执行 ping"
echo ""

# 查看权限规则
echo "5. 查看更新后的权限规则:"
uv run python -m salt.cli permission list
echo ""

# 测试权限
echo "6. 测试权限:"
uv run python -m salt.cli permission check \
  --command=ping \
  --target="web-001" \
  --cluster=prod \
  --user="demo-user"
echo ""

# 再次尝试执行命令（应该通过，但可能因为没有实际的 Salt API 而失败）
echo "7. 再次尝试执行 ping 命令（权限检查应该通过）:"
echo "   注意: 如果没有配置 Salt API，命令会因为连接失败而报错，但权限检查已通过"
uv run python -m salt.cli -c prod ping --tgt="*" 2>&1 || echo "   （连接失败是正常的，权限检查已通过）"
echo ""

# 添加更多规则示例
echo "8. 添加更多权限规则示例:"

# Web 服务器管理员
uv run python -m salt.cli permission add \
  --user="web-admin" \
  --command=cmd \
  --target_pattern="web-.*" \
  --cluster=prod \
  --description="Web 服务器管理员"

# 数据库管理员
uv run python -m salt.cli permission add \
  --user="db-admin" \
  --command=execute \
  --target_pattern="db-[0-9]+" \
  --cluster=prod \
  --description="数据库管理员"

# 开发环境全局权限
uv run python -m salt.cli permission add \
  --user="*" \
  --command=ping \
  --target_pattern="*" \
  --cluster=dev \
  --description="所有用户可以在 dev 环境执行 ping"

echo ""

# 查看所有规则
echo "9. 查看所有权限规则:"
uv run python -m salt.cli permission list
echo ""

# 测试不同用户的权限
echo "10. 测试不同用户的权限:"

echo "   - demo-user 在 prod 环境执行 ping:"
uv run python -m salt.cli permission check \
  --command=ping \
  --target="*" \
  --cluster=prod \
  --user="demo-user"

echo "   - web-admin 在 prod 环境对 web-001 执行 cmd:"
uv run python -m salt.cli permission check \
  --command=cmd \
  --target="web-001" \
  --cluster=prod \
  --user="web-admin"

echo "   - db-admin 在 prod 环境对 db-001 执行 execute:"
uv run python -m salt.cli permission check \
  --command=execute \
  --target="db-001" \
  --cluster=prod \
  --user="db-admin"

echo "   - 任意用户在 dev 环境执行 ping:"
uv run python -m salt.cli permission check \
  --command=ping \
  --target="*" \
  --cluster=dev \
  --user="anyone"

echo ""

# 清理（可选）
echo "11. 清理权限规则（可选）:"
echo "    如果要清理所有规则，运行: salt permission clear --confirm=True"
echo ""

echo "=== 快速开始完成 ==="
echo ""
echo "更多信息请查看: src/openfga/README.md"
