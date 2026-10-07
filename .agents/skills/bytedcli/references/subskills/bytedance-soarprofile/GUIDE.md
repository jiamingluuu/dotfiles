# SoarProfile

Use this route when the user names SoarProfile or `bytedcli soarprofile`, or asks to profile a specific RISC-V server (currently an ORCA server), including time-bounded CPU load, PMU/process metrics, profiling data, or workload bottleneck analysis with the SoarProfile Agent. Generic profiling, performance, Benchmark, or Experiment intent that is not about a RISC-V server and does not name SoarProfile must stay with its normal owner.

Load the SoarProfile capability Skill before choosing commands:
https://skills.bytedance.net/skill/skills:skills.byted.org/soarprofile/public/soarprofile

## Bootstrap

1. Load the remote Skill above and select its raw capability or Agentic API path.
2. Install the official plugin if the `soarprofile` command is unavailable:

```bash
bytedcli self plugin install --name soarprofile
bytedcli self plugin doctor --name soarprofile
```

The official package is `@bytedance-dev/bytedcli-plugin-soarprofile` and requires bytedcli `>=0.115.0`.

3. Plugin upgrades are explicit; update from the latest dist-tag, then validate the installation:

```bash
bytedcli self plugin update --name soarprofile
bytedcli self plugin doctor --name soarprofile
```

4. Reuse bytedcli ByteCloud authentication. SoarProfile has no separate login and must never receive a manually copied JWT.
5. Use runtime help as the command contract, then prefer JSON output for Agent consumption:

```bash
bytedcli soarprofile --help
bytedcli soarprofile <family> --help
bytedcli --json soarprofile <family> <operation> [options]
```
