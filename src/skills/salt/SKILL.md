---
name: salt
description: "Salt CLI tool for managing SaltStack infrastructure via CherryPy REST API. Use when working with Salt commands, SaltStack operations, minion management, or when the user asks about: (1) Salt command usage and syntax, (2) Managing Salt minions (ping, execute commands, run scripts), (3) Salt key management (accept, reject, delete keys), (4) Viewing job history and minion information, (5) Multi-environment Salt cluster configuration, (6) Salt API authentication and token management, (7) Troubleshooting Salt CLI issues, or (8) Any questions about 'salt' command parameters and options."
---

# Salt CLI

Salt CLI 是一个用于通过 SaltStack CherryPy REST API 管理基础设施的命令行工具。

## 快速开始

### 基本命令结构

```bash
salt [全局参数] <子命令> [子命令参数]
```

### 常用命令示例

```bash
# 列出所有集群环境
salt clusters

# Ping 所有 minions
salt ping

# 在指定环境执行命令
salt -c prod ping --tgt="web-*"

# 执行 shell 命令
salt cmd run --tgt="*" --command="uptime"

# 管理 minion keys
salt keys list
salt keys accept --mid="new-minion"
```

## 全局参数

### -c, --cluster
指定集群环境（对应配置文件中的 name 字段）。

```bash
salt -c prod ping
salt -c dev minions
```

未指定时使用配置文件中的第一个环境。

### --raw
输出原始 JSON 格式，不进行美化。

```bash
salt --raw ping
salt --raw jobs
```

## 子命令概览

| 命令 | 用途 | 示例 |
|------|------|------|
| `clusters` | 列出所有配置的集群 | `salt clusters` |
| `ping` | 测试 minion 连接 | `salt ping --tgt="*"` |
| `cmd` | 执行 shell 命令 | `salt cmd run --tgt="*" --command="uptime"` |
| `execute` | 执行脚本 | `salt execute --tgt="*" --script_content="..."` |
| `minions` | 查看 minion 信息 | `salt minions --mid="minion-01"` |
| `jobs` | 查看任务历史 | `salt jobs --jid="..."` |
| `keys` | 管理 minion keys | `salt keys accept --mid="new-minion"` |

## 详细文档

### 命令参考
完整的命令参数、使用示例和常见场景，请参阅 [commands.md](references/commands.md)。

该文档包含：
- 所有子命令的详细参数说明
- 目标主机格式（通配符、列表等）
- 常见使用场景（新 minion 加入、批量部署、健康检查等）
- 输出示例

### 配置指南
环境配置、Token 管理和故障排查，请参阅 [configuration.md](references/configuration.md)。

该文档包含：
- 配置文件格式和字段说明
- Token 缓存机制
- 多环境配置示例
- 安全建议
- 常见问题排查

## 工作流程

### 初始设置

1. 创建配置文件 `~/.config/salt/credentials.json`
2. 添加集群环境配置
3. 运行 `salt clusters` 验证配置
4. 运行 `salt ping` 测试连接

### 日常操作

**检查 minion 状态：**
```bash
salt ping
salt minions
```

**执行命令：**
```bash
salt cmd run --tgt="web-*" --command="systemctl status nginx"
```

**管理 keys：**
```bash
salt keys list
salt keys accept --mid="new-minion"
```

**查看任务：**
```bash
salt jobs
```

### 多环境管理

```bash
# 生产环境
salt -c prod ping

# 开发环境
salt -c dev ping

# 切换环境执行命令
salt -c staging cmd run --tgt="*" --command="hostname"
```

## 认证流程

Salt CLI 自动管理认证 token：

1. 首次执行命令时自动登录获取 token
2. Token 缓存到 `~/.config/salt/tokens/<cluster_name>.json`
3. 后续请求使用缓存的 token
4. Token 过期时自动重新登录
5. 401 错误时自动清除缓存并重试

无需手动管理 token。

## 目标主机选择

Salt 支持灵活的目标主机选择：

```bash
# 所有 minions
salt ping --tgt="*"

# 通配符匹配
salt ping --tgt="web-*"
salt ping --tgt="*-prod"

# 单个主机
salt ping --tgt="minion-01"

# 多个主机（逗号分隔）
salt ping --tgt="minion-01,minion-02,minion-03"
```

## 输出格式

### 美化输出（默认）
使用 rich 库美化输出，包含颜色、表格和格式化的 JSON。

```bash
salt ping
# 输出：
# minion-01: ✓ True
# minion-02: ✓ True
```

### 原始输出
使用 `--raw` 参数输出原始 JSON，适合脚本处理。

```bash
salt --raw ping
# 输出：
# {"return": [{"minion-01": true, "minion-02": true}]}
```

## 常见问题

### 配置文件不存在
创建 `~/.config/salt/credentials.json` 并添加集群配置。详见 [configuration.md](references/configuration.md)。

### 认证失败
检查配置文件中的 username、password 和 eauth 是否正确。

### 连接失败
验证 base_url 是否正确，Salt API 服务是否运行。

### Token 过期
Salt CLI 会自动处理 token 过期，无需手动干预。如果持续出现问题，删除 `~/.config/salt/tokens/` 下的缓存文件。

## 最佳实践

1. **使用环境参数**：生产环境始终使用 `-c prod` 明确指定
2. **目标主机验证**：执行危险操作前先用 `ping` 验证目标
3. **原始输出用于脚本**：自动化脚本使用 `--raw` 参数便于解析
4. **定期检查 keys**：使用 `salt keys list` 查看待接受的 minions
5. **查看任务历史**：使用 `salt jobs` 追踪命令执行历史

## 开发和测试

### 开发模式运行
```bash
uv run salt clusters
uv run salt -c prod ping
```

### 测试脚本
项目包含完整的测试脚本：
```bash
./test_salt_cli.sh
```

详细测试指南参见项目根目录的 `TESTING.md`。
