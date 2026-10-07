---
name: merlin-service
description: 管理 Merlin 线上服务（Bernard）：查询服务配置、创建服务、部署模型、查看日志、调用 API、从 TCC 批量克隆服务到线上并生成线上 TCC。当用户说"部署模型/创建服务/Bernard/vLLM 部署/查看线上服务/deploy model/service 信息/从 TCC 克隆服务/测试克隆到线上/clone-from-tcc/批量上线"时使用。
---

# 线上服务管理（Bernard）

管理 Merlin 线上服务（Bernard 平台）：创建服务、部署模型、查看容器日志、验证 API。

## 前置条件

- `bytedcli merlin` 可用
- 已登录：`bytedcli auth login`

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

---

## 查询服务

```bash
# 列出所有服务
bytedcli merlin deploy service list

# 按精确 PSM 查询它对应的 Bernard service ID
bytedcli merlin service get-psm-detail --psm example.models.deploy -j

# 只有模糊 PSM 或 service ID 片段时搜索
bytedcli merlin deploy service list --tab all --keyword demo-service -j

# 查询指定服务详情
bytedcli merlin deploy service get --service-id <service-id> -j

# 查看可用 GPU 配额
bytedcli merlin deploy quota --service-id <service-id> -j
```

服务 URL 格式：`https://ml.bytedance.net/serviceList/<service_id>`

`service get-psm-detail` 按完整 PSM 精确查询；`deploy service list --keyword` 是模糊搜索。存在多个 service ID 时，先用 `deploy list` 核对各候选的 region、GPU 类型和部署状态，再用 `deploy log-list` 查询目标时间窗内的实例数与扩缩容历史，不要自动选取一个。

---

## 元数据发现（部署前自助探索）

部署前先用只读命令查清可用的 region / GPU / 框架 / CUDA / 资源容量，避免硬编码：

```bash
# 可用部署地区（region）
bytedcli merlin deploy meta regions -j

# 可用 GPU 类型
bytedcli merlin deploy meta gpu-types -j

# 官方框架与版本（默认官方镜像；--v2 列官方镜像 2.0 的 model_type + 基础镜像）
bytedcli merlin deploy meta frameworks
bytedcli merlin deploy meta frameworks --v2 -j

# 框架可用的 CUDA 版本
bytedcli merlin deploy meta cuda-versions -j

# 机型规格（来自 Bernard constant）
bytedcli merlin deploy meta machine-specs -j

# 资源套餐 / flavor（socket package，--type 默认 Accelerated-Computing）
bytedcli merlin deploy meta packages --type Accelerated-Computing -j

# 已构建镜像（ICM）版本（custom-build / 官方镜像 2.0 服务）
bytedcli merlin deploy image-versions --service-id <service-id> --version latest -j
```

推荐部署流程：`deploy meta frameworks(--v2)` / `cuda-versions` → `deploy meta regions` + `gpu-types` → `deploy quota --service-id <id>` → `service check-uniq`（确认 id/psm 可用）→ `deploy service create` → `service build-status`（等构建）→ 部署 → `deploy status` / `deploy get` / `deploy list` 检查状态。

部署这一步按服务类型走不同命令，三者互斥：

- 普通单体服务（`--k8s-service-type regular_service`）：用 `deploy create`。
- storm 多角色服务（`--k8s-service-type storm_service` / `storm_service_pool`）：用 `deploy roleset create`，不要用 `deploy create`。
- storm 服务编排（`--k8s-service-type storm_service_application`）：用 `deploy application create`。

```bash
# 创建前检查 service id / psm 是否可用
bytedcli merlin deploy service check-uniq --target service-id --value demo-svc -j
bytedcli merlin deploy service check-uniq --target psm --value demo.product.module -j
```

---

## 确认与预览（update / delete 必读）

所有写操作（service update/delete、deploy update/delete、roleset、application）默认拒绝执行，必须显式确认：

- `--dry-run`：只打印将要发送的 payload / 目标，不调用接口（无需 `--yes`）。
- `--yes`：确认执行；缺失时返回带 `hint` 的结构化错误，便于 agent 直接补齐命令。

```bash
# 先预览
bytedcli merlin deploy service delete --service-id <service-id> --dry-run -j
# 确认执行
bytedcli merlin deploy service delete --service-id <service-id> --yes
```

> service delete 在该服务仍有 deployment 时会被后端拒绝；先删除 deployment 再删服务。

---

## 变更历史与排障（service log-list）

每次 service create/update 都会留一条变更日志（含完整 config 快照）。排障时对比更新前后差异：

```bash
# 列出变更历史（最近 N 条）
bytedcli merlin deploy service log-list --service-id <service-id> --page-size 10 -j

# 查看某条变更的完整 config 快照
bytedcli merlin deploy service log-get --service-id <service-id> --log-id <log-id> -j

# 对比两条变更之间 config 的字段级差异（added / removed / changed）
bytedcli merlin deploy service log-diff --service-id <service-id> --from-log-id <旧> --to-log-id <新>
```

典型用法：服务更新后行为异常 → `service log-list` 找到更新前后两条 log id → `service log-diff` 看具体改了哪些字段（cpus / 镜像 / env / model 等）来定位问题。

部署级变更（实例数扩缩容等）另有独立的变更历史，用 `deploy log-list` 查询：

```bash
# 列出部署变更历史（用户/平台触发的实例数等变更，默认 --source platform，最多显示 --page-size 条）
bytedcli merlin deploy log-list --service-id <service-id> -j

# 自动扩缩容（bytepaas autoScaleCluster 工单）产生的变更
bytedcli merlin deploy log-list --service-id <service-id> --source bytepaas -j

# US-TTP 站点（控制台 ml-ttp-us.byteintl.net）：站点选对即可，Bernard API host 由 CLI 自动路由，无需 --origin
bytedcli --site us-ttp-bdee merlin deploy log-list --service-id <service-id> -j
```

`deploy service log-list` 记录 service 配置快照变更，`deploy log-list` 记录 deployment 实例/扩缩容变更，`deploy logs` 是容器日志，三者互不重叠。`deploy log-list` 的后端会返回全量历史，超过 `--page-size`（默认 20）的部分会被截断并显式提示，JSON 输出带 `current_count` / `truncated` 字段。

---

## Canary 小流量

Canary（小流量）是一个与 prod 并存的独立部署，通过 `--canary-type` 指定，网关据此把一小部分流量切到 canary 部署：

```bash
# 永久小流量部署
bytedcli merlin deploy create --service-id <service-id> --region <region> --gpu-type <type> --instances 1 --canary-type canary

# 时限小流量（到期自动回收，需配合 --expire-time）
bytedcli merlin deploy create --service-id <service-id> --region <region> --gpu-type <type> --instances 1 --canary-type canary-temporary --expire-time <unix-seconds>

# storm / application 服务同样支持 canary：
bytedcli merlin deploy roleset create ... --canary-type canary
bytedcli merlin deploy application create ... --canary-type canary
```

`--canary-type` 取值：`prod`（默认）| `canary`（小流量）| `canary-temporary`（时限小流量）| `debug` | `debug-temporary` | `temporary`。用 `deploy list --service-id <id>` 可同时看到 prod 与 canary 部署。

---

## 创建服务（custom-build + vLLM）

准备 JSON 配置文件，用 `--body-file` 创建：

```bash
bytedcli merlin deploy service create --body-file /tmp/service-config.json -j
```

JSON 配置关键字段：

```json
{
  "id": "<service-id>",
  "psm": "example.models.deploy",
  "cpus": 64,
  "mem": 481280,
  "gpus": 4,
  "container_image": "",
  "container_image_type": "custom-build",
  "model_location": "modelzoo://",
  "model_type": "tensorflow",
  "enable_ipv6": true,
  "num_ports": 8,
  "custom_build_meta": {
    "base_image": "seed.infer.debian12.python312.cuda124.torch29.base:latest",
    "runtime": 0,
    "load_path": "<scm-relative-path-to-start-script>",
    "image_namespace": "bernard",
    "scms": [
      { "name": "toutiao/runtime", "path": "/opt/tiger/toutiao/runtime", "version": "1.0.1.450" },
      { "name": "tce/tce_tools", "path": "/opt/tiger/tce/tce_tools", "version": "1.0.0.132" },
      { "name": "lab/bernard/load", "path": "/opt/tiger/toutiao/load", "version": "1.0.0.69" },
      { "name": "<your-scm>", "path": "/opt/tiger/<your-dir>", "version": "<version>" },
      { "name": "data/inf/hdfs_client", "path": "/opt/tiger/hdfs_client", "version": "1.9.28.81" }
    ],
    "packages": [
      {
        "name": "vllm==0.18.0 && pip --no-cache-dir install transformers==5.3.0",
        "package_type": "pip"
      }
    ]
  },
  "feature_gate": {
    "laplace_arch": "x86",
    "shm": { "enabled": true, "size": 100000 }
  },
  "envs": [
    "BERNARD_MULTI_MODELS=<model-name>:<version>",
    "TCE_ENABLE_SIDECAR=100",
    "TCE_INSTALL_SIDECAR=True",
    "USE_BERNARD_STDOUT=1",
    "BGCP_LOGGING_STDOUT=1",
    "IGNORE_LIVENESS_CHECK=1",
    "MODEL_HDFS_PATH=hdfs://haruna/home/...",
    "TOOL_CALL_PARSER=qwen3_coder"
  ],
  "real_put_envs": true
}
```

### 关键参数说明

| 字段                   | 说明                                                         |
| ---------------------- | ------------------------------------------------------------ |
| `container_image`      | custom-build 时必须为空字符串 `""`                           |
| `load_path`            | 启动脚本路径，相对于 `/opt/tiger/`，只能是文件（不能是目录） |
| `lab/bernard/load` SCM | **必须包含**，负责执行 load_path 和注册服务                  |
| `shm.size`             | MB 单位，须 < `mem`，用于 /dev/shm 存放模型                  |
| `packages.name`        | 支持 `&&` 串联多条 pip 命令                                  |
| `real_put_envs`        | 设为 `true` 确保 envs 被写入                                 |

### 必须的环境变量

| 变量                       | 作用                                                                                          |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| `BERNARD_MULTI_MODELS`     | 触发 Bernard load 机制执行 load_path（值为 `<model>:<version>`，版本需通过 model store 注册） |
| `TCE_ENABLE_SIDECAR=100`   | load 机制依赖                                                                                 |
| `TCE_INSTALL_SIDECAR=True` | load 机制依赖                                                                                 |
| `USE_BERNARD_STDOUT=1`     | 日志输出到 /dev/bernard_stdout                                                                |
| `BGCP_LOGGING_STDOUT=1`    | 日志捕获                                                                                      |
| `IGNORE_LIVENESS_CHECK=1`  | 跳过初始健康检查（模型加载耗时长）                                                            |

> **注意**：缺少以上环境变量会导致容器启动后只显示 "Hello from Bernard Container!" banner，不执行 start.sh。

---

## 等待构建

```bash
# 主动轮询镜像构建状态（custom-build / 官方镜像 2.0）
bytedcli merlin deploy service build-status --service-id <service-id> -j
# 也可从服务详情读取 custom_build_meta.build_status: "building" → "ok" → 可部署
bytedcli merlin deploy service get --service-id <service-id> -j
# 构建失败可重试（需 --yes，支持 --dry-run）
bytedcli merlin deploy service build-retry --service-id <service-id> --yes
# 构建通常需 5-10 分钟（pip install vLLM 较慢）
```

---

## 创建部署

```bash
bytedcli merlin deploy create \
  --service-id <service-id> \
  --region lf-default \
  --gpu-type l40 \
  --instances 1

# socket 服务：先从已有部署抄 is_socket / minipod 字段，再照抄进 create
bytedcli merlin deploy list --service-id <service-id> -j
bytedcli merlin deploy create \
  --service-id <service-id> \
  --region <region> \
  --gpu-type <type> \
  --instances 1 \
  --is-socket --minipod-placement hpcCluster-<id> --minipod-affinity-level s2
```

参数说明：

- **region**: `lf-default`, `hl-default`, `lq-default` 等，用 `deploy quota` 查看可用配额
- **gpu-type**: L40 (48GB), L20 (96GB), A100/A800 (80GB) 等
- **is-socket**: socket 部署的容量不由 GPU quota 记账，所以不带这个 flag 时后端会把本次创建算进 GPU 配额，可能报 `error_code 392`（业务线卡型 Quota 卡量超过阈值，严禁扩容）——即使同一个服务已经在该 region 跑着 socket 实例。判断办法是 `deploy list` 看已有部署的 `is_socket`，为 `true` 就要带上该 flag，并把同一 region 那条的 `minipod_placement` / `minipod_affinity_level` 一起抄过来。这与 `Resource pool not found`（该 psm 在这个 region + gpu_type 上没有资源池）是两回事，处置也不同。
- **minipod-placement / minipod-affinity-level**: 只对 socket 部署生效，必须与 `--is-socket` 同时给；单独传会被 CLI 直接拒绝并提示补 flag（打到后端只会拿到上面那个指不到真因的 392）。各 region 对应不同的 hpcCluster，所以要抄同一 region 那条部署的值。
- 报 `"image is in status: building"` 说明构建未完成

---

## 官方镜像 2.0（official-custom-build）

官方镜像 2.0 是一种服务镜像模式（不是单独的部署类型），部署仍走该服务对应的部署入口。
`model_type` 必须是 `deploy meta frameworks --v2` 列出的 `official_image_v2_config.service_type` key；`base_image` 省略时后端会按 `model_type` 自动从 TCC 解析。

```bash
# 先查可用 model_type
bytedcli merlin deploy meta frameworks --v2 -j

# 创建官方镜像 2.0 服务（base-image 可省略）
bytedcli merlin deploy service create \
  --id demo-svc --psm demo.product.module \
  --container-image-type official-custom-build \
  --model-type <v2-model-type> --model-name demo-model --model-version v1 \
  --base-image demo/base:1 \
  --dry-run
```

---

## storm_service（多角色 roleset 部署）

storm 服务在 `service create` 时用 `--k8s-service-type storm_service`（或 `storm_service_pool`）+ `--roleset-config-file`（每角色配置数组）。部署走 `deploy roleset`（对应 `POST /api/v2/rolesets`），不是普通 `deploy create`。

```bash
# 1) 创建 storm 服务（roleset_config 为每角色数组）
bytedcli merlin deploy service create \
  --id demo-storm --psm demo.product.module \
  --k8s-service-type storm_service \
  --roleset-config-file ./roleset_config.json --dry-run

# 2) 创建 roleset 部署（roleset_deployment_config 每角色需 role_name/gpu_type/stateful/quota_resource_level/quota_resource_type）
bytedcli merlin deploy roleset create \
  --service-id demo-storm --region demo-region --replicas 1 \
  --roleset-deployment-config-file ./roleset_deploy.json --yes

# 3) 列举 / 查看 / 扩缩 / 删除
bytedcli merlin deploy roleset list --service-id demo-storm -j
bytedcli merlin deploy roleset get --roleset-id <id> -j
bytedcli merlin deploy roleset scale --roleset-id <id> --replicas 2 --yes
bytedcli merlin deploy roleset delete --roleset-id <id> --yes
```

### 推荐：用 `deploy roleset gen-config` 自动生成 `roleset_deploy.json`

不用手写 `roleset_deployment_config`。`gen-config` 会读服务自己的 `roleset_config`（自动带出 role 列表、`is_socket`、`num_pods`），你只需给每个 role 指定 GPU；对 `cfs_enabled` 的 role，它还会自动从 Bernard TCC `cfs_config` 解析并回填 `cfs_cluster` / `cfs_protocol`：

```bash
# 一步生成完整配置文件（含 cfs 自动回填），再喂给 create
bytedcli merlin deploy roleset gen-config \
  --service-id demo-storm --region demo-region \
  --role-gpu decode=mi308x,prefill=ff45d \
  --output ./roleset_deploy.json

bytedcli merlin deploy roleset create \
  --service-id demo-storm --region demo-region --replicas 1 --is-pool \
  --roleset-deployment-config-file ./roleset_deploy.json --yes

# 可选：覆盖每角色 num_pods、或用 -j 让上层程序消费 config + warnings
bytedcli merlin deploy roleset gen-config --service-id demo-storm --region demo-region \
  --role-gpu decode=mi308x --role-gpu prefill=ff45d --role-pods decode=2 -j

# 手动查/挑 cfs 集群（gen-config 内部用的就是这个；多个候选时用 --minipod 消歧）
bytedcli merlin deploy meta cfs-clusters --region demo-region --gpu ff45d
```

`gen-config` 的取数来源（无需前后端即可推导整份配置）：role 列表 / `is_socket` / `num_pods` / `cfs_enabled` 来自 `deploy service get`；`gpu_type` 由 `--role-gpu` 指定（候选见 `deploy meta gpu-types`、可用余量见 `deploy quota`）；`cfs_cluster` / `cfs_protocol` 来自 `deploy meta cfs-clusters`（按 region 的 idc 前缀 + gpu 匹配，多候选时用 `--minipod` 消歧）。若某 cfs role 没匹配到集群，会保留空缺并打印 warning，提示用 `deploy meta cfs-clusters` 手动确认。

`roleset_config.json`（service create 用）：

```json
[
  {
    "role_name": "prefill",
    "cpus": 32,
    "mem": 131072,
    "gpus": 8,
    "num_pods": 1,
    "envs": [],
    "container_image_type": "official",
    "model_type": "demo-framework"
  },
  {
    "role_name": "decode",
    "cpus": 16,
    "mem": 65536,
    "gpus": 4,
    "num_pods": 2,
    "envs": [],
    "container_image_type": "official",
    "model_type": "demo-framework"
  }
]
```

`roleset_deploy.json`（roleset create 用）：

```json
[
  {
    "role_name": "prefill",
    "gpu_type": "demo-gpu",
    "stateful": false,
    "quota_resource_level": "guarantee",
    "quota_resource_type": "normal"
  },
  {
    "role_name": "decode",
    "gpu_type": "demo-gpu",
    "stateful": false,
    "quota_resource_level": "guarantee",
    "quota_resource_type": "normal"
  }
]
```

> storm 部署不支持 `quota_resource_type: ondemand`；pool 模式（`--is-pool`）下 `replicas` 固定为 1，并需在每角色配置里给 `num_pods`。

> **cfs 必填（易踩坑）**：若某个 role 在服务里开了 `cfs_enabled`（看 `deploy service get --service-id <id>` 的 `roleset_config.<role>.feature_gate.cfs_enabled`），其 `roleset_deployment_config` 条目必须带 `cfs_cluster`（以及 `cfs_protocol`，通常 `rdma`），否则后端只回隐晦的 `error_code 384: cfs_cluster is not set, please close cfs_enabled in service`。**最省心的做法是用上面的 `deploy roleset gen-config` 自动回填**；若手写，`deploy roleset create` 也会在创建前本地预检并给出明确报错，`cfs_cluster` 的值可用 `deploy meta cfs-clusters --gpu <gpu> --region <region>` 查到（或从历史部署 `deploy roleset list` 的 `cfs_cluster` 字段取）。手写示例（prefill 开了 cfs）：
>
> ```json
> [
>   {
>     "role_name": "decode",
>     "gpu_type": "demo-gpu",
>     "stateful": false,
>     "quota_resource_level": "guarantee",
>     "quota_resource_type": "normal",
>     "num_pods": 1
>   },
>   {
>     "role_name": "prefill",
>     "gpu_type": "demo-gpu",
>     "stateful": false,
>     "quota_resource_level": "guarantee",
>     "quota_resource_type": "normal",
>     "num_pods": 1,
>     "cfs_cluster": "demo-cfs-cluster",
>     "cfs_protocol": "rdma"
>   }
> ]
> ```

---

## storm_service_application（多 storm 服务编排）

`service create` 用 `--k8s-service-type storm_service_application` + `--application-config-file`（含 `updateStrategy` 与 `stormServices[]`，`role_name` 全局唯一），可选 `--scheduling-config-file`。部署走 `deploy application`（对应 `POST /api/v2/applications`）。

```bash
# 1) 创建 application 服务
bytedcli merlin deploy service create \
  --id demo-app --psm demo.product.module \
  --k8s-service-type storm_service_application \
  --application-config-file ./application_config.json --dry-run

# 2) 创建 application 部署
bytedcli merlin deploy application create \
  --service-id demo-app --region demo-region \
  --application-roleset-deployment-config-file ./app_deploy.json --yes

# 3) 列举 / 查看 / 更新 / 删除
bytedcli merlin deploy application list --service-id demo-app -j
bytedcli merlin deploy application get --application-id <id> -j
bytedcli merlin deploy application update --application-id <id> --body-file ./app_update.json --yes
bytedcli merlin deploy application delete --application-id <id> --yes
```

`app_deploy.json`（application create 用，每条对应一个 storm 服务）：

```json
[
  {
    "storm_service_name": "prefill-svc",
    "storm_service_type": "storm_service",
    "replicas": 1,
    "roleset_deployment_config": [
      {
        "role_name": "prefill",
        "gpu_type": "demo-gpu",
        "stateful": false,
        "quota_resource_level": "guarantee",
        "quota_resource_type": "normal"
      }
    ]
  }
]
```

> wire-format 差异：roleset 用 `canary_type`（snake_case），application 用 `canaryType`（camelCase），CLI 已分别处理。

---

## 监控部署

```bash
# 列出部署
bytedcli merlin deploy list --service-id <service-id> -j

# 实例健康/状态计数（确认部署是否就绪）
bytedcli merlin deploy status --deployment-id <id> -j

# 容器详情（host、containerID、webshell URL）
bytedcli merlin deploy get --deployment-id <id> -j

# 获取实例 webshell（TTY）URL（浏览器打开即得 shell；可用 --container-id 过滤单实例）
bytedcli merlin deploy webshell --deployment-id <id> -j
bytedcli merlin deploy webshell --deployment-id <id> --container-id <containerID>

# 容器日志（普通服务）
bytedcli merlin deploy logs \
  --service-id <service-id> \
  --host <ipv6-from-detail> \
  --container-id <containerID-from-detail>

# 生产网读取 i18n-tt 容器日志（自动切换到 Bernard 内网日志网关）
BYTEDCLI_NETWORK_PROFILE=prod bytedcli --site i18n-tt merlin deploy logs \
  --service-id <service-id> \
  --host <ipv6-from-detail> \
  --container-id <containerID-from-detail>

# storm_service / 多角色服务日志（innerhost 类型，普通 deploy logs 不适用）
bytedcli merlin deploy inner-log \
  --service-id <storm-service-id> --psm demo.product.module \
  --host <pod-ip> --pod-name <pod> --log-name log/run/executor_0.log --download

# 重启部署（重建 pod，需 --yes，支持 --dry-run）
bytedcli merlin deploy restart --deployment-id <id> --yes

# 迁移单个 pod（删除该实例，由平台在其他机器上重新调度；需 --yes，支持 --dry-run）
# 普通服务用 --deployment-id；storm 服务用 --roleset-id；storm application 用 --application-instance-id；都不传则按 pod 名自动定位。
bytedcli merlin deploy instance migrate --pod <pod-name> --deployment-id <id> --dry-run
bytedcli merlin deploy instance migrate --pod <pod-name> --deployment-id <id> --yes
bytedcli merlin deploy instance migrate --pod <storm-pod> --roleset-id <roleset-id> --comment "rebalance" --yes
```

> 生产网必须设置 `BYTEDCLI_NETWORK_PROFILE=prod`，bytedcli 会据此自动选择可达的 Bernard 日志地址。

> `deploy inner-log` 是 storm_service / storm_service_application 多角色服务的日志路径（后端 `innerhost_log_url`）；不带 `--download` 返回加密代理 URL，带 `--download` 直接下载日志内容。普通单体服务仍用 `deploy logs`。

> `deploy instance migrate` 通过删除指定 pod 触发平台重新调度（对应后端 `DELETE /instances/<pod>`），属于破坏性操作，默认拒绝执行，必须带 `--yes`（或先用 `--dry-run` 预览）。默认 `force` 删除；如需非强制可加 `--no-force`。

> `deploy webshell` 返回每个实例的 TTY relay URL（即 `deploy get` 里的 webshell 链接）；URL 含 `bpm/apply` 表示需先申请 webshell 权限。

日志正常流程：

1. "Hello from Bernard Container!" — load 初始化
2. HDFS download — 模型下载
3. vLLM serve started — 服务启动
4. "Application startup complete." — API 就绪
5. "service is ready!" — 健康检查通过（约 5-7 分钟）

---

## 验证 API

```bash
# 从 deploy get 获取 tasks[0].host 和 tasks[0].ports[0]

# 健康检查
curl -6 "http://[<ipv6>]:<port>/health"

# Chat Completion
curl -6 -X POST "http://[<ipv6>]:<port>/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{"model": "<model-name>", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100}'
```

---

## 更新 / 扩缩 / 删除

```bash
# 扩缩或更新普通 deployment（需 --yes，支持 --dry-run 预览）
bytedcli merlin deploy update --deployment-id <id> --instances 3 --dry-run
bytedcli merlin deploy update --deployment-id <id> --instances 3 --yes

# 更新服务配置（可传具体字段或 --body-file）
bytedcli merlin deploy service update --service-id <service-id> --description "new desc" --yes

# 删除部署 / 服务（删除服务前需先删完其 deployment）
bytedcli merlin deploy delete --deployment-id <id> --yes
bytedcli merlin deploy service delete --service-id <service-id> --yes
```

---

## start.sh 模板

```bash
#!/usr/bin/env bash
exec > /dev/bernard_stdout 2>&1
set -exuo pipefail

if [ -z "${MODEL_HDFS_PATH:-}" ]; then
    echo "Error: MODEL_HDFS_PATH not set"; exit 1
fi

MODEL_DIR=$(basename "$MODEL_HDFS_PATH")
mkdir -p /dev/shm/model_download && cd /dev/shm/model_download

/opt/tiger/hdfs_client/bin/hdfs get -s -c 128 --ct 32 -t 8 "$MODEL_HDFS_PATH" .

vllm serve "$MODEL_DIR" \
    --tensor-parallel-size 2 \
    --pipeline-parallel-size 2 \
    --port $PORT --host "::" \
    --enable-auto-tool-choice --tool-call-parser $TOOL_CALL_PARSER
```

关键点：

- `exec > /dev/bernard_stdout 2>&1`：确保日志在 `deploy logs` 可见
- `$PORT`：Bernard 自动注入（`TCE_SERVICE_PORT`）
- TP × PP = gpus 总数（如 TP=2, PP=2 对应 4 GPU）

---

## 从 TCC 批量克隆服务到线上（clone-from-tcc）

一条命令把「测试 TCC 配置里引用的一批 Bernard 服务」整体克隆到线上 PSM，并可选地生成对应的线上 TCC 配置。适用于测试链路验证后整体上线的场景。

### 工作流

1. 读取源 TCC 配置的 YAML，找出所有 `target: sd://<psm>?cluster=<service_id>` 引用的 Bernard 服务
2. 逐个 GET 源服务完整配置，派生新 `service_id`，替换 `psm`
3. 改写 `envs` 里的 `BERNARD_MS_CLUSTER`（= 新 service_id）与 `BERNARD_SD_TAGS.cluster`（= sd tag，默认跟随新 service_id）
4. 用 `auto_bind_psm_meta`（服务树挂载）创建服务，创建后 PUT 绑定业务标签
5. （可选）按源 YAML 结构生成线上 TCC 配置，把已克隆服务的 target 改写到新 psm + 新 cluster

### 关键参数

| 参数                                                                          | 说明                                                                                                                                   |
| ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `--tcc-ns` / `--tcc-conf` / `--tcc-env`                                       | 源 TCC 配置位置（env 默认 prod）                                                                                                       |
| `--new-psm`                                                                   | 克隆目标 PSM（所有服务）                                                                                                               |
| `--service-id-replace <old:new>`                                              | service_id 字符串替换，如 `_test:_online`                                                                                              |
| `--strip-tokens <tokens>`                                                     | 按下划线整段删除 token（替换后执行），如 `test,qa,xperf,two_card`                                                                      |
| `--sd-tag <tag>`                                                              | 固定 `BERNARD_SD_TAGS.cluster`；省略则逐服务跟随新 service_id                                                                          |
| `--bind-parent-id` / `--bind-path`                                            | 服务树挂载 `auto_bind_psm_meta`（**必填**，否则后端报 error_code 466）                                                                 |
| `--biz-tags <tags>`                                                           | 业务标签，2 或 3 级，如 `demo_l1,demo_l2,demo_l3`（create 后 PUT `service_tags_batch`）                                                |
| `--only <ids>`                                                                | 只克隆指定 service_id（原始或新 id 均可匹配），先冒烟再批量                                                                            |
| `--create-deployment` + `--deploy-region <region>` + `--deploy-instances <n>` | 克隆后为每个服务创建部署实例（gpu_type 取自服务配置，region 必填且是**配额池 region**如 `demo-region-1`，n 默认 1）；**消耗 GPU 配额** |
| `--create-online-tcc` + `--online-tcc-ns [--online-tcc-conf]`                 | 克隆后生成线上 TCC（conf 默认源 conf 去掉尾部 `_test`）                                                                                |
| `--dry-run` / `--yes`                                                         | 预览 / 执行                                                                                                                            |

### 服务树挂载与业务标签（必读）

- **服务树挂载**（`--bind-parent-id` + `--bind-path`）：seed 服务创建时必须指定挂载节点，否则报 `error_code 466 should be mounted under ...`。挂载节点 id/path 可用 `bytedcli bytetree` 反解，或参考同 PSM 下已有服务的 `all_parent_id_list`（末位即父节点 id）。
- **业务标签**（`--biz-tags`）：对应前端「业务标签」，存在独立接口 `PUT /p/bernard/api/v2/tags/service_tags_batch`，**不在**服务配置里；后端要求 2 或 3 级层级标签（如 `demo_l1,demo_l2,demo_l3`），单个标签会被拒。标签绑定失败不会回滚已创建的服务，会以 warning 透出。

### 推荐流程（先冒烟，再批量）

> **命名先确认（必读）**：`--strip-tokens` / `--service-id-replace` 派生出的新 `service_id` 可能不完全符合预期（如残留 `_debug`/`_3`，或 `demo_svc_25` 与 `demo_svc25` 不一致）。**务必先 `--dry-run` 看 Clone Plan 表里的「→ New Service ID」，与业务方确认命名后再执行**。命名规则无法精确覆盖的个别服务，先按规则批量创建，再对个别服务「删除旧的 + 用正确名字重建」（复用相同 `--new-psm`/`--bind-*`/`--biz-tags`），并同步更新已生成的线上 TCC target。

```bash
# 1) dry-run 预览：确认 service_id 派生（重点核对命名）、env 改写、挂载、标签、部署、线上 TCC YAML
bytedcli merlin deploy service clone-from-tcc \
  --tcc-ns example.infra.demo_test_tcc --tcc-conf demo_v1_test \
  --new-psm demo.seed.example \
  --strip-tokens test,qa,xperf,two_card \
  --bind-parent-id 100000000 --bind-path '|Demo-Org|demo_group|demo_layer|online' \
  --biz-tags demo_l1,demo_l2,demo_l3 \
  --create-deployment --deploy-region demo-region-1 --deploy-instances 1 \
  --create-online-tcc --online-tcc-ns demo.infra.example \
  --dry-run
# 2) 单个冒烟：先克隆一个验证线上可用
bytedcli merlin deploy service clone-from-tcc \
  --tcc-ns example.infra.demo_test_tcc --tcc-conf demo_v1_test \
  --new-psm demo.seed.example \
  --strip-tokens test,qa,xperf,two_card \
  --bind-parent-id 100000000 --bind-path '|Demo-Org|demo_group|demo_layer|online' \
  --biz-tags demo_l1,demo_l2,demo_l3 \
  --only demo_service_xperf_test --yes
# 3) 批量 + 建实例 + 生成线上 TCC（--create-deployment 会消耗 GPU 配额，先算好总量）
bytedcli merlin deploy service clone-from-tcc \
  --tcc-ns example.infra.demo_test_tcc --tcc-conf demo_v1_test \
  --new-psm demo.seed.example \
  --strip-tokens test,qa,xperf,two_card \
  --bind-parent-id 100000000 --bind-path '|Demo-Org|demo_group|demo_layer|online' \
  --biz-tags demo_l1,demo_l2,demo_l3 \
  --create-deployment --deploy-region demo-region-1 --deploy-instances 1 \
  --create-online-tcc --online-tcc-ns demo.infra.example \
  --yes
```

### 创建实例（部署）

`--create-deployment` 在每个服务克隆成功后创建一个部署：`gpu_type` 取自服务配置，`--deploy-region` 必填、实例数 `--deploy-instances`（默认 1）。单实例 GPU 数由服务配置固定（1~8 不等），批量前先估算总配额需求。

**部署 region 是「配额池 region」，不是服务配置里的展示地区**：

- 服务配置 `icm_url_list` 的 key（如 `Demo-Region-Display`）是展示地区，**不能**直接当部署 region，否则报 `error_code 342 Invalid Region`。
- 部署 region 用配额池代码（如 `demo-region-1`）。获取方式：查同 PSM 下已有服务的部署 `bytedcli merlin deploy list --service-id <已有服务> -j`，取其 `region`。
- 不同 `gpu_type` 的资源池可能只存在于特定 region：如 `l20` 在 `demo-region-1`，而 `l20-16`（vGPU）可能没有该 region 的池（报 `Resource pool not found ... l20-16`），需换到有对应池的 region 或改用其它 gpu_type。

部署失败不影响服务本身，会以 warning 透出。也可事后单独部署：`bytedcli merlin deploy create --service-id <id> --region <配额region> --gpu-type <type> --instances 1`。

### 注意事项

- **占位/别名 target 会 404**：源 TCC 里指向代理/非 Bernard 服务的 target（GET 404）会被优雅跳过并计入 failed，不影响其它服务；生成的线上 TCC 里这些 target 保持原样不改写。
- **重复引用去重**：同一服务被多个 YAML 路径引用时只克隆一次。
- **线上 TCC 只创建草稿**：`--create-online-tcc` 生成配置后仍需按 TCC 流程发布/部署（`bytedcli tcc` 或前端）才真正生效。
- **conf 目录**：新 TCC 会自动匹配源配置所在目录（如 `/default`）在目标 namespace 下的同名目录，找不到则退回根目录。

---

## 单服务克隆 + 注入 checkpoint（service clone）

克隆**单个** Bernard 服务到新的 service_id，并可选地改写其 bootstrap 配置里的值（`CODANCE_BOOTSTRAP_CONFIG` 的 base64 YAML），常用于把一个新预分片的 checkpoint 指到 `downloads.joint_dit.src_merlin`。与 `clone-from-tcc`（按 TCC 克隆全部引用服务）不同，这里只克隆一个服务。

```bash
# 预览：GET 源服务、注入 bootstrap、打印 env / bootstrap 改动，不创建
bytedcli merlin deploy service clone \
  --from demo_dit_sp4 \
  --new-id demo_dit_v2_offline_sp4 \
  --set-bootstrap downloads.joint_dit.src_merlin=hdfs://harunawl/.../ckpt \
  --dry-run

# 执行克隆（需 --yes）
bytedcli merlin deploy service clone \
  --from demo_dit_sp4 --new-id demo_dit_v2_offline_sp4 \
  --set-bootstrap downloads.joint_dit.src_merlin=hdfs://harunawl/.../ckpt \
  --yes
```

关键参数：

| 参数                                 | 说明                                                                                 |
| ------------------------------------ | ------------------------------------------------------------------------------------ |
| `--from <service-id>`                | 源服务（必填）                                                                       |
| `--new-id <service-id>`              | 新服务 id（必填）                                                                    |
| `--new-psm <psm>`                    | 目标 PSM，默认继承源服务                                                             |
| `--set-bootstrap <dot.path>=<value>` | 改写 bootstrap YAML 的某个点路径（可重复），保留注释与格式                           |
| `--sd-tag <tag>`                     | `BERNARD_SD_TAGS.cluster`，默认取新 service_id                                       |
| `--bind-parent-id` / `--bind-path`   | 服务树挂载 `auto_bind_psm_meta`（同 psm 复用时通常可省略；报 error_code 466 时再补） |
| `--biz-tags <tags>`                  | 业务标签（2 或 3 级）                                                                |
| `--dry-run` / `--yes`                | 预览 / 执行                                                                          |

> `--set-bootstrap` 要求源服务 `configfile` 是形如 `{"CODANCE_BOOTSTRAP_CONFIG":"<base64 yaml>"}` 的 JSON；否则报 `MERLIN_CLONE_BOOTSTRAP_ERROR`。`BERNARD_MS_CLUSTER` 与 `BERNARD_SD_TAGS.cluster` 会自动跟随新 service_id 改写。

---

## Troubleshooting

| 现象                                              | 原因                                                             | 解决                                                                                                                                                                                                         |
| ------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 日志只有 banner                                   | 缺 `BERNARD_MULTI_MODELS` 等 env                                 | 补全环境变量，重建部署                                                                                                                                                                                       |
| `image is in status: building`                    | 构建中                                                           | 等 build_status=ok                                                                                                                                                                                           |
| `container_image is required`                     | custom-build 缺字段                                              | 设为 `""`                                                                                                                                                                                                    |
| Build failed                                      | load_path 是目录或绝对路径                                       | 改为相对文件路径                                                                                                                                                                                             |
| `Not enough GPU quota`                            | 配额不足                                                         | 换 region 或 gpu-type                                                                                                                                                                                        |
| `error_code 392` 业务线卡型 Quota 卡量超过阈值    | socket 部署漏带 `--is-socket`，被算进 GPU 配额；或业务线真的封顶 | 先 `deploy list` 看已有部署是否 `is_socket: true`，是则补 `--is-socket` + `--minipod-placement` / `--minipod-affinity-level` 重试；确实封顶才去缩容同业务线服务或找卡型 owner 抬阈值（换 region / 池子无效） |
| 部署后一直 NotReady                               | 模型加载中                                                       | 正常，等 5-7 分钟                                                                                                                                                                                            |
| clone 报 `error_code 466 should be mounted under` | 缺服务树挂载                                                     | 传 `--bind-parent-id` + `--bind-path`                                                                                                                                                                        |
| clone 业务标签 warning                            | 标签接口失败或标签级数不对                                       | 用 2/3 级 `--biz-tags`，服务已建可事后重试标签                                                                                                                                                               |
| 线上 TCC 报 `DirID should not be empty`           | 目标目录未解析                                                   | 确认 `--online-tcc-ns` 存在且有目录；命令会自动匹配源目录                                                                                                                                                    |
| 部署报 `error_code 342 Invalid Region`            | 用了展示地区（如 Demo-Region-Display）当部署 region              | 改用配额池 region（如 `demo-region-1`），从同 PSM 已有部署取                                                                                                                                                 |
| 部署报 `Resource pool not found ... l20-16`       | 该 region 无对应 gpu_type 的资源池                               | 换有该 gpu 池的 region，或改 gpu_type                                                                                                                                                                        |

---

## 关联技能

- `merlin-job-launch`：创建训练任务
- `merlin-recipe-eval-run`：运行评估
- `merlin-checkpoints`：Checkpoint 管理
