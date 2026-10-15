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

最小修复：通过已固定版本的官方 [disk-size 输入](https://github.com/ReactiveCircus/android-emulator-runner/blob/a421e43855164a8197daf9d8d40fe71c6996bb0d/action.yml) 将三个模拟器启动位置的数据分区设置为 2048M。官方 [源码](https://github.com/ReactiveCircus/android-emulator-runner/blob/a421e43855164a8197daf9d8d40fe71c6996bb0d/src/emulator-manager.ts) 将它写入 disk.dataPartition.size。假设：指定较小的专用测试分区后，原磁盘容量检查应通过并能完成同一套验收。待新运行核验；没有通过延长超时或跳过功能断言处理。

常规工作流将验证新版 Action 下的 JVM/Robolectric、Lint、三个 APK 构建及嵌入式 Hook / 恢复；Root 工作流仍保留手动触发，不能将常规通过写为 Root 已复跑。

本轮只维护测试工具；2026-10-07 真机测试包及其 APK 哈希保持原样。真机状态继续为 NOT RUN。
