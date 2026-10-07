# ByteFlow Skill 维护约定

本目录维护 bytedcli 内置 ByteFlow helper。`scripts/byteflow_api.py` 是 Python 直连实现，不复用 TS 侧 ByteCloud site helper；修改站点或控制面时，必须同步以下位置：

- `SITE_ORIGINS`：helper `--site` 到 ByteFlow API host 的映射，不一定等于控制台 host。
- `CONSOLE_SITE_BY_HOST`：控制台 URL host 到 helper site 的反推映射，只用于解析 console URL。
- `auth_site_for_helper_site()`：helper site 到 bytedcli auth site 的映射，确保取 JWT 时使用正确 SSO 环境。
- `SKILL.md` 与 `references/*`：补充用户可见示例、站点说明和排障提示。
- `test/skills/byteflow_api.test.ts`：补最小离线测试，覆盖新增 site/alias 的 URL 构造与 JWT site 归一。

TikTok ROW ByteFlow 控制台 `https://cloud.tiktok-row.net/byteflow` 对应 helper site `i18n-tt`，API base 是 `https://bc-sg-gw.tiktok-row.net/api/v1/byteflow/api/v1`；别名 `row`、`tiktok-row` 也应保持可用。不要把它误归到 `i18n`，后者指向 `cloud-i18n.bytedance.net`。
