# WJ Questionnaire Workflow

Use this reference when the user wants to answer a WJ questionnaire, especially when the prompt says
to read linked material before answering.

## Read

1. Read the questionnaire:

```bash
bytedcli --json wj read --url '<wj q/v2 url>'
```

2. Inspect `data.questionnaire.formConfigs[].questions[]` and `data.answerTemplate`.
   The template may include fresh `server_time` and `rnd`; keep them in the file. The CLI uses
   these fields to generate the WJ submit `body_sign`.
3. If the questionnaire description or a question contains a document link, read that document
   before choosing answers. For Lark wiki/docx links, use:

```bash
lark-cli docs +fetch --as user --doc '<doc or wiki url>'
```

Completion criterion: every required question has a selected answer justified by either the
questionnaire content, linked material, or the user's explicit preference.

## Answer File

Start from `data.answerTemplate`, then fill `answers` using question ids.

Supported structured answers:

```json
{
  "answers": {
    "single_question_id": { "option": "option key/id/content" },
    "multi_question_id": { "options": ["option key/id/content"] },
    "rating_question_id": 10,
    "text_question_id": "text answer",
    "upload_question_id": ["https://data.bytedance.net/survey/oapi/v1/upload_files/proxy/..."],
    "non_score_single_question_id": {
      "option": "option key/id/content",
      "text": "optional follow-up text"
    }
  }
}
```

Question type mapping:

- `2` single choice: use `option`.
- `3` multi choice: use `option` or `options`.
- `4` rating / NPS: use a number/string or `{ "degree": 10 }`.
- `8` long text: use a string or `{ "text": "..." }`.
- `25` upload: use an array of uploaded file URLs.
- `28`, `29`, `30` non-score choice: use `option` or `options`; add `text` when the option asks for
  extra feedback.

For an unsupported type, use a raw backend payload:

```json
{
  "answers": {
    "question_id": {
      "raw": {
        "type": 99,
        "uuid": "question-uuid"
      }
    }
  }
}
```

## Upload

For upload-style questions, upload the file first:

```bash
bytedcli --json wj upload --url '<wj q/v2 url>' --file ./screenshot.png --content-type image/png --yes
```

Put the returned `data.url` into that question's answer array.

## Submit And Lottery

Submit with explicit confirmation:

```bash
bytedcli --json wj submit --url '<wj q/v2 url>' --answers-file ./answers.json --yes
```

If the user asked for lottery execution, or the questionnaire advertises a prize and the user asked
to complete the whole flow:

```bash
bytedcli --json wj submit --url '<wj q/v2 url>' --answers-file ./answers.json --draw --yes
```

or, after a previous submit:

```bash
bytedcli --json wj lottery get --url '<wj q/v2 url>' --response-id <response_id>
bytedcli --json wj lottery execute --url '<wj q/v2 url>' --response-id <response_id> --yes
```

Completion criterion: submit returns `status: "success"` with `data.responseId`. When lottery is
requested via `wj submit --draw`, record either `data.drawResult.win` or the structured
`data.drawError`. When lottery is executed separately, record `status: "success"` and `data.win`.

## Auth

`wj` automatically combines saved SSO session cookies and Chrome/Vivaldi/Chromium cookies for
`wj.bytedance.com`, `bytedance.com`, and `sso.bytedance.com`.

If `wj read` still returns `WJ_AUTH_REQUIRED`:

1. Run `bytedcli auth login --session --auto --yes`.
2. Open the questionnaire once in Chrome and let WJ finish its SSO callback. The CLI reads matching
   Chrome/Vivaldi/Chromium cookies on the next run; do not copy cookie values by hand.
3. Retry `wj read`.

Never print cookie values in logs, terminal output, answer files, or skill docs.
