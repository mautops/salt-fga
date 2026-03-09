#!/bin/bash

# Salt CLI 全面测试脚本
# 用于测试 salt 命令行工具的所有功能

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 打印测试标题
print_test() {
    echo -e "\n${YELLOW}[测试 $((TOTAL_TESTS + 1))]${NC} $1"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

# 打印成功
print_success() {
    echo -e "${GREEN}✓ 通过${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# 打印失败
print_failure() {
    echo -e "${RED}✗ 失败: $1${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

# 执行测试命令
run_test() {
    local description=$1
    shift
    print_test "$description"

    if "$@"; then
        print_success
    else
        print_failure "命令执行失败"
    fi
}

echo "========================================="
echo "Salt CLI 全面测试"
echo "========================================="

# 1. 测试 clusters 命令
run_test "列出所有集群配置" salt clusters

# 2. 测试 ping 命令
run_test "Ping 所有 minions" salt ping
run_test "Ping 指定 minion" salt ping --tgt="minion-01"

# 3. 测试 cmd 命令
run_test "在所有 minions 上执行命令" salt cmd run --tgt="*" --command="uptime"
run_test "在指定 minion 上执行命令" salt cmd run --tgt="minion-01" --command="hostname"

# 4. 测试 minions 命令
run_test "列出所有 minions" salt minions
run_test "查看指定 minion 信息" salt minions --mid="minion-01"

# 5. 测试 jobs 命令
run_test "列出所有任务" salt jobs
# 注意：需要一个真实的 jid 才能测试单个任务查询
# run_test "查看指定任务" salt jobs --jid="20240101000000000000"

# 6. 测试 keys 命令
run_test "列出所有 keys" salt keys
run_test "列出所有 keys (使用 list 子命令)" salt keys list
# 注意：以下命令会修改 key 状态，谨慎使用
# run_test "接受 minion key" salt keys accept --mid="test-minion"
# run_test "拒绝 minion key" salt keys reject --mid="test-minion"
# run_test "删除 minion key" salt keys delete --mid="test-minion"

# 7. 测试 execute 命令
run_test "执行脚本" salt execute --tgt="minion-01" --script_content="echo 'Hello from script'"

# 8. 测试 --raw 输出模式
run_test "使用 raw 模式输出" salt --raw ping

# 9. 测试 -c 指定集群
# 注意：需要在配置文件中有多个集群才能测试
# run_test "使用指定集群" salt -c prod ping

# 10. 测试错误处理
print_test "测试无效的 minion ID"
if salt ping --tgt="nonexistent-minion-12345" 2>/dev/null; then
    print_failure "应该返回空结果或错误"
else
    print_success
fi

# 打印测试总结
echo ""
echo "========================================="
echo "测试总结"
echo "========================================="
echo -e "总测试数: ${TOTAL_TESTS}"
echo -e "${GREEN}通过: ${PASSED_TESTS}${NC}"
echo -e "${RED}失败: ${FAILED_TESTS}${NC}"
echo "========================================="

# 返回失败数作为退出码
exit $FAILED_TESTS
