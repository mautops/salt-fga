# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 Salt CLI 工具，用于封装 SaltStack Cherry API 的各种功能。该工具通过命令行方式执行 Salt 模块，并使用 rich 库美化输出结果。

## 核心架构

### 多环境配置管理
- 配置文件位置: `~/.config/salt/credentials.json`（用户级配置，不纳入版本控制）
- 配置格式为 JSON 数组，每个环境包含：
  - `name`: 环境名称（如 prod, dev, test）
  - `description`: 环境描述
  - `base_url`: Salt API 地址
  - `username`: 认证用户名
  - `password`: 认证密码
  - `eauth`: 认证方式（通常为 "file"）
  - `token_expire`: Token 过期时间（如 "10h"）
- 命令行通过 `-c/--cluster` 参数指定环境
- 如果未指定环境，使用配置文件中的第一个环境作为默认环境

### API 认证流程
- 使用 `/login` 端点获取认证 token
- 登录响应格式：`{"return": {"token": "...", "expire": 1234567890.0, ...}}`（部分版本可能返回列表格式）
- Token 通过 `X-Auth-Token` header 传递给后续请求
- Token 应缓存到 `~/.config/salt/tokens/<cluster_name>.json`
- 优先使用 API 返回的 `expire` 时间戳，回退到基于 `token_expire` 配置计算
- Token 过期时自动重新登录并刷新缓存

### 项目结构设计
```
salt/
├── pyproject.toml          # 项目配置和依赖
├── src/                    # 源代码目录
│   ├── salt/               # 主包目录
│   │   ├── __init__.py
│   │   ├── cli.py          # CLI 入口，使用 fire 管理命令
│   │   ├── client.py       # Salt API 客户端封装
│   │   ├── config.py       # 配置管理（读取 ~/.config/salt/credentials.json）
│   │   ├── auth.py         # Token 管理（缓存、过期检查、刷新）
│   │   ├── formatter.py    # 输出格式化（rich 美化 + 原始输出）
│   │   └── commands/       # 子命令目录
│   │       ├── __init__.py
│   │       ├── clusters.py # 查看和管理环境配置
│   │       ├── ping.py     # test.ping 测试连接
│   │       ├── cmd.py      # cmd.run 执行 shell 命令
│   │       ├── execute.py  # run_execute.run 执行脚本
│   │       ├── minions.py  # /minions 接口，查看 minion 信息
│   │       ├── jobs.py     # /jobs 接口，查看任务历史
│   │       └── keys.py     # /keys 接口，管理 minion keys
│   ├── openfga/            # OpenFGA 权限管理模块
│   │   ├── __init__.py
│   │   ├── models.py       # 权限规则数据模型
│   │   ├── store.py        # 权限规则存储（本地文件）
│   │   ├── checker.py      # 权限检查器（默认拒绝策略）
│   │   ├── commands.py     # 权限管理命令
│   │   ├── authorization_model.fga   # OpenFGA 模型定义（DSL 格式）
│   │   └── README.md       # 权限系统使用指南
│   └── skills/             # 扩展技能和插件目录
├── examples/               # 示例脚本
│   └── openfga-quickstart.sh  # 权限系统快速开始
└── tests/                  # 测试目录
    └── test_openfga.py     # 权限系统测试

用户配置目录 (~/.config/salt/):
├── credentials.json       # 环��配置文件
├── permissions.json       # 权限规则配置文件
└── tokens/                # Token 缓存目录
    ├── prod.json
    ├── dev.json
    └── test.json
```

### 技术栈
- **fire**: CLI 参数管理，自动将类方法转换为命令行接口
- **requests**: HTTP 客户端，调用 Salt API
- **rich**: 终端输出美化，支持表格、JSON、进度条等
- **uv**: Python 依赖管理工具

## 开发规范

### 命令实现模式
每个子命令应该：
1. 在 `src/salt/commands/` 目录下创建独立的 Python 文件
2. 实现一个类，包含命令的主要逻辑
3. 通过 `cli.py` 中的 fire 自动注册为子命令
4. 接收必要的参数（tgt, fun, arg, kwarg 等）
5. 调用 `client.py` 中的 API 客户端
6. 使用 `formatter.py` 格式化输出

### API 调用示例
```python
# 标准的 Salt API 请求格式
{
    "client": "local",      # 客户端类型
    "tgt": "*",            # 目标主机（支持通配符）
    "fun": "test.ping",    # 要执行的函数
    "arg": [],             # 位置参数列表
    "kwarg": {}            # 关键字参数字典
}
```

### 输出格式化
- 默认使用 rich 美化输出（表格、颜色、JSON 高亮）
- 提供 `--raw` 参数支持原始输出
- 错误信息使用 rich 的 `Console.print_exception()` 展示

## 常用命令

### 开发环境设置
```bash
# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/python
```

### 运行 CLI
```bash
# 查看所有环境
salt clusters

# 使用默认环境执行命令
salt ping

# 指定环境执行命令
salt -c prod ping
salt -c prod ping --tgt "minion-001"
salt -c prod cmd --tgt "*" --command "df -h"
salt -c prod execute --tgt "minion-001" --script_content "#!/bin/bash\necho hello\nhostname"
salt -c prod minions
salt -c prod jobs
salt -c prod keys

# 原始 JSON 输出
salt --raw ping

# 开发模式运行
uv run python -m salt.cli clusters
uv run python -m salt.cli -c prod ping
```

### 测试
```bash
# 运行所有测试
uv run pytest

# 运行单个测试文件
uv run pytest tests/test_client.py
```

## 关键注意事项

1. **多环境配置**:
   - 配置文件存储在用户目录 `~/.config/salt/credentials.json`
   - 首次运行时如果配置文件不存在，应提示用户创建
   - 支持通过 `-c/--cluster` 参数切换环境

2. **认证 Token 管理**:
   - Token 缓存到 `~/.config/salt/tokens/<cluster_name>.json`
   - 包含 token 值和获取时间戳
   - 根据 `token_expire` 配置自动判断是否过期
   - 过期时自动重新登录获取新 token

3. **错误处理**:
   - API 调用失败时提供清晰的错误信息
   - 配置文件不存在或格式错误时给出友好提示
   - 网络错误、认证失败等场景的错误处理

4. **目标主机格式**: 支持单个主机、通配符、列表等多种格式

5. **命令参数**: 区分位置参数（arg）和关键字参数（kwarg）

6. **输出模式**: 同时支持美化输出和原始输出两种模式

7. **CLI 参数设计**:
   - 全局参数: `-c/--cluster` 指定环境，`--raw` 原始输出
   - 子命令: `clusters`, `ping`, `cmd`, `execute`, `minions`, `jobs`, `keys`
   - 使用 fire 自动解析参数，保持简洁的命令行接口

8. **CherryPy REST API 端点**:
   - `POST /login` — 登录获取 token，返回格式：`{"return": {"token": "...", "expire": ..., ...}}`
   - `POST /` — 执行 Salt 命令（local/runner/wheel client），请求体为 JSON 数组：`[{client, tgt, fun, ...}]`
   - `GET /minions[/{mid}]` — 查看 minion 信息
   - `POST /minions` — 异步执行命令（local_async），返回 jid
   - `GET /jobs[/{jid}]` — 查看任务历史
   - `GET /keys[/{mid}]` — 查看 minion keys
   - `POST /keys` — 生成新 key（返回 tarball）
   - `POST /run` — 不使用 session 直接执行命令（内嵌认证），请求体为 JSON 数组：`[{client, tgt, fun, username, password, eauth, ...}]`

9. **Key 管理**:
   - 使用 `wheel` 客户端通过 `POST /` 端点管理 keys
   - 接受 key: `client="wheel"`, `fun="key.accept"`, `kwarg={"match": mid}`
   - 拒绝 key: `client="wheel"`, `fun="key.reject"`, `kwarg={"match": mid}`
   - 删除 key: `client="wheel"`, `fun="key.delete"`, `kwarg={"match": mid}`

10. **客户端类型**:
    - `local` — 在 minions 上执行模块（需要 tgt）
    - `local_async` — 异步执行，立即返回 jid
    - `runner` — 在 master 上执行 runner 模块
    - `wheel` — master 端操作（如 key 管理），不需要 tgt
