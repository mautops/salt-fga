# Salt Skill

这是为 Salt CLI 工具创建的 Claude Code skill，提供完整的命令参考和使用指南。

## Skill 内容

### SKILL.md
主文档，包含：
- 快速开始指南
- 全局参数说明（-c, --raw）
- 所有子命令概览
- 工作流程示例
- 认证流程说明
- 最佳实践

### references/commands.md
详细的命令参考，包含：
- 所有子命令的完整参数说明
- 使用示例和输出示例
- 目标主机格式（通配符、列表等）
- 常见使用场景（新 minion 加入、批量部署、健康检查、故障排查）

### references/configuration.md
配置和故障排查指南，包含：
- 配置文件格式和字段详解
- Token 缓存机制
- 多环境配置示例
- 安全建议
- 常见问题排查

## 使用方式

1. 将 `salt-cli.skill` 文件安装到 Claude Code
2. 当用户询问 Salt 命令相关问题时，skill 会自动触发
3. Skill 提供完整的命令参考和使用指南

## 触发场景

Skill 会在以下场景自动触发：
- Salt 命令使用和语法问题
- 管理 Salt minions（ping、执行命令、运行脚本）
- Salt key 管理（accept、reject、delete）
- 查看任务历史和 minion 信息
- 多环境 Salt 集群配置
- Salt API 认证和 token 管理
- Salt CLI 故障排查
- 任何关于 'salt' 命令参数和选项的问题

## Skill 特点

1. **渐进式信息披露**：
   - SKILL.md 提供快速参考和概览
   - references/ 包含详细文档，按需加载

2. **完整的命令覆盖**：
   - 所有子命令（clusters, ping, cmd, execute, minions, jobs, keys）
   - 全局参数和输出模式
   - 目标主机选择语法

3. **实用的场景示例**：
   - 新 minion 加入流程
   - 批量部署脚本
   - 健康检查
   - 故障排查

4. **配置和安全**：
   - 完整的配置文件格式说明
   - Token 管理机制
   - 安全最佳实践

## 文件位置

- Skill 源码：`src/skills/salt/`
- 打包文件：`salt.skill`
