# Root / Vector 100 轮混合生命周期压力测试

## 范围与验收协议 / Scope and acceptance contract

2026-10-17：只在一次性 GitHub Actions 模拟器测试。固定 Magisk 30.7、Vector 2.2 / 3080 Release、Android API 35 google_apis x86_64、Ubuntu 24.04；三个独立环境分别从同一提交构建原始模块与两组靶场，不使用 LSPatch 重打包，不测试真机或商业 App。

每个环境必须完成 **100 个生命周期复合轮次**，不是把字段断言数当作轮数：冷进程重启、同进程任务重开、Home/Launcher 往返、靶场广告关闭、普通页等待交替执行，各 20 轮。广告轮连续轮换即时按钮、延迟按钮与缺按钮三种情况。分五段执行，每段 20 轮；序号、广告变体和光线输入在段间不归零。机制及判据沿用[生命周期测试](lifecycle-testing.md)。

| 边界 | 操作与独立检查 |
| --- | --- |
| 第 20 轮后 | 移除保护组作用域 → 全套 baseline → 重新加入 → 全套 hooked |
| 第 40 轮后 | 真正重启 → boot_id 改变 → 模块/作用域读回 → 全套 hooked |
| 第 60 轮后 | 再次移除作用域 → baseline → 重新加入 → hooked |
| 第 80 轮后 | 再次真正重启 → boot_id 改变 → 模块/作用域读回 → hooked |

边界验证**额外计数**，不算进 100 轮。沿用原有六阶段检查，共 12 套 × 8 = 96 次冒烟断言/环境，其中 48 次是原有检查，48 次是压力期间的六套边界检查。压力期间两次重启，加上安装框架和原有保护保持检查，共四次真实重启/环境。三环境全部通过才可记录整组 PASS；部分完成不补记成功。

作用域移除期间，保护组与对照组都必须恢复原始运动事件和跳转，广告不被自动关闭；加入后保护组必须重新过滤运动，对照组仍能跳转。每套冒烟启动都会强制停止并重新打开靶场，避免旧进程继续加载的 Hook 掩盖作用域变化。普通页和光线传感器判据不放宽。

所有运动生命周期轮保存前后状态、PID 与本轮特有光线值：冷轮 PID 必须变，任务重开和后台轮 PID 不变；后台恢复计数为 2；最终进程仍须存在。页面轮在等待后重新检查页面和 PID，不能只信早先落盘的成功快照。

## 崩溃采集与失败保留

每环境预期 33 个采集段：原有 12 段、5 段生命周期、8 段作用域变更/行为、8 段压力重启前后/配置/行为。每段保留未经标签筛选的 logcat 流与实际 START/END 标记，以及 crash/all 缓冲、DropBox、三个包的退出历史、dmesg、boot_id 和原始 tombstones。缺失标记、采集失败或判据识别出的功能段测试包崩溃/ANR，使测试失败。代码只改测试基础设施，不改产品权限、策略或关闭规则。

继续分别触发 Java 与 SIGABRT 两个预期校准崩溃；原始记录保留，不算产品故障。Java 校准的异常栈与最终退出原因必须分开解释，因为清理对话框可能使最终历史为 FORCE STOP；原生校准必须有 SIGABRT 与 tombstone backtrace。ANR 有判据回归，但未增加真实 ANR 正例。

重启离线期间没有连续 ADB 流；重启前后分别采集，并补采可读取的启动缓冲。33 段完整不等于设备从未丢日志，也不覆盖所有故障。Actions 原始日志 ZIP 保留 7 天，下载后在本地保留，关键 JSONL、校验清单和运行链接写入仓库。

## 执行状态

首轮提交：`d218bf41097424a29889af64522b1e06b015b7d9`，[Root 39020188810](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188810)。trial 2 在第 7 轮失败，只有前 6 轮完整通过，不补记为 100 轮。其 `stress-001-020/capture.json` 为 complete=true、operation_succeeded=false；日志保留完整，但功能检查未完成。

原始系统事件给出具体原因：09:18:30.389 探针已 onResume；运动注入后 09:18:30.730 出现 `wm_relaunch_resume_activity`，随后同一 PID 5369 的 ProbeActivity 暂停、销毁、重建并于 09:18:30.809 再次 onResume；窗口从 1080×1920 改为 1920×1080（rotation 0→1）。系统自动旋转引入了额外的 Activity 重建，不符合本轮 warm 场景要求的恰好一次恢复。该失败段采集未检出目标包崩溃/ANR，不能把判据失败称为模块崩溃。

trial 2 原始 [ZIP 12097045163](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188810/artifacts/12097045163) 已下载并核对 SHA-256 `c4fd6271d7db260c5d0843b1df430b7366b5ffc059f907e8df6e28581765b846` 和 ZIP CRC。它是失败样本，不替代最终验收。

最小修正只固定测试模拟器显示方向：`accelerometer_rotation=0`、`user_rotation=0`，必须实际读回；不关闭或伪造应用的运动传感器。Root 安装框架前及每段生命周期开始时设置；运动强度、PID、恢复次数、对照跳转及关闭判据全部保持。新增“忽略设置写入必须失败”等边界回归后，本地 25 项 Python 测试通过。设置回归先失败、再实现通过；真正的原始复现仍需由下一轮模拟器运行验证，不以假 ADB 代替。

首轮 trial 1 完成 100 轮、96 次冒烟、33 个采集段及四次真实重启，下载 ZIP 后独立核验全部通过；单环境通过不替代整组结果。trial 3 只完成前 62 轮，在第 63 轮保护组启动时超时。原始日志确认是一次**非预期原生崩溃**，不能归入 trial 2 的旋转问题：PID 7020 在 09:26:44.666 收到 SIGSEGV；系统 `am_crash` 与退出历史确认保护组 reason=5 / status=11，tombstone 显示 ART `art_sigsegv_handler` / 线程创建栈。进程 cmdline 为 `<pre-initialized>`，现有包名判据漏识别，但完整原文确已采集且功能测试已因启动超时失败。根因尚未确认，不能归罪或免责于模块、Vector 或模拟器中的任一方。

因此补充了功能窗口内系统 `am_crash` / `am_anr` 事件的精确包名识别；旧窗口与相似前缀的其他包不能误算。用真实失败日志窗口回放已确认新判据拒绝该崩溃。新增回归先失败再通过，全部脚本回归增至 27 项。**这修复的是异常识别漏判，不是上述原生崩溃的根因。**

中间提交 `6693e23f624a8ce7d82ba26143cf973679b76b39` 的 [Root 39020929804](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020929804) 在准备阶段主动取消，未进入行为验收；[配套常规运行 39020929775](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020929775)及[首轮常规运行 39020188801](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188801)也被后继提交替代并取消。均不计 PASS。

加强判据后的复测提交：`fad716ffb93fd9dc04b857ac1f08c9e808907918`；[Root 39021343711](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343711) 首次尝试三环境全部 PASS，并已下载原始 ZIP 独立核验。配套[常规回归 39021343697](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343697) FAIL，具体结果分开记录于下。**Root 复测通过不能把先前原生崩溃标为已修复，也不能替代嵌入式路径的失败。**

## Root 最终结果与证据

| 环境 / job | 生命周期 | 冒烟断言 | 完整采集段 | 实际重启 | 证据 |
| --- | --- | --- | --- | --- | --- |
| trial 1 / 117363874876 | 100/100 | 96/96 | 33/33 | 4 | [逐轮 JSONL](evidence/root-stress-fad716f-trial-1-verification.jsonl) · [冒烟 JSONL](evidence/root-stress-fad716f-trial-1-verification-behavior.jsonl) · [校验](evidence/root-stress-fad716f-trial-1-verification.json) |
| trial 2 / 117363874742 | 100/100 | 96/96 | 33/33 | 4 | [逐轮 JSONL](evidence/root-stress-fad716f-trial-2-verification.jsonl) · [冒烟 JSONL](evidence/root-stress-fad716f-trial-2-verification-behavior.jsonl) · [校验](evidence/root-stress-fad716f-trial-2-verification.json) |
| trial 3 / 117363874840 | 100/100 | 96/96 | 33/33 | 4 | [逐轮 JSONL](evidence/root-stress-fad716f-trial-3-verification.jsonl) · [冒烟 JSONL](evidence/root-stress-fad716f-trial-3-verification-behavior.jsonl) · [校验](evidence/root-stress-fad716f-trial-3-verification.json) |

总计 300 轮、288 次重复冒烟断言、99 段完整采集、12 次实际重启；其中压力期间重启 6 次、作用域移除/重新加入 6 对。每环境各完成两个预期校准崩溃，全组 6 次；每个 worker 另通过相同的 27 项 Python 回归，不累加成 81 种不同测试。上述数字是不同维度，不能相加当作独立测试数。

逐项从 ZIP 核对了序号 1..100 不缺失/重复、五类各 20 次、广告变体连续、两组运动行为、光线输入、恢复次数、PID 存活/变化、普通页与关闭结果；核对了每次作用域读回和 baseline/hooked 原始状态、33 段实际 START/END 标记、9 类命令退出码及字节数、四次重启前后 boot_id 与各生命周期段所属 boot 链。功能窗口未检出判据覆盖的测试包 Java/native 崩溃、ANR 或系统 am_crash/am_anr 事件。独立核验不是只读取 PASS 汇总。

三环境 live logcat 文件字节数之和分别为 230,342,681 / 229,506,156 / 227,666,484（含各段读取的旧缓冲，不能作为互不重复日志大小相加计算覆盖时长）。原始校准 crash / DropBox 均保留：trial 1 的 Java 最终退出为 FORCE STOP；trial 2、3 为 APP CRASH(EXCEPTION)。三者 native 校准均为 APP CRASH(NATIVE)、status=6 / SIGABRT，并有 tombstone backtrace。不是本轮非预期 SIGSEGV 的“修复证明”。

| 完整 ZIP（保留至 2026-10-24，另已本地保存） | 文件数 | SHA-256 |
| --- | --- | --- |
| [trial 1 / 12096958900](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343711/artifacts/12096958900) | 464 | `00465f983088a7c8fd069067c90485917b3ca85ae8650cc26505908ff5e7a51c` |
| [trial 2 / 12097591640](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343711/artifacts/12097591640) | 463 | `6d9f66049ebfee9e17b32dfbc55d2611ec389745498dfaea14cab8f3a53a398b` |
| [trial 3 / 12097710134](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343711/artifacts/12097710134) | 463 | `24cd72ef343d52a5e7268e0cd1b4c6fd311f2347b619927d1e1beb600c144b8d` |

原始文件通过 API SHA-256 与 ZIP CRC 校验。首轮三个 ZIP 也全部本地保留：trial 1 SHA-256 `4da6f27ad2c94001a6514145c049e197630664d01dbeb318dc2f2bc8c54ad3f1`；trial 2、3 哈希见前述失败记录及[原生故障证据](evidence/root-stress-d218bf4-native/README.md)。固定方向后未再出现导致本次失败的旋转/恢复计数异常，只支持受控方向下的本次结果，不证明自动旋转兼容性。

## 配套嵌入式回归：FAIL，待定位

同一 `fad716f` 提交的常规路径通过 27 项 Python、45 项 JVM/Robolectric（0 failures/errors/skips）、构建、Lint、两个缺模块负例、原始 baseline 及三套 hooked 冒烟共 32 项断言。随后只完成生命周期第 1–9 轮；第 10 轮普通页最终为 `MAIN / NONE / normalClicks=0 / navigated=false`，但 `hook=false`，故按严格条件失败，没有放宽或补记为 100 轮。卸载恢复阶段未执行。

PID 7127 的日志有 LSPatch bootstrap completed，但未见同进程的 `AntiShake: Java hooks installed`。这是诊断线索，不是根因证明；该失败进程没有进一步运动探针，尚不能区分仅 Hook 诊断标记异常还是保护未完整加载。不能根据普通页没有传感器事件就宣称保护成功。

该段 capture.complete=true、operation_succeeded=false；日志采集完整不等于功能通过。[原始失败输出](evidence/embedded-stress-fad716f-failure.txt) · [核验清单](evidence/embedded-stress-fad716f-verification.json) · [ZIP 12096932350](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343697/artifacts/12096932350)，SHA-256 `175db233569ab48f893fd3c7f03650bfa43a75f823d66a53adf39b96e0294889` 已核对，完整 ZIP 本地保留。之前 2026-10-16 的通过记录只对应其原提交，不移用于本次。

本轮没有改变应用代码或发布稳定版；Root 工作流已恢复为仅手动触发，保留适配 100 轮的 60 分钟上限。本轮结论是 **限定组合下三环境 Root 100 轮已完成，原生崩溃根因与嵌入式标记异常仍开放**。后续优先定位这两类问题，不以重跑得到绿勾代替修复；真机测试继续暂缓。

## English summary

Three independent disposable API 35 x86_64 environments each run 100 alternating lifecycle cycles, 20 of each kind: cold process restart, same-process task reopening, Home/Launcher round trip, fixture-ad closure and ordinary-page observation. Five 20-cycle chunks retain global ordinals, ad variants and unique light inputs. No physical devices or commercial apps are included; Magisk 30.7, Vector 2.2 / 3080 Release and Ubuntu 24.04 remain pinned. Product code, permissions and policies are unchanged.

After cycles 20 and 60, remove scope, verify baseline behavior, restore scope, and verify real hooked behavior in freshly started processes. After cycles 40 and 80, perform actual kernel reboots, require changed boot IDs, read back configuration and verify behavior again. Boundary checks are additional, not counted among the 100 cycles. Including the six original smoke stages, each environment requires 96 repeated smoke assertions and four actual reboots, two of which occur during stress.

All 33 expected capture segments retain verified live-log boundaries and diagnostic snapshots: crash/all buffers, DropBox, per-package exit history, kernel logs, boot IDs and native tombstones. Two isolated expected Java/native crashes calibrate collection. Reboot downtime cannot have an uninterrupted ADB stream; pre/post capture does not establish universal crash coverage. No real ANR calibration is added. Raw archives were downloaded and checked against API SHA-256/ZIP CRC, cycle records, actual states/PIDs/light inputs, scope configuration and boot chains before marking the final Root run PASS.

This bounded fixture test cannot establish long-term stability, vendor-ROM/ARM compatibility, commercial ad support, universal non-navigation, or comparative superiority. Historical tester packages and stable releases are unchanged.

The first Root run at `d218bf4` failed overall. Trial 1 completed 100 cycles, 96 smoke assertions and 33 capture segments; trial 2 failed in cycle 7 after six completed cycles due to system rotation/recreation. Trial 3 completed 62 cycles and failed starting cycle 63: the protected process PID 7020 suffered an unexpected SIGSEGV, with ART/thread-creation frames and native-crash exit history. Its debuggerd cmdline was `<pre-initialized>`, so the previous name-based crash classifier missed it, although the raw crash buffer/tombstone/exit record were retained and behavior correctly failed on startup timeout. The native crash's root cause remains unconfirmed; it is not attributed to or cleared for the module, Vector or emulator.

The focused harness repair locks only emulator display rotation and verifies setting readback; injected sensors and strict behavior/resume/PID checks remain unchanged. Exact-package `am_crash` / `am_anr` recognition now also detects pre-initialized crashes. A replay of the actual captured failing window is rejected, and all 27 script regressions pass. This repairs detection, **not the native crash itself**. The intermediate `6693e23` Root run was cancelled before behavior checks; superseded regular runs are also cancelled, not passes.

Final Root run `39021343711` at `fad716f` passed in all three environments on attempt 1: 100 cycles, 96 smoke assertions, 33 captures, four actual reboots and two calibration crashes per worker. Totals are 300 cycles, 288 repeated smoke assertions, 99 captures, 12 actual reboots (six during stress), and six stress scope removal/restoration pairs. These are different dimensions, not distinct-test totals. Permanent per-cycle/smoke JSONL and verification manifests are linked in the table. All complete ZIPs, including earlier failures, are retained locally; Actions copies expire on 2026-10-24. Java calibration exit reasons were FORCE STOP in trial 1 and APP CRASH(EXCEPTION) in trials 2/3; all native calibrations retained SIGABRT/native exit status 6 and backtraces.

The companion embedded run `39021343697` **failed**, despite passing 27 script regressions, 45 JVM/Robolectric executions, build/Lint, both missing-module negatives and 32 smoke assertions. Nine lifecycle cycles passed; cycle 10's ordinary page reported Hook=false, so the suite stopped before 100 cycles and restoration. Its PID 7127 bootstrapped LSPatch without a matching successful module-hook installation log. No motion probe was run in that failed process, so this does not yet distinguish marker-only failure from incomplete protection. Full collection succeeded while the tested operation failed; both facts are retained separately. The failure ZIP SHA-256/CRC and raw output were checked and archived.

The native-crash root cause and embedded marker failure remain open. A later passing Root sample cannot mark them fixed, establish comparative stability, or validate rotation-triggered recreation. Product code and historical tester kits are unchanged, no stable Release was published, and Root triggering is restored to manual-only. Physical-device testing remains deferred.
