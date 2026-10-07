# Workflow Schema

## Core model

- `schema_json` is the workflow draft graph.
- Root keys used by the CLI:
  - `nodes`: node list
  - `edges`: execution dependencies
  - `versions`: optional schema markers / feature flags

Example node:

```json
{
  "id": "155172",
  "type": "3",
  "meta": { "position": { "x": 3400, "y": 315.4 } },
  "data": {
    "nodeMeta": { "title": "ShopEmailCheck" },
    "inputs": { "inputParameters": [], "llmParam": [] },
    "outputs": [],
    "version": "3"
  }
}
```

Example edge:

```json
{
  "sourceNodeID": "155172",
  "targetNodeID": "900001"
}
```

## Important node kinds

- `1`: Start
- `2`: End
- `3`: LLM
- `5`: Code
- `8`: Condition
- `13`: Output
- `21`: Loop
- `28`: Batch
- `30`: Input
- `45`: HTTP request
- `58`: JSON serialization
- `61`: RPC request
- `9`: Legacy SubWorkflow

## Data references

Node inputs usually reference prior outputs like this:

```json
{
  "type": "ref",
  "content": {
    "source": "block-output",
    "blockID": "155172",
    "name": "result"
  },
  "rawMeta": { "type": 1 }
}
```

Observed `rawMeta.type` mapping:

- `1`: string
- `2`: integer
- `3`: boolean
- `4`: float
- `6`: object
- `99`: list

## End node behavior

- End does not infer outputs from graph edges.
- End returns whatever is declared in `data.inputs.inputParameters`.
- Top-level End outputs may be scalar or object.
- Object outputs use `input.type = object`, `value.type = object_ref`, and nested `schema[]` field mappings.

## Mutation rules used by `bytedcli aicolate workflow apply`

- Preserve unknown node fields.
- Generate new node ids in the `100000-199999` range.
- Treat `edges` as execution ordering, not as the only data-flow source.
- When inserting a node before End, rewire predecessor edges so End executes after the new node.
- Update End mappings explicitly; a new node output does nothing until End references it or a downstream node consumes it.

## Supported ops

Low-level ops:

- `add_node`
- `remove_node`
- `connect`
- `disconnect`
- `set_node_title`
- `move_node`
- `set_input_literal`
- `set_input_ref`
- `set_output_schema`
- `replace_end_mapping`
- `append_end_field_from_node`

High-level helpers:

- `insert_llm_before_end`
- `clone_node_shape_from_existing`

## CLI usage

Preview first:

```bash
bytedcli aicolate workflow apply --id <wfId> --space <spaceId> --ops-file <opsFile.json> --dry-run
```

Save only after reviewing the diff:

```bash
bytedcli aicolate workflow apply --id <wfId> --space <spaceId> --ops-file <opsFile.json> --save
```

`ops-example.json` in this references folder is documentation-only. In real runs, pass a file path that exists in your current local filesystem.

When you intentionally want full-schema replacement instead of structured ops:

```bash
bytedcli aicolate workflow export --id <wfId> --space <spaceId> --schema > dag.json
bytedcli aicolate workflow apply --id <wfId> --space <spaceId> --schema-file dag.json --dry-run
```

For a human-readable YAML representation of the same DAG schema:

```bash
bytedcli aicolate workflow export --id <wfId> --space <spaceId> --format yaml --output dag.yaml
```

Use `--drop-ui` when UI-only coordinates and icon URLs are not needed. `--schema`
is the raw JSON mode and cannot be combined with `--format yaml`.

When the exported workflow is intended for the FireFlow runtime, use the runtime
conversion instead of native YAML:

```bash
bytedcli aicolate workflow export --id <wfId> --space <spaceId> \
  --format runtime-yaml --output ./fireflow-bundle
```

Knowledge Retriever Python/IDL generation is an IPR-specific extension of this
export path. It is not emitted by JSON/native YAML export, is not consumed by
runtime import, and must not be presented as a generic export of knowledge-base
content or a portable Knowledge Retriever implementation.

The bundle contains a FireFlow-compatible `workflow.yaml`, prompt files under
`prompts/`, executable Knowledge Retriever clients under
`knowledge/knowledge_retrieval_<nodeId>.py` for top-level nodes and
`knowledge/knowledge_retrieval_<ownerNodeId>_<nodeId>.py` for nested blocks,
shared Euler Thrift resources under
`knowledge/idl/`, and a `manifest.json`. The Python client calls `Retrieve` over
buffered transport using fixed IPR service routing (for example,
`sd://demo.ecom.mixrag?idc=<idc>&cluster=default`); it accepts `Query`/`query`,
fixes MixRAG `USER_ID` to OpenCoze's experiment-routing value `1`, and writes all
RPC and node settings as editable top-level constants rather than reading local
business configuration.
Dataset ids come from the Knowledge Retriever node. Since the canvas does not
expose the MixRAG `rag_strategy_id`, the generated per-dataset map contains
explicit `None` placeholders. Sidecars are emitted for top-level nodes and
blocks nested inside Batch nodes; they do not modify the runtime node schema or
manifest and are not invoked by FireFlow automatically. Execution requires
`bytedeuler~=2.0`, ByteDance Service Discovery, and the complete `knowledge/idl`
directory including `__init__.py`.
Aicolate End nodes are not emitted: routes entering them resolve to the FireFlow
terminals `approve`, `reject`, or `unknown`, which the executor synthesizes.
Referenced SubWorkflow nodes are recursively exported under
`subworkflows/<workflowId>/` by default; pass `--no-subworkflows` to disable
recursion.

Every non-native node is converted to a `type: code` node so the bundle stays
runnable and self-describing:

- HTTP nodes become executable `code` using the Python standard library
  (`urllib`) with JSON response handling. Authentication values are not
  embedded as credentials; inject them in the runtime when required.
- RPC, Batch, SubWorkflow, and any unknown node become non-executing `code`
  adapters: their sources return `adapter_required` instead of running, and the
  reasons are recorded in manifest warnings because their orchestration is
  runtime-specific.
- HTTP sources keep an `AICOLATE_NODE_TYPE = 'http'` marker plus editable
  `CONFIG`, but no original-node snapshot. RPC, Batch, SubWorkflow, and unknown
  non-executing adapters additionally carry `AICOLATE_METADATA`, allowing import
  to restore their original payload and outgoing edge ports without losing data.
- Natural Code, HTTP, IfElse, and Prompt nodes use editable `input_schema`,
  `output_schema`, `on_error`, and Prompt `parameters` fields instead of
  `AICOLATE_METADATA`. These fields preserve input/output types, vision inputs,
  LLM parameters, timeout/retry settings, and Condition operand types;
  `platform_id` provides stable cross-node reference remapping without storing
  a node snapshot, including references embedded as
  `{{block_output_<id>.<output>}}`. Import uses the current YAML values rather
  than an older native-node snapshot.
- The first runtime node follows the target of the AICOLATE Start edge. A
  missing or invalid Start edge is reported as a warning rather than silently
  treated as a valid entry point.
- Async AICOLATE code without `await` is normalized to synchronous
  `def main(inputs: dict)` and removes `Args` / `Output` annotations.

To go the other way, `workflow import --file <workflow.yaml | bundleDir> --format runtime-yaml`
rebuilds an AICOLATE schema from a runtime bundle. Import currently requires the
explicit `--format runtime-yaml` flag. Add `--output <path>` to write the schema
JSON, or `--save --id <wfId> --space <spaceId>` to persist it to an existing
workflow. To create a new workflow under a project, use
`--space <spaceId> --project-id <projectId>`; the name defaults to `workflow.yaml`
`name` with a millisecond timestamp suffix to avoid collisions. Explicit
`--name` is used as-is, and `--desc` sets the description. Import reads only
`workflow.yaml` and `prompts/*.yaml`; `knowledge/*.py` and `knowledge/idl/*` are
not consumed during import. Natural nodes use their current YAML fields, while
non-natural adapters restore their original payload from metadata embedded in
the adapter source.
Routes and prompt definitions come from the YAML files. Code sources are restored
to the AICOLATE executor contract
(`async def main(args: Args) -> Output` with `params = args.params`). HTTP adapter
markers and `CONFIG` are restored to a native AICOLATE HTTP node (`type: "45"`)
instead of remaining a Code node. The imported End node uses the executor-required
id `900001` and returns the last runtime node's outputs through
`data.inputs.inputParameters`.
