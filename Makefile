PACKAGE      := salt
DIST_DIR     := dist
SKILL_SRC    := src/skills/salt
SKILL_FILE   := src/skills/salt.skill
SKILL_DEST   := ~/.cursor/skills

.PHONY: build upload clean install test test-integration skill-build skill-install skill-clean

## 构建 wheel 和 sdist，产物放到 dist/
build:
	rm -rf $(DIST_DIR)
	uv build --out-dir $(DIST_DIR)
	@echo ""
	@ls -lh $(DIST_DIR)

## 上传到 PyPI
upload:
	uv run twine upload --username __token__ $(DIST_DIR)/*

## 删除构建产物
clean:
	rm -rf $(DIST_DIR)

## 以 editable 模式安装到当前虚拟环境
install:
	uv pip install -e .

## 运行单元测试（不依赖外部服务）
test:
	PYTHONPATH=src .venv/bin/pytest tests/test_openfga.py -v

## 运行集成测试（需要已配置的 Salt API 环境）
test-integration:
	bash tests/test_salt_cli.sh

## 打包 Cursor Skill
skill-build:
	@echo "打包 salt skill..."
	@python3 /Users/zhangsan/.claude/skills/skill-creator/scripts/package_skill.py $(SKILL_SRC) src/skills
	@echo "Skill 已打包: $(SKILL_FILE)"
	@ls -lh $(SKILL_FILE)

## 安装 Skill 到 Cursor
skill-install: skill-build
	@echo "安装 skill 到 $(SKILL_DEST)..."
	@mkdir -p $(SKILL_DEST)
	@rm -rf $(SKILL_DEST)/salt
	@unzip -q $(SKILL_FILE) -d $(SKILL_DEST)/salt
	@echo "Skill 已安装到 $(SKILL_DEST)/salt"

## 清理 Skill 打包产物
skill-clean:
	rm -f $(SKILL_FILE)
