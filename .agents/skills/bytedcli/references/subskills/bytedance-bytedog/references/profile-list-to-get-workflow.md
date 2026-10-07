# ByteDog Profile List 到 Get 标准流程

本文用于 Agent 执行“从历史记录中找到 ByteDog profiling 任务，再拿结果文件”的标准流程。需要完整参数、输出字段或边界条件时，同时阅读 `bytedog-command-reference.md`。

## 适用场景

用户已经创建过 profiling 任务，但没有提供 detail URL，或希望按目标信息搜索历史记录时使用本流程。

历史命令以 `bytedog-command-reference.md` 为准。根据用户要找的 profile 类型选择对应的 `bytedcli bytedog profile ... list` 叶子命令；Java heap、allocation、GC、thread、lock 的历史记录也使用对应 Java list 命令查询。

## 标准步骤

1. 选择站点与历史类型。

   `--site` 是全局参数，写在 `bytedcli` 后、`bytedog` 前。历史类型要与用户要找的 profile 类型一致。

2. 选择过滤条件。

   `python-thread-dump`、`python-memory`、`python-gc` 的 list 可按 `--ip`、`--creator`、`--status` 筛选，也可省略筛选条件。普通历史命令至少提供一个过滤条件：`--ip`、`--pod`、`--psm`。`profile sprofile list` 只接受 `--ip`，不接受 `--pod` 或 `--psm`；`profile je-continuous list` 无需目标过滤，也可选传 `--ip` 或 `--pod`。

   `profile <type> list` 不做 IP 归一化，按传入文本过滤历史记录；如果用户给的是 hostname 或不确定的机器标识，优先让用户确认实际 IP 或直接使用能匹配历史记录的文本。

   查可用结果文件或可交给 `profile get` 的 detail URL 时，默认加 `--status GOOD`。只有需要排查运行中或失败任务时，再改用 `--status RUNNING` / `--status BAD` 或省略状态过滤。

3. 查询历史记录。

   ```bash
   bytedcli bytedog profile oncpu list \
     --pod demo-pod \
     --psm demo.service \
     --status GOOD \
     --page-size 10
   ```

   `sprofile` 示例：

   ```bash
   bytedcli bytedog profile sprofile list \
     --ip example-host \
     --status GOOD \
     --page-size 10
   ```

   JSON 模式方便外层流程稳定读取 `detail_url`：

   ```bash
   bytedcli --json bytedog profile je-flamegraph list \
     --ip example-host \
     --status GOOD \
     --page-size 10

   bytedcli --json bytedog profile java-gc list \
     --pod demo-pod \
     --status GOOD \
     --page-size 10
   ```

4. 选择目标 detail URL。

   从列表结果中选择状态可用、时间最匹配、目标信息最匹配的记录，并记录 `detail_url`。如果列表结果太多，继续增加过滤条件或翻页；不要把当前页条数当作总数。

5. 用 detail URL 获取结果。

   ```bash
   bytedcli bytedog profile get \
     --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce' \
     --output-dir ./bytedog-output
   ```

   `profile get` 只在详情页任务状态为 `GOOD` 时获取结果。若为了排查而选择了 `INIT` / `RUNNING` 记录，不要把 `detail_url` 当作已就绪的结果；保留该 URL，等待任务完成后重试同一条 `profile get` 命令。若选择了 `BAD` 记录，保留命令输出的任务错误、hint 和 `detail_url`，不要继续解析结果文件。若任务状态为 `GOOD` 但详情页没有结果 URL，命令会成功返回 `status`、`result_urls` 和空 `files`，且不会生成 `data-format.md`；不要继续读取不存在的文件。Java heap dump `.hprof` 不会自动下载，命令会输出远端 TOS URL，需要手动下载后再用 HPROF 工具分析。

6. 批量获取多个历史结果。

   选择多条 `detail_url` 后，用英文逗号拼接：

   ```bash
   bytedcli bytedog profile get \
     --url 'https://example.bytedog/profiling/on-cpu-profiling/detail?id=1001&from=tce,https://example.bytedog/profiling/jemalloc-profiling/detail?id=1005&from=machine' \
     --output-dir ./bytedog-output
   ```

   获取完成且输出包含 `data-format.md` 时先读它，再解析 `.collapse`、`.json` 等结果文件。若输出包含远端文件 URL，先按提示手动下载，再用对应工具分析。若 `files` 为空，向用户说明详情页未返回可下载结果 URL，并保留选中的 `detail_url` 与 `result_urls`。

## Agent 输出要求

- 向用户汇报使用的过滤条件、选中的 detail URL、输出目录、任务 `status`、`result_urls`、结果文件路径，以及不会自动下载的远端文件 URL；只有输出里实际包含 `data-format.md` 时才汇报并读取它。
- 如果没有查到历史记录，说明实际使用的过滤条件并确认 site。普通历史命令可放宽 `--ip`、`--pod`、`--psm`；`sprofile list` 只调整 `--ip`；`je-continuous list` 只调整或移除 `--ip`、`--pod`。
- 如果查到多条候选记录，优先说明为什么选择目标记录；不能判断时列出候选 `detail_url` 和关键字段让用户选择。
