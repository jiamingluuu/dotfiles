# Safe Domain / 内容安全

`bytedance-safe` skill 的完整说明已经迁移到 safecli 项目维护，本仓只保留 bytedcli root skill 的跳转入口。

Source of truth:
https://skills.bytedance.net/skill/skills:skills.byted.org/douyin/governance_and_experience/bytedance-safe

## 使用方式

1. 先加载上面的远程 skill，按远程 skill 的最新说明选择具体 `safe ...` 子命令。
2. Safe 命令由 npm 分发的 `safecli` 插件提供；如果本机还没有安装，先执行：

```bash
bytedcli self plugin install --name safecli
bytedcli self plugin doctor --name safecli
```

3. 需要最新命令树或参数时，以插件运行时 help 为准：

```bash
bytedcli safe --help
bytedcli safe <sub-domain> --help
```
