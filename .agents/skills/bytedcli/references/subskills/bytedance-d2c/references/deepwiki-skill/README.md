# DeepWiki Skill

专注于 DeepWiki 文档和知识搜索的 capability。

## 可用命令

```
bytedcli deepwiki search --format snippets   # 搜索知识库片段
bytedcli deepwiki search --format summary    # 快速总结 + 文件定位
bytedcli deepwiki analyze                    # 深度分析与源码定位
bytedcli deepwiki get-collection             # 获取 collection name
bytedcli deepwiki get-content                # 获取完整文档内容
```

## 快速开始

### 前置要求
- 已安装 bytedcli 并完成 `bytedcli auth login`
- 仓库已生成 DeepWiki 索引
- 拥有仓库访问权限

### 基础用法

#### 1. 搜索文档
```bash
# 获取 collection name
COLLECTION=$(bytedcli --json deepwiki get-collection --repo-name "douyinfe/semi-design")

# 搜索知识
bytedcli --json deepwiki search --format snippets \
  --query "Button component usage" \
  --collection-name "$COLLECTION" \
  --limit 5
```

#### 2. 综合搜索
```bash
bytedcli --json deepwiki analyze \
  --query "Form validation architecture" \
  --repo-url "https://github.com/DouyinFE/semi-design.git" \
  --repo-name "douyinfe/semi-design" \
  --creator "your-email-prefix"
```

#### 3. 获取完整文档
```bash
# 先搜索获取 doc_id
bytedcli --json deepwiki search --format snippets --query "..." --repo-name "..." > results.json

# 提取 doc_id 并获取完整内容
bytedcli --json deepwiki get-content \
  --doc-id "_sys_auto_gen_doc_id-xxx" \
  --repo-name "douyinfe/semi-design"
```

## 命令说明

### `deepwiki search --format snippets`
搜索知识库片段，返回相关文档片段。

**参数：**
- `--query`: 搜索查询（必需）
- `--repo-name`: 仓库全名（可选）
- `--collection-name`: Collection 名称（可选）
- `--limit`: 结果数量（可选，默认 10）
- `--format`: `summary`（默认，快速答案 + 文件）或 `snippets`（原始文档块）

**耗时：** ~15 秒

### `deepwiki analyze`
综合搜索，返回答案和文件路径。

**参数：**
- `--query`: 搜索查询（必需）
- `--repo-url`: Git 仓库 URL（必需）
- `--repo-name`: 仓库全名（必需）
- `--creator`: 用户邮箱前缀（必需）
- `--branch`: 分支名（可选）

**耗时：** ~75 秒

### `deepwiki get-collection`
获取仓库或包的 collection name。

**参数：**
- `--repo-name`: 仓库全名（二选一）
- `--package-name`: 包名（二选一）
- `--query`: 查询上下文（可选）

**耗时：** ~120 秒

### `deepwiki get-content`
获取完整文档内容（必须在片段搜索之后调用）。

**参数：**
- `--doc-id`: 文档 ID（必需，来自片段搜索结果）
- `--repo-name`: 仓库全名（可选）
- `--collection-name`: Collection 名称（可选）

## 使用场景

### 场景 1: 查找 API 文档
```bash
COLLECTION=$(bytedcli --json deepwiki get-collection --package-name "@douyinfe/semi-ui")
bytedcli --json deepwiki search --format snippets \
  --query "Button API props" \
  --collection-name "$COLLECTION"
```

### 场景 2: 搜索内部知识
```bash
bytedcli --json deepwiki search --format snippets \
  --query "React 编码规范" \
  --collection-name "internal" \
  --limit 5
```

### 场景 3: 全面理解架构
```bash
# 多次调用获取全面理解
bytedcli --json deepwiki analyze --query "Monorepo 结构" --repo-url "..." --repo-name "..." --creator "..."
bytedcli --json deepwiki analyze --query "Form 组件模块" --repo-url "..." --repo-name "..." --creator "..."
bytedcli --json deepwiki analyze --query "工具库" --repo-url "..." --repo-name "..." --creator "..."
```

## 最佳实践

### 查询优化
- ✅ **好的查询**（<3 个特征）：`"Form validation usage"`
- ❌ **不好的查询**（>3 个特征）：`"Form with validation and errors and submit"`
- 💡 **建议**：将复杂查询拆分成多个聚焦的查询

### 工具选择
- **查找文档片段** → `deepwiki search --format snippets`
- **需要完整答案** → `deepwiki analyze`
- **不知道 collection** → `deepwiki get-collection`
- **需要完整文档** → `deepwiki get-content`

### 性能考虑
- 优先使用 `deepwiki search --format snippets`（最快，15秒）
- 仅在需要综合答案时使用 `deepwiki analyze`（75秒）
- 缓存 collection_name，避免重复调用 `deepwiki get-collection`

## 输出格式

所有命令在 `--json` 下输出 JSON 格式：
- 成功：JSON 输出到 stdout，退出码 0
- 失败：错误信息输出到 stderr，退出码 1

可以使用 `jq` 处理输出：
```bash
bytedcli --json deepwiki search --format snippets --query "..." --repo-name "..." | jq '.[] | .file_name'
```

## 故障排除

### 找不到知识
- 检查仓库是否已生成 DeepWiki 索引
- 验证 collection_name 是否正确
- 尝试使用 repo_name 代替 collection_name

### 权限错误
- 验证用户拥有仓库访问权限
- 检查 creator 参数是否正确
- 确保已登录代码平台

### 超时问题
- 检查网络连接
- 简化查询（减少特征）
- 使用 `deepwiki search --format snippets` 代替 `deepwiki analyze`

## 技术特性

- ✅ 零依赖：仅使用 Node.js 内置模块
- ✅ 跨平台：支持 macOS、Linux、Windows
- ✅ 易集成：标准 JSON 输出
- ✅ 易调试：错误信息清晰
- ✅ 可组合：通过 shell 脚本组合使用

## 相关链接

- [DeepWiki 门户](https://aiden-deepwiki.bytedance.net/)
- [生成索引](https://aiden-deepwiki.bytedance.net/)
