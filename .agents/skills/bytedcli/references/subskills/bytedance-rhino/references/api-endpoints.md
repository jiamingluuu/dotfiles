# Rhino OpenAPI 速查

默认 `Domain: rhino_v2`，成功 envelope 通常为 `{"status_code":0,"msg":"success","data":...}`。

## Netflow

| 命令                   | Method | Path                                      | 参数                                               |
| ---------------------- | ------ | ----------------------------------------- | -------------------------------------------------- |
| `rhino netflow list`   | GET    | `/perf/api/v2/netflow/record/task/list`   | `page_num,page_size,is_global,psm,keyword,creator` |
| `rhino netflow get`    | GET    | `/perf/api/v2/netflow/record/task/detail` | `record_task_id,psm,is_global`                     |
| `rhino netflow delete` | GET    | `/perf/api/v2/netflow/record/task/delete` | `record_task_id,psm`                               |
| `rhino netflow create` | POST   | `/perf/api/v2/netflow/record/task/save`   | body + `is_global`                                 |

## Task

| 命令                    | Method | Path                                                 | 参数                                               |
| ----------------------- | ------ | ---------------------------------------------------- | -------------------------------------------------- |
| `rhino task list`       | GET    | `/perf/api/v2/task/list`                             | `page_num,page_size,is_global,psm,keyword,creator` |
| `rhino task get`        | GET    | `/perf/api/v2/task/detail`                           | `task_id,is_global`                                |
| `rhino task create`     | POST   | `/perf/api/v2/task/save`                             | body + `is_global`                                 |
| `rhino task execute`    | POST   | `/perf/api/v2/task/exec`                             | `{"task_id":456,...}`                              |
| `rhino task close`      | POST   | `/perf/api/v2/task/stop`                             | `{"task_id":456}`                                  |
| `rhino task qps update` | POST   | `/perf/api/v2/task/adjust_qps`                       | `{"task_id":456,"qps":500}`                        |
| `rhino task result list` | GET    | `/perf/api/v2/task/execute/result/list`              | `task_id,page_num,page_size,is_global`             |
| `rhino task result get` | GET    | `/perf/api/v2/task/execute/result/detail`            | `task_id,result_id,is_global`                      |

## PSM

| 命令                                      | Method | Path                                        | 参数                                                      |
| ----------------------------------------- | ------ | ------------------------------------------- | --------------------------------------------------------- |
| `rhino psm list`                          | GET    | `/perf/api/v2/psm/list`                     | `page_num,page_size,is_global,keyword`                    |
| `rhino psm switch update --enabled true`  | POST   | `/perf/api/v2/psm/switch/on` or `/batch_on` | `{"psm":"example.psm"}` or `{"psm_list":["example.psm"]}` |
| `rhino psm switch update --enabled false` | POST   | `/perf/api/v2/psm/switch/off`               | `{"psm":"example.psm"}`                                   |
