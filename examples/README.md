# Salt CLI 示例

本目录包含 Salt CLI 工具的使用示例。

## OpenFGA 权限系统

### 功能演示

运行完整的功能演示：

```bash
.venv/bin/python examples/openfga-demo.py
```

这个脚本演示了：
- 默认拒绝策略
- 添加权限规则
- 查看权限规则
- 权限检查测试
- 正则表达式匹配
- 删除规则

### 快速开始

运行快速开始脚本（需要配置 Salt API）：

```bash
./examples/openfga-quickstart.sh
```

这个脚本演示了：
- 设置用户
- 添加权限规则
- 测试权限
- 执行命令
- 多用户场景

## 更多信息

- OpenFGA 权限系统文档: `src/openfga/README.md`
- 实现总结: `OPENFGA_IMPLEMENTATION.md`
- 项目文档: `CLAUDE.md`
