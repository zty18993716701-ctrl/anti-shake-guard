# 更新后 Root / Vector 复测与崩溃采集

## 本轮范围 / Scope

2026-10-16，复测当前模块与更新后的 CI 工具，不同时升级框架。继续固定 Magisk 30.7、Vector 2.2 / 3080 Release、API 35 google_apis x86_64；Root runner 固定 ubuntu-24.04，避免 ubuntu-latest 的后续系统迁移引入额外变量。三个全新独立环境分别完成未配置、启用、内核重启保持、移除作用域、恢复作用域和停用六阶段，每阶段仍为 8 项断言。不是 Root 环境下的 100 轮压力测试，也不是物理设备或商业广告 App 验证。

本轮不修改 APK、传感器策略、作用域、权限或广告关闭规则。仅在一次性模拟器的三个自建测试包内触发受控崩溃；不对用户手机或真实 App 执行这些命令。

## 采集内容与通过条件

每个功能阶段运行期间保留无 tag 过滤的 `logcat -b all` 连续流；开始、结束均写入随机唯一标记，并确认两端标记实际进入本地流。标记缺失、流中断、关键命令非零退出、必要快照为空，都会使采集不完整并使测试失败。功能错误与采集错误同时发生时保留原始功能错误，不由日志收尾覆盖。

每段另外保存：

- crash 缓冲原文及全缓冲快照（不再只保留 AndroidRuntime / Vector 标签）；
- 完整 DropBox 文本快照、三个测试包的进程退出记录、kernel dmesg 与 boot_id；
- `/data/tombstones` 原文件及拉取结果；没有新原生崩溃时允许目录没有文件，但不允许拉取命令失败被忽略；
- `capture.json`：覆盖标记、各命令退出码/大小、采集完整性与操作成功状态。

两次真正重启分别在重启前与重启后采集快照，并以不同 boot_id 验证重启。重启时 ADB 不可用，不能宣称该间隙存在不中断的 ADB 流；重启后补采可用的本次启动缓冲。采集完成表示本轮限定的命令、标记和原始文件通过校验，不保证设备从未丢弃任何系统日志，也不等于覆盖硬件掉电等所有故障。

## 正例校准与异常判定

安装本轮 APK 后，先在独立校准段执行：

1. 对模块首页执行 Android 官方 `am crash --user 0`，必须观察到对应包的 `shell-induced crash` 与框架调用栈。异常日志到达后清理可能阻塞的崩溃对话框，不把强制清理当作自然退出证明。[Android 15 shell 实现](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-15.0.0_r1/services/core/java/com/android/server/am/ActivityManagerShellCommand.java)
2. 对未保护的 control 靶场进程发送 SIGABRT，必须在 crash 缓冲看到该进程，并在拉取的 tombstone 中找到该包及 `backtrace:`。

上述预期崩溃与产品功能段分开记录，不从原始日志中删除。功能段仅检查本段 START/END 之间的测试包 Java 崩溃、原生崩溃及 ANR；旧校准记录不会被误算为新产品故障。DropBox、退出历史和 tombstone 可能保留之前的校准事件，需结合段标记、包名、PID 和 boot_id 阅读。

本地新增采集回归使用真实子进程读写测试日志，但在 ADB 边界使用假程序；不冒充 Android 崩溃正例。15 项现有/新增脚本回归通过。真实 Java / 原生校准与 Root 行为仍须云端通过，当前未记录 PASS。

## 执行记录

待云端运行。此次提交使用限定消息、main 分支和采集器路径的一次性 push 条件触发；完成后恢复原来的 workflow_dispatch 手动入口，不新增周期性任务。

## English summary

This run retests the current source and updated CI with pinned Magisk 30.7 / Vector 2.2, API 35 x86_64 and Ubuntu 24.04. Three independent disposable environments retain the six existing scope/reboot/recovery stages, with 8 assertions each. Application behavior and APK code are unchanged.

Each phase records unfiltered live logcat with confirmed START/END markers, crash/all-buffer snapshots, DropBox, per-package exit history, kernel logs, boot IDs and native tombstones. Missing coverage, required empty output or failed collection commands fail the run without replacing a primary test error. Dedicated Java and SIGABRT calibration crashes must appear in the real crash buffer; the native case also requires a tombstone backtrace. Expected calibration crashes are kept separate from functional failures.

ADB is unavailable during reboot; this is not a claim of gap-free boot capture or universal crash coverage. Local ADB-boundary tests are not Android runtime validation. Cloud results remain pending; this is neither Root stress-test completion nor physical-device/commercial-app verification. The temporary single-run push trigger will be removed after review, preserving manual-only Root execution.
