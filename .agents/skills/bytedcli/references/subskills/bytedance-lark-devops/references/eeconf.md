# EEConf 密钥注入提单

`bytedcli lark-devops eeconf secret create` 把 EEConf 加密改造的密钥注入提单（注入 `EECONF_SECRET_*` 解密密钥）封装成带业务语义的命令。

## 背景

飞书内部安全治理专项将 EEConf 配置从明文切换为加密存储。依赖 EEConf SCM 包的服务需要注入两把解密密钥（`EECONF_SECRET_PSM_CONFIG` 私有配置、`EECONF_SECRET_PUBLIC_CONFIG` 公共配置），否则正式切流后无法重启/发布。注入通过提交 BPM 工单自动执行（延迟上线，随下次服务升级带上）。

| 平台 | `--platform` | 控制面（regions） | 泳道开关 |
| --- | --- | --- | --- |
| TCE | `tce` | `cn` / `i18nbd` / `boe` | 支持 `--all-envs` |
| Bernard | `bernard` | `cn` / `i18nbd` | 不支持 |

> `i18nbd` 含 US-TTP3。I18N-TT / US-TTP / EU-TTP 控制面因权限问题无法自动注入，需 owner 手动处理。

## 提单流程

```bash
# 1) 默认 dry-run，只预览将要提交的 payload，不会真正提单
bytedcli --json lark-devops eeconf secret create --platform tce --psms demo.a.service --regions cn

# 2) 确认无误后加 --yes 真正提交（TCE 可带 --all-envs 注入泳道）
bytedcli --json lark-devops eeconf secret create --platform tce --psms demo.a.service,demo.b.service --regions cn,boe --all-envs --yes

# 3) Bernard 平台（无 --all-envs，控制面只有 cn/i18nbd）
bytedcli --json lark-devops eeconf secret create --platform bernard --psms demo.a.service --regions cn --yes
```

## `lark-devops eeconf secret create`

- 必填参数：
  - `--platform <tce|bernard>`：目标平台（不同平台控制面与字段不同）
  - `--psms <psms>`：PSM 列表，逗号分隔或重复传入（最多 10 个）
  - `--regions <regions>`：控制面，逗号分隔或重复传入。tce 取值 `cn` / `i18nbd` / `boe`；bernard 取值 `cn` / `i18nbd`
- 可选参数：
  - `--all-envs`：仅 TCE 有效，勾选后同时给 ppe/boe 泳道注入，默认仅 prod（Bernard 不支持此参数）
  - `--yes`、`--bpm-site <site>`（默认复用全局 `--site`）
- 底层 workflow config id：TCE `33818`（`tce_secret_injection`）、Bernard `35817`（`bernard_secret_injection`），由 `--platform` 自动选择，无需手动指定 cid

## 通用约定

- 安全约定：**默认 dry-run**，只打印将要提交的 `{ workflow_config_id, config }`；**必须显式 `--yes`** 才真正 `POST` 提单。
- `--psms` / `--regions` 支持逗号/空格分隔或重复传入，会自动去重；psms 超过 10 个直接报 `EECONF_INPUT_ERROR`（请分批提单）。
- `--regions` 非法取值会报错并列出该平台允许的控制面。
- 输出：
  - `--json`：dry-run 返回 `dry_run:true` + `payload`；提交成功返回 `dry_run:false`、`platform`、`record_id`、`workflow_config_id`。
  - 非 `--json`：dry-run 展示 payload 预览与「Add --yes」提示；提交成功展示 Record ID 与详情链接。
- 提交成功后可在浏览器查看工单详情页：`https://bpm.bytedance.net/record/<record_id>`。
- 如果 PSM 在 EEConf 平台没有同名配置空间，自动化只会注入 `EECONF_SECRET_PUBLIC_CONFIG`（预期行为）。

## Notes

- 如遇鉴权问题，先执行 `bytedcli auth login`。
- 工单为**延迟上线**：注入的环境变量会随下次服务升级生效；提交后建议核对注入的环境变量数量是否符合预期。
- 若工单状态为执行失败，可能是部分控制面成功、部分失败；常见错误（TCE 有未完成工单、命中集群封禁需加白 `sec_auto_check`、缺少 Env、请求超时）请查工单日志排查。
