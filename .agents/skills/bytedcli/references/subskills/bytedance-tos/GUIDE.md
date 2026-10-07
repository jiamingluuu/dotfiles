---
name: bytedance-tos
description: "Operate TOS (ByteDance object storage) via bytedcli: list buckets and objects, get URLs, authenticated download, upload/delete objects, view user info and records, and discover sites/VRegions. Use when tasks mention TOS or object storage."
---

# bytedcli TOS

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- TOS 控制台能力（Bucket 列表、收藏 Bucket、申请/审批记录）
- 查看某个 bucket 下的对象列表
- 获取某个 bucket 对象的下载地址
- 通过已登录的 TOS 控制台会话下载私有对象
- 上传本地文件到指定 TOS bucket
- 删除指定 TOS bucket 对象
- 需要查询 TOS 支持的站点与 VRegion（best-effort，带 1 天缓存）

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 站点与 VRegion 自动发现（best-effort）
bytedcli tos list-sites

# 当前用户信息
bytedcli tos get-user-info

# 收藏的 bucket
bytedcli tos list-starred-buckets --page 1 --size 5

# 可访问的 bucket
bytedcli tos list-viewable-buckets --page 1 --size 5

# 查看 bucket 对象（列目录内容记得带尾 /；--prefix aaa 走字符串前缀匹配）
bytedcli tos list-objects --bucket-id 123 --prefix datasets/ --limit 100

# 获取对象下载地址
bytedcli tos get-object-url --bucket-id 123 --key datasets/sample.txt

# 认证下载到文件（已存在时需显式加 --force）
bytedcli tos download-object --bucket-id 123 --key datasets/sample.txt --output ./sample.txt

# 将文本对象原样写入管道；不能与 --json 同用，也不会向交互终端直出
bytedcli tos download-object --bucket-id 123 --key scripts/install.sh --stdout | sh

# 删除对象（必须显式确认）
bytedcli tos delete-object --bucket-id 123 --key datasets/sample.txt --yes

# 上传本地文件到 bucket；默认对象名是本地文件名
bytedcli tos upload-object --bucket-id 123 --file ./sample.txt

# 指定完整对象 key
bytedcli tos upload-object --bucket-id 123 --file ./sample.txt --key datasets/sample.txt

# 指定目录前缀，对象名仍取本地文件名
bytedcli tos upload-object --bucket-id 123 --file ./sample.txt --prefix datasets

# i18n-tt US-East/maliva bucket：必须显式传全局 vregion/vdc
bytedcli --site i18n-tt --vregion US-East --vdc maliva tos upload-object --bucket-id 123 --file ./sample.txt

# 申请记录（apply/toaudit）
bytedcli tos list-records --status apply --record-type 1 --page 1 --size 5
bytedcli tos list-records --status toaudit --page 1 --size 5

# BOE
bytedcli --site boe tos list-starred-buckets --page 1 --size 5
# i18n
bytedcli --site i18n-bd tos list-starred-buckets --page 1 --size 5
```

## Notes

- `user-info` has been renamed to `get-user-info`; the old name still works as a hidden alias
- `list-objects` 的 `--prefix` 采用 S3 风格字符串前缀匹配（BFF 隐含 `delimiter="/"`）：`--prefix aaa` 会命中 `aaabbb.txt`；想列 `datasets/` 目录内容必须传 `--prefix datasets/`，只传 `datasets` 只会看到目录 rollup 条目（此时返回体带 `hint` 引导）。`has_more=true` 时用上一页最后一个对象 key 作为 `--last-key` 继续翻页
- `get-object-url` 默认输出内网下载地址；如需办公网地址可传 `--type office`，两种都要可传 `--type both`
- `download-object` 使用当前 bytedcli 登录态读取私有对象；必须且只能选择 `--output` 或 `--stdout`。覆盖文件需加 `--force`
- `delete-object` 是破坏性操作，必须传 `--yes`
- `upload-object` 会覆盖同名对象；需要自定义对象名时使用 `--key`，只想指定目录时使用 `--prefix`
- i18n-tt 的 US-East/maliva TOS bucket 需要同时传 `--site i18n-tt --vregion US-East --vdc maliva`，bytedcli 会走 maliva 网关；只传 `--site i18n-tt` 会继续打默认控制面，可能出现 bucket not found
- 默认文本模式；结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json tos list-starred-buckets ...`）
- 环境切换使用 `--site`（或 `BYTEDCLI_CLOUD_SITE`）

## References

- `references/tos.md`
