# DevFlow 服务部署信息查询引用文档

本引用文档用于通过本仓库 CLI 查询 DevFlow 部署与资源信息，适用于查看服务信息、项目信息、TCC 部署信息、部署情况、泳道信息、scm 编译情况和 MR 信息等。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 查询某个服务当前的部署信息
- 查看服务信息、项目信息、部署情况、泳道信息
- 查询 scm 编译情况、编译信息
- 查询服务的 DevFlow 任务信息
- 查询 TCC 的部署信息

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考 `DeployRequest`，以下参数在 skill 层都视为非必要参数；如果用户对话中没有明确指出，则可以不传：

- `type` 为查询类型；当用户明确给出查询类型时则必须传，比如用户说查询服务部署信息携带参数`--type "1"`，支持多个值，多个值使用逗号分隔，可取值如下：
  - `0`：全部类型，当用户未明确指定查询类型时，默认查询全部类型
  - `1`：部署信息，明确指出查询服务部署信息、泳道信息、scm信息等
  - `2`：MR 信息，明确指出查询mr相关信息等
- `service_name`：指定项目名称；当用户明确提到“项目”“前端项目”“Goofy 项目”“Ufra 项目”“Gecko 项目”“Lego插件”“Lambda服务”并且句子里包含项目名时，应优先抽取项目名作为 `service_name`；如果用户对话中没有明确指出，则可以不传
- `repo_name`：仓库名称，例如 `iesarch/devflow_admin`；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断
- `psm`：服务对应的 PSM 标识；如果用户对话中没有明确指出，则可以不传
- `branch`：目标分支名称；如果用户对话中没有明确指出，则可以不传，优先让 CLI 自动推断
- `region`：部署区域，例如 `cn`、`i18n`；如果用户对话中没有明确指出，则可以不传
- `dc`：部署机房；如果用户对话中没有明确指出，则可以不传
- `provider`：服务类型或部署提供方。**如果用户提到“前端”、“Goofy”，请直接固定传入 `--provider="GoofyDeploy"`**；提到“TCE”，传入 `--provider="TCE"`；提到“TCC”，传入 `--provider="TCC"`；提到“FaaS”，传入 `--provider="ByteFaaS"`； 提到“Ufra”、 “Gecko-Ufra”，传入 `--provider="Gecko-Ufra"`； 提到“添加repo/仓库”、 “部署依赖”，传入 `--provider="Repo"`； 提到“Gecko”，传入 `--provider="Gecko"`； 提到“Lambda”，传入 `--provider="Lambda"`； 提到“Lego”，传入 `--provider="Lego"`。如果未明确提及，则不传。
- `lane`：泳道名称，通常以 `boe_` 或 `ppe_` 开头；如果用户对话中没有明确指出，则可以不传；如果用户只说“在 ppe/boe 上部署”但没有给出具体泳道名，也不传
- `task_id`：已有 DevFlow 任务 ID；如果用户对话中没有明确指出，则可以不传；只有上下文已经明确某个任务时再一并传入
- `clusters`：部署集群列表；如果用户对话中没有明确指出，则可以不传

补充说明：

- `region`、`dc`、`lane`、`clusters` 支持多个值，多个值使用逗号分隔
- skill 层不要为了补齐这些参数频繁追问用户；用户未明确给出的参数，优先省略

## 执行原则

- `dc` 中的机房代码必须大写（如 `LF`、`HL`）；用户提供小写时先转为大写，多个机房逐项处理
- 不要为了补齐非必需参数频繁追问用户
- 能从当前对话、仓库上下文，直接使用
- 不需要执行任何git命令来获取参数
- 当用户查询 TCC 的部署信息时，优先复用本引用文档，通过 `provider=TCC` 进入统一的 `service info` 查询链路
- 如果用户未明确指定 `service_name`、`psm`、`repo_name`、`region`、`dc`、`provider`、`lane`、`task_id`、`clusters`，可以不传，这些都是非必须参数
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow service info --psm="<psm>" --bytedcli-skill-dir="<skill所在目录>"
```

根据上下文补充参数，例如：

```bash
bytedcli devflow service info --service_name="<service_name>" --psm="<psm>" --repo_name="<repo_name>" --branch="<branch>" --region="<region1>,<region2>" --dc="<dc1>,<dc2>" --provider="<provider>" --lane="<lane1>,<lane2>" --task_id="<task_id>" --clusters="<cluster1>,<cluster2>" --type="<type1>,<type2>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 不主动对输出做总结、概要、改写、提炼或格式化
- 只有用户明确要求解释时，才补充说明
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明
