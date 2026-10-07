# Lego plugin actions

<!-- Load: MANDATORY for plugin get/register/compile/version/compile-detail/commit/branch actions; CONDITIONAL for end-to-end release when plugin or compiled version must be resolved; Do NOT Load for order tracking or pipeline confirm with a known order id. -->

### plugin get

查询插件详情。

```bash
bytedcli --site cn lego --region online plugin get --name demo_plugin
```

| 参数            | 必填 | 说明   |
| --------------- | ---- | ------ |
| `--name <name>` | 是   | 插件名 |

JSON：`data.plugin`，含 `plugin_name`、`scm_id`、`kind`、`is_adaptive`、`is_multi_ver`、`status`、`language`、`default_adaptive_run_mode`、`is_enable_category_pipeline`。

> `plugin version list` 不需要手动传 SCM id；service 层会用这里的 `scm_id` 自动作为请求参数。

### plugin register

注册新插件（写操作）。默认 dry-run 预览；确认后加 `--yes` 执行。

```bash
bytedcli --site cn lego --region online plugin register \
  --plugin-name demo_plugin --scm-path example/demo/demo_plugin \
  --plugin-type mul_ver_native --owners demo-owner --owners sample-owner --parent-id 123 \
  --language go --is-adaptive
```

| 参数                                        | 必填 | 说明                                                                                                 |
| ------------------------------------------- | ---- | ---------------------------------------------------------------------------------------------------- |
| `--plugin-name <pluginName>`                | 是   | 插件名                                                                                               |
| `--scm-path <scmPath>`                      | 是   | SCM 仓库路径（非空、不含空格）                                                                       |
| `--plugin-type <ipc\|json\|mul_ver_native>` | 是   | `ipc`=IPCKind（IDL 模式）、`json`=JsonKind（JSON 模式）、`mul_ver_native`=MulVerNative（多版本插件） |
| `--owners <owner...>`                       | 是   | 插件 owner，可重复传入多个                                                                           |
| `--parent-id <parentId>`                    | 是   | 服务树父节点 id（psm tree）                                                                          |
| `--language <lang>`                         | 是   | `go \| java \| node \| python \| rust \| cpp`                                                        |
| `--category-list <category...>`             | 否   | 项目类目，可重复                                                                                     |
| `--is-adaptive`                             | 否   | 标记为自适应插件                                                                                     |
| `--default-adaptive-run-mode <ipc\|native>` | 否   | 默认自适应运行模式：`ipc`=IPC、`native`=Native                                                       |
| `-y, --yes`                                 | 否   | 执行 live 注册                                                                                       |

行为：未传 `--yes` 时默认 dry-run，只返回请求体不执行。JSON：默认 dry-run → `{ dry_run: true, request }`；`--yes` → `{ message }`。

### plugin compile

创建编译任务（写操作）。默认 dry-run 预览；确认后加 `--yes` 执行。

```bash
bytedcli --site cn lego --region online plugin compile \
  --plugin-name demo_plugin --version-type offline --branch master
```

| 参数                         | 必填   | 说明                                          |
| ---------------------------- | ------ | --------------------------------------------- |
| `--plugin-name <pluginName>` | 是     | 插件名                                        |
| `--version-type <type>`      | 是     | 版本类型：`offline \| online \| test`         |
| `--branch <branch>`          | 二选一 | Git 分支                                      |
| `--commit-hash <commitHash>` | 二选一 | Git commit hash（与 `--branch` 至少提供一个） |
| `--multi-arch`               | 否     | 开启多架构编译                                |
| `--ipc-only`                 | 否     | 开启 ipc_only                                 |
| `--user-env <json>`          | 否     | 编译时用到的环境变量（JSON 字符串 map）       |
| `-y, --yes`                  | 否     | 执行 live 编译                                |

`--user-env` 示例只写单行内联 JSON：

```bash
bytedcli --site cn lego --region online plugin compile \
  --plugin-name demo_plugin --version-type offline --branch master \
  --user-env '{"region":"sg","mode":"fast"}'
```

行为：未传 `--yes` 时默认 dry-run，只返回请求体不执行。JSON：默认 dry-run → `{ dry_run: true, request }`（含 `plugin`、`branch`、`commitHash`、`versionType`、`multiArch`、`ipcOnly`、`userEnv`）；`--yes` → `{ version }`。

编译是异步任务，用 `plugin compile-detail get` 轮询状态（见 [状态与错误参考](statuses-and-errors.md) 的 ScmBuildStatus 终态）。

### plugin version list

列出编译版本。

```bash
bytedcli --site cn lego --region online plugin version list --plugin-name demo_plugin
```

| 参数                           | 必填 | 说明                |
| ------------------------------ | ---- | ------------------- |
| `--plugin-name <pluginName>`   | 是   | 插件名              |
| `--page <page>`                | 否   | 页码，默认 `1`      |
| `--page-size <pageSize>`       | 否   | 每页条数，默认 `20` |
| `--branch <branch>`            | 否   | 按分支过滤          |
| `--commit-hash <commitHash>`   | 否   | 按 commit 过滤      |
| `--version-key <versionKey>`   | 否   | 按版本关键词过滤    |
| `--operator <operator>`        | 否   | 按操作者过滤        |
| `--version-type <versionType>` | 否   | 按版本类型过滤      |

行为：service 层先用 `--plugin-name` 拉插件详情，既验证插件存在，也判断 multi-version / ipc-only 分支，并用详情里的 `scm_id` 作为请求参数。插件不存在时停止并返回 `LEGO_PLUGIN_NOT_FOUND`；调用方无需也无法手动传入 SCM id。JSON：`{ count, versions, kind, ipc_only, online_version, version_regions, page, page_size }`。普通插件与多版本插件走不同的后端 endpoint，但 CLI 参数一致。

选择版本时使用完整的 `versions` 数组：

- 用户指定具体版本时，精确匹配版本号并确认所有已返回的 `status` / `status_arm` 都是 `build_ok` / `success`。版本不存在或未成功时停止，不执行 `order create`，也不替换为相近版本。
- 用户说“最新版本”时，把完整 JSON 输入 skill 自带脚本：

  ```bash
  python3 <skill-dir>/scripts/lego_workflow_state.py select --kind latest-successful-version < version-list.json
  ```

  脚本只保留所有已返回架构状态均成功的版本，再按 `create_time` 选择唯一最新项。成功候选的时间缺失、非法或并列时返回 `selected=null`；此时展示 `reason` 并停止，不改用列表顺序或版本号继续选择。`selected` 非空时，在 `order create` dry-run 中回显具体版本。

### plugin compile-detail get

查询某个编译版本详情。

```bash
bytedcli --site cn lego --region online plugin compile-detail get --plugin-name demo_plugin --version 1.0.0.1
```

| 参数                         | 必填 | 说明       |
| ---------------------------- | ---- | ---------- |
| `--plugin-name <pluginName>` | 是   | 插件名     |
| `--version <version>`        | 是   | 编译版本号 |

JSON：`data.detail`，含 `status`、`status_arm`（字符串，见 [状态与错误参考](statuses-and-errors.md) 的 ScmBuildStatus）、`branch_name`、`commit_hash`、`type`、`create_user`、`create_time` 等。

### plugin commit list

```bash
bytedcli --site cn lego --region online plugin commit list --plugin-name demo_plugin
```

| 参数                         | 必填 | 说明   |
| ---------------------------- | ---- | ------ |
| `--plugin-name <pluginName>` | 是   | 插件名 |

JSON：`{ items, count }`，每个 item 含 `hash`、`message`。

### plugin branch list

```bash
bytedcli --site cn lego --region online plugin branch list --plugin-name demo_plugin --keyword main
```

| 参数                         | 必填 | 说明           |
| ---------------------------- | ---- | -------------- |
| `--plugin-name <pluginName>` | 是   | 插件名         |
| `--keyword <keyword>`        | 是   | 分支关键词过滤 |

JSON：`{ items, count }`，`items` 为分支名字符串数组。
