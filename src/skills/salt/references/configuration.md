# Salt CLI 配置指南

## 配置文件位置

Salt CLI 使用用户级配置文件，位于：
```
~/.config/salt/credentials.json
```

## 配置文件格式

配置文件为 JSON 数组，每个元素代表一个集群环境：

```json
[
  {
    "name": "prod",
    "description": "Production Environment",
    "base_url": "https://salt-api.prod.example.com",
    "username": "saltuser",
    "password": "your-password",
    "eauth": "file",
    "token_expire": "10h"
  },
  {
    "name": "dev",
    "description": "Development Environment",
    "base_url": "https://salt-api.dev.example.com",
    "username": "devuser",
    "password": "dev-password",
    "eauth": "file",
    "token_expire": "8h"
  }
]
```

## 配置字段说明

### name (必需)
环境名称，用于 `-c/--cluster` 参数指定环境。

**示例：** `"prod"`, `"dev"`, `"test"`

### description (必需)
环境描述，用于 `salt clusters` 命令显示。

**示例：** `"Production Environment"`, `"Development Environment"`

### base_url (必需)
Salt CherryPy REST API 的基础 URL。

**格式：** `https://hostname[:port]`

**示例：**
- `"https://salt-api.example.com"`
- `"https://salt-api.example.com:8000"`

### username (必需)
Salt API 认证用户名。

### password (必需)
Salt API 认证密码。

### eauth (必需)
Salt 外部认证系统类型。

**常见值：**
- `"file"` - 基于文件的认证
- `"pam"` - PAM 认证
- `"ldap"` - LDAP 认证

### token_expire (必需)
Token 过期时间配置。

**格式：**
- `"10h"` - 10 小时
- `"30m"` - 30 分钟
- `"60s"` - 60 秒

## Token 缓存

Salt CLI 自动缓存认证 token 以提高性能：

**缓存位置：**
```
~/.config/salt/tokens/<cluster_name>.json
```

**缓存内容：**
```json
{
  "token": "6d1b722e...",
  "timestamp": 1234567890.123,
  "cluster": "prod",
  "expire": 1234567890.123
}
```

**自动管理：**
- Token 过期时自动重新登录
- 401 错误时自动清除缓存并重试
- 无需手动管理

## 首次配置步骤

### 1. 创建配置目录
```bash
mkdir -p ~/.config/salt
```

### 2. 创建配置文件
```bash
cat > ~/.config/salt/credentials.json << 'EOF'
[
  {
    "name": "prod",
    "description": "Production Environment",
    "base_url": "https://your-salt-api.com",
    "username": "your-username",
    "password": "your-password",
    "eauth": "file",
    "token_expire": "10h"
  }
]
EOF
```

### 3. 验证配置
```bash
# 列出所有配置的集群
salt clusters

# 测试连接
salt ping
```

## 多环境配置示例

```json
[
  {
    "name": "prod",
    "description": "Production - US East",
    "base_url": "https://salt-api-us-east.example.com",
    "username": "prod-user",
    "password": "prod-password",
    "eauth": "file",
    "token_expire": "10h"
  },
  {
    "name": "prod-eu",
    "description": "Production - EU West",
    "base_url": "https://salt-api-eu-west.example.com",
    "username": "prod-user",
    "password": "prod-password",
    "eauth": "file",
    "token_expire": "10h"
  },
  {
    "name": "staging",
    "description": "Staging Environment",
    "base_url": "https://salt-api-staging.example.com",
    "username": "staging-user",
    "password": "staging-password",
    "eauth": "file",
    "token_expire": "8h"
  },
  {
    "name": "dev",
    "description": "Development Environment",
    "base_url": "https://salt-api-dev.example.com",
    "username": "dev-user",
    "password": "dev-password",
    "eauth": "pam",
    "token_expire": "4h"
  }
]
```

## 安全建议

1. **文件权限**：确保配置文件只有当前用户可读
   ```bash
   chmod 600 ~/.config/salt/credentials.json
   ```

2. **密码管理**：考虑使用环境变量或密钥管理工具
   - 不要将配置文件提交到版本控制
   - 定期更换密码

3. **Token 过期时间**：
   - 生产环境建议较短的过期时间（如 4-8 小时）
   - 开发环境可以使用较长的过期时间（如 10-12 小时）

4. **网络安全**：
   - 始终使用 HTTPS
   - 验证 SSL 证书
   - 使用 VPN 或专用网络访问 Salt API

## 故障排查

### 配置文件不存在
```
Error: Configuration file not found at ~/.config/salt/credentials.json
```

**解决方案：** 按照"首次配置步骤"创建配置文件

### 配置文件格式错误
```
Error: Invalid JSON format in configuration file
```

**解决方案：** 使用 JSON 验证工具检查配置文件格式

### 认证失败
```
Error: Login failed: 401 Unauthorized
```

**解决方案：**
1. 检查 username 和 password 是否正确
2. 检查 eauth 类型是否匹配 Salt Master 配置
3. 验证用户是否有相应权限

### 连接失败
```
Error: Connection failed: Connection refused
```

**解决方案：**
1. 检查 base_url 是否正确
2. 验证 Salt API 服务是否运行
3. 检查网络连接和防火墙设置
