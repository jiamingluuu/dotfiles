---
name: ai-approval-iam
description: "IAM 权限拦截路由。当 cloud-approval 主 Skill 感知到 IAM 权限相关场景时——包括业务操作返回无权限、permission denied、authorization denied、缺少权限点、RBAC 拦截、SCP 拦截、需要申请访问权限或查看审批进度——整理证据并路由到 IAM Skill（项目 iam 或全局 bytedcli iam）。用于 IAM 路由和缺失依赖引导；不解释 IAM 业务字段、不发起申请，也不维护 IAM 补救状态机。"
---

# Approval → IAM 路由层

本文件是 cloud-approval 到 IAM 能力的路由层。核心职责：感知权限信息 → 整理证据 → 路由到 IAM Skill。

## 触发条件

当以下任一场景出现时触发本路由，不要求结构化字段或特定返回格式：

| 场景类型 | 典型表现 |
|---|---|
| 业务操作被权限拦截 | 返回 permission denied、authorization denied、无权限、缺少权限点、RBAC 拦截、SCP 拦截 |
| 用户主动查询或申请 IAM 权限 | “查询 IAM 资源”、”检查权限”、”申请角色”、”查看审批进度”、”管理角色授权”、”查询策略或用户” |
| 错误信息包含 IAM 领域关键词 | provider=iam、IAM 错误码、permission check failed、role/policy 相关拒绝信息 |
| 结构化路由信号 | `next_action.provider == “iam”` 或等价标识（有则用，无不强求） |

核心原则：不要停在”权限不足”。只要能从错误、上下文或用户说明中识别出这是 IAM 权限问题，就立即进入路由流程。

## 路由流程

1. **感知**：从业务报错、CLI stderr、API 响应或用户转述中识别 IAM 权限场景。保留原始证据（错误码、request ID、主体、资源、权限点等），如存在则原样保留，不补造。

2. **选择路由目标**：按优先级尝试：

   **优先：项目 IAM Skill** — 读取 [bytedance-iam](../../bytedance-iam/GUIDE.md)（即 `skills/bytedance-iam/SKILL.md`）。
   该 Skill 通过 `bytedcli iam` 入口，包含完整的 permission check → plan → apply 状态机和补救流程。如果当前在本项目上下文中，优先使用此 Skill。

   **备选：全局 bytedance-iam Skill** — 如果项目 IAM Skill 不可用或不在本项目上下文中，切换到全局 `bytedcli iam` Skill（`~/.agents/skills/bytedance-iam/SKILL.md`）。

3. **检查依赖**：运行 `command -v bytedcli`。未安装时展示安装命令，不擅自安装：

```bash
npm install -g @bytedance-dev/bytedcli@latest --registry=https://bnpm.byted.org
```

4. **交接**：已安装时运行 `bytedcli iam --help` 确认可用，然后切换到目标 IAM Skill，原样交接用户目标和现有证据。后续诊断、check、plan、申请、重查全部由 IAM Skill 接管。

## 禁止事项

- 不调用通用 `ticket create`。
- 不要求权限错误先转换成结构化 `next_action`，也不补造 `approval_context`。
- 不解析或标准化 IAM 的主体、资源、权限、角色和策略字段。
- 不根据错误文本、用户说明或路由信号直接执行申请。
- 不复制或改写 IAM Skill 的状态机、命令参数、退出码和安全规则。
- IAM CLI 或 IAM Skill 不可用时停止交接，不自行拼装领域命令。
