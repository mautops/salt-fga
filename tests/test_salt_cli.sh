#!/bin/bash
# Salt CLI 集成测试
# 需要已配置好的 Salt API 环境（~/.config/salt/credentials.json）
# 使用 --no-auth 跳过权限检查，适合无 OpenFGA 的测试环境

SALT="${SALT_CMD:-salt-fga}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

pass() { echo -e "  ${GREEN}✓ $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}✗ $1${NC}"; FAIL=$((FAIL + 1)); }

run() {
    local desc=$1; shift
    echo -e "\n${YELLOW}>> $desc${NC}"
    if "$@" 2>/dev/null; then
        pass "$desc"
    else
        fail "$desc"
    fi
}

echo "========================================"
echo "Salt CLI 集成测试"
echo "========================================"

# clusters
run "列出所有集群" $SALT --no-auth clusters
run "列出所有集群 (list 子命令)" $SALT --no-auth clusters list

# ping
run "Ping 所有 minions" $SALT --no-auth ping
run "Ping 指定 tgt" $SALT --no-auth ping --tgt "minion-01"
run "Ping (raw 输出)" $SALT --no-auth --raw ping

# cmd
run "cmd: 执行命令 (直接调用)" $SALT --no-auth cmd --tgt "*" --command "uptime"
run "cmd run: 执行命令 (子命令)" $SALT --no-auth cmd run --tgt "minion-01" --command "hostname"

# execute
run "execute: 执行脚本" $SALT --no-auth execute --tgt "minion-01" --script_content "echo hello"
run "execute: 指定 shell" $SALT --no-auth execute --tgt "minion-01" --script_content "echo hello" --shell "bash"

# minions
run "查看所有 minions" $SALT --no-auth minions
run "查看指定 minion" $SALT --no-auth minions --mid "minion-01"

# jobs
run "查看任务历史" $SALT --no-auth jobs

# keys
run "列出所有 keys (默认)" $SALT --no-auth keys
run "列出所有 keys (list 子命令)" $SALT --no-auth keys list
run "查看指定 minion 的 key" $SALT --no-auth keys list --mid "minion-01"

# permission
run "查看 OpenFGA 配置状态" $SALT --no-auth permission status
run "列出权限规则" $SALT --no-auth permission list

# 多环境
if [ -n "$TEST_CLUSTER" ]; then
    run "指定集群: $TEST_CLUSTER" $SALT -c "$TEST_CLUSTER" --no-auth ping
fi

echo ""
echo "========================================"
echo -e "通过: ${GREEN}${PASS}${NC}  失败: ${RED}${FAIL}${NC}"
echo "========================================"

exit $FAIL
