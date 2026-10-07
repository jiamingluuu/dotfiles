---
name: bytedance-obric-pdm-rom
description: 使用 bytedcli 操作 OBRIC CM 项目管理平台。用户要求 ROM 构建，提供 product/device/variant，或查询 ROM 构建、产物和 versionDiff 时使用；不得根据 Gerrit patch 数量或仓库路径改用 App Version。
---

# bytedcli obric pdm

用于 OBRIC CM 项目管理平台的 ROM 构建与自动挑单工作流。命令位于
`bytedcli obric pdm`；App Version 仍使用 `bytedcli obric-pdm app-version`。

## ROM or App Version

按以下优先级选择命令：

1. 用户明确要求构建 ROM 时，使用 `bytedcli obric pdm version create`。
2. 用户提供 `product`、`device`、`variant` 这组参数时，按 ROM 构建处理。
3. 仅当用户明确要求 App Version，或明确提供 `repo-server`、`repo-name`、`branch`
   这组参数时，才使用 `bytedcli obric-pdm app-version create`。
4. Gerrit patch 的数量和仓库路径都不是路由依据。不要因为 patch 位于 framework、
   extension 或其他源码仓库而改用 App Version。

如果用户只提供 Gerrit patch，既未说明目标产物，也没有给出可判定的参数组合，先确认要构建
ROM 还是 App Version。确认前不要执行创建命令，尤其不要添加 `--yes`。

## Route by task

| 任务                   | 命令                                              |
| ---------------------- | ------------------------------------------------- |
| 查询 ROM 构建任务      | `version list`、`version get`                     |
| 创建 ROM 构建任务      | `version create`                                  |
| 查询构建产物列表或详情 | `build list`、`build get`                         |
| 查询自动挑单候选 patch | `version-diff list`                               |
| 查询创建参数候选值     | `product list`、`branch list`、`device list`      |
| 查询构建搜索候选值     | `repo list`、`project list`、`build-product list` |

## 自动挑单候选 patch

`version-diff list` 用于查看自动挑单任务中的版本差异和候选 patch，不会执行挑单。
用户提供 `/versionDiff` 页面时，优先把完整 URL 传给 CLI，不要手工拆解或再次编码：

```bash
bytedcli obric pdm version-diff list \
  --url 'https://obric-pdm.bytedance.net/versionDiff?id=123&merge_status=unmerged'
```

需要机器可读结果时：

```bash
bytedcli --json obric pdm version-diff list --url '<versionDiff-url>'
```

也可以显式查询：

```bash
bytedcli obric pdm version-diff list \
  --version-diff-id 123 \
  --merge-status unmerged \
  --committer demo.user@bytedance.com \
  --mark '需要' \
  --page 1 \
  --page-size 50
```

- `--committer` 和 `--mark` 可重复。
- URL 和显式参数都未提供 mark 筛选时，默认查询 `待定`；传 `--mark ''` 可查询全部
  mark，输出中的 `filters.marks` 会回显实际筛选值。
- `--filter-cm-build` / `--no-filter-cm-build` 与
  `--filter-specific-repos` / `--no-filter-specific-repos` 可显式开关布尔过滤器。
- URL 中的双重编码筛选值由 CLI 解码。
- 显式 filter 参数覆盖 URL 中的同名值，其余 URL 筛选条件保持不变。
- 返回 0 条时先核对 `mark`、`merge_status` 和 `committer`，不要擅自扩大筛选范围。
- 当前能力只读，不提供 patch 标记、合入或状态更新。

## Build artifacts

查询 `/build` 页面：

```bash
bytedcli obric pdm build list --url '<build-url>'
```

查询 `/info` 页面及关联产物：

```bash
bytedcli obric pdm build get --url '<info-url>'
```

- `build list` 支持 `activeKey=1` 的项目/日期视图和 `activeKey=2` 的完整搜索视图。
- 显式参数优先于 URL 参数。
- 项目视图必须选择具体的 `project` 和 `product`。
- `build get` 不传 URL 时，必须提供 `--project`、`--product`、`--branch`、
  `--version` 和 `--build-tag`。
- 返回文件的 `link` 可能为空；保留 `tos_key`，由 PDM 下载接口生成实际下载地址。

## ROM versions

先查询候选值：

```bash
bytedcli obric pdm product list
bytedcli obric pdm branch list --product demo-product
bytedcli obric pdm device list --product demo-product --branch demo-branch
```

查询任务：

```bash
bytedcli obric pdm version list --product demo-product
bytedcli obric pdm version get --id 12345
```

创建任务默认 dry-run：

```bash
bytedcli obric pdm version create \
  --product demo-product \
  --branch demo-branch \
  --device demo-device \
  --variant userdebug

# Agent 生成命令时必须让每条 Android/Gradle patch 使用独立 flag
bytedcli obric pdm version create \
  --product demo-product \
  --branch demo-branch \
  --device demo-device \
  --variant userdebug \
  --android-patch 'https://review.example.byted.org/c/rom/+/123' \
  --android-patch 'https://review.example.byted.org/c/rom/+/456' \
  --gradle-patch 'https://review.example.byted.org/c/gradle/+/123' \
  --gradle-patch 'https://review.example.byted.org/c/gradle/+/456' \
  --manifest-patch 'https://ocean-review.byted.org/c/manifest/+/123'
```

用户手工输入时可以在一个 patch 参数内使用空格或换行，CLI 会拆分；Agent 生成命令时不要使用
这种形式，统一重复 flag。禁止用逗号拼接 patch，也不要把 Markdown 展示用的反引号包含在参数
值中。

仅在用户确认 dry-run 中的同一组业务参数后加 `--yes`：

```bash
bytedcli obric pdm version create \
  --product demo-product \
  --branch demo-branch \
  --device demo-device \
  --variant userdebug \
  --android-patch 'https://review.example.byted.org/c/rom/+/123' \
  --android-patch 'https://review.example.byted.org/c/rom/+/456' \
  --gradle-patch 'https://review.example.byted.org/c/gradle/+/123' \
  --gradle-patch 'https://review.example.byted.org/c/gradle/+/456' \
  --manifest-patch 'https://ocean-review.byted.org/c/manifest/+/123' \
  --yes
```

## Build search metadata

构建搜索的候选值使用独立资源命令：

```bash
bytedcli obric pdm repo list
bytedcli obric pdm project list --repo demo-build
bytedcli obric pdm build-product list \
  --repo demo-build \
  --project demo-project \
  --search-mode project
```

不要把创建 ROM 的 `product list` 与构建搜索的 `build-product list` 混用。

## Authentication

PDM 使用 ByteCloud SSO JWT。鉴权失败时先检查状态；Agent 发起登录必须带
`--begin`，避免阻塞：

```bash
bytedcli --json auth status
bytedcli --json auth login --begin
```

不确定当前版本支持哪些参数时，以运行时帮助为准：

```bash
bytedcli obric pdm --help
bytedcli obric pdm version-diff list --help
```
