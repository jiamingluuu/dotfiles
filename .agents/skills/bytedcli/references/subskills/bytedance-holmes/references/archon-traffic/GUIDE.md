---
name: archon-traffic
description: 为 C++ 业务仓库接入或升级 Archon 流量录制/回放依赖（archon / archon-gen / folly / fbthrift / traffic_sinker_lib / mongo-cxx-driver）。TrustPress 录制与 TikDiff 引流回放共用这一套编译期底座。当任务提到 Archon 流量录制接入、TrustPress 接入、TikDiff 接入、链式请求有序录制、traffic_sinker_lib 迁移、替换 trustpress_databus_lib、dep_graph.blade 依赖核对或依赖升级时使用。同时覆盖只有 BUILD、没有 dep_graph.blade 的仓库（BUILD-only 体检）以及 Archon 初始化由共享框架仓承载的仓库（改动清单拆成业务仓 / 框架仓两栏）。改动落在业务仓库的 dep_graph.blade、BUILD 与 sinker 注入点，不涉及 bytedcli 命令。
---

# Archon 流量录制依赖接入与升级

`archon` + `archon-gen` + `folly` / `fbthrift` + `traffic_sinker_lib` 是 Archon 流量录制的**编译期底座**，不专属某一个产品：TrustPress 录制、TikDiff 引流回放都跑在这套依赖之上，接入方式与核对口径一致。所以本文按「Archon 流量录制」组织，只在涉及具体开关 / 存储通道时才区分 TrustPress 与 TikDiff。

## 权威来源

本文是可执行的操作手册，**版本基线与平台侧配置的唯一权威源是下面两篇文档**；本文里的参考 commit、版本下限都是从文档 1 抄来的快照，发现对不上时以文档为准：

- [TrustPress - 特色功能 · 接入流程](https://bytedance.larkoffice.com/wiki/IokbwE3AJiIjVVk5cnDcYBBYnhh#OvaEdXZnFo2xIoxThUElgyS3gpf)：依赖基线、Archon 版本下限、`ARCHON_ENABLE_TRUSTPRESS` 开关、录制参数、可开启的集群与 idc、`holmes_rec_conf` 平台侧流量源配置、示例 MR。
- [[使用说明] Archon 接入 TrustPress 流量录制](https://bytedance.larkoffice.com/wiki/SWcwwlmRviyHHLkvQeBcIrqynVb)：`archon::diff::trustpress::Sinker` 接口契约与自定义 sinker 示例（需要自己写落库通道时看这篇）。

## 适用场景

- **新增接入**：某个 C++ 业务服务要接 Archon 流量录制（TrustPress 录制、TikDiff 引流回放，或两者都要），需要在业务仓库里补齐依赖并注入 sinker。
- **依赖更新**：已接入的仓库要把这套依赖核对/升级到各自分支的最新 HEAD，或从旧 sinker（`data/trustpress_databus_lib`）迁移到新 sinker（`data-arch/traffic_sinker_lib`）。
- **接入前体检 / MR 自检**：判断一个 MR 的依赖是否都已是最新，产出可粘贴到 MR 描述里的核对表。

不适用：TrustPress 压测任务的创建与查询（用 `bytedcli holmes trust-press ...`）、TikDiff 引流任务的创建与诊断（用 `bytedcli holmes tikdiff ...`）。本文只管业务仓库侧的编译期依赖接线。

## 先探测依赖图形态

不同业务仓的依赖声明方式不一样，脚本第一步先探测形态（`detect_dep_layout`），后续判定口径完全由形态决定。**不要假设每个仓库都有 `dep_graph.blade`**：

| `dep_layout`   | 判定条件                             | 判定口径                                                                                       |
| -------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `dep_graph`    | 根目录有 `dep_graph.blade`           | 完整逻辑：远端 HEAD 水位（`stale` / `ok(latest)`）、`--verify` 下限校验、`--apply` 自动改写依赖 |
| `build_only`   | 无 `dep_graph.blade`，但有 `BUILD`   | 「BUILD-only 体检模式」：只判存在性 + 分支名，禁用依赖改写                                     |
| `unsupported`  | 两者都没有（例如纯 CONFIG / 数据仓） | 输出 `not_applicable` 并**软退出（exit 0）**：本仓不是 C++ 服务仓，Archon 录制不适用           |

只有仓库根目录的 `dep_graph.blade` 算依赖图。`blade_root/BLADE_ROOT.local` 之类的其它 `*.blade` 只承载编译 flag，**不参与依赖解析**，不要因为看到 `*.blade` 就当成依赖图去解析。

## 必需依赖清单

Archon 流量录制链路要求以下依赖同时在位（TrustPress / TikDiff 通用）。**判定与改写的目标值一律是执行时从远端解析的分支 HEAD**，下表 commit 只是人工对照用的参考水位，会过期，不要照抄进 `dep_graph.blade`：

| 依赖                           | 分支 + 参考 commit（非权威，仅供对照）                               | 说明                                                                                       |
| ------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `data/archon`                  | `master` @ `cb0eb3388830767afd6a8d0063d647ad93507d14`                | 提供 `archon::diff::use_trustpress_external_storage` 与 response dump；版本需 ≥ `1.114.18` |
| `data-arch/archon-gen`         | `master` @ `f115c591e079b9ff2792222bf0b8a9c5347a1660`                | archon 的 thrift codegen 工具，必须与 archon 同代，否则生成代码与运行时不匹配              |
| `data-arch/fbthrift`           | `archon-v2018.08.20.00` @ `8cf3fa70c375d29eb8ae0f6f24244602c74716ea` | **固定分支**，不要取 master                                                                |
| `data-arch/folly`              | `archon-v2022.11.14.00` @ `dc0f20685273225039d7ef112c3597e6f06d3f11` | **固定分支**，不要取 master                                                                |
| `data-arch/traffic_sinker_lib` | `master` @ `b6d1a98c18341ef973b0e96d4126038006fe50b3`                | 新 sinker，提供 `traffic_sinker::MultiSinker`                                              |

三条硬性约束：

- **`data/trustpress_databus_lib` 必须删除**。它是旧 sinker，只实现 databus 落库，会忽略 `SinkContext` 里的 `sink_type` / `pair_id` / `task_id`，链式有序录制（`recording_mode=ORDERLY`，走 `sink_type=2`）在它上面落不下来。新老 sinker 同时留在依赖里还会引入重复符号风险。
- **接 `traffic_sinker::MultiSinker` 时必须有 `bytedoc/mongo-cxx-driver`**。`traffic_sinker_lib` 的 BUILD 直接依赖 `bytedoc/mongo-cxx-driver:bsoncxx,mongocxx`，`sink_type=2` 还会用它写 Bytedoc 元信息；业务仓库 `dep_graph.blade` 里没有这一项时，要主动补。很多接入 MR 没有新增它，是因为仓库原本已经有（如 `data/tiktok_ecom_video_sort!4709`）；不是因为它不需要。只有仍用自定义 Databus-only sinker、完全不接 `MultiSinker` 时才可以不引入。
- **bpt 供给不等于缺依赖**。若仓库用 `bpt/folly` / `bpt/fbthrift` 供给底层库，脚本只标 `alt` 让人确认兼容性，不自动补 `data-arch/folly` / `data-arch/fbthrift`，避免两套库同时进依赖图。

> **每次运用本技能都要重新拉依赖的最新值**：脚本默认对每个依赖跑一次 `git ls-remote` 取分支 HEAD，上表 commit 只在显式 `--offline` 且该依赖在 `dep_graph.blade` 中缺失时用于兜底补齐。`ref` 是契约的一部分（`fbthrift` / `folly` 固定在 `archon-v*` 分支），不要改成 master。

> `folly` / `fbthrift` 还有另一条供给路径：部分业务仓库用 bpt 包（`bpt/folly` = `cpp3rdlib/folly#v2018.08.20.00#...#bpt`）而不是 `data-arch/*` 的 git 条目。脚本会把这种情况标成 `alt` 并指出实际供给方，**不要再补一个 `data-arch/folly` 条目**——两份 folly / fbthrift 同时进依赖图会冲突。这类仓库要不要迁到 archon 兼容分支，属于人工决策。

## 自动判断仓库状态

后续批量替换时，用户只给仓库名即可，先跑体检脚本，再按 `onboarding_status` 分流，不要让用户自己判断“已接入 / 旧 sinker / 从未接入”：

```bash
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo> --verify --format md
```

| `onboarding_status`        | 判定条件                                                                                                            | 自动处理                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `not_applicable`           | `dep_layout=unsupported`（既无 `dep_graph.blade` 也无 `BUILD`）                                                      | 不处理，软退出并说明「本仓不是 C++ 服务仓，Archon 录制不适用」                   |
| `not_onboarded`            | 没有 `data/archon`、没有 `traffic_sinker_lib`、也没有旧 `trustpress_databus_lib` / 旧代码引用                       | 完整接入：补依赖、BUILD、`MultiSinker`、启动开关、conf 参数                      |
| `legacy_sinker_upgrade`    | `dep_graph.blade`、BUILD 或代码里仍有 `trustpress_databus_lib` / `trustpress_databus::DatabusSinker`                | 迁移旧 sinker：删旧依赖、换 BUILD、改注入点、补 `mongo-cxx-driver`、补开关和参数 |
| `shared_framework_managed` | `dep_layout=build_only` + 本仓没有 `int main` / 自有 handler + BUILD 依赖了共享框架 target                           | 只出体检与两栏改动清单（业务仓 / 框架仓），不自动 apply                          |
| `partial_new_sinker`       | 已有 `traffic_sinker_lib`，但缺 `mongo-cxx-driver` / BUILD / `MultiSinker` / `ARCHON_ENABLE_TRUSTPRESS` / conf 参数 | 补齐缺项，不重复加已有依赖                                                       |
| `dependency_update`        | 新 sinker 已接，但依赖落后于远端 HEAD 或缺必需项                                                                    | 只升级/补依赖，并生成 CR code diff 链接                                          |
| `ready_with_alt_review`    | folly / fbthrift 由 `bpt/*` 等替代供给                                                                              | 不自动补 git 条目，要求人工确认兼容性                                            |
| `ready`                    | 依赖、BUILD、注入点、开关、conf 都齐                                                                                | 不改代码，只输出核对结论                                                         |

判断优先级固定为：**不适用 > 旧 sinker 残留 > 共享框架承载 > 新 sinker 半接入 > 依赖更新 > bpt 替代供给 > ready**。例如一个仓库既有 `traffic_sinker_lib` 又漏了启动开关，应归为 `partial_new_sinker`，不要只因为依赖达标就判 ready。

批量处理来自仓库盘点文档（如 [海外 TikDiff Predict 服务盘点](https://bytedance.larkoffice.com/wiki/OT6Jw8qpQidbEdk7h78co0vjnLh)）时，先按 Codebase repo 去重；同一 PSM 多区域共用仓库只提一个 MR，tiktok predict 系 ROW / US 分叉仓库需要分别处理。

## 工作流

### Step 1 — 体检：判断仓库处于哪个状态

```bash
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo>
```

脚本读业务仓库的 `dep_graph.blade`，默认联网解析每个依赖的分支 HEAD 作为目标值，并输出 `onboarding_status`。同时检查 BUILD 接线、sinker 注入点、启动开关、conf 参数，输出依赖级结论：

> Step 2 ~ Step 3 只适用于 `dep_layout=dep_graph`。脚本输出的 `dep_layout` 是 `build_only` 时跳到「BUILD-only 仓」一节，是 `unsupported` 时直接结束（`not_applicable`）。

| 结论            | 含义                                     | 下一步                           |
| --------------- | ---------------------------------------- | -------------------------------- |
| `missing`       | `dep_graph.blade` 里没有这个依赖         | 走「新增接入」，Step 2 起        |
| `alt`           | 主 key 缺失，但由 `bpt/*` 等替代条目供给 | 人工确认版本是否兼容，脚本不改写 |
| `stale`         | 落后于远端分支 HEAD                      | 直接升到 HEAD                    |
| `ok(latest)`    | 等于远端分支 HEAD                        | 无需改动                         |
| `ok(ref?)`      | 远端 HEAD 没取到，但等于内置参考 commit  | 结论未核实，见下方警告           |
| `unknown(ref?)` | 远端 HEAD 没取到，且与参考 commit 不同   | 结论未核实，见下方警告           |

同时会给出 `legacy_sinker`（是否还挂着旧 sinker）、`build_wired`（BUILD 里有没有 `traffic_sinker` 目标）、`sinker_injected`（代码里有没有注入 `MultiSinker`）、`sinker_init_order`（注册是否早于 Archon / 全局 / 父类资源初始化）、`switch_wired`（每个候选启动入口是否在同一脚本内把 `ARCHON_ENABLE_TRUSTPRESS` 透传给 `-archon_enable_trustpress`）、`switch_default_off`（每条透传链路是否都来自 `${ARCHON_ENABLE_TRUSTPRESS:-false}` 这种默认关闭形态）、`switch_candidate_scripts` / `switch_unwired_scripts` / `switch_unsafe_default_scripts`（逐文件证据）、`conf_wired`（4 个录制参数是否齐全）。任一未就绪都说明接入没做完，哪怕依赖版本都达标。

`switch_wired` 不是仓库级字符串并集：checker 会逐启动脚本追踪 `ARCHON_ENABLE_TRUSTPRESS -> shell 变量（可经过 common_flags）-> exec flag`，任何一个候选入口断链都会为 `false`，并在 `switch_unwired_scripts` 中列出文件。`switch_default_off=false` 时再看 `switch_unsafe_default_scripts`，逐个把链路改成默认 `false`，否则实例一上线就在录制。

### Step 2 — 确认目标值来源

Step 1 已经联网解析过每个依赖的分支 HEAD（远端地址从业务仓库 `origin` 推导，无需手填 host），`stale` 就是"落后于 HEAD"，不需要再人工比 SHA 新旧。两种例外必须处理：

- 出现 `ok(ref?)` / `unknown(ref?)`：说明 `git ls-remote` 没跑通（无网络、无权限，或上游改了分支名），脚本退回内置参考 commit 给结论。这个结论**可以用**，但必须当成「未核实」处理：
  - 脚本不会自动改写这些条目，避免把比参考值更新的依赖降级回去；
  - 脚本会输出一段 🔴 警告块，**必须原样粘进 MR 描述**（见 Step 9），让业务方自己判断要不要拉到最新；
  - 参考 commit 由技能维护者手工更新，**存在忘记更新而过期的可能**，所以它既不能证明「已是最新」，也不能证明「一定落后」；
  - 分支被上游改名时要同步更新脚本 `REQUIRED_DEPS` 里的 `ref`，否则会长期停在这个状态。
- 只想离线出一份对照表：加 `--offline`，行为同上（按参考水位判定 + 警告），仅缺失项会用参考 commit 补齐。

若要判断"当前 commit 是否已包含某个必需改动"（例如 review 别人的 MR），用 Codebase 确认那个改动的 commit 是否在当前 SHA 的祖先链里 —— 只比日期在有分叉的分支上会误判。

### Step 3 — 改 `dep_graph.blade`

```bash
# 先看 diff 不落盘
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo> --dry-run

# 确认无误后写入（目标值 = 本次解析到的远端 HEAD）
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo> --apply
```

`--apply` 只改依赖图：补齐 `missing` 条目、把 `stale` 条目 `info` 行改写成本次解析到的 HEAD、删除 `data/trustpress_databus_lib` 整个条目。代码接线（BUILD、注入点、启动开关、conf 参数）由 Agent 按后续步骤改，脚本只负责指出缺项，避免盲目 patch 不同仓库的启动脚本。写入是逐行文本替换，保留原文件缩进与逗号风格，不会把整个 JSON 重新序列化打乱 diff；新条目按字典序插入，写完会做一次 JSON 解析自检。重复执行幂等。

**脚本永不反向降级**：目标值只可能是本次解析到的远端 HEAD，参考 commit 不会被写进已存在的条目；`ok(ref?)` / `unknown(ref?)` 项不参与改写，避免拿不到最新值时把依赖改回一个过期 SHA。

代价是升级面会变大：把 archon / archon-gen 拉到 HEAD 后必须重跑一次全量编译（Step 6），不能沿用旧的编译结论。

### Step 4 — 改 BUILD 接线

`dep_graph.blade` 只声明版本，真正参与链接的是 BUILD 里的依赖目标。把旧 sinker 目标换成新的：

```
# 删除
"data/trustpress_databus_lib:master@//data/trustpress_databus_lib:trustpress_databus",
# 新增
"data-arch/traffic_sinker_lib:master@//data-arch/traffic_sinker_lib:traffic_sinker",
```

**注意不止一处**：除了顶层 BUILD 的公共依赖列表，凡是独立链接同一批依赖的子目标（工具、benchmark、单测二进制等）都要同步，漏一个就会在该目标上链接失败。用 `grep -rn "trustpress_databus\|traffic_sinker" --include=BUILD .` 收口。

### Step 5 — 注入 sinker

注入点的锚是 `archon::diff::use_trustpress_external_storage(...)`，它在不同仓库里的位置不同（可能在 `main.cpp`，也可能在某个 resource manager / 全局上下文初始化里），用 grep 定位而不是猜路径：

```bash
grep -rn "use_trustpress_external_storage" --include="*.cpp" --include="*.h" .
```

替换 include 与实例类型：

```cpp
// - #include <trustpress_databus_lib/databus_sinker.h>
#include <traffic_sinker_lib/multi_sinker.h>

// MultiSinker 按 TrustPress 下发的 sink_type 分流：1 -> Databus，2 -> Bytedoc + TOS。
archon::diff::use_trustpress_external_storage(std::make_shared<traffic_sinker::MultiSinker>());
```

**注册顺序是硬约束**：上面这行必须发生在 `archon::common::ArchonContext::init(...)`、`rpc::GlobalContext::init(...)` 或封装它们的父类 / 框架资源 `init()` **之前**。Archon 会在初始化过程中创建 TrustPress dump handler 并立即读取全局 sinker；若先初始化、后注册，会出现 `enable trustpress but not set sinker` / `init trustpress dump handler failed`，而后续注册不会重试 handler 初始化。推荐结构：

```cpp
archon::diff::use_trustpress_external_storage(
    std::make_shared<traffic_sinker::MultiSinker>());
RETURN_IF_ERROR(BaseResourceManager::init());  // 或 ArchonContext::init / GlobalContext::init
```

体检脚本会把顺序输出为 `before_init`、`after_init`、`init_not_found` 或 `not_injected`。只有 `before_init` 算就绪；`after_init` 必须移动调用，`init_not_found` 需要沿调用链人工确认，不能仅凭 grep 到 `MultiSinker` 判定 ready。

`MultiSinker` 会 eager 创建两个子 sinker；即使某条落库通道当前没配好，也不应该导致启动崩溃或阻塞——验证时要确认这一点。

### Step 6 — 改启动开关与录制参数

依赖和注入点只解决“能编/能落库”，真正是否录制由启动参数控制。参数含义、默认值和调优方法以 [TrustPress 录制参数介绍](https://bytedance.larkoffice.com/wiki/IokbwE3AJiIjVVk5cnDcYBBYnhh#F3B3dG3jEodc19xcIWZldraUgdb) 为准。所有接入 MR 都要检查两类代码改动：

```bash
# run.sh / real_run / real_run_tce 等启动脚本：默认关闭，只允许通过环境变量打开
archon_enable_trustpress=${ARCHON_ENABLE_TRUSTPRESS:-false}
exec ./binary ... -archon_enable_trustpress=${archon_enable_trustpress}

# server.conf：录制队列与策略参数；400 MB 按 400 × 1024 × 1024 字节配置
archon.diff.trustpress_maximum_strategy 10
archon.diff.trustpress_maximum_queue_bytes 419430400
archon.diff.trustpress_maximum_dump_in_minute 1200
archon.diff.trustpress_update_interval_in_ms 10000
```

`trustpress_maximum_dump_in_minute` 默认写 1200，可按业务 QPS 上调（如 ecom sort 4800），但必须显式写在 conf 里；线上默认仍是 `ARCHON_ENABLE_TRUSTPRESS=false`，只在需要录制的少量实例上打开。

### Step 7 — 编译与符号验证

```bash
./build.sh    # 或业务仓库自己的全量编译入口
```

编译通过后，在产物上确认符号替换干净、archon 版本达标：

```bash
nm -C <binary> | grep -c "traffic_sinker::MultiSinker"      # 期望 > 0
nm -C <binary> | grep -c "trustpress_databus::"             # 期望 0，非 0 说明旧 sinker 还在被引用
strings <binary> | grep -m1 -o "archon [0-9.]*"             # 期望版本 ≥ 1.114.18
```

### Step 8 — 本地起服务验证

带上 TrustPress 开关起本地服务（flag 名以业务仓库为准，通常是 `-archon_enable_trustpress=true`），确认：

- TrustPress dump handler 正常 init / start；
- `MultiSinker` 构造完成，没有因为缺配置而崩溃或卡住启动；
- endpoint 发现与心跳链路正常。

本地验证时先显式加 `-archon_enable_trustpress=true`，再确认默认路径仍是关闭的。稀疏录制场景 `trustpress_maximum_queue_bytes` 要大于 QPS×60。Archon 版本下限：BUILD 挂 `traffic_sinker` 需 ≥ 1.113.4，`dep_graph.blade` 这套基线需 ≥ 1.114.18。

### Step 9 — 提 MR

MR 描述里必须带依赖核对表，让 reviewer 不用翻 `dep_graph.blade` 就能判断是否达标：

```bash
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo> --format md
```

输出的 markdown 表可直接粘贴，末尾还会自动生成一段「本次依赖变更（供 CR）」表：**升级项给 `compare/<old>...<new>` 的 code diff 链接，首次引入 / 移除的依赖给仓库地址**，reviewer 点开就能看这次到底把依赖挪了多少，不用自己拼链接。MR 模式（`--mr`）下变更是拿 MR base 侧的 `dep_graph.blade` 对比出来的，本地模式下是「当前值 → 计划写入值」。

> 🔴 **只要输出里出现 `ok(ref?)` / `unknown(ref?)`，就必须把脚本生成的那段 🔴 警告块一起粘进 MR 描述**，不能只贴表格。这些行的结论来自技能内置的参考 commit，而参考 commit 可能已经过期（维护者未必及时更新），reviewer 与业务方需要据此自行确认是否要把依赖拉到各分支最新 HEAD。省掉这段警告，等于把「未核实」包装成「已达标」。

除此之外在描述里写清：升级了哪几个依赖及原因、是否新加 `bytedoc/mongo-cxx-driver` 及原因、注入点文件、启动开关与 conf 参数改了哪些、编译与本地验证结论、以及**后续不在本 MR 范围的线上动作**：`ARCHON_ENABLE_TRUSTPRESS=true` 只在实例极少的集群开（1 个即可，建议 < 50）、在 `holmes_rec_conf` 的 `${psm}.yaml` 里配流量源与 `traffic_methods`、TOS bucket 与 Bytedoc 库开通、把占位 method 换成真实 method。这些步骤和审批（MR 一般要平台值班人过一遍，部分能力还要一键 oncall 申请白名单）看[接入流程](https://bytedance.larkoffice.com/wiki/IokbwE3AJiIjVVk5cnDcYBBYnhh#OvaEdXZnFo2xIoxThUElgyS3gpf)。

## BUILD-only 仓（无 `dep_graph.blade`）

不少 C++ predict / 服务仓只有 `BUILD`，依赖写在 `global_settler(prefer_deps=[...])` 的简写（`<repo>:<branch>`）或完整 target（`<repo>:<branch>@//<path>:<target>`）里。**BUILD 里没有 SHA pin**，所以水位判定（`stale` / `ok(latest)`）和 `--verify` 的 commit 祖先比较都不适用，脚本自动降级为「存在性 + 分支名」体检：

| BUILD-only 结论    | 含义                                                                                                              | 处理                                            |
| ------------------ | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| `present`          | BUILD 里直接声明了该依赖                                                                                          | 只需核对分支名                                  |
| `transitive`       | 本仓没有该条目，但由上游 target 传递带入（`libtimetomb_archon`、`mage_predict:libpredict_common`、`cppservice_*archon` 之类，常配 `defs=['ARCHON','USE_NEW_FOLLY']`） | 视为已供给，不要再补一条同名依赖                |
| `alt`              | 由 bpt / `cpp3rdlib/*` 包供给 folly / fbthrift                                                                    | 人工确认版本兼容性，别硬塞 git 条目             |
| `branch_mismatch`  | 固定分支约束不满足（`fbthrift` 必须 `archon-v2018.08.20.00`、`folly` 必须 `archon-v2022.11.14.00`），简写里也照查 | 必须改回固定分支                                |
| `absent`           | 完全没有供给（最常见是 `traffic_sinker_lib`）                                                                     | 按改动清单补 BUILD target                       |
| `absent(optional)` | `archon-gen` / `mongo-cxx-driver` 未声明                                                                          | BUILD-only 仓通常不需要单独补，见下方说明       |

`data-arch/traffic_sinker_lib` 的 BUILD **自带** `bytedoc/mongo-cxx-driver:v1.0.0`，codegen 也由上游 idl 仓提供，所以这两项在 BUILD-only 形态下按 optional 处理，`absent(optional)` 不算待办。

脚本会把仓库根 `BUILD` 与所有子目录 `BUILD` 一起解析（依赖声明常常拆在子目录），所以 `present` / `transitive` 的判定不局限于根 BUILD。

BUILD-only 形态下的行为差异，务必记住三条：

- **禁用依赖改写**：`--apply` / `--dry-run` 直接以 `exit 3` 报错。BUILD 是构建脚本而不是 JSON 依赖图，自动改写会误改语义，只输出人工步骤清单。
- **`--verify` 不适用**：仍会输出体检结论，但额外打一条 warning 说明没有 SHA pin、下限校验做不了，不要拿它当准入门禁。
- **接线搜索范围更宽**：启动脚本按 `apps/<app>/run/real_run`、`run/*`、`*.sh` 匹配，录制参数按 `conf/<cluster>/server.conf`、`conf/app.conf` 等 `*.conf` 匹配，所以 `switch_wired` / `conf_wired` 在这类仓库同样有效。

**dmon 老录制路线要单独识别**：命中 `HOLMES_REC_USE_TPRESS_DMON`、`tpress-dmon-bootstrap.sh`、`HOLMES_REC_SERVER_URL` 任一信号时，脚本会给一条 ⚠️ 提示。这是老 dmon 录制路线，与 `archon::diff` 新路线不是同一套东西（老路线只改启动脚本 + log target，代码里没有 `archon::diff`），**不能当成"已接入"**，要先和业务方确认迁移策略（并行保留还是直接替换）。

## 共享框架承载（Archon 初始化不在业务仓）

有一类业务仓（典型是共用同一套 predict 框架的多个仓库）本身**没有 `int main`、也没有自己的 handler**：`main` 由各自的 `*_predict_common` 仓提供（`timetomb::Bootstrap<Handler, idl::...::archon::XxxServer>`），真正的 Archon server 初始化在框架库 `data/libtimetomb` 的 `include/timetomb/boostrap.h`（`archon::common::ArchonContext::init(conf)` 与 `ServerFactory::ArchonServerPtr server = CreateServer::create_server(...)` → `server->serve()`）；上层的共享框架库仓（脚本 `SHARED_FRAMEWORK_TARGETS` 里列的那几个 predict 框架仓）本身也只是库，同样没有 `dep_graph.blade`、没有 `int main`，Archon 依赖声明反而落在各业务仓自己的 BUILD 里（因此没有 SHA pin）。

脚本命中「BUILD-only + 本仓找不到 `int main` / `use_trustpress_external_storage` + BUILD 依赖了 `SHARED_FRAMEWORK_TARGETS` 中的共享框架 target」时，输出 `onboarding_status=shared_framework_managed`，并把改动拆成两栏：

| 栏位                          | 内容                                                                                                                                                                                      |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **可落业务仓**                | BUILD 加 `traffic_sinker` target；`conf/<cluster>/server.conf` 或 `conf/app.conf` 补 4 个 `archon.diff.trustpress_*` 参数；业务仓自带的启动脚本加 `ARCHON_ENABLE_TRUSTPRESS:-false` 默认关闭开关并透传 flag |
| **必须落框架 / common 仓** | `use_trustpress_external_storage(std::make_shared<traffic_sinker::MultiSinker>())` 注入，建议落点 `*_predict_common/service/main.cpp` 的 `before_setup_environment`，并确保早于父类 / Archon 初始化 |

注入本身是给单例赋值，但调用时机不能任意：必须在父类 / Archon 初始化创建 TrustPress handler 之前完成。这类业务仓没有自己的 handler / main，唯一干净的落点就在 common 仓。因此：

- 该改动**必须由框架 owner 确认**，一处改动会影响所有下游服务，要先评估推全策略（默认关闭开关 + 灰度仓库列表）。
- 这条路线**暂无先例 MR**（框架仓、common 仓、框架库仓的历史里都没有 `traffic_sinker` / `trustpress` 相关改动），首个仓库需要人工评审 + 框架 owner 确认后再推全。
- 技能对该形态**只做体检与改动清单输出，不做自动 apply**；`shared_framework_managed` 不是"卡死"的终态，输出里给的就是可执行清单，按两栏分别推动即可。

## 校验模式：只做准入判断，不改代码

给定仓库或给定 MR，校验这套依赖是否**不低于技能内置参考 commit**（下限校验，按 commit 祖先关系判定，不是比字符串也不是比日期）：

```bash
# 校验本地仓库
python3 scripts/check_archon_traffic_deps.py --repo /path/to/<biz_repo> --verify

# 直接校验一个 MR，不需要本地 clone 业务仓库
python3 scripts/check_archon_traffic_deps.py --mr https://code.<host>/<repo>/merge_requests/<iid> --verify --format md
```

`--mr` 走 Codebase 的 MR 只读 ref（`refs/merge-requests/<iid>/tmp-squash`，回退 `tmp-merge` / `head`）读取该 MR 上的 `dep_graph.blade`，并用 `mr^` 拿 base 侧内容算出本次真正动了哪些依赖。祖先判定用 `git clone --filter=tree:0` 只拉 commit 图，秒级完成，不落地大仓库。

| 下限校验结论    | 含义                                              | 处理               |
| --------------- | ------------------------------------------------- | ------------------ |
| `pass(>=ref)`   | 参考 commit 是当前 commit 的祖先（含相等）        | 通过               |
| `fail(<ref)`    | 当前 commit 是参考 commit 的祖先，确实落后        | 必须升级后才能接入 |
| `fail(missing)` | 依赖压根不在依赖图里，也没有替代供给              | 补齐条目           |
| `diverged`      | 两个 commit 互不为祖先（分支被 rebase / 改名）    | 人工确认           |
| `unknown(alt)`  | 该依赖由 `bpt/*` 等替代路径供给，跨供给方式不可比 | 人工确认版本兼容性 |
| `unknown`       | commit 对象拉不到（无网络 / 无权限）              | 修连通性后重跑     |

退出码：`2` = 下限校验未通过（有 `fail(*)`），`1` = 还有其它待办（依赖不是最新、BUILD / 注入点没接完、结论未核实），`0` = 干净或不适用（`not_applicable`），`3` = 用法或环境错误（`--repo` 指错、BUILD-only 仓用了 `--apply`、MR 链接非法、文件读不出来）。CI 或 RM 卡点可以直接看退出码；`3` 说明脚本没跑成，不要当成"依赖不达标"。脚本不会抛 traceback，异常统一收敛成一行 `error: ...`。

`--mr` 是只读入口：它不检查 BUILD 接线与 sinker 注入点（输出里标成"未检查（MR 模式）"），这两项要在本地仓库上用 `--repo` 跑。

## 常见坑

| 现象                                                   | 根因                                                                 | 处理                                                                                                   |
| ------------------------------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| archon 升了但生成代码报错 / 行为对不上                 | 只升 `data/archon` 忘了 `data-arch/archon-gen`，codegen 与运行时错代 | 两者一起升；archon-gen 落后是最高频的漏项                                                              |
| 把 `fbthrift` / `folly` 升到 master 后编译大面积失败   | 这两个依赖走 `archon-v*` 固定分支，master 与 archon 不兼容           | 只在原分支内升 commit，分支名不要改                                                                    |
| 链接期报 `traffic_sinker::MultiSinker` 未定义          | 只改了 `dep_graph.blade`，BUILD 里没换目标；或漏了子目标             | 按 Step 4 全仓 grep `--include=BUILD`                                                                  |
| 链接期报 Bytedoc / mongo 相关缺符号                    | 缺 `bytedoc/mongo-cxx-driver`                                        | 在 `dep_graph.blade` 补该条目                                                                          |
| 编译通过但录制落不下来、`sink_type=2` 数据缺失         | 仍在用旧 `trustpress_databus_lib`，或注入点没换成 `MultiSinker`      | 检查 `sinker_injected`，并确认产物里 `trustpress_databus::` 符号为 0                                   |
| 文档里的参考 commit 和实际写入的不一致                 | 参考 commit 只是对照水位，目标值取执行时的远端 HEAD                  | 以脚本输出的 `remote_head` 为准，不要把参考 commit 照抄进 `dep_graph.blade`                            |
| 结论全是 `ok(ref?)` / `unknown(ref?)`                  | 拿不到远端 HEAD（无网络 / 无权限 / ref 被改名）                      | 先修连通性重跑；确实只能离线出结论时，把 🔴 警告块一并贴进 MR 描述                                     |
| `data-arch/folly` 报 `fail(missing)`，但仓库确实能编过 | 该仓库用 `bpt/folly` 供给 folly，主 key 自然缺失                     | 升级脚本内置清单里的 `alternatives` 后会标成 `alt`；确认 bpt 版本是否满足 archon 要求，别硬塞 git 条目 |
| reviewer 看不出依赖到底动了多少                        | MR 描述只贴了核对表，没贴 code diff 链接                             | 把脚本输出的「本次依赖变更（供 CR）」表一起贴上                                                        |
| 有的接入 MR 没有新增 `mongo-cxx-driver`                | 仓库原本已有该依赖，或没接 `MultiSinker`                             | 接 `traffic_sinker::MultiSinker` 且 `dep_graph.blade` 不含该条目时必须补；已有则不重复加               |
| 依赖/注入都改了，线上仍不录制                          | 启动脚本没透传 `-archon_enable_trustpress`，或 conf 缺录制参数       | 按 Step 6 补 `ARCHON_ENABLE_TRUSTPRESS:-false` 和 4 个 `archon.diff.trustpress_*` 参数                 |
| 脚本以 `exit 3` + 一行 `error: ...` 结束             | `--repo` 指到不存在的路径、MR 链接非法，或在 BUILD-only 仓上用了 `--apply` / `--dry-run` | `3` 一律是用法/环境问题，不是「依赖不达标」；修正参数，BUILD-only 仓按人工步骤清单改                      |
| BUILD-only 仓看不到 `stale` / `ok(latest)`             | BUILD 没有 SHA pin，水位判定不适用                                   | 用「存在性 + 分支名」结论；要水位就得先把依赖迁进 `dep_graph.blade`                                    |
| 一个启动脚本已接线，但 TCE 入口仍不录制              | 旧检查把不同脚本里的 env / flag 做了仓库级并集                         | 看 `switch_unwired_scripts`，逐入口补齐 env → shell 变量 → exec flag 闭环                               |
| `switch_wired=true` 但服务一启动就在录制             | 某条透传链路默认值不是 `false`                                        | 看 `switch_unsafe_default_scripts`；改成 `${ARCHON_ENABLE_TRUSTPRESS:-false}`                            |
| 只有 `HOLMES_REC_*` / `tpress-dmon-bootstrap.sh`       | 这是 dmon 老录制路线，不是 `archon::diff` 新路线                     | 按 BUILD-only 一节先确认迁移策略，不要当成已接入                                                       |

## 脚本

- [scripts/check_archon_traffic_deps.py](scripts/check_archon_traffic_deps.py)：依赖核对与自动改写。**运行第一步先探测依赖图形态**（`dep_graph` / `build_only` / `unsupported`），`dep_graph` 形态下**默认每次运行都用 `git ls-remote` 解析各依赖分支 HEAD 作为目标值**，无需额外传参。可选 `--verify`（下限校验，BUILD-only 形态不适用）、`--mr <url>`（直接校验 MR，只读）、`--offline`（跳过远端解析，退回参考水位并附 🔴 警告块）、`--dry-run` / `--apply`（仅 `dep_graph` 形态支持）、`--format text|md|json`、`--deps <file.json>`（覆盖内置依赖清单，可临时增删依赖、改 ref 或补 `alternatives` / `build_alternatives` / `build_transitive_providers` / `build_optional` / `build_pinned_branch`）、`--git-base` / `--web-base`（覆盖推导出的 git / web 地址前缀）。远端地址从业务仓库 `origin` 推导，不硬编码任何 host；`--format json` 里 `needs_action` / `gate_failures` / `gate_unclear` / `alt_supplied` / `changes`（含 code diff 链接）/ `needs_manual_review` / `ref_based_conclusion` / `ref_fallback_warning` / `switch_default_off` 以及每项的 `remote_head` 适合上层 Agent 直接消费（`ref_fallback_warning` 非空即说明本次结论未经远端核实，必须透传到 MR 描述）。BUILD-only 形态的 json 额外给 `dep_layout` / `apply_supported` / `shared_framework` / `framework_targets` / `has_own_entrypoint` / `dmon_legacy_signals` / `build_only_todo` / `manual_steps`。
