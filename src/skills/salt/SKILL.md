---
name: salt
description: "Salt CLI tool for managing SaltStack infrastructure via CherryPy REST API. Use when working with Salt commands, SaltStack operations, minion management, or when the user asks about: (1) Salt command usage and syntax, (2) Managing Salt minions (ping, execute commands, run scripts), (3) Salt key management (accept, reject, delete keys), (4) Viewing job history and minion information, (5) Multi-environment Salt cluster configuration, (6) Salt API authentication and token management, (7) OpenFGA permission management, (8) Troubleshooting Salt CLI issues, or (9) Any questions about 'salt' command parameters and options."
---

# Salt CLI

Salt CLI 是一个用于通过 SaltStack CherryPy REST API 管理基础设施的命令行工具，集成了 OpenFGA 权限控制系统。

## 快速开始

### 基本命令结构

```bash
salt-fga [全局参数] <子命令> [子命令参数]
```

### 常用命令示例

```bash
# 列出所有集群环境
salt-fga clusters

# Ping 所有 minions
salt-fga ping

# 在指定环境执行命令
salt-fga -c prod ping --tgt="web-*"

# 执行 shell 命令（两种等价写法）
salt-fga cmd run --tgt="*" --command="uptime"
salt-fga cmd --tgt="*" --command="uptime"

# 管理 minion keys
salt-fga keys list
salt-fga keys accept --mid="new-minion"
```

## 全局参数

### -c, --cluster

指定集群环境（对应配置文件中的 name 字段）。未指定时使用配置文件中的第一个环境。

```bash
salt-fga -c prod ping
salt-fga -c dev minions
```

### --raw

输出原始 JSON 格式，不进行美化。

```bash
salt-fga --raw ping
salt-fga --raw jobs
```

### --no-auth

禁用 OpenFGA 权限检查（需要当前系统用户是超级管理员）。

```bash
salt-fga --no-auth ping
salt-fga --no-auth cmd --tgt="*" --command="uptime"
```

## 子命令概览

| 命令         | 用途                  | 示例                                                |
| ------------ | --------------------- | --------------------------------------------------- |
| `clusters`   | 列出所有配置的集群    | `salt-fga clusters`                                 |
| `ping`       | 测试 minion 连接      | `salt-fga ping --tgt="*"`                           |
| `cmd`        | 执行 shell 命令       | `salt-fga cmd --tgt="*" --command="uptime"`         |
| `execute`    | 执行脚本内容          | `salt-fga execute --tgt="*" --script_content="..."` |
| `minions`    | 查看 minion 信息      | `salt-fga minions --mid="minion-01"`                |
| `jobs`       | 查看任务历史          | `salt-fga jobs --jid="..."`                         |
| `keys`       | 管理 minion keys      | `salt-fga keys accept --mid="new-minion"`           |
| `permission` | 管理 OpenFGA 权限规则 | `salt-fga permission status`                        |

## 子命令详解

### clusters

列出所有配置的集群环境。

```bash
salt-fga clusters           # 等价写法
salt-fga clusters list      # 等价写法
```

### ping

执行 `test.ping` 测试 minion 连接。

```bash
salt-fga ping               # ping 所有 minions（默认 tgt="*"）
salt-fga ping --tgt="web-*"
salt-fga -c prod ping --tgt="minion-01"
```

参数：

- `--tgt`: 目标主机，默认 `*`

### cmd

在目标主机上执行 shell 命令（调用 `cmd.run` 模块）。

```bash
salt-fga cmd run --tgt="*" --command="df -h"
salt-fga cmd --tgt="*" --command="df -h"    # 等价写法
salt-fga -c prod cmd --tgt="web-*" --command="systemctl status nginx"
```

参数：

- `--tgt`: 目标主机（必填）
- `--command`: 要执行的 shell 命令（必填）

### execute

在目标主机上执行脚本内容（调用 `run_execute.run` 模块）。

```bash
salt-fga execute --tgt="minion-01" --script_content="#!/bin/bash\nhostname"
salt-fga execute --tgt="*" --script_content="echo hello" --shell="sh"
```

参数：

- `--tgt`: 目标主机（必填）
- `--script_content`: 脚本内容字符串（必填）
- `--shell`: 脚本解释器，默认 `bash`

### minions

查看 minion 信息。

```bash
salt-fga minions                    # 查看所有 minions
salt-fga minions --mid="minion-01"  # 查看指定 minion
```

参数：

- `--mid`: Minion ID，不指定时返回全部

### jobs

查看任务执行历史。

```bash
salt-fga jobs                        # 查看所有任务
salt-fga jobs --jid="2024..."        # 查看指定任务
```

参数：

- `--jid`: Job ID，不指定时返回全部

### keys

管理 minion keys，支持 `list`、`accept`、`reject`、`delete` 子命令。

```bash
salt-fga keys                        # 默认：列出所有 keys（等价 keys list）
salt-fga keys list                   # 列出所有 keys
salt-fga keys list --mid="minion-01" # 查看指定 minion 的 key
salt-fga keys accept --mid="new-minion"
salt-fga keys reject --mid="bad-minion"
salt-fga keys delete --mid="old-minion"
```

参数：

- `--mid`: Minion ID（list 可选，accept/reject/delete 必填）

### permission

管理 OpenFGA 权限规则（需要管理员权限，由系统用户名判断）。

```bash
# 查看配置状态
salt-fga permission status

# 初始化 OpenFGA Store 和授权模型
salt-fga permission init
salt-fga permission init --name="my-salt-store"

# 授权/撤销命令权限
salt-fga permission grant_cmd --user="alice" --command="ping"
salt-fga permission grant_cmd --user="alice" --command="cmd"
salt-fga permission revoke_cmd --user="alice" --command="cmd"

# 授权/撤销主机访问权限
salt-fga permission grant_target --user="alice" --target="web-01"
salt-fga permission revoke_target --user="alice" --target="web-01"

# 管理集群成员
salt-fga permission add_member --user="alice" --cluster="prod"
salt-fga permission add_member --user="alice" --cluster="prod" --as_admin=True
salt-fga permission remove_member --user="alice" --cluster="prod"

# 列出所有权限规则
salt-fga permission list
salt-fga permission list --type_filter="command"   # 只看命令权限
salt-fga permission list --type_filter="target"    # 只看主机权限
salt-fga permission list --type_filter="cluster"   # 只看集群成员

# 调试权限检查
salt-fga permission check --user="alice" --command="ping" --target="*" --cluster="prod"
```

## 配置文件

### 集群配置：`~/.config/salt/credentials.json`

```json
[
  {
    "name": "prod",
    "description": "生产环境",
    "base_url": "https://salt-api.example.com",
    "username": "saltuser",
    "password": "secret",
    "eauth": "file",
    "token_expire": "10h"
  },
  {
    "name": "dev",
    "description": "开发环境",
    "base_url": "https://salt-dev.example.com",
    "username": "saltuser",
    "password": "secret",
    "eauth": "file",
    "token_expire": "10h"
  }
]
```

字段说明：

- `name`: 环境名称（`-c` 参数使用此值）
- `base_url`: Salt API 地址
- `eauth`: 认证方式（通常为 `file`）
- `token_expire`: Token 过期时间，支持 `10h`、`30m`、`3600s` 格式

### OpenFGA 权限配置：`~/.config/salt/openfga.json`

```json
{
  "api_url": "http://localhost:8080",
  "store_id": "01JF...",
  "authorization_model_id": "01JF..."
}
```

字段说明：

- `api_url`: OpenFGA 服务地址
- `store_id`: 运行 `salt-fga permission init` 后自动填入
- `authorization_model_id`: 运行 `salt-fga permission init` 后自动填入

> **超级管理员不在此文件中配置**，超管由系统管理员在 OpenFGA 层面单独维护，不通过 salt CLI 管理。

## 权限系统

### 工作原理

1. 每次执行命令时，通过 `COPAW_AUTH_TOKEN` 环境变量调用用户服务获取当前用户 ID
2. 向 OpenFGA 发起三项权限检查：
   - 用户是否为集群成员（`member` of `cluster:xxx`）
   - 用户是否有执行该命令的权限（`can_execute` on `command:xxx`）
   - 用户是否有访问目标主机的权限（`can_access` on `target:xxx`，通配符目标跳过）
3. 三项均通过才允许执行

### 降级策略

- OpenFGA **未初始化**（`store_id` 或 `authorization_model_id` 为空）时，**自动放行**所有命令
- 使用 `--no-auth` 参数可跳过权限检查（需要当前系统用户是超级管理员）

### 环境变量

| 变量                 | 用途                                | 默认值                     |
| -------------------- | ----------------------------------- | -------------------------- |
| `COPAW_AUTH_TOKEN`   | 用于获取当前用户 ID 的 Bearer Token | 无（未设置则权限检查失败） |
| `COPAW_API_BASE_URL` | 用户认证 API 地址                   | `http://localhost:8088`    |

### 超级管理员管理

> **重要**: 超级管理员由系统管理员在 OpenFGA 层面直接维护，**不通过 `salt-fga permission` 子命令管理，也不在任何配置文件中配置**。AI 工具（包括本工具）不应尝试添加或修改超级管理员权限。

### 权限初始化流程

```bash
# 1. 启动 OpenFGA 服务
# 2. 配置 ~/.config/salt/openfga.json（只需填入 api_url）
# 3. 初始化 Store 和授权模型（当前系统用户自动成为第一个超级管理员）
salt-fga permission init

# 4. 添加用户到集群
salt-fga permission add_member --user="alice" --cluster="prod"

# 5. 授权命令和主机
salt-fga permission grant_cmd --user="alice" --command="ping"
salt-fga permission grant_cmd --user="alice" --command="cmd"
salt-fga permission grant_target --user="alice" --target="web-01"
```

## 认证流程

Salt CLI 自动管理 Salt API 的认证 token：

1. 首次执行命令时自动登录获取 token
2. Token 缓存到 `~/.config/salt/tokens/<cluster_name>.json`
3. 优先使用 API 返回的 `expire` 时间戳判断过期
4. Token 过期时自动重新登录
5. 遇到 401 错误时自动清除缓存并重试

## 目标主机选择

```bash
salt-fga ping --tgt="*"                          # 所有 minions
salt-fga ping --tgt="web-*"                      # 通配符匹配
salt-fga ping --tgt="minion-01"                  # 单个主机
salt-fga ping --tgt="minion-01,minion-02"        # 多个主机（逗号分隔）
```

注意：通配符目标（包含 `*` 或 `?`）会跳过 OpenFGA 的 `can_access` 主机权限检查。

## 输出格式

```bash
# 美化输出（默认）- 使用 rich 库，带颜色和格式
salt-fga ping

# 原始 JSON 输出 - 适合脚本处理
salt-fga --raw ping
```

## 常见问题

### 配置文件不存在

创建 `~/.config/salt/credentials.json` 并添加集群配置。

### 权限检查失败 - 未指定用户名

设置 `COPAW_AUTH_TOKEN` 环境变量，或使用 `--no-auth` 参数（需要管理员权限）。

### 权限被拒绝

使用 `salt-fga permission check` 调试，确认用户是集群成员且有相应命令和主机权限。

### Token 过期

Salt CLI 会自动处理。如果持续出现问题，删除 `~/.config/salt/tokens/` 下的缓存文件。

### OpenFGA 未初始化时的行为

未配置 OpenFGA 时，所有命令自动放行（降级策略）。需要权限控制时运行 `salt-fga permission init`。

## 最佳实践

1. **生产环境始终指定集群**: `salt-fga -c prod ping`
2. **执行危险操作前先验证目标**: 先用 `ping` 确认目标主机
3. **自动化脚本使用 `--raw`**: 便于 JSON 解析
4. **定期检查 keys**: `salt-fga keys list` 查看待接受的 minions
5. **权限最小化原则**: 只授予用户实际需要的命令和主机权限
6. **OpenFGA 降级感知**: 生产环境确保 OpenFGA 已初始化，避免意外放行

## 权限操作规范

> **严格禁止**: 不得使用 `fga` CLI 或任何其他方式直接操作 OpenFGA 权限数据。所有权限管理**必须且只能**通过 `salt-fga permission` 子命令完成。

合法的权限操作方式：

```bash
salt-fga permission grant_cmd --user alice --command ping
salt-fga permission revoke_cmd --user alice --command cmd
salt-fga permission grant_target --user alice --target web-01
salt-fga permission add_member --user alice --cluster prod
salt-fga permission remove_member --user alice --cluster prod
salt-fga permission list
```

超级管理员的添加与移除属于系统运维操作，超出 AI 工具的职责范围，不应由 AI 执行。
