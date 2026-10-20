# 防止摇一摇跳转插件-防抖卫士

[中文介绍](#chinese) · [English introduction](#english)

Android 防运动触发跳转实验工程，基于 [Sensor Disabler](https://github.com/wardellbagby/sensor-disabler) 的传感器过滤思路，提供模块源码、自建测试靶场和可追溯的验收记录。

An experimental Android project for preventing unwanted motion-triggered navigation, based on the sensor-filtering approach in [Sensor Disabler](https://github.com/wardellbagby/sensor-disabler). This repository contains the module, controlled test apps, and traceable validation evidence.

**0.2 实验验证版 / Experimental validation build.** 需要 Root / Xposed 兼容环境；不支持 iPhone。自动关闭目前仅支持本项目靶场。 / Requires a Root / Xposed-compatible environment; no iPhone support. Automatic ad closing currently supports only this project's fixtures.

<a id="chinese"></a>

## 中文介绍

### 1. 项目解决什么问题

某些 Android 广告页面会把晃动、转动或拿起手机当作跳转指令，让用户在没有明确点击的情况下离开当前内容。本项目探索在应用处理这些运动输入之前进行源头拦截，并在可验证的场景中结束广告页面。

只限制陀螺仪可能不够：加速度、重力、线性加速度、旋转向量，以及部分可用于推断姿态的输入，都可能被应用用于运动判断。因此，当前策略覆盖明确列出的多类 Java 传感器，而不是只处理单个陀螺仪接口。

项目希望逐步实现“更容易启用、更少误伤、更稳定”。这些是研发目标；目前没有完成竞品对照或用户体验测量，不把它们当作已经证明的产品优势。

### 2. 当前实现范围

| 能力 | 当前行为与范围 |
| --- | --- |
| 按应用保护 | 由用户在 Xposed 兼容管理器中选择作用域；模块排除自身和系统应用。验收只推荐保护组靶场。 |
| Java 运动传感器过滤 | 隐藏策略列出的运动/姿态传感器，并拒绝对应的监听和触发注册；不修改全机传感器开关。 |
| 非运动传感器保留 | 光线、距离等不在屏蔽列表中的类型保留；黑盒测试实际验证了光线事件。 |
| 靶场广告关闭 | 只处理本项目保护组靶场 v1；核对包名、版本、页面、已知父页面、焦点及按钮标记。 |
| 保守关闭决策 | 有合法关闭按钮时优先点击；符合规则但缺按钮时安全返回；未知父页面和普通页面不自动操作。 |
| 启用引导 | 检查两组靶场的安装、停用和版本状态，提供固定测试入口及停用说明。安装成功不显示为保护已生效。 |
| 传感器 Hook 回滚 | 必需传感器 Hook 安装失败时，尝试逆序撤销已记录的传感器 Hook；失败会记录到框架日志。 |

保护从目标进程加载后持续到进程退出，**包括后台**。它并不只在广告可见时过滤输入，因此可能影响受保护应用正常的体感、方向、指南针或计步功能。停用模块或改变作用域后，需要强制停止并重新打开目标应用。

### 3. 实现与验证方式

模块在 Java 层过滤静态与动态传感器列表，并拦截运动传感器的监听/触发注册。过滤前复制列表，避免直接改动 Android 的共享传感器清单。具体类型见 [MotionPolicy](validation/policy/src/main/java/dev/antishake/policy/MotionPolicy.java)，注入入口见 [GuardModule](validation/guard/src/main/java/dev/antishake/guard/GuardModule.java)。

两个靶场来自相同源码：保护组加入模块作用域，对照组保持未选中。测试要求对照组仍接收到实际运动事件并跳转，保护组运动事件为 0 且保持在探针页，同时保留非运动光线事件。

靶场中的 Hook 标记仅用于诊断，不能单独作为拦截成功的依据。黑盒验收还会独立检查传感器事件、页面状态和导航行为；模块没有加载时，保护模式必须按指定原因失败。

自动关闭采用针对靶场的明确规则，不依赖通用 OCR 或“看到跳过就点击”的全局策略，也没有真实商业 App 的关闭规则。

### 4. 已完成的验证

| 日期 / 层级 | 已记录的结果 | 证据 |
| --- | --- | --- |
| 2026-09-25：策略与页面回归 | 41 项 JVM/Robolectric 测试执行通过；页面框架模拟使用 API 28 / 35，不执行 Xposed 注入。 | [验证状态](docs/verification.md) |
| 2026-09-26：嵌入式真实 Hook | LSPatch v1.2，三轮保护各 8 项断言通过；未启用基线和恢复原始 APK 的基线也通过。 | [嵌入式结果](docs/embedded-hook-results.md) |
| 2026-09-26：Root / Vector 生命周期 | 6 阶段 × 8 项断言通过，覆盖启用、真正重启、移除作用域、恢复作用域和停用恢复。 | [Root 结果](docs/root-results.md) |
| 2026-10-01：三个独立环境 | 3 × 48 次场景断言及 3 × 3 次日志超时回归执行全部通过。 | [重复性复测](docs/repeatability-testing.md) |
| 2026-10-15：构建工具维护后 | 代码回归、Lint、三个 APK 构建及 40 次黑盒断言通过，解决云端模拟器磁盘不足导致的启动失败。 | [维护与复测](docs/ci-maintenance.md) |
| 2026-10-16：混合生命周期 | 45 项 JVM/Robolectric、8 项 Python 回归、40 次既有黑盒断言及 100 轮模拟器混合复测通过；冷启动、同进程重开、前后台、靶场广告及普通页面各 20 轮。 | [逐轮证据与修复记录](docs/lifecycle-testing.md) |
| 2026-10-16：更新后 Root 与完整诊断 | 三环境 144 次功能断言、6 次受控 Java/原生崩溃、36 个 Root 采集段通过；嵌入式 100 轮带完整日志再通过，脚本回归增至 19 项。 | [复测与原始日志核验](docs/root-crash-retest.md) |
| 2026-10-17：Root 100 轮混合压力 | 最终三环境各 100 轮、96 次冒烟、33 段诊断通过，含压力期间作用域切换和重启恢复；脚本回归 27 项。首轮原生崩溃根因仍未确认，配套嵌入式回归第 10 轮失败。 | [完整结果、失败与原始证据](docs/root-stress-testing.md) |
| 2026-10-18：单 DEX 候选与启动定位 | 首次嵌入式完成 100 次额外启动、100 轮混合、40 项冒烟及恢复；235 个 PID 的构造/包回调/安装逐一匹配。早期 Root 组合与独立复测失败，日志缺口保留；后续结果见下一行。 | [调查、归档核验与限制](docs/startup-diagnosis.md) |
| 2026-10-18：采集修复后复测 | Root 三组各 100 轮、96 项冒烟、4 次重启及 33 段完整采集全部独立核验通过。嵌入式完成 100 次启动和 95 混合轮，第 96 轮空状态超时，随后运行器关机，无设备工件。后续取证见下一行。 | [完整结果与哈希索引](docs/evidence/coverage-8a2dce8-index.json) |
| 2026-10-20：只读探针复测 | 两组行为 PASS，100 混合轮 / 100 次启动及恢复完成，完整归档已核验；但 500 条探针状态因计数接口错误全部不可用，诊断 FAIL。已用先失败后通过的回归修正探针并复测，原第 24 次保护失效尚未证实修复。 | [完整调查与新索引](docs/evidence/probe-ad9711b-index.json) |
| 2026-10-20：修正后探针可用 | 两组行为和探针读取均 PASS：100 混合轮 / 100 次启动，500 条有效状态，完整日志 SHA/CRC/覆盖与行为核验通过，各 47 项 Java、39 项脚本。实际框架字节码解释了构造阶段尚未跟踪的正常状态；历史回调漏发仍开放，已启动三组独立启动复现。 | [探针状态及完整索引](docs/evidence/registry-8c81d42-index.json) |

这些数字是对应运行的测试或断言执行次数，其中多个阶段复用相同场景，不能相加后宣称有同等数量的独立测试。真实 Hook 的设备证据来自固定 API 35、google_apis、x86_64 云端模拟器组合。

Root 路径已验证的组合是 Magisk v30.7 + Vector v2.2 / 3080 Release。更新后的 CI 已于 2026-10-16 在三个全新环境复跑通过；各轮结果只对应其记录的固定提交，不追溯为其他版本或设备通过。

2026-10-17 的 Root 限定压力复测也已通过，但**不是全项目全部通过**：首轮出现过一次非预期 ART 原生崩溃，后续通过不等于根因已修复；同提交嵌入式路径在第 10 轮普通页读到 Hook=false，未完成其 100 轮。两个问题均保留开放，详见上表证据。

2026-10-18 的单 DEX 候选在一次完整嵌入式复测中未再出现回调遗漏，但不追溯更改历史失败，也不代表 Root 原生崩溃已修复或达到稳定发布标准。Root 默认执行独立 100 轮混合验收；额外启动诊断与历史组合复现可单独选择，不冒充混合轮数。

**尚未完成：** ARM 真机、厂商系统、真实商业广告 SDK、NDK / direct channel 覆盖、长期压力测试、管理器图形界面易用性、竞品对照及法律审查。模拟器通过不代表这些项目已经通过。

### 5. 如何开始验证

前提是一台已具备兼容框架的专用 Android 测试设备或隔离模拟器。应用最低安装版本为 Android 8.0 / API 26，但这不表示已完成 Android 8.0 及以后所有版本的运行验收。模块使用 legacy Xposed API 82；项目不提供一键 Root。

1. 从同一次构建获取模块、保护组和对照组三个 APK。当前没有正式稳定版 Release；可自行构建，或查看仍在保留期内的 Actions 产物。
2. 在未启用模块时运行两组探针，确认轻摇或转动能触发实际运动事件和跳转，建立有效基线。
3. 在兼容管理器中启用模块，作用域**只选保护组** `dev.antishake.fixture.protectedapp`；对照组 `dev.antishake.fixture.control` 保持未选中。
4. 按框架要求完成生效步骤，强制停止并重开两组。保护组应显示 Hook=true、运动事件=0、不跳转；对照组仍应跳转。探针界面读数需点击“刷新探针读数”更新。
5. 测试普通广告、延迟按钮、缺按钮和正常内容页，检查关闭、安全返回以及不误操作的行为。
6. 停用模块或移除作用域，强制停止并重开靶场，确认原始运动和手动关闭行为恢复。

[真机验收步骤](docs/device-acceptance.md)和[测试包来源说明](docs/tester-kit.md)提供更完整的记录方法。模拟器脚本会注入虚拟传感器输入，只接受明确指定的模拟器编号，不应改成真机序列号强行运行。不同构建的调试签名可能不同，请勿混用三件套；签名冲突时先确认旧包及测试数据的来源。

### 6. 工程结构与构建

| 路径 | 用途 |
| --- | --- |
| `validation/policy` | 运动类型过滤与广告关闭决策，以及纯策略测试。 |
| `validation/guard` | Xposed 模块、传感器 Hook、靶场关闭逻辑和启用引导。 |
| `validation/fixture` | 同源码的保护组/对照组靶场，生成两个 APK。 |
| `validation/scripts` | 基线、嵌入式 Hook、Root 生命周期及证据采集脚本。 |
| `docs` | 验收范围、复用调查、审查、运行结果及持久 JSONL 证据。 |
| `upstream`、`licenses` | 上游参考实现、版权和依赖许可。 |

构建需要 Java 17、Android SDK `platforms;android-35`、`build-tools;34.0.0`，并设置 `JAVA_HOME` 和 `ANDROID_HOME`。工程提供 Gradle 8.9 wrapper。

~~~sh
git clone https://github.com/zty18993716701-ctrl/anti-shake-guard.git
cd anti-shake-guard/validation
./gradlew :policy:test :guard:testDebugUnitTest \
  :fixture:testProtectedAppDebugUnitTest :fixture:testControlDebugUnitTest \
  :guard:assembleDebug :fixture:assembleDebug \
  :guard:lintDebug :fixture:lintProtectedAppDebug :fixture:lintControlDebug
~~~

| APK | 相对 validation 目录的位置 |
| --- | --- |
| 模块 | `guard/build/outputs/apk/debug/guard-debug.apk` |
| 保护组 | `fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk` |
| 对照组 | `fixture/build/outputs/apk/control/debug/fixture-control-debug.apk` |

本地编译成功只证明构建流程成功。Robolectric 不执行 Xposed 注入，仍需独立的设备黑盒验收。

### 7. 自动化、隐私与恢复

- [常规工作流](.github/workflows/validation.yml)：构建、JVM/Robolectric、Python 判据回归、Lint、无 Hook 基线、未加载模块负例、三轮 LSPatch 真实 Hook、100 轮混合生命周期和恢复基线。LSPatch 测试使用 Java 21，只重打包自建靶场。
- [Root 工作流](.github/workflows/root-validation.yml)：手动触发三个独立云端任务，各完成 100 轮生命周期，穿插作用域移除/恢复和真正重启；保留原有停用恢复及受控 Java/原生崩溃校准。每任务上限 60 分钟，不需要真机。
- 两条路径均保留无标签过滤的日志、DropBox、退出历史和诊断清单。采集失败不得当作“没有崩溃”；重启期间仍有 ADB 不可用的明确边界，见[完整诊断说明](docs/root-crash-retest.md)。
- Actions 产物保留 7 天，旧下载链接可能过期；仓库中的 JSONL 和结果说明用于持久追溯。第三方框架和修补镜像不进入交付产物。

模块未申请网络或无障碍权限，首页只查询两个靶场的安装状态。靶场将用于验收的事件计数和页面状态写入自身私有目录。框架自身的高权限、安全性和兼容性需要独立评估。

出现异常时，在框架管理器停用模块或取消作用域，然后强制停止并重新打开目标应用。只关闭模块首页不会撤销目标进程中已注入的 Hook。

### 8. 下一阶段

- 优先定位压力首轮的 ART 原生崩溃根因与本次嵌入式 Hook 标记异常；Root 100 轮已通过，不将复测成功当作两个故障已修复。
- 继续维护 SDK / 诊断兼容性，补真实 ANR 正例及更多启动期断连运行样本；完整产品级稳定性验收仍未完成。
- 在专用 ARM 真机和不同厂商系统上记录兼容性与副作用。
- 完成同条件竞品对照，以及至少 5 名独立体验者的启用测试。
- 在正式产品推广前完成针对实际功能和宣传的法律审查。

源码公开、免费或开源都不等于法律免责。项目不替换广告、不重定向流量、不伪造广告展示或点击事件，也不把“已公开”表述为产品验收完成。

### 9. 参与与许可证

欢迎提交可复现的问题：说明来源提交、Android/机型、框架版本、作用域、操作步骤及预期/实际结果。请先移除账号、设备标识和日志中的敏感内容；新规则应有保护组/对照组证据和不误操作的测试。完整要求见 [SECURITY.md](SECURITY.md)。

本项目改编自 Wardell Bagby 的 Sensor Disabler，保留 MIT 原版权声明；新增应用代码同样按 [MIT](LICENSE) 提供。Xposed 编译 API、Gradle wrapper 和外部测试工具各自保留其许可，不能将独立依赖统一视为 MIT。项目并非上游官方续作，也不代表上游作者背书。详见 [NOTICE.md](NOTICE.md)。

### 10. 进一步阅读

[验收与对比计划](docs/acceptance.md) · [完整构建/黑盒说明](validation/README.md) · [验证状态](docs/verification.md) · [开源复用取舍](docs/reuse-research.md) · [双轴审查](docs/review.md)

[嵌入式 Hook](docs/embedded-hook-testing.md) · [Root 测试方案](docs/root-testing.md) · [Vector CLI 调查](docs/root-scope-research.md) · [重复性复测](docs/repeatability-testing.md) · [测试者安装包](docs/tester-kit.md)

---

<a id="english"></a>

## English introduction

### 1. Purpose and motivation

Some Android advertising screens interpret shaking, rotating, or picking up a phone as an instruction to navigate away from the current content, even without an explicit tap. Anti-Shake Guard explores blocking relevant motion inputs before an application processes them, together with ad-screen closing in controlled, verifiable scenarios.

Blocking the gyroscope alone may be insufficient. Applications can also use acceleration, gravity, linear acceleration, rotation vectors, and inputs that reveal orientation. The current policy therefore covers an explicit list of Java sensor types rather than a single gyroscope interface.

The development goals are easier activation, fewer unintended effects, and greater stability. Comparative testing and user-experience measurements remain incomplete; these goals are not established advantages over other tools.

### 2. Implemented capabilities

| Capability | Current behavior and scope |
| --- | --- |
| Per-application protection | The user selects scope in an Xposed-compatible manager. The module excludes itself and system applications; validation recommends only the protected fixture. |
| Java motion-sensor filtering | Hides listed motion/orientation sensors and rejects matching listener or trigger registrations, without changing a device-wide sensor switch. |
| Other sensor types preserved | Types outside the blocklist, such as light and proximity, remain available. Black-box tests specifically verify light events. |
| Fixture ad closing | Supports only this project's protected fixture v1, checking package, version, activity, known caller, focus, and button marker. |
| Conservative closing decisions | Prefers a validated close button; returns to a known parent when permitted and no button is available. Unknown callers and ordinary content screens are left untouched. |
| Setup assistance | Checks installation, disabled state, and version compatibility for both fixtures; provides test entries and recovery instructions. Installation is not displayed as verified protection. |
| Sensor-hook rollback | If a required sensor hook fails to install, attempts to undo recorded sensor hooks in reverse order and logs failures. |

Protection lasts from target-process loading until that process exits, **including time in the background**. Filtering is not limited to visible ads and can affect legitimate motion, orientation, compass, or step-related features. After disabling the module or changing scope, force-stop and reopen the target application.

### 3. Implementation and validation approach

The module filters static and dynamic Java sensor lists and intercepts motion-sensor listener/trigger registration. It copies lists before filtering to avoid mutating Android's shared sensor inventory. See [MotionPolicy](validation/policy/src/main/java/dev/antishake/policy/MotionPolicy.java) for the type list and [GuardModule](validation/guard/src/main/java/dev/antishake/guard/GuardModule.java) for injection.

Two fixtures are built from the same source: one is selected for protection and the other remains outside scope. Tests require actual motion events and navigation in the control, zero motion events and no navigation in the protected fixture, and preserved non-motion light events.

The fixture's Hook marker is diagnostic only. Black-box checks independently inspect sensor events, screen state, and navigation. Protected-mode validation must fail for a specific reason when the module is not loaded.

Automatic closing uses explicit fixture rules. It does not use general OCR or a global “tap anything labeled Skip” approach, and no commercial-app closing rules are included.

### 4. Validation evidence

| Date / layer | Recorded result | Evidence |
| --- | --- | --- |
| 2026-09-25: policy and screen regressions | 41 passing JVM/Robolectric test executions. Framework simulations use API 28 / 35 and do not perform Xposed injection. | [Verification status](docs/verification.md) |
| 2026-09-26: embedded real hooks | LSPatch v1.2: three protected rounds of 8 assertions passed, together with the unhooked baseline and restoration using the original APK. | [Embedded-hook results](docs/embedded-hook-results.md) |
| 2026-09-26: Root / Vector lifecycle | 6 stages × 8 assertions passed, covering enablement, an actual reboot, scope removal/restoration, and recovery after disabling. | [Root results](docs/root-results.md) |
| 2026-10-01: three independent environments | All 3 × 48 scenario assertions and 3 × 3 timeout-evidence regression executions passed. | [Repeatability results](docs/repeatability-testing.md) |
| 2026-10-15: CI maintenance | Code regressions, Lint, three APK builds, and 40 black-box assertions passed after resolving runner disk exhaustion during emulator startup. | [Maintenance results](docs/ci-maintenance.md) |
| 2026-10-16: mixed lifecycle | 45 JVM/Robolectric executions, 8 Python checks, 40 existing smoke assertions, and 100 mixed emulator cycles passed: 20 each for cold starts, same-process reopenings, background returns, fixture ads, and ordinary pages. | [Cycle evidence and harness fixes](docs/lifecycle-testing.md) |
| 2026-10-16: updated Root and full diagnostics | Three environments passed 144 functional assertions, 6 deliberate Java/native crashes and 36 Root capture segments. Embedded validation passed another 100 cycles with full logs; script regressions increased to 19. | [Retest and raw-log verification](docs/root-crash-retest.md) |
| 2026-10-17: 100-cycle mixed Root stress | Final three environments each passed 100 cycles, 96 smoke assertions and 33 capture segments, including stress scope changes/reboot recovery; 27 script regressions passed. An earlier native crash remains unresolved; the companion embedded run failed at cycle 10. | [Full results, failures and raw evidence](docs/root-stress-testing.md) |
| 2026-10-18: single-DEX candidate and startup diagnosis | The first embedded retest completed 100 additional cold starts, 100 mixed cycles, 40 smoke assertions and restoration. Construction/callback/installation matched for each of 235 PIDs. Earlier combined and independent Root retests failed; evidence gaps remain explicit. See the next row for later results. | [Diagnosis, archive verification and limits](docs/startup-diagnosis.md) |
| 2026-10-18: collector retest | All three Root archives independently passed 100 cycles, 96 smoke assertions, four reboots and 33 complete segments each. Embedded passed 100 starts and 95 mixed cycles, then failed with empty startup state at cycle 96 before runner shutdown; no device artifact exists. See the next row for later diagnosis. | [Full results and hash index](docs/evidence/coverage-8a2dce8-index.json) |
| 2026-10-20: read-only probe retest | Both behavior suites passed 100 mixed cycles / 100 starts and restoration; full archives verified. Diagnostic FAIL: all 500 probe states unavailable due to an incorrect registry API assumption. A red-to-green regression repaired the probe; its completed Android retest is recorded below. Historical startup-24 protection loss is not fixed. | [Full diagnosis and new index](docs/evidence/probe-ad9711b-index.json) |
| 2026-10-20: corrected probe usable | Behavior and probe-read health PASS: 100 mixed cycles / 100 starts, 500 valid state rows, full SHA/CRC/coverage/behavior verification, 47 Java and 39 script tests per job. Actual framework bytecode explains the normal untracked construction phase. Historical callback loss remains open; three independent startup trials are running. | [Probe state and full index](docs/evidence/registry-8c81d42-index.json) |

Counts refer to test or assertion executions in their respective runs. Stages reuse scenarios; adding these counts does not give a count of distinct tests. Real-hook device evidence comes from fixed API 35, google_apis, x86_64 cloud-emulator combinations.

The validated Root combination is Magisk v30.7 with Vector v2.2 / 3080 Release. The updated CI passed in three fresh environments on 2026-10-16. Every result applies only to its recorded commit, not to other versions or devices.

The bounded 2026-10-17 Root stress retest passed, but **the project is not all-green**: the first run had an unexpected ART native crash whose root cause remains open. The same-commit embedded route failed with Hook=false on cycle 10's ordinary page and did not complete 100 cycles. Later Root success does not repair or override either failure.

The 2026-10-18 single-DEX candidate had no callback omissions in one fully verified embedded retest. Historical failures remain unchanged; this does not establish a Root native-crash fix or stable-release readiness. Root defaults to the independent 100-cycle mixed suite. Extra startup diagnostics and the historical combined reproduction are separate selectable modes, not substitutes for mixed-cycle counts.

**Not yet validated:** physical ARM devices, vendor ROMs, commercial advertising SDKs, NDK/direct-channel coverage, long-running stress behavior, manager-GUI usability, comparative performance, and legal review. Emulator results do not establish these outcomes.

### 5. Getting started

Use a dedicated Android test device or isolated emulator that already has a compatible framework. The minimum installation version is Android 8.0 / API 26; this does not mean runtime compatibility has been validated across all supported installation versions. The module uses legacy Xposed API 82 and does not install Root for you.

1. Obtain the module and both fixture APKs from the same build. There is no stable Release package at present; build locally or inspect Actions artifacts that are still retained.
2. With the module disabled, run both probes and confirm that gentle motion produces actual sensor events and navigation. This establishes a usable baseline.
3. Enable the module in the compatible manager and select **only** `dev.antishake.fixture.protectedapp`. Keep `dev.antishake.fixture.control` outside scope.
4. Apply any activation steps required by the framework, then force-stop and reopen both fixtures. The protected probe should show Hook=true, zero motion events, and no navigation; the control should still navigate. Use the probe's refresh button to update its displayed snapshot.
5. Test normal ads, delayed buttons, missing buttons, and ordinary content screens for closing, safe return, and absence of unintended interaction.
6. Disable the module or remove scope, force-stop and reopen the fixtures, and verify that motion and manual-closing behavior return to baseline.

See the [physical-device checklist](docs/device-acceptance.md) and [tester-kit provenance](docs/tester-kit.md) for fuller procedures. Emulator scripts inject virtual sensor values and require an explicit emulator serial; they should not be adapted by substituting a physical-device serial. Debug signatures can differ between builds, so do not mix APK sets. Investigate the existing installation and test data before resolving signature conflicts.

### 6. Repository layout and building

| Path | Purpose |
| --- | --- |
| `validation/policy` | Motion-type filtering, ad-closing decisions, and policy tests. |
| `validation/guard` | Xposed module, sensor hooks, fixture closing, and setup screen. |
| `validation/fixture` | Shared source for protected/control fixtures, producing two APKs. |
| `validation/scripts` | Baseline, embedded-hook, Root-lifecycle, and evidence-collection scripts. |
| `docs` | Scope, reuse research, reviews, results, and persistent JSONL evidence. |
| `upstream`, `licenses` | Upstream reference implementation, copyright, and dependency notices. |

Use Java 17, Android SDK `platforms;android-35`, and `build-tools;34.0.0`; configure `JAVA_HOME` and `ANDROID_HOME`. The repository provides a Gradle 8.9 wrapper.

~~~sh
git clone https://github.com/zty18993716701-ctrl/anti-shake-guard.git
cd anti-shake-guard/validation
./gradlew :policy:test :guard:testDebugUnitTest \
  :fixture:testProtectedAppDebugUnitTest :fixture:testControlDebugUnitTest \
  :guard:assembleDebug :fixture:assembleDebug \
  :guard:lintDebug :fixture:lintProtectedAppDebug :fixture:lintControlDebug
~~~

| APK | Path relative to validation |
| --- | --- |
| Module | `guard/build/outputs/apk/debug/guard-debug.apk` |
| Protected fixture | `fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk` |
| Control fixture | `fixture/build/outputs/apk/control/debug/fixture-control-debug.apk` |

A successful build verifies compilation, not protection. Robolectric does not execute Xposed injection; separate device-level black-box checks remain necessary.

### 7. Automation, privacy, and recovery

- [Regular workflow](.github/workflows/validation.yml): builds, JVM/Robolectric, Python evidence-check regressions, Lint, an unhooked baseline, missing-module negative checks, three real LSPatch rounds, 100 mixed lifecycle cycles, and restoration. The LSPatch step uses Java 21 and repackages only this project's fixture.
- [Root workflow](.github/workflows/root-validation.yml): manually launches three independent cloud jobs, each running 100 lifecycle cycles interleaved with scope removal/restoration and actual reboots, retaining disable/recovery checks and deliberate Java/native crash calibration. Each job is limited to 60 minutes; no physical device is required.
- Both paths retain unfiltered logs, DropBox, exit history and capture manifests. Collection failure is not evidence of no crashes; ADB is still unavailable during reboot. See [full diagnostic boundaries](docs/root-crash-retest.md).
- Actions artifacts are retained for 7 days, so older downloads may expire. Repository JSONL files and reports preserve the recorded evidence. Third-party frameworks and patched images are excluded from deliverables.

The module requests neither network nor accessibility permissions. Its setup screen queries installation state only for the two fixtures. Fixtures store test event counts and screen state in their own private directory. Framework privileges, security, and compatibility require separate consideration.

To recover, disable the module or remove scope in the manager, then force-stop and reopen the target application. Closing the module's setup screen does not undo hooks already installed in another process.

### 8. Next development stages

- First investigate the earlier ART native crash and current embedded Hook-marker failure. The passing Root 100-cycle retest does not establish that either fault is fixed.
- Maintain SDK/diagnostic compatibility, add runtime ANR calibration and collect more startup-disconnection samples. Full product-level stability acceptance remains incomplete.
- Record compatibility and unintended effects on dedicated ARM devices and vendor ROMs.
- Perform controlled comparisons and activation studies with at least 5 independent participants.
- Complete legal review of the actual functionality and claims before formal product promotion.

Public hosting, free distribution, and open-source licensing do not provide legal immunity. The project does not replace ads, redirect traffic, or fabricate ad impressions/clicks. Public source availability does not mean product validation is complete.

### 9. Contributing and licensing

Reproducible reports are welcome: include the source commit, Android/device model, framework version, scope, steps, and expected/actual behavior. Remove account information, device identifiers, and sensitive log content. New rules should include protected/control evidence and tests against unintended actions. See [SECURITY.md](SECURITY.md).

The project adapts Wardell Bagby's Sensor Disabler and preserves its MIT copyright notice. New application code is also provided under [MIT](LICENSE). The Xposed compile-time API, Gradle wrapper, and external test tools retain their respective licenses; not every dependency is MIT. This is not an official upstream continuation or endorsement. See [NOTICE.md](NOTICE.md).

### 10. Further reading

[Acceptance and comparison plan](docs/acceptance.md) · [Build and black-box guide](validation/README.md) · [Verification status](docs/verification.md) · [Reuse decisions](docs/reuse-research.md) · [Code review](docs/review.md)

[Embedded-hook plan](docs/embedded-hook-testing.md) · [Root test plan](docs/root-testing.md) · [Vector CLI research](docs/root-scope-research.md) · [Repeatability](docs/repeatability-testing.md) · [Tester kit](docs/tester-kit.md)

This README is bilingual. Most detailed test records and the current application interface are primarily in Chinese.
