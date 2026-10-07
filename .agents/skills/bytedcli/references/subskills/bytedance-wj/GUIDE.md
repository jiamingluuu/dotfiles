---
name: bytedance-wj
description: "Operate WJ / ByteSurvey questionnaires on wj.bytedance.com via bytedcli: read q/v2 questionnaire URLs, generate answer templates, upload file-question assets, submit structured answers, and query or execute lottery draws. Use when tasks mention wj.bytedance.com/q/v2, ByteSurvey, WJ, 问卷, 答题, 上传问卷截图, response_id, or 抽奖."
---

# ByteDance WJ / ByteSurvey

Use `bytedcli wj` for WJ / ByteSurvey questionnaire workflows backed by
`https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/` URLs.

## Commands

```bash
# Read questions and generate an editable data.answerTemplate.
bytedcli --json wj read --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/'

# Upload a local file for upload-style questions, then put the returned URL into the answer file.
bytedcli --json wj upload --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/' --file ./screenshot.png --content-type image/png --yes

# Submit edited answers. Write operations require --yes.
bytedcli --json wj submit --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/' --answers-file ./answers.json --yes

# Submit and execute the lottery draw in one command when response_id is returned.
bytedcli --json wj submit --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/' --answers-file ./answers.json --draw --yes

# Query lottery metadata after submit.
bytedcli --json wj lottery get --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/' --response-id <response_id>

# Execute lottery draw after submit. Write operations require --yes.
bytedcli --json wj lottery execute --url 'https://wj.bytedance.com/q/v2/<task_id>/<unique_str>/<sign>/' --response-id <response_id> --yes
```

## Workflow

For answering, uploading, and lottery execution, read
[`references/questionnaire-workflow.md`](references/questionnaire-workflow.md). It is the source of
truth for the read-material -> answer-file -> submit -> lottery sequence and supported answer
shapes.

## Auth

Some questionnaires redirect to ByteDance SSO. Prepare a reusable session first:

```bash
bytedcli auth login --session --auto --yes
```

The CLI also tries Chrome/Vivaldi/Chromium WJ cookies when saved SSO cookies are not enough. If
`wj read` still returns `WJ_AUTH_REQUIRED`, open the questionnaire once in Chrome to finish WJ's SSO
authorization, then retry.

## Safety

- `wj upload`, `wj submit`, and `wj lottery execute` are write operations and require `--yes`.
- `wj submit --draw --yes` performs two write operations under one confirmation: submit answers,
  then execute lottery draw when the response contains `response_id`.
- Do not submit or draw on behalf of another user unless the user explicitly asked for that exact
  action.
