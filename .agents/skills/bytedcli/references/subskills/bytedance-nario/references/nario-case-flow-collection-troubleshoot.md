# Nario 案例：无推荐或无采集流量排障

当用户反馈 Nario 模板或场景没有推荐场景、没有打标流量、没有采集流量，或覆盖率始终为零时，使用本案例。

## 首轮检查

1. 从用户输入或 Nario URL 中识别模板 ID、可选的场景 ID、空间 ID、PSM、method 和环境。
2. 读取模板详情和统计：

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template get --template-id 3000001
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template diagnosis get --template-id 3000001
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template statistics get --template-id 3000001 --with-flow-info
```

3. 读取模板下的场景，必要时包含规则详情：

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario scene list \
  --template-id 3000001 \
  --page 1 \
  --page-size 20
```

4. 如果模板配置有效但场景流量为零，按 PSM 和 method 检查临时/历史流量证据：

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario flow-temporary list \
  --psm example.psm \
  --method GetDemo \
  --page 1 \
  --page-size 10
```

## 决策树

| 分支                         | 检查内容                                      | 解释                                                |
| ---------------------------- | --------------------------------------------- | --------------------------------------------------- |
| 模板已禁用                   | `is_enable` 或等价详情字段                    | 已禁用模板可能不参与正常打标/推荐链路。             |
| 不在度量白名单               | `in_measure_whitelist` 或所有者确认的等价字段 | 覆盖率或推荐链路可能跳过该模板。                    |
| 没有场景                     | 场景列表为空                                  | 创建场景前，模板无法采集场景命中。                  |
| 存在场景但流量为零           | 统计中有场景数，但命中/流量数为零             | 继续检查流量采集和打标日志。                        |
| 没有临时流量                 | `flow-temporary list` 对 PSM+method 返回空    | 可能是接口没有录制流量、未接入 FTF，或未启用录制。  |
| 规则过窄                     | 场景规则检查的字段不存在或很少相等            | 使用聚焦的 `tagging scene-debug execute` 验证。     |
| 存在流量但打标日志中没有模板 | consumer 日志中没有出现模板 ID                | 可能是场景缓存/TOS 未刷新，或 consumer 未加载模板。 |

## 跨模块检查

必要时使用其他 bytedcli domain；Nario skill 可以调用它们作为辅助工具，无需局限在本模块内。

| 需求                       | 建议模块                              |
| -------------------------- | ------------------------------------- |
| 推荐失败的 consumer 日志   | `bytedcli log` / Argos skill。        |
| 缓存上传或流量计数指标     | `bytedcli apm grafana` 或指标 skill。 |
| 功能开关和白名单 key       | `bytedcli tcc`。                      |
| FTF 任务关联或任务流量证据 | `bytedcli ftf`。                      |
| TOS 场景缓存证据           | 可用且已授权时使用 `bytedcli tos`。   |

## 回答格式

按四部分汇总：

1. 基础配置：模板启用状态、白名单状态、PSM/method、场景数。
2. 流量证据：统计或日志中是否存在已采集/已打标流量。
3. 规则证据：最重要的场景规则行，以及代表性流量是否满足这些规则。
4. 后续操作：聚焦场景调试、验证缓存刷新，或在需要时申请权限/升级处理。

不要仅根据缺少日志得出“未命中”的结论。应区分没有已存储流量、没有推荐、模板未加载，以及聚焦场景规则未命中。
