# 数据帝国：千万并发的战争

以 Java 后端工程师的视角，在小说中理解高并发与大数据。现有十三章正文，覆盖当前阶段的学习主线。第十四章仅保留可选进阶设想，尚无正文。

- [开始阅读](https://wupzl.github.io/data-empire-reader/)
- [交互实验室](https://wupzl.github.io/data-empire-reader/practice.html)
- [内容整理与技术校正](EDITORIAL.md)
- [学习书架](https://wupzl.github.io/)

支持手机与桌面阅读、全书正文搜索、章节与章内目录、上下章切换、阅读位置记忆、字号调整、深浅色模式、代码高亮与复制。无需账号、后端或数据库。

## 本机预览

使用 Python 3.10+ 和 Node.js 18+。Node 仅在构建时用于将公式转成 MathML，不是读者设备的依赖。

```bash
python -m pip install -r requirements.txt
python build.py
python -m http.server 4175 --directory docs
```

访问 http://localhost:4175/ 。正文、脚本、代码高亮、公式和技术架构示意均为本地静态资源，外部场景插图失败时显示提示。

## 内容维护与连载

1. 编辑 `chapters/01.md` 至 `13.md`；完整原稿保存在 `source/data-empire-original.md`，不要覆盖。续写原稿另存于 `source/data-empire-continuation-original.md`，同样保留原始字节。第十三章原稿另存于 `source/data-empire-chapter13-original.md`。
2. 新章节发布时新增 `chapters/14.md`，向 `book.json` 的 `chapters` 列表添加标题和主题，并更新 `next` 预告。保留下一章“待续”标记，不生成空正文页。
3. 运行 `python build.py`，检查生成页面后，将章节、配置和 `docs/` 一起提交。导航、章节数量、搜索索引随构建更新。
4. 技术更正与新增教学内容记录到 `EDITORIAL.md`。交互实验位于 `assets/labs.js`，面试题卡位于 `assets/quizzes.js`。

## 交互实验

19 个实验全部在浏览器中计算：利特尔法则、库存原子性、消息积压、令牌桶、深分页、分片路由、MapReduce WordCount、数据倾斜、Watermark、Kafka Lag、API 容量规划、数据口径去重、Granule 裁剪、分析查询资源、单位请求成本、数据库库存竞争、金丝雀流量阶段、故障演练检查、SLO 错误预算与 Burn Rate。支持修改参数、逐步执行或重置，并说明适用条件。

另有十二组共 112 道面试题卡，可翻页并展开参考答案。原稿可见问题保留，缺失题卡与答案按各章主题补充并明确标注。

这些是教学模拟，不连接实际 Redis、Kafka、Flink 或 Java 服务。原文的监控数值和验收报告为虚构场景，不能当作实测证据。

## 验证

模型与边界检查：

```bash
node tests/models.cjs
```

完整浏览器验证（验证依赖独立于站点构建）：

```bash
python -m pip install playwright
python -m playwright install chromium
python verify.py
```

`verify.py` 使用本地文件拦截运行页面，不需要另外启动服务器。检查链接、锚点、原稿完整性、390/768/1440px 布局、实验、题卡、搜索、复制、主题、字号与进度恢复，截图输出到忽略的 `test-results/`。

## 发布

GitHub Pages 使用 `main` 分支的 `/docs` 目录。内部资源使用相对路径，适配仓库子路径。学习书架和切换菜单使用站点根路径，面向 `wupzl.github.io` 部署。

## 隐私与许可

进度、字号、主题只保存在当前浏览器，不跨设备同步。没有统计脚本。外部插图仍可能请求其原始图片服务。KaTeX 上游许可证见 `vendor/KaTeX-LICENSE.txt`；原创正文和项目整体尚未另行指定开源许可证。


项目切换菜单已接入 [Agent 帝国：代码审判者](https://wupzl.github.io/coding-agent-reader/)，九章小说式 Coding Agent 工程阅读。


项目切换菜单已接入 [面试官的审判](https://wupzl.github.io/interview-proof-reader/)，七章技术面试小说与七组本地训练，第八章待续。


项目切换菜单已接入 [LangChain 帝国](https://wupzl.github.io/langchain-empire-reader/)，五章正文，第六章待续。
