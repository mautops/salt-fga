# Salt CLI 命令参考

## 全局参数

### -c, --cluster
指定要使用的集群环境。

```bash
salt -c prod ping
salt -c dev minions
```

如果不指定，使用配置文件中的第一个环境作为默认环境。

### --raw
输出原始 JSON 格式，不进行美化。

```bash
salt --raw ping
salt --raw minions
```

## 子命令

### clusters
列出所有配置的集群环境。

```bash
salt clusters
```

**输出示例：**
```
Available Clusters:
┌──────┬─────────────────┬──────────────────────────────┐
│ Name │ Description     │ Base URL                     │
├──────┼─────────────────┼──────────────────────────────┤
│ prod │ Production Env  │ https://salt-api.prod.com    │
│ dev  │ Development Env │ https://salt-api.dev.com     │
└──────┴─────────────────┴──────────────────────────────┘
```

### ping
测试与 minions 的连接状态（执行 test.ping）。

```bash
# Ping 所有 minions
salt ping

# Ping 指定 minion
salt ping --tgt="minion-01"

# Ping 使用通配符
salt ping --tgt="web-*"
```

**参数：**
- `--tgt`: 目标主机，默认为 `*`（所有 minions）

**输出示例：**
```
minion-01: ✓ True
minion-02: ✓ True
web-server-01: ✓ True
```

### cmd
在 minions 上执行 shell 命令（使用 cmd.run 模块）。

```bash
# 在所有 minions 上执行命令
salt cmd run --tgt="*" --command="uptime"

# 在指定 minion 上执行命令
salt cmd run --tgt="minion-01" --command="hostname"

# 执行复杂命令
salt cmd run --tgt="web-*" --command="df -h | grep /dev/sda"
```

**参数：**
- `--tgt`: 目标主机（必需）
- `--command`: 要执行的 shell 命令（必需）

**输出示例：**
```
minion-01:
  14:23:45 up 10 days,  3:45,  2 users,  load average: 0.15, 0.10, 0.08
```

### execute
在 minions 上执行脚本（使用 run_execute.run 模块）。

```bash
# 执行简单脚本
salt execute --tgt="minion-01" --script_content="echo 'Hello World'"

# 执行多行脚本
salt execute --tgt="*" --script_content="#!/bin/bash
echo 'Starting backup...'
tar -czf /tmp/backup.tar.gz /etc/
echo 'Backup completed'"

# 使用不同的 shell
salt execute --tgt="minion-01" --script_content="print('Hello')" --shell="python"
```

**参数：**
- `--tgt`: 目标主机（必需）
- `--script_content`: 脚本内容（必需）
- `--shell`: Shell 类型，默认为 `bash`

### minions
查看 minion 信息（通过 GET /minions 端点）。

```bash
# 列出所有 minions
salt minions

# 查看指定 minion 详细信息
salt minions --mid="minion-01"
```

**参数：**
- `--mid`: Minion ID（可选）

**输出示例：**
```json
{
  "return": [{
    "minion-01": {
      "os": "Ubuntu",
      "osrelease": "20.04",
      "kernel": "5.4.0-42-generic"
    }
  }]
}
```

### jobs
查看任务历史和状态（通过 GET /jobs 端点）。

```bash
# 列出所有任务
salt jobs

# 查看指定任务详情
salt jobs --jid="20240101000000000000"
```

**参数：**
- `--jid`: Job ID（可选）

**输出示例：**
```json
{
  "return": [{
    "20240101000000000000": {
      "Function": "test.ping",
      "Target": "*",
      "User": "saltuser"
    }
  }]
}
```

### keys
管理 minion keys（通过 GET /keys 和 wheel.key 模块）。

```bash
# 列出所有 keys
salt keys
salt keys list

# 查看指定 minion 的 key
salt keys list --mid="minion-01"

# 接受 pending key
salt keys accept --mid="new-minion"

# 拒绝 key
salt keys reject --mid="untrusted-minion"

# 删除 key
salt keys delete --mid="old-minion"
```

**子命令：**
- `list [--mid]`: 列出所有 keys 或指定 minion 的 key
- `accept --mid`: 接受指定 minion 的 key
- `reject --mid`: 拒绝指定 minion 的 key
- `delete --mid`: 删除指定 minion 的 key

**输出示例（list）：**
```json
{
  "return": {
    "local": ["master.pem", "master.pub"],
    "minions": ["minion-01", "minion-02"],
    "minions_pre": ["new-minion"],
    "minions_rejected": []
  }
}
```

## 目标主机格式（tgt）

Salt 支持多种目标主机格式：

### 通配符
```bash
salt ping --tgt="*"           # 所有 minions
salt ping --tgt="web-*"       # 所有以 web- 开头的 minions
salt ping --tgt="*-prod"      # 所有以 -prod 结尾的 minions
```

### 单个主机
```bash
salt ping --tgt="minion-01"
```

### 列表（使用 fire 的列表语法）
```bash
salt ping --tgt="minion-01,minion-02,minion-03"
```

## 常见使用场景

### 场景 1: 新 Minion 加入
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

### 场景 2: 批量部署
```bash
# 1. 执行部署脚本
salt execute --tgt="web-*" --script_content="#!/bin/bash
cd /opt/app
git pull origin main
systemctl restart app
echo 'Deployment completed'"

# 2. 验证部署
salt cmd run --tgt="web-*" --command="systemctl status app"
```

### 场景 3: 健康检查
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

### 场景 4: 故障排查
```bash
# 1. 查看最近的任务
salt jobs

# 2. 查看指定任务详情
salt jobs --jid="20240101000000000000"

# 3. 检查 minion 状态
salt minions --mid="problematic-minion"
```
