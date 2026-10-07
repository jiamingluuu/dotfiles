# Nario 案例：聚焦调试 PSM 场景

当用户提供已存储流量 PID 和目标模板/场景，并询问该特定场景能否命中流量时，使用本案例。

## 为什么需要这条路径

全流量打标回答“完整 Nario 打标流程会命中什么”；聚焦场景调试回答“使用所提供的模板、特征和规则上下文计算时，这一个场景能否命中该流量”。模板已禁用、用户希望避免扫描全部场景，或问题仅关注目标场景结果时，使用聚焦路径。

## 工作流

1. 从用户输入中解析 PSM、PID、模板 ID、场景 ID、可选的空间 ID 和环境。
2. 用户仅提供 PSM、PID、模板 ID 和场景 ID 时，优先使用从数据源构建的路径。CLI 会读取 FTF 流量详情、Nario 模板详情和 Nario 场景详情，然后为后端构建 `/openapi/psm_scene/debug` payload：

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging scene-debug execute \
  --psm example.psm \
  --pid sample-pid \
  --template-id 3000001 \
  --scene-id 2200001 \
  --build-from-sources
```

3. 如果用户需要在调用后端前检查生成的 payload，添加 `--dry-run --build-from-sources`。生成的 payload 包含 FTF 请求/响应、模板 `scene_meta`、特征列表、目标 `psm_scene` 和 `log_id`。
4. 如果缺少 FTF 历史流量且用户未指定 `--flow-type`，CLI 会回退到场景流量。仅当用户明确知道来源时才使用其他流量类型。
5. 仅当用户已有经过检查的自定义 payload，或自动构建的 payload 需要所有者修正时，使用 `--payload-file`：

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging scene-debug execute \
  --psm example.psm \
  --pid sample-pid \
  --template-id 3000001 \
  --scene-id 2200001 \
  --payload-file ./psm_scene_debug.json
```

## 结果汇总

向用户反馈以下内容：

| 项目     | 含义                                        |
| -------- | ------------------------------------------- |
| 目标     | PSM、PID、模板 ID、场景 ID。                |
| 输入来源 | 使用了哪个流量集合或 payload 来源。         |
| 匹配结果 | 根据后端调试输出，场景是否命中。            |
| 规则证据 | 导致命中或未命中的关键特征/规则行。         |
| 注意事项 | 任何缺失字段、模板禁用状态或 payload 假设。 |

如果 CLI 返回 `NARIO_DEBUG_PAYLOAD_INCOMPLETE`，不要将其表述为后端未命中。它表示聚焦调试请求尚未构建完成。
