# 内容整理与技术校正

本项目是一部持续连载的小说式技术读物。现有十二章正文；第十三章《永不崩溃的防线——性能回归、灰度发布与混沌工程》仅有原稿预告，尚未发布。

## 原稿与维护入口

`source/data-empire-original.md` 完整保存用户提供的原稿，不覆盖、不补写结局。`chapters/01.md` 至 `12.md` 为整理后的维护版本。日常修改章节后运行 `python build.py`；不必重新导入原稿。

保留故事、代码、技术论证、现有章末预告与图片来源。清除独立的“下一章。”对话残留、复制的站点 favicon 徽标；修复标题层级、公式转义和复制出的交互控件文本。技术架构示意保留为本地正文代码块，不依赖远程图片服务。外部场景插图保留原链接、来源和失败提示。

## 按章节校正与澄清

| 章节 | 整理与技术说明 |
| --- | --- |
| 1 | 在阅读提示中明确利特尔法则的稳态条件与统计边界，区分在途请求数与线程数；补全可调 QPS、平均响应时间的交互。 |
| 2 | 明确 Lua 原子性是命令不被穿插，不代表错误回滚或跨系统事务；重建非原子库存扣减与原子检查扣减的逐步对比；令牌桶明确为手动补充模型。 |
| 3 | 深分页显示 OFFSET 加页大小的处理量；游标读取页大小之外仍有索引定位等成本，不将记录数称为实测耗时。分片使用大整数运算，避免 JavaScript 大 ID 精度丢失。 |
| 4 | 明确热点 80% 时热点 Reducer 为 82%、其余各 2% 的前提：剩余记录分配给全部十个 Reducer；WordCount 使用空白分词、区分大小写。 |
| 5 | 提示 Spark 并非要求全部数据驻留内存；保留执行计划与磁盘溢写讨论。 |
| 6 | Watermark 教学模型明确秒级近似、单输入和零 allowed lateness；按窗口关闭判断 [0,10) 窗口是否接受后到事件，避免把一切早于 Watermark 的事件都当作必须丢弃。 |
| 7 | Kafka Lag 已为零时清空时间为零；有积压且消费能力不高于生产速率时显示无法清空，不输出负时间或除零。 |
| 8 | API 容量公式向上取整，单实例吞吐与负载比例不得为零；保留虚构验收报告的说明，末章导航标注待续。 |

上述说明用于限定模型的适用条件，不声称完成真实分布式系统压测。正文中的 Java、SQL、Lua 与流处理代码为讲解片段，本网站不在浏览器内执行这些服务端代码。

## 面试题卡补充

原稿复制结果只留下每组当前可见的一道题，其他题卡与多数答案缺失。保留十一组原问题，并依据各章主题补充为 102 道可翻页、可展开答案的题卡；题卡中标注补充来源，不将补充内容冒充原稿。

## 官方参考

- [Redis Lua 原子执行语义](https://redis.io/docs/latest/develop/programmability/eval-intro/)
- [Redis Lua 错误与回滚说明](https://redis.io/docs/latest/develop/programmability/redis-lua-api/)
- [MySQL LIMIT 优化](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)
- [Flink Watermark 生成、多输入与空闲输入](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/event-time/generating_watermarks/)
- [Flink 窗口生命周期与迟到数据](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/operators/windows/)
- [Spark RDD 缓存与持久化](https://spark.apache.org/docs/latest/rdd-programming-guide.html)

## 阅读与隐私

无需账号。阅读位置、字号、主题只保存在当前浏览器，不跨设备同步。全文搜索、公式、代码高亮、交互脚本均使用本地静态资源。只有保留的外部场景插图可能向图片服务发起网络请求；失败不影响正文。

界面与阅读功能沿用同一作者的 PyTorch 阅读项目。KaTeX 的上游许可证保存在 `vendor/KaTeX-LICENSE.txt`。没有为原创正文或项目整体另行指定开源许可证。

## 阅读排版修订

补充第三章原稿缺失的 B+ 树概念图，明确聚簇与二级索引叶子内容；将行列存储改为对照表与布局示例。统一改善代码、公式、表格与段落层级，长代码保留缩进并支持键盘滚动。

## 第四至第八章结构化修订

第四章将文件分块与副本放置分成两个层次，补充 Hadoop 分工、HDFS 读取步骤、Shuffle 流程和 YARN 层次；第五章整理 SQL 计划演化与 Broadcast Join。第六至八章同步重排窗口对比、实时链路、背压方向、执行资源、广播路径和面试节奏，监控与容量指标改为有明确表头的表格，清除复制残留的图表刻度和 favicon 徽标。图解使用本地 HTML/CSS，移动端按步骤阅读。保留小说叙事和完整原稿。

## 第九至第十二章续写整理（2026-10-24）

续写原稿完整保存为 `source/data-empire-continuation-original.md`，SHA-256 记录在 `book.json`；原有八章原稿继续保留。第八章入口改为第九章已发布，首页展示十二章及第十三章待续，延续现有纯白、米白、深色主题。

- 第九章：修复被压成一行的 PySpark 汇总代码，并给出已初始化 SparkSession 与业务时区前提；重排数仓分层、维度关系、湖仓层次与实时/历史双路径。补齐重复支付、去重与退款口径交互，明确 ¥400、¥300、¥270 的区别。
- 第十章：补齐行列布局与 MergeTree 合并图解；明确普通 MergeTree 不强制主键唯一，增量物化视图需要另外处理历史回补、修改与撤销。Granule 扫描数量由读者指定；查询资源场景为人工赋值示意，不是数据库性能预测或产品基准。
- 第十一章：成本、分层存储与负载表现改为表格；原稿残留曲线坐标无法还原分类金额，不据此编造数据。补齐单位成本计算，拒绝零请求量。保留正确的线程池先入队再扩至最大线程数的调度说明。
- 第十二章：并发库存改为可逐步操作的 SQL 模型；同时说明 CHECK 约束可能拒绝负库存，不声称所有数据库都会产生同一结果。核心事务与异步任务分开展示，保留幂等、Outbox 与可恢复预占的边界。

本次新增五个交互实验，并按四章各十题补齐缺失的面试题卡及参考回答。补充题卡注明来源范围。第十二章是工程蓝图，仓库不包含可直接运行的完整 Spring Boot 服务，也没有声称执行过分布式压测；Compose、Deployment、k6 均为上下文中的配置或脚本示例。

技术语义参考：[MergeTree](https://clickhouse.com/docs/reference/engines/table-engines/mergetree-family/mergetree)、[增量物化视图](https://clickhouse.com/docs/concepts/features/materialized-views/incremental-materialized-view)、[Java 21 ThreadPoolExecutor](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html)、[Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)。
