# Salt CLI 测试指南

本文档提供 Salt CLI 工具的完整测试指南。

## 前置条件

1. 已安装依赖：`uv sync`
2. 已配置集群：`~/.config/salt/credentials.json`
3. Salt API 服务可访问

## 快速测试

运行自动化测试脚本：

```bash
./test_salt_cli.sh
```

## 手动测试用例

### 1. 集群管理

```bash
# 列出所有配置的集群
salt clusters

# 使用指定集群
salt -c prod ping
salt -c dev ping
```

### 2. Ping 测试

```bash
# Ping 所有 minions
salt ping

# Ping 指定 minion
salt ping --tgt="minion-01"

# Ping 使用通配符
salt ping --tgt="web-*"

# 原始输出模式
salt --raw ping
```

### 3. 命令执行

```bash
# 在所有 minions 上执行命令
salt cmd run --tgt="*" --command="uptime"

# 在指定 minion 上执行命令
salt cmd run --tgt="minion-01" --command="hostname"

# 执行复杂命令
salt cmd run --tgt="*" --command="df -h | grep /dev/sda"
```

### 4. 脚本执行

```bash
# 执行简单脚本
salt execute --tgt="minion-01" --script_content="echo 'Hello World'"

# 执行多行脚本
salt execute --tgt="*" --script_content="
#!/bin/bash
echo 'Starting backup...'
tar -czf /tmp/backup.tar.gz /etc/
echo 'Backup completed'
"

# 使用不同的 shell
salt execute --tgt="minion-01" --script_content="print('Hello from Python')" --shell="python"
```

### 5. Minion 管理

```bash
# 列出所有 minions
salt minions

# 查看指定 minion 详细信息
salt minions --mid="minion-01"

# 原始输出
salt --raw minions
```

### 6. 任务管理

```bash
# 列出所有任务
salt jobs

# 查看指定任务详情
salt jobs --jid="20240101000000000000"

# 原始输出
salt --raw jobs
```

### 7. Key 管理

```bash
# 列出所有 keys
salt keys
salt keys list

# 查看指�� minion 的 key
salt keys list --mid="minion-01"

# 接受 pending key
salt keys accept --mid="new-minion"

# 拒绝 key
salt keys reject --mid="untrusted-minion"

# 删除 key
salt keys delete --mid="old-minion"
```

## 输出模式测试

### 美化输出（默认）

```bash
salt ping
# 输出带颜色和格式化的结果
```

### 原始输出

```bash
salt --raw ping
# 输出原始 JSON 数据
```

## 错误处理测试

### 1. 无效的 minion

```bash
salt ping --tgt="nonexistent-minion"
# 应该返回空结果或明确的错误信息
```

### 2. 网络错误

```bash
# 临时修改配置文件中的 base_url 为无效地址
salt ping
# 应该显示连接错误
```

### 3. 认证错误

```bash
# 临时修改配置文件中的密码为错误密码
salt ping
# 应该显示认证失败错误
```

### 4. Token 过期

```bash
# 删除 token 缓存
rm ~/.config/salt/tokens/*.json

# 执行命令，应该自动重新登录
salt ping
```

## 性能测试

### 1. 大规模 minion 测试

```bash
# 测试对大量 minions 的响应
time salt ping --tgt="*"
```

### 2. 并发命令测试

```bash
# 同时执行多个命令
salt cmd run --tgt="*" --command="sleep 5" &
salt cmd run --tgt="*" --command="uptime" &
wait
```

## 集成测试场景

### 场景 1：新 Minion 加入

```bash
# 1. 查看 pending keys
salt keys list

# 2. 接受新 minion
salt keys accept --mid="new-minion"

# 3. 验证连接
salt ping --tgt="new-minion"

# 4. 执行测试命令
salt cmd run --tgt="new-minion" --command="hostname"
```

### 场景 2：批量部署脚本

```bash
# 1. 准备部署脚本
cat > deploy.sh << 'EOF'
#!/bin/bash
echo "Deploying application..."
cd /opt/app
git pull origin main
systemctl restart app
echo "Deployment completed"
EOF

# 2. 执行部署
salt execute --tgt="web-*" --script_content="$(cat deploy.sh)"

# 3. 验证部署
salt cmd run --tgt="web-*" --command="systemctl status app"
```

### 场景 3：健康检查

```bash
# 1. Ping 所有 minions
salt ping

# 2. 检查磁盘空间
salt cmd run --tgt="*" --command="df -h"

# 3. 检查内存使用
salt cmd run --tgt="*" --command="free -h"

# 4. 检查负载
salt cmd run --tgt="*" --command="uptime"
```

## 故障排查

### 查看详细日志

```bash
# 使用 Python 直接运行以查看详细错误
python -m salt.cli ping --tgt="*"
```

### 验证配置

```bash
# 检查配置文件
cat ~/.config/salt/credentials.json

# 检查 token 缓存
ls -la ~/.config/salt/tokens/
cat ~/.config/salt/tokens/*.json
```

### 测试 API 连接

```bash
# 使用 curl 直接测试 API
curl -X POST https://your-salt-api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-password",
    "eauth": "pam"
  }'
```

## 预期结果

所有测试应该：
1. 正确连接到 Salt API
2. 成功认证并获取 token
3. 正确执行命令并返回结果
4. 美化输出易于阅读
5. 错误信息清晰明确
6. Token 自动缓存和刷新

## 已知限制

1. `execute` 命令的脚本内容需要目标 minion 支持 `run_execute.run` 模块
2. Key 管理操作需要相应的权限
3. 某些命令可能需要较长时间执行，请耐心等待
