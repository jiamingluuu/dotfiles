---
name: bytedance-kani
description: "Skill for Kani 权限审批、知识库检索与 Kani OpenAPI 查询。Use when tasks mention Kani、Protego、kani_* namespace、权限申请/审批、创建Kani权限申请工单、Kani知识库、work order、approval list、kani knowledge search、kani openapi."
---

# Kani 权限审批

## 如何调用

调用方式、站点切换、JSON 输出约定见：`../../invocation.md`

## When to use

- 需要查询/跟踪 Kani 权限审批工单（我发起的/待我审批的/已完成的）
- 需要按状态、审批角色（applicant/reviewer）、是否加急等维度筛选
- 需要创建Kani权限申请工单
- 需要检索 Kani 权限系统知识库，回答权限申请、审批、排障类问题
- 需要通过 `kani openapi` 先查 namespace / role / resource / group / permission，再用 workflow 发起申请

## 前置条件

- 需要鉴权，先登录：`bytedcli auth login --session`

## 快速入口

常用命令速查见：`references/quickstart.md`

## Module Routing

按任务类型读取对应 reference，避免把所有命令细节都堆在本文件：

- `knowledge`：Kani 权限系统知识、FAQ、流程与排障经验：`references/knowledge.md`
- 通用总览、鉴权语义、跨模块入口：`references/kani-openapi.md`
- `resource` / `permission`：`references/kani-openapi/resource.md`
- `namespace`：`references/kani-openapi/namespace.md`
- `role` / `member related-role`：`references/kani-openapi/role.md`
- `group`：`references/kani-openapi/group.md`
- `workflow`：`references/kani-openapi/workflow.md`
- `write-log`：`references/kani-openapi/write-log.md`

## References

- `references/knowledge.md`
- `../../invocation.md`
- `references/quickstart.md`
- `references/kani-openapi.md`
- `references/kani-openapi/resource.md`
- `references/kani-openapi/namespace.md`
- `references/kani-openapi/role.md`
- `references/kani-openapi/group.md`
- `references/kani-openapi/workflow.md`
- `references/kani-openapi/write-log.md`
- `../../troubleshooting.md`
