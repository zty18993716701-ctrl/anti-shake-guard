# 构建工具维护：Node.js 24

2026-10-15，针对三环境复测中 `setup-java v4` 弃用及 Node.js 20 强制迁移提醒，更新两个 GitHub 工作流的四类 Action。版本来自上游正式发布，并将标签解析到完整提交 SHA；应用 Java 17、LSPatch Java 21、SDK API 35 和场景断言均保留。

| Action | 新版 / 固定提交 | 官方说明 |
| --- | --- | --- |
| checkout | v7.0.1 / `3d3c42e5aac5ba805825da76410c181273ba90b1` | [固定版本 README](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/README.md) |
| setup-java | v6.1.0 / `b843ebf9b913146b38da2eaa7aeddf76074ae1ad` | [固定版本 README](https://github.com/actions/setup-java/blob/b843ebf9b913146b38da2eaa7aeddf76074ae1ad/README.md) |
| setup-android | v4.0.4 / `be39fa834029ff78f1a44aa3bb0819b8fc2bd8fd` | [固定版本定义](https://github.com/android-actions/setup-android/blob/be39fa834029ff78f1a44aa3bb0819b8fc2bd8fd/action.yml) |
| upload-artifact | v7.0.2 / `cf430e030ddbb5b0abf93d22962f4752f3646cd9` | [固定版本定义](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/action.yml) |

四份固定提交的 action.yml 均声明 node24。官方迁移要求 Actions runner 至少 v2.327.1；当前使用 GitHub 托管的 ubuntu-latest，实际兼容性以云端任务为准。checkout v7 对 pull_request_target / workflow_run 的 fork 代码获取更严格，本项目不使用这两个事件且保持 persist-credentials=false。Java 的 Maven 签名/凭据变化不涉及本项目的 Temurin 版本输入。SDK setup 默认命令行工具升级至 22.0，需实际构建确认。

## 本轮验证

首次执行：[38682826433](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38682826433)，提交 `4073447128d3d9ae5b93bf745cd1f837416dadc0`。构建、JVM/Robolectric、Lint、新版 Java/SDK 准备及产物上传成功；模拟器启动失败，功能断言未执行，整体 FAIL。两个 Action 弃用警告在该任务日志中未再出现。

直接错误：Emulator 37.2.12 报告创建 userdata 分区需要 7372.80 MB，而 runner 对应位置只有 7253.52 MB；进程已退出，Action 随后等到 300 秒超时。没有证据证明为应用或 Hook 回归。

第一次修复假设：通过官方 disk-size 输入设置 2048M，使较小测试分区通过容量检查。[第二轮 38687262227](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38687262227)，提交 `4d8ed4c47674a36d924203320c4fac00f164d99e`，配置日志确认已写入，但仍要求 7372.80 MB，可用 7253.42 MB，再次 FAIL。该假设被本轮证据否定，设置已撤回。

最终修复：APK 构建完成后停止 Gradle，记录并删除该一次性 GitHub Linux runner 的 `/home/runner/.gradle/caches`，记录空闲容量，再启动模拟器。该缓存只用于此前构建，后面的脚本不再运行 Gradle；APK、JUnit 和 Lint 产物留在项目 build 目录，不删除。常规和 Root 工作流均采用相同顺序。保留原启动超时和全部功能断言。

## 成功复测与证据

第三轮 [38688294231](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38688294231)，提交 `82eb0067b2eb14d1b2c086951f8a4f627040317f`，job `116268116583`，整体 PASS。任务记录释放 637M Gradle 缓存，安装模拟器前 df 显示根卷可用约 13G；之后模拟器实际启动成功。前两轮失败保留，不将它们改写为通过。

| 验证项 | 结果 |
| --- | --- |
| 新版 checkout、Java 17 / 21、SDK 准备 | PASS |
| JVM/Robolectric、Lint、三个原始 APK 构建 | PASS |
| 无 Hook 基线 | 8/8 PASS |
| 未加载模块必须失败的负例检查 | PASS，脚本要求特定失败原因 |
| LSPatch 真实 Hook | 三轮各 8/8 PASS |
| 移除补丁、恢复原始 APK | 基线 8/8 PASS |
| 新版产物上传及任务收尾 | PASS |

共 40 次黑盒场景断言，复用 8 个场景；不是 40 种测试。保护组运动事件为 0 且不跳转，对照组仍因运动跳转；两组保留 123 lux 光线事件。靶场自动关闭/安全返回与正常页面不误操作通过。基线中广告由脚本手动关闭，不算自动关闭。

- [原始行为 JSONL](evidence/ci-node24-82eb006.jsonl)：从该任务日志提取 40 条断言及 5 条汇总；仅新增按固定脚本顺序标注的 phase 字段。
- [私有产物](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38688294231/artifacts/11952165688)：APK、JUnit、Lint 和设备证据，保留至 2026-10-22；API 报告 ZIP SHA-256 为 `3e4a89c638bb906b6f72069c4c385bf3a7e5c2d335369a9c613eff5555612131`，本轮未下载解压核验该 ZIP。
- 本轮原有两类 Action 弃用提示不再出现。SDK 命令行工具 22.0 另外输出 sdkmanager 弃用提醒，仍需在后续独立维护中处理；不宣称所有警告归零。既有 Lint 原型提醒也未隐藏。

Root 工作流已同步 Action 和缓存释放配置，仍保留手动触发，本轮未重新运行其 Root 生命周期测试。2026-10-01 的三环境 Root 结果仅对应其原始固定提交，不能移用于新的构建环境。

本轮只维护测试工具；2026-10-07 真机测试包及其 APK 哈希保持原样。真机状态继续为 NOT RUN。
