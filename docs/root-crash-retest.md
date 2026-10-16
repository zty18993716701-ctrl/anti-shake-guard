# 更新后 Root / Vector 复测与崩溃采集

## 本轮范围 / Scope

2026-10-16，复测当前模块与更新后的 CI 工具，不同时升级框架。继续固定 Magisk 30.7、Vector 2.2 / 3080 Release、API 35 google_apis x86_64；Root runner 固定 ubuntu-24.04，避免 ubuntu-latest 的后续系统迁移引入额外变量。三个全新独立环境分别完成未配置、启用、内核重启保持、移除作用域、恢复作用域和停用六阶段，每阶段仍为 8 项断言。不是 Root 环境下的 100 轮压力测试，也不是物理设备或商业广告 App 验证。

本轮不修改应用源码、传感器策略、作用域、权限或广告关闭规则。APK 在各环境从同一提交重新构建，Root 路径不重打包。仅在一次性模拟器的三个自建测试包内触发受控崩溃；不对用户手机或真实 App 执行这些命令。

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

本地新增采集回归使用真实子进程读写测试日志，但在 ADB 边界使用假程序；不冒充 Android 崩溃正例。开发期间从 15 项回归增加到 19 项，新增断连后的 root 就绪、权限拒绝、UID 实际读回与真机编号拒绝检查。测试曾抓到“必要快照为空仍成功”和“行末 ANR 漏检”，修复后通过。ANR 判据有本地回归，但本轮没有触发真实 ANR 正例，不宣称完整 ANR 故障覆盖。

## 执行记录

| 运行 / 提交 | 整体结果与原因 |
| --- | --- |
| [38898272619](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38898272619) / `51983b7` | FAIL，三个环境的 Java 正例已捕获；native 校准将 applicationId 当作 Activity 命名空间，启动 `control/.MainActivity` 失败，未执行功能阶段。修复为实际的 `dev.antishake.fixture.MainActivity`。 |
| [38898781396](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38898781396) / `940cac7` | FAIL，一个环境完成 48 项功能检查和两类校准；其余两个在启动期 `adb root` 报 `unable to connect for root: closed`。不将单个成功环境替代全组结果。 |
| [38899488202](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488202) / `7299ce7a1e0a6dc87402b08f877941ae93462695` | PASS，三个全新环境全部成功，首次尝试 `run_attempt=1`，详见下表。 |

第二轮的 root 握手失败被固化为回归：仅对启动期连接关闭、offline、缺少设备及传输超时做最多 30 秒的协商；始终要求实际读回 UID=0，不支持 root 的环境立即失败。没有给功能断言加宽松重试。最终三个环境没有再次出现导致任务退出的握手失败，但其运行日志也没有实际触发该重试分支；不能因此宣称已测得消除概率性故障。相同就绪检查用于镜像准备、Root 路径和嵌入式诊断入口。

本次使用限定提交消息、main 分支与采集脚本路径的一次性 push 条件触发；最终验收后恢复原来的 workflow_dispatch 手动入口，不新增周期性任务。

常规嵌入式路径也接入同一采集器，整体包裹原始基线、LSPatch、100 轮生命周期与卸载恢复；移除原先可能为空的标签过滤收尾日志。它仅为诊断将一次性模拟器的 adbd 切换为调试 root，不安装 Magisk / Vector，也不改变嵌入式验证路径或产品前提。两个路径的运行提交与结果分别记录，不能互相代替。

## Root 最终结果与持久证据

| 环境 | 功能断言 | 受控 Java / 原生校准 | 完整采集段 | 持久行为证据 |
| --- | --- | --- | --- | --- |
| trial 1 / job 116968645632 | 48/48 PASS | 2/2 PASS | 12/12 PASS | [JSONL](evidence/root-crash-7299ce7-trial-1.jsonl) |
| trial 2 / job 116968645495 | 48/48 PASS | 2/2 PASS | 12/12 PASS | [JSONL](evidence/root-crash-7299ce7-trial-2.jsonl) |
| trial 3 / job 116968645199 | 48/48 PASS | 2/2 PASS | 12/12 PASS | [JSONL](evidence/root-crash-7299ce7-trial-3.jsonl) |

共 144 次场景断言、6 次预期崩溃校准和 36 个采集段；不是 144 种不同测试。每环境两次 kernel boot_id 均实际变化，涵盖框架安装重启和保护重启保持。每个 Root worker 另行通过相同的 19 项脚本回归，不能累加为不同测试。

三个完整 ZIP 均已下载并通过 SHA-256 / ZIP CRC 校验；每包 169 个文件。另逐项核对了 12 份 capture.json、原始起止标记、9 类诊断命令的退出码与文件字节数、48 项断言、两个重启前后 boot_id、Java crash 缓冲、DropBox，以及原生 backtrace。校验摘要及确切哈希见[机器可读清单](evidence/root-crash-7299ce7-verification.json)。原始功能记录字段保持不变，只增加 phase 标签。

| 环境 | 完整 Actions 证据包（保留 7 天） | ZIP SHA-256 |
| --- | --- | --- |
| trial 1 | [12045812563](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488202/artifacts/12045812563) | `a8e394335b3777fd24e17afa1d60330f0443e7a5adfcfd59d1c2b829b94aaa1a` |
| trial 2 | [12045084300](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488202/artifacts/12045084300) | `94564802e882cb6d24efe1b8c830e80ee7e83810a3800faeb19020ab16e095a6` |
| trial 3 | [12045054850](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488202/artifacts/12045054850) | `95743f0c73b4dec3dc1a543c2226af31e17d3f31d6e95d94358f6e6fdb0c6744` |

**校准退出原因必须区分：** 最终三环境的 Java 异常均保存在 crash 缓冲与 DropBox，但退出历史最终为 `reason=10 (USER REQUESTED) / FORCE STOP`，来自校准脚本清理对话框。因此不把它们表述为自然的 Java 崩溃退出。原生校准则都为 `reason=5 (APP CRASH(NATIVE)) / status=6`，且有包含 SIGABRT 与 backtrace 的 tombstone。早先失败轮次曾观察到 Java reason=4，不能移用于最终轮次。

正常功能段的标记窗口内未发现本判据识别的测试包崩溃或 ANR。预期校准崩溃保留在原始文件中，不算产品故障，也没有被删去。物理设备、商业 SDK、真实 ANR 正例、长时间压力及竞品对照仍未验证；不能宣称“绝不崩溃”或“更稳定”。

## 嵌入式完整日志复测

**PASS。** [38899488231](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488231)，同一提交 `7299ce7a1e0a6dc87402b08f877941ae93462695`，job `116967974390`。19 项脚本回归、45 项 JVM/Robolectric、Lint、三个 APK 构建、两个缺模块负例、40 项既有冒烟断言及 100 轮混合生命周期全部通过。中途被后继提交取消的常规运行不计入结果。

`embedded-suite/logcat-all.txt` 为 35,211,787 字节，起止标记完整，9 类诊断命令均成功；不再用空的标签过滤文件证明无崩溃。此路径未注入预期崩溃，crash 缓冲或 tombstone 为空不自动表示采集失败；两个 Root 正例验证同一采集器确实能保留崩溃，但不能将其误称为嵌入式框架内的崩溃正例校准。

[完整产物 12045877724](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488231/artifacts/12045877724)，34 个文件，保留至 2026-10-23。已实际下载并核对 SHA-256 `1553bdc30604ffef73bc992589403e3d1863faeaa6dc03d0db8a907f69e7f45f` 与 ZIP CRC；另从 JUnit XML 核对 45 项执行无失败、错误或跳过，并核对 101 条生命周期记录、五类各 20 轮、两类缺模块负例及完整采集清单。

持久文件：[行为 JSONL](evidence/embedded-crash-7299ce7.jsonl) · [核验摘要](evidence/embedded-crash-7299ce7-verification.json)。所有最终 Root/嵌入式原始 ZIP 均保存在本任务本地证据目录，不依赖 Actions 的 7 天保留期。未覆盖真实设备，也未替换历史测试者安装包或创建稳定版 Release。Root 工作流恢复为仅手动触发，一次性 push 条件已移除。

## English summary

This run retests the current source and updated CI with pinned Magisk 30.7 / Vector 2.2, API 35 x86_64 and Ubuntu 24.04. Three independent disposable environments retain the six existing scope/reboot/recovery stages, with 8 assertions each. Application behavior and APK code are unchanged.

Each phase records unfiltered live logcat with confirmed START/END markers, crash/all-buffer snapshots, DropBox, per-package exit history, kernel logs, boot IDs and native tombstones. Missing coverage, required empty output or failed collection commands fail the run without replacing a primary test error. Dedicated Java and SIGABRT calibration crashes must appear in the real crash buffer; the native case also requires a tombstone backtrace. Expected calibration crashes are kept separate from functional failures.

ADB is unavailable during reboot; this is not a claim of gap-free boot capture or universal crash coverage. Local ADB-boundary tests are not Android runtime validation. This is neither Root stress-test completion nor physical-device/commercial-app verification. The temporary single-run push trigger is restored to manual-only after review.

The same collector also wraps the existing embedded baseline/LSPatch/lifecycle/restoration suite, replacing its tag-filtered exit log. Its adbd runs as debug root solely to read diagnostics; no Root/Xposed framework is installed in that embedded path. The two validation paths retain separate run/commit evidence.

Root run [38899488202](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488202), commit `7299ce7a1e0a6dc87402b08f877941ae93462695`, passed in all three independent environments on the first attempt: 144 repeated scenario assertions, 6 deliberate calibration crashes, and 36 complete capture segments. Each worker also passed the same 19 script regressions. All three ZIPs were downloaded and checked against their API SHA-256 digests and ZIP CRCs; phase markers, raw records, diagnostic command status/sizes, reboot IDs and native backtraces were independently checked. See the linked JSONL files and machine-readable verification manifest.

Earlier runs remain failures: an incorrect fixture Activity name blocked native calibration; then two environments failed during transient adbd root negotiation, despite one successful environment. The bounded readiness helper retains UID=0 verification and does not retry product assertions. The final successful runs did not exercise that transient-retry branch at runtime, so they do not establish a measured flake-elimination rate.

Java calibration produced real exception stacks and DropBox entries, but final exit reasons were FORCE STOP due to explicit dialog cleanup. Native calibration retained APP CRASH(NATIVE), SIGABRT and tombstone backtraces. Expected calibration crashes are not product failures. No targeted unexpected crash/ANR was detected within functional-phase marker windows; this does not prove universal absence of crashes. Runtime ANR calibration, physical devices, commercial SDKs and comparative reliability remain unvalidated.

Embedded run [38899488231](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38899488231) passed at the same commit: 19 script regressions, 45 JVM/Robolectric executions, build/Lint, both missing-module negatives, 40 existing smoke assertions and 100 mixed lifecycle cycles. Its unfiltered live log contains 35,211,787 bytes with complete boundary markers and all 9 diagnostic commands successful. The 34-file ZIP was downloaded and verified against SHA-256/CRC, JUnit XML and raw lifecycle records. No deliberate crash was injected in the embedded route, so shared-collector calibration under Root is not mislabeled as embedded-framework crash calibration. Full original ZIPs are retained locally; permanent JSONL/verification summaries are linked above. Root execution is restored to manual-only.
