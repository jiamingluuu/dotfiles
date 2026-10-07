---
name: bytedance-elearning
description: "Operate ByteDance eLearning courses through bytedcli: inspect course lessons, complete video learning for the real remaining duration, read exam questions, save answers, and submit exams. Use when users provide elearning.larkoffice.com course URLs or ask to 学习课程、读取培训题目、答题、提交考试. Lottery draws are not automated and must be completed manually on the page."
---

# ByteDance eLearning

Use `bytedcli elearning` for course learning and exams. Read `references/workflow.md` before running a learning or exam write flow.

```bash
bytedcli --json elearning course get --url 'https://elearning.larkoffice.com/student/course-detail/demo-course-id'
bytedcli --json elearning course start --url 'https://elearning.larkoffice.com/student/course-detail/demo-course-id' --yes
bytedcli --json elearning exam get --url 'https://elearning.larkoffice.com/student/course-detail/demo-course-id' --yes
bytedcli --json elearning exam update --answers-file ./answers.json --yes
bytedcli --json elearning exam submit --answers-file ./answers.json --yes
```

Authentication reuses the browser session for `elearning.larkoffice.com` and `exam.larkoffice.com`. If authentication fails, open both sites in Chrome and finish login, then retry.

Lottery draws are not supported by this skill. After the course or exam finishes, tell the user to return to the eLearning page and draw manually if the page offers a lottery.
