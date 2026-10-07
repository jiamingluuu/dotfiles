# eLearning workflow

Run `course get` first. Use the returned lesson IDs when a course contains more than one video or exam.

`course start` is a write operation and requires `--yes`. It waits for each video's real remaining duration, reports incremental online time, and skips lessons already completed. Never describe it as fast-forwarding or bypassing required learning time.

`exam get` can create or resume an answering record, so it requires `--yes`. Save `data.answerTemplate` from the JSON output into a file. Fill each answer with option labels: a single choice uses `["B"]`; a multiple choice can use `["A", "C"]`.

Use `exam update` to save answers without submitting. Use `exam submit` only after the user has reviewed the complete answer file. Both commands require `--yes`. Answer files are tied to the active `record_id` and `record_version`; rerun `exam get` when a record becomes stale.

After successful completion, inspect the live eLearning page. If it offers a lottery, tell the user to draw manually. Do not invent or call a lottery endpoint.
