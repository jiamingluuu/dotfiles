---
name: bytedance-nat
description: 字节内场 NAT（DCS）的配置出口及历史流量只读查询。按 PSM、VDC、源身份查出口，按目的公网 IP 和时间查询历史连接。使用独立 nat 命令，后端为 Pisces；火山云 NAT 使用 volcano，不承接办公室 NAT。
---

# 字节内场 NAT（DCS）

## 边界

这是 DCS 基础设施的内场自建 NAT 只读查询域，与 Bytebox 并列，后端为 Pisces。
入口是 bytedcli nat，不是 Bytebox 的子命令，也不承接火山云或办公室 NAT；
不修改、转发或依赖 ByteCloud Oncall 的业务命令；不使用 oncall nat。
不执行配置写入、发布、机器修复或自动申请权限。

用户明确查询内场自建 NAT 时直接使用本 Skill；火山云 NAT 使用 volcano 命令域，
不调用本域。只有用户仅说 NAT、且已有上下文无法判断场景时，才先询问是内场、火山云还是办公室出口；
已明确内场场景时不重复询问。

## 工作流

1. 根据已有上下文选择场景；内场工作负载使用本 Skill，火山云和办公室出口问题不使用。
2. 查询配置出口时，收集 PSM、可选 VDC 和精确源身份，阅读
   [配置出口查询](references/nat-egress.md)。
3. 查询历史连接时，收集 PSM、目的公网 IP、带时区的整秒起止时间，
   阅读 [历史流量查询](references/nat-traffic.md)。优先使用短时间窗口。
4. 执行查询前，用下方两条 help 分别确认当前可执行文件支持出口和历史查询。
   Skill 安装不代表 CLI 已安装或发布；没有经过确认的最低发行版本时，以实际帮助为准，
   不猜版本号。命令不存在属于能力缺失，不是认证失败，不反复授权，也不回退到 Oncall。
   可使用用户指定且经验证的隔离分支构建，不覆盖全局 bytedcli。
   命令可用后再检查认证；认证失败按 bytedcli auth 的提示处理，不收集或输出凭据。
5. 报告查询范围、结果与限制。配置出口不是已生效证明，也不是某条连接的实际出口；
   当前 Pod/Host 身份不能替代历史身份。
6. HTTP 500、超时、未配置查询通道、截断或空结果必须分别报告；
   失败不能解释成没有流量。保留脱敏错误码和查询标识用于后端排查。

## 命令

```bash
bytedcli nat egress get --help
bytedcli nat traffic get --help
bytedcli nat egress get --psm example.service.api --vdc demo-vdc --source 10.0.0.1
bytedcli --json --http-timeout-ms 45000 nat traffic get --psm example.service.api --dst-ip 203.0.113.1 --start 2026-09-01T00:00:00+08:00 --end 2026-09-01T00:01:00+08:00
```
