# VNet Dashboards

vnet 平台在 `/api/grafana/search` 维护了一份 Grafana 大盘索引（200+ 条），按 `product`、`component`、`instance_type`、`type` 分类，每条带 `custom_variables` 描述如何把资源 ID 注入 dashboard URL 变量。

`bytedcli vnet dashboards` 命令把这份索引以 CLI 形式暴露出来，并支持按资源 ID 注入 URL 变量生成可点击的实例级大盘链接。

## 命令

```bash
bytedcli vnet dashboards \
  [--product <product>] \
  [--instance-type <type>] \
  [--type cluster|traffic|probe|node|resource] \
  [--keyword <kw>] \
  [--id <resource-id> [--region <region>]] \
  [--site cn|sdv|sg]
```

至少需要 `--product` / `--instance-type` / `--type` / `--keyword` / `--id` 任一过滤参数。

## 典型用例

```bash
# 列出 PrivateLink 产品下所有大盘
bytedcli vnet dashboards --product PrivateLink

# 找按实例查的大盘
bytedcli vnet dashboards --product PrivateLink --instance-type Endpoint --type resource

# 直接拿某 ep 的实例级大盘 URL（自动解析 region/instance_type）
bytedcli vnet dashboards --id ep-xxxxxx -j

# 全文按大盘名搜
bytedcli vnet dashboards --keyword 拨测
```

## URL 注入规则

对每个匹配 `--id` 资源类型的大盘 entry（`instance_type` 非空且 `custom_variables` 非空）：

```
原 link:  https://example.grafana.host/d/<uid>/...?orgId=1&var-Env=Online
custom_variables: [{"variableKey":"InstID","dataKey":"id"}]
资源属性:  { id: "ep-xxxxxx", region: "cn-beijing" }

link_with_id:
  https://example.grafana.host/d/<uid>/...?orgId=1&var-Env=Online&var-InstID=ep-xxxxxx&var-Region=cn-beijing
```

- `custom_variables` 为空字符串/`[]`/无效 JSON：跳过注入，输出原 link
- `dataKey` 在资源属性中查不到：debug 日志，跳过该变量
- 产品级 entry（`instance_type` 为空）：不注入资源 ID，但仍保留原 link 输出，方便点进产品级大盘

## 不做

- 不拉 panel 列表（请用 `bytedcli grafana panel list --url <link>`）
- 不读 panel 指标数值（请用 `bytedcli apm grafana query`）
- 不缓存索引
