请帮我生成一份过去一周的 Git 提交周报，Git 工作目录是：/disk2/zhangsunwen/EvalGen

执行步骤：

**第一步 调用call_git_agent 获取过去 14 天的提交及其差异**：
   请使用自然语言查询，例如：
   query: "使用git工具，把我查看一下/disk2/zhangsunwen/EvalGen最近7天的提交以及代码差异，git show一下，访问完整差异内容"

根据返回的 diff 内容，分析本次提交：
- 新增功能：新增了哪些文件、函数、类？添加了什么逻辑？
- 修改内容：修改了哪些现有逻辑？参数、返回值、调用方式有什么变化？
- 修复问题：修复了什么 bug？错误处理、边界条件有什么改进？
- 重构部分：代码结构、命名、模块拆分有什么调整？

每项分析要具体，说明修改了哪些文件、添加/删除了什么代码。

**第二步：写入分析文档**
将分析结果写入文件：workspace/weekly_commits.md
格式：
### 提交 {hash} | {date} | {author}
- **提交信息**：{原始message}
- **变更文件**：{文件列表，含增删行数}
- **详细分析**：
  - 新增功能：xxx
  - 修改内容：xxx
  - 修复问题：xxx
  - 重构部分：xxx

**第三步：调用 Report Agent 生成周报**
调用 call_report_agent：
   query: "请调用工具获取报告模板并读取提交分析记录 workspace/weekly_commits.md，按照模板格式生成一份完整的技术周报，保存到 workspace/weekly_report.md"

**第四步：确认完成**
告诉我周报已生成，并显示保存路径。

开始执行。