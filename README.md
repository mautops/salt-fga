# Salt CLI

Salt CLI 是一个用于执行 SaltStack Cherry API 的命令行工具，提供简洁的命令行接口和美化的输出。

## 安装

```bash
# 克隆项目
git clone <repository-url>
cd salt

# 安装依赖
uv sync

# 使用
./.venv/bin/salt <command>
```

## 配置

配置文件位置：`~/.config/salt/credentials.json`

配置格式：

```json
[
  {
    "name": "prod",
    "description": "saltproject 生产环境",
    "base_url": "https://salt-api.gz.cvte.cn",
    "username": "saltadmin",
    "password": "your-password",
    "eauth": "file",
    "token_expire": "10h"
  }
]
```

## 使用示例

### 查看所有环境

```bash
salt clusters
```

### 执行 ping 测试

```bash
# 测试所有主机
salt ping

# 测试指定主机
salt ping --tgt "minion-001"

# 指定环境
salt -c prod ping
```

### 执行脚本

```bash
salt execute --tgt "minion-001" --script_content "echo hello\nhostname"

# 指定 shell 类型
salt execute --tgt "minion-001" --script_content "echo hello" --shell bash
```

### 原始输出模式

```bash
# 使用 --raw 参数输出原始 JSON
salt --raw ping
salt --raw clusters
```

## 命令说明

### 全局参数

- `-c, --cluster`: 指定环境名称（默认使用配置文件中的第一个环境）
- `-r, --raw`: 使用原始 JSON 输出（默认使用 rich 美化输出）

### 子命令

- `clusters`: 列出所有环境配置
- `ping`: 执行 test.ping 测试连接
- `execute`: 执行脚本命令

## Token 管理

Token 会自动缓存到 `~/.config/salt/tokens/<cluster_name>.json`，并根据配置的过期时间自动刷新。

## 开发

```bash
# 安装开发依赖
uv sync --group dev

# 运行测试
uv run pytest
```

## 架构说明

详细的架构说明请参考 [CLAUDE.md](./CLAUDE.md)。
