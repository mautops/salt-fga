# Salt CLI

Salt CLI 是一个用于执行 SaltStack CherryPy REST API 的命令行工具，提供简洁的命令行接口和美化的输出，并集成了基于 OpenFGA 的权限控制系统。

## 安装

```bash
git clone <repository-url>
cd salt
uv sync
./.venv/bin/salt-fga <command>
```

## 配置

### 集群配置：`~/.config/salt/credentials.json`

```json
[
  {
    "name": "prod",
    "description": "saltproject 生产环境",
    "base_url": "https://salt-api.example.com",
    "username": "saltadmin",
    "password": "your-password",
    "eauth": "file",
    "token_expire": "10h"
  }
]
```

字段说明：

- `name`: 环境名称，对应 `-c` 参数
- `base_url`: Salt CherryPy REST API 地址
- `eauth`: 认证方式（`file`、`pam`、`ldap`）
- `token_expire`: Token 过期时间（`10h`、`30m`、`60s`）

## 使用示例

```bash
# 查看所有环境
salt-fga clusters

# 测试 minion 连接
salt-fga ping
salt-fga -c prod ping --tgt "web-*"

# 执行 shell 命令
salt-fga cmd --tgt "*" --command "df -h"
salt-fga cmd run --tgt "web-*" --command "systemctl status nginx"

# 执行脚本
salt-fga execute --tgt "minion-001" --script_content "echo hello\nhostname"
salt-fga execute --tgt "*" --script_content "echo hello" --shell bash

# 查看 minion 信息
salt-fga minions
salt-fga minions --mid "minion-001"

# 查看任务历史
salt-fga jobs
salt-fga jobs --jid "20240101000000000000"

# 管理 minion keys
salt-fga keys list
salt-fga keys accept --mid "new-minion"
salt-fga keys reject --mid "untrusted-minion"
salt-fga keys delete --mid "old-minion"

# 原始 JSON 输出
salt-fga --raw ping
```

## 全局参数

| 参数            | 说明                               |
| --------------- | ---------------------------------- |
| `-c, --cluster` | 指定集群环境名称（默认使用第一个） |
| `--raw`         | 输出原始 JSON，不美化              |
| `--no-auth`     | 跳过权限检查（需要超级管理员身份） |

## 权限系统（OpenFGA）

Salt CLI 集成 OpenFGA 进行细粒度权限控制。**未配置 OpenFGA 时，所有命令自动放行。**

### OpenFGA 配置：`~/.config/salt/openfga.json`

```json
{
  "api_url": "http://localhost:8080",
  "store_id": "",
  "authorization_model_id": ""
}
```

> **注意**：`store_id` 和 `authorization_model_id` 由 `salt-fga permission init` 自动填入，无需手动设置。

### 初始化

```bash
# 初始化 OpenFGA Store 和授权模型（当前系统用户自动成为第一个超级管理员）
salt-fga permission init
```

### 超级管理员管理

超级管理员**必须通过 `fga` CLI 手动操作**，不支持通过 salt CLI 或直接编辑配置文件添加。这样设计是为了防止 AI 工具在无人授权的情况下自动添加或修改管理员权限。

#### 添加超级管理员

```bash
# 查看当前 Store ID
salt-fga permission status

# 使用 fga CLI 添加超级管理员（将 <store_id> 和 <username> 替换为实际值）
fga tuple write --store-id <store_id> \
  '[{"user":"user:<username>","relation":"admin","object":"cluster:system"}]'
```

#### 移除超级管理员

```bash
fga tuple delete --store-id <store_id> \
  '[{"user":"user:<username>","relation":"admin","object":"cluster:system"}]'
```

#### 查看所有超级管理员

```bash
fga tuple read --store-id <store_id> --object "cluster:system"
```

### 权限管理命令

```bash
# 查看配置状态
salt-fga permission status

# 授权/撤销命令执行权限
salt-fga permission grant_cmd --user alice --command ping
salt-fga permission grant_cmd --user alice --command cmd
salt-fga permission revoke_cmd --user alice --command cmd

# 授权/撤销主机访问权限
salt-fga permission grant_target --user alice --target web-01
salt-fga permission revoke_target --user alice --target web-01

# 管理集群成员
salt-fga permission add_member --user alice --cluster prod
salt-fga permission add_member --user alice --cluster prod --as_admin True
salt-fga permission remove_member --user alice --cluster prod

# 列出所有权限规则
salt-fga permission list
salt-fga permission list --type_filter command
salt-fga permission list --type_filter target

# 调试权限检查
salt-fga permission check --user alice --command ping --target "*" --cluster prod
```

### 权限模型说明

用户执行命令需同时满足：

1. 是目标集群的成员（`member of cluster:xxx`）
2. 有执行该命令的权限（`can_execute on command:xxx`）
3. 有访问目标主机的权限（`can_access on target:xxx`，通配符目标跳过此检查）

### 环境变量

| 变量                 | 说明                            | 默认值                     |
| -------------------- | ------------------------------- | -------------------------- |
| `COPAW_AUTH_TOKEN`   | 获取当前用户 ID 的 Bearer Token | 无（未设置则权限检查失败） |
| `COPAW_API_BASE_URL` | 用户认证 API 地址               | `http://localhost:8088`    |

## Token 管理

Token 自动缓存到 `~/.config/salt/tokens/<cluster_name>.json`，过期时自动刷新，遇到 401 自动重试。

## 开发

```bash
# 安装开发依赖
uv sync --group dev

# 单元测试（不依赖外部服务）
make test

# 集成测试（需要已配置的 Salt API 环境）
make test-integration

# 安装 Cursor Skill
make skill-install
```

## 架构说明

详细的架构说明请参考 [CLAUDE.md](./CLAUDE.md)。
