# Magpie Bridge (鹊桥)

这是 bytedcli 根路由中的精简入口；完整 Magpie 命令契约以 `bytedcli magpie --help` 为准。

Use this route when the user asks about JSB methods, JSB creation or iteration, JSB parameters or response schemas, Lark iteration groups for JSB, pulling JSB code templates, or authenticating with Magpie Bridge.

## Bootstrap

```bash
# bytedcli prepares the magpie runtime automatically on first use
bytedcli magpie --help

# Magpie reuses bytedcli's ByteCloud session; log in only when needed
bytedcli auth status
bytedcli auth login
```

## Common commands

```bash
# List JSB methods for a host
bytedcli magpie jsb list --host tiktok

# Create a new JSB method
bytedcli magpie jsb create

# Iterate an existing JSB method (add/remove params)
bytedcli magpie jsb iterate --name x.myMethod --host tiktok

# Open the Lark iteration group for a JSB
bytedcli magpie jsb open-group --name x.myMethod --host tiktok

# Pull Anycode code template to local project
bytedcli magpie jsb pull-code --name x.myMethod --host tiktok --dir ./project
```

## Notes

- Full support: overseas hosts (TikTok, TikTok Lite, etc.)
- Partial support: domestic hosts (Douyin, etc.) — under active development
- No separate Magpie login is required when invoked through bytedcli
- Run `bytedcli magpie <command> --help` before any non-trivial invocation
