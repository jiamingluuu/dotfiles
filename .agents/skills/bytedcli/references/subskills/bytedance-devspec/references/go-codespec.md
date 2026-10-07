# ByteDance Golang Code Specification

Verified source page: `https://devspec.bytedance.net/codespecs/bytedance_go`

Use this command for current machine-readable data:

```bash
bytedcli --json devspec guideline get --name bytedance_go --locale en
```

For a smaller rule index:

```bash
bytedcli --json devspec guideline get --name bytedance_go --locale en --summary
```

Known page facts from Browser/API verification:

- English title: `ByteDance Golang Code Specification`
- Chinese title: `字节跳动 Golang 代码规范`
- Unique name: `bytedance_go`
- Version: `1.0.1`
- Item count: `66`
- API endpoint: `/guideline/api/v1/guidelines/bytedance_go?lang=en|zh`
- Auth flow: ByteDance SSO OAuth2, then DevSpec callback `/guideline/api/v1/internal/sso_callback`

Severity mapping for agents:

- `required`: blocking requirement; treat violations as errors.
- `suggested`: recommended practice; treat violations as warnings.
- `optional`: contextual guidance; apply when the surrounding code makes it relevant.

First verified rule:

- Rule id: `byted_s_package_name_same_with_dir`
- Level: `required`
- Topic: Package naming
- Guidance: Package name should be the same as the directory name and should be short and meaningful. Test code may use a `_test` package.

## Scan Rules

The scan-rule hub supports language-filtered rule lists. Use:

```bash
bytedcli --json devspec scan-rule list --language Go
bytedcli --json devspec scan-rule list --language JavaScript
bytedcli --json devspec scan-rule list --language TypeScript --severity critical major
bytedcli --json devspec language list
```

Verified scan-rule endpoints:

- `/guideline/api/v3/rules`
- `/guideline/api/v3/languages`

Useful filters mirror the page UI: language, severity, category, analyzer, status, and rule-name search.

Language aliases for scan rules:

- Go: `go`, `golang`, common misspellings like `golnag`.
- Python: `python`, `py`, `py3`, common misspellings like `pyhton`.
- JavaScript: `javascript`, `js`, `node`, `nodejs`, `ecmascript`, common misspellings like `javascrpt`.
