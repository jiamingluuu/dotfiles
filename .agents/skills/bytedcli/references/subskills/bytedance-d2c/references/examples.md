# D2C CLI examples

End-to-end examples for the bytedcli commands behind this namespace. All examples use placeholder ids and URLs.

Every capability here is either a bytedcli command or your own reasoning. See [capability-map.md](capability-map.md) for upstream provenance and the pinned revision.

## Check a segmentation task, then download its artifacts

```bash
# 1. Read current state
bytedcli --json d2c task get --task-id demo-task-0001

# 2. When status is completed, download the archive yourself
curl -L "<download_url from step 1>" -o demo-artifacts.tar.gz
tar -xzf demo-artifacts.tar.gz -C ./demo-artifacts --strip-components 1
```

A completed task responds like:

```json
{
  "status": "success",
  "data": {
    "task_id": "demo-task-0001",
    "kind": "visual-segmentation",
    "status": "completed",
    "terminal": true,
    "download_url": "https://example.invalid/artifacts/demo-task-0001.tar.gz",
    "message": null
  },
  "error": null
}
```

A task still in progress responds with `"status": "running"`, `"terminal": false` and a null `download_url`.

## Follow a running task

Re-read on an interval and stop as soon as `terminal` is true:

```bash
for _ in $(seq 1 20); do
  terminal=$(bytedcli --json d2c task get --task-id demo-task-0001 | jq -r '.data.terminal')
  [ "$terminal" = "true" ] && break
  sleep 30
done
bytedcli --json d2c task get --task-id demo-task-0001
```

## Check a render-screenshot task

```bash
bytedcli --json d2c task get --task-id demo-task-0002 --kind render-screenshot
```

## Read a Figma node's curated description

```bash
bytedcli --json d2c figma get-description \
  --figma-page-url https://www.figma.com/design/demoFileKey/demo-page \
  --figma-node-id 274-11320
```

A node without a curated description yet:

```json
{
  "status": "success",
  "data": {
    "figma_page_url": "https://www.figma.com/design/demoFileKey/demo-page",
    "figma_node_id": "274:11320",
    "found": false,
    "description": null,
    "updated_at": null
  },
  "error": null
}
```

Note `figma_node_id` is echoed in canonical `:` form even though `-` was passed.

## Pasting a URL straight from Figma

Query string and hash are stripped, so this is equivalent to the example above:

```bash
bytedcli --json d2c figma get-description \
  --figma-page-url 'https://www.figma.com/design/demoFileKey/demo-page?node-id=274-11320&t=abc' \
  --figma-node-id 274-11320
```
