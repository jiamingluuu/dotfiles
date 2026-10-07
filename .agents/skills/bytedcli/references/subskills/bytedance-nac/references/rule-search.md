# NSG 规则检索五态匹配

本 reference 是 `nac rule search` 的完整匹配契约。该命令调用 `POST /v2/rule/match_all`，查询编译前但已 normalize 的四种正式规则来源；灰度规则仍位于独立表中。它不改变 `nac rule conflict-check` 或 `nac admin rule search` 的语义。

五态中的 `precise` 只表示当前候选字段必须匹配已有规则的具体值并排除该字段为 `all` 的规则；它仍属于编译前、多结果的模糊规则检索，不等于指定 Agent 上的数据面精确匹配。要判断流量在数据面编译后规则中实际命中哪一条，使用 `nac admin rule search`。

## 查询规划与过滤下推

执行命令前，先从用户输入中提取全部可由 `nac rule search` 表达的条件，包括五元组五态、`rule_type`、所有权、来源、ID、名称、备注、动作、优先级和布尔元数据，并全部下推到同一次或拆分后的服务端查询。只有服务端确实没有对应表达能力的剩余条件，才允许在已经充分收窄的 JSON 结果上做本地过滤。

每次执行规则查询前，必须逐项自检：

- 是否可用 `empty`、`any`、`precise` 或 `all` 表达？
- 是否可先按 `rule_type`、所有权或来源收窄？

任一问题的答案为“可以”，就不得执行无过滤的全量查询。不得为了编写更熟悉的 `jq` 表达式而放弃服务端已有过滤能力。

## 五元组字段与独立匹配

候选五元组是源 Host、目的 Host、源端口、目的端口和协议。每个 Host 侧展开为 IP、Domain、数字 TCE PSM ID、PSM 四个独立字段。规则返回字段中的 PSM ID 是 `psm_id`；CLI 查询参数是 `--src-tce-psm` / `--dst-tce-psm`，不得发明 `--src-psm-id` / `--dst-psm-id`。

- Host 的 IP、Domain、TCE PSM ID、PSM 只在**已有规则预处理** `all/empty/concrete` 状态时互相影响。
- 进入匹配阶段后，所有候选字段都互相独立。一个字段的候选模式不会改变、推导或放宽任何其他字段。
- 每个字段独立产生匹配谓词，最终对全部字段谓词执行 AND；这里的 AND 是独立结果的组合，不是 Host 字段在匹配阶段互相影响。
- 每个字段可提供 1–10 个逗号分隔值。同一字段的全部候选值必须由同一条已有规则完整包含，不能把多条规则的匹配结果合并为一次命中。
- 引号包裹整个逗号列表，并决定 `value` 或 `precise` 模式；引号不是列表项的一部分。

## 候选五态

五态只适用于五元组字段。后端原始接口不传某个候选字段时，该字段表示 `empty`，不是 `any`。为了让用户在 CLI 中省略选项时得到“不限制”的通常行为，CLI 请求构造必须主动为省略的五元组字段发送 `*`。因此必须区分：

- **CLI 省略选项**：CLI 向后端发送 `*`，最终是 `any`。
- **后端请求缺少字段**：后端直接解释为 `empty`。
- **CLI 显式空字符串**：CLI 向后端发送空字符串，同样选择 `empty`。

CLI 还必须保留参数中的字面双引号和显式空字符串：

| 候选模式 | CLI 参数值 | 含义 |
|---|---|---|
| `any` | CLI 不传或 `*` | CLI 在线协议中发送 `*`；不限制，已有规则的三种状态都可匹配 |
| `all` | 字面量 `"*"` | 只匹配已有规则的 `all` 状态 |
| `empty` | 空字符串 | 只匹配已有规则的 `empty` 状态 |
| `value` | 普通值或普通逗号列表 | 匹配已有规则的 `all`，或能包含全部候选值的 `concrete` |
| `precise` | 字面量 `"value"` 或带引号列表 | 只匹配能包含全部候选值的 `concrete`，排除 `all` |

Shell 示例：

```bash
# any
bytedcli --json nac rule search --dst-domain '*'

# all：实际参数值包含双引号
bytedcli --json nac rule search --dst-domain '"*"'

# empty
bytedcli --json nac rule search --dst-domain ''

# value
bytedcli --json nac rule search --dst-domain example.com

# precise：实际参数值包含双引号
bytedcli --json nac rule search --dst-domain '"example.com"'
```

## 已有规则三态与 5×3 关系

已有规则经过预处理后，每个字段是 `all`、`empty` 或 `concrete`：

- 一个 Host 侧的 IP、Domain、TCE PSM ID、PSM 全部缺失时，四个字段都为 `all`。
- 一个 Host 侧至少有一个具体类型时，存在的类型为 `concrete`，缺失的同侧类型为 `empty`。因此候选规则的 `empty` 只匹配“已有规则该字段没有值，并且同侧至少一个其他 Host 字段有值”。
- 端口和协议缺失时为 `all`，存在时为 `concrete`；端口和协议没有 `empty` 状态，因此候选 `empty` 在这些字段上不会命中。

| 候选模式 | 已有 `all` | 已有 `empty` | 已有 `concrete` |
|---|---:|---:|---:|
| `any` | 匹配 | 匹配 | 匹配 |
| `all` | 匹配 | 不匹配 | 不匹配 |
| `empty` | 不匹配 | 匹配 | 不匹配 |
| `value` | 匹配 | 不匹配 | 包含全部候选值时匹配 |
| `precise` | 不匹配 | 不匹配 | 包含全部候选值时匹配 |

上述 Host 关联只负责产生已有规则各字段的状态。状态产生后，IP、Domain、TCE PSM ID、PSM 分别独立参与匹配，不在匹配阶段再次互相推导。

## 用户描述到独立字段条件

- “只查目的 Host 使用 IP，IP 具体值不限，目的 PSM、PSM ID、Domain 都没有配置”：目的 IP 使用 `any`，其余三个目的 Host 字段分别使用 `empty`。

  ```bash
  bytedcli --json nac rule search \
    --dst-ip '*' \
    --dst-psm '' \
    --dst-tce-psm '' \
    --dst-domain ''
  ```

- “只查没有配置目的 IP、但配置了其他目的 Host 字段的规则”：目的 IP 使用 `empty`，未被用户继续限制的其他目的 Host 字段使用 `any`。已有规则的 `dst_ip=empty` 已经表示目的 IP 没有值且至少一个其他目的 Host 字段有值。

  ```bash
  bytedcli --json nac rule search --dst-ip ''
  ```

不得因为一个字段使用 `any`、`empty` 或具体值，就在匹配阶段替其他字段推导候选模式。只有用户明确描述了其他字段的条件时才设置相应条件。

## 严格 Host 地址类型

用户按 Host 地址类型查询时，必须直接使用 `nac rule search` 的五态参数在服务端筛选，不能先执行无条件全量查询再用 `jq` 或其他本地逻辑判断字段。严格限定一侧为 IP、PSM、PSM ID 或 Domain 的通用模板是：

- 选中的 Host 字段传 `*`，即 `any`；命令中的 shell 单引号只负责保护参数，参数值本身不包含字面引号。
- 同侧其他三个 Host 字段全部传空字符串，即 `empty`。
- 已有 Host 为 `all` 时，同侧四个字段状态均为 `all`；三个 `empty` 条件会排除这种规则。选中字段的 `any` 随后只能与该字段的 `concrete` 状态共同满足全部 AND 条件，因此得到严格地址类型。

严格的 “IP 到 Domain”：

```bash
bytedcli --json nac rule search \
  --src-ip '*' \
  --src-psm '' \
  --src-tce-psm '' \
  --src-domain '' \
  --dst-ip '' \
  --dst-psm '' \
  --dst-tce-psm '' \
  --dst-domain '*'
```

严格的 “PSM 到 PSM”：

```bash
bytedcli --json nac rule search \
  --src-ip '' \
  --src-psm '*' \
  --src-tce-psm '' \
  --src-domain '' \
  --dst-ip '' \
  --dst-psm '*' \
  --dst-tce-psm '' \
  --dst-domain ''
```

严格的源 PSM ID：

```bash
bytedcli --json nac rule search \
  --src-ip '' \
  --src-psm '' \
  --src-tce-psm '*' \
  --src-domain ''
```

目的 PSM ID 使用同一模板，将选中字段写成 `--dst-tce-psm '*'`，并把 `--dst-ip`、`--dst-psm`、`--dst-domain` 设为 `empty`。

### 地址类型 OR

单次 `nac rule search` 会把所有字段条件按 AND 组合。“源是某类型或目的是某类型”无法用一次请求表达时，必须分别执行两次带严格 Host 类型条件的服务端查询：第一条只约束源侧，第二条只约束目的侧；未约束的一侧保持 `any`。最后合并两份 JSON，并以 `rule_type + id` 作为联合键去重。不得为实现 OR 改成一次无条件全量查询后本地筛选。

## 各字段的具体包含关系

- **IP**：每个 IP 列表项只接受单 IP 或 CIDR；整个字段可包含 1–10 个逗号分隔项。每个候选网络必须完全落在已有规则的一段 IP 区间内；不能用多段已有区间拼接覆盖，也不接受候选横杠 IP 范围。
- **Port**：候选接受单端口或 `start-end`。每个候选端口范围必须完整落在已有规则的一段范围内，仅有相交不算包含。
- **Domain / PSM**：以候选具体值匹配已有规则的模式，大小写敏感。`*`、`?` 只有出现在已有规则模式中才具有模式含义；候选普通值中的这些字符不是查询通配符。
- **TCE PSM ID**：只接受数字，比较前去掉前导零。
- **Protocol**：转换为小写并去重，候选协议集合必须是已有规则协议集合的子集。

空列表项、裸 `*` 与具体值混用、超过 10 个值、非法 IP/CIDR、非法端口、非数字 TCE PSM ID 和非法协议由后端返回 HTTP 400。Agent 必须保留服务端 `code/msg`，不能自行改写成解析错误。

## 已有规则预处理和结果

查询前，服务端在内存 SQLite 中计算 Host mask、端口/协议存在状态和 `match_valid`。已有规则包含非法 IP、端口、TCE PSM ID 或协议时，`match_valid=false`，从匹配结果中排除。服务端还会对已有规则协议做小写去重、去除 TCE PSM ID 前导零，并清理 Domain/PSM 两端空白。

SQL 在同一只读快照中完成最终匹配，一次查询返回完整规则行并按优先级数值升序排列；数值越小优先级越高。CLI 不重新排序、不截断 JSON，也不把被排除的无效规则补回结果。

## 元数据过滤保持旧契约

五态不得扩展到 `id`、`username`、`priority`、`action`、`comment`、`name`、`record`、`reversed`、`internal`、`rule_type`、`source`：

- `username`、`comment`、`name`、`source` 这些字符串元数据不传或 `*` 表示不限制，空字符串匹配空值。
- `record`、`reversed`、`internal` 不传表示不限制，`true`/`false` 表示精确过滤。
- `--rule-type` 可省略；省略表示查询所有有权读取的 NSG 规则类型。显式传入时必须是非空的具体规则类型，空字符串非法。
- `--action` 接受 `*` 或支持的动作语义值，空字符串非法。
