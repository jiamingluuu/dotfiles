# Lego 站点与认证

<!-- Load: MANDATORY for site/region selection and LEGO_AUTH_REQUIRED; CONDITIONAL for all Lego actions when site context is incomplete; Do NOT Load when site and region are already validated. -->

## Site 与 Region

`--site` 选控制面 domain；`--region` 选该 site 下的 vregion，解析后作为 `x-bcgw-vregion` header 下发。

### 站点（`--site`）

| 规范 site | 常见别名                                                          |
| --------- | ----------------------------------------------------------------- |
| `cn`      | `prod`、`online`                                                  |
| `boe`     | —                                                                 |
| `i18n-bd` | `i18n`                                                            |
| `i18n-tt` | `i18ntt`、`row`、`tiktok-row`                                     |
| `us-ttp`  | `usttp`、`ttp-us`、`ttp-us-limited`、`us-ttp-bdee`、`us-ttp-usts` |
| `eu-ttp`  | `euttp`、`ttp-eu`                                                 |

> `us-ttp-bdee` / `us-ttp-usts` 不是独立 site，只是 `us-ttp` 的别名。
> Lego 不支持 `boe-i18n`：全局 `--site boe-i18n` / `boei18n` 或 Lego `--region boe_i18n` 都会报 `LEGO_INPUT_ERROR`。

### Region（`--region`，CLI 输入 → 后端 header 值）

| site      | 是否必填 `--region` | CLI 输入值 → 后端值                                                                                                           |
| --------- | ------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `cn`      | **必填**            | `online → online`，`sinf → sinf`                                                                                              |
| `boe`     | 可省略              | `boe → boe`                                                                                                                   |
| `i18n-bd` | **必填**            | `us_compliance → USCompliance`，`non_tt_sg → Non-TT-SG`，`non_tt_us → Non-TT-US`，`sinf_i18n → sinfi18n`，`us_ttp3 → US-TTP3` |
| `i18n-tt` | **必填**            | `sg → sg`，`us → us`，`my_compliance → MyCompliance`                                                                          |
| `us-ttp`  | 可省略              | `ttp_us_limited → ttp-us-limited`                                                                                             |
| `eu-ttp`  | 可省略              | `ttp_eu → ttp-eu`                                                                                                             |

- 多 region 的 site（`cn` / `i18n-bd` / `i18n-tt`）省略 `--region` 会报 `LEGO_INPUT_ERROR`，错误 `hint` 会列出该 site 的允许值。
- 非法 `--region` 同样报 `LEGO_INPUT_ERROR`。
- 运行时可 `bytedcli lego --help` 查看 Regions 段。

## 认证

Lego 复用 ByteCloud SSO/JWT。请求头会带 `x-jwt-token` 与 `x-bcgw-vregion`。

```bash
bytedcli auth login
```

- 认证失败抛 `LEGO_AUTH_REQUIRED`，`hint` 指引 `bytedcli auth login`。
- 站点认证隔离按 SSO 环境生效：`i18n-tt`、`eu-ttp`（TikTok SSO）需单独登录；`cn` / `i18n-bd`（ByteDance SSO）通常共享登录态。

> Lego 不支持自定义 base URL / web origin 覆盖；请求目标严格由内置站点表解析，不接受任何环境变量 Host 覆盖。
