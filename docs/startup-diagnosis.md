# 启动期故障定位 / Startup failure diagnosis

状态：**调查中，尚未证实修复**。只测试一次性 Android API 35 x86_64 模拟器；不测试真机或商业 App，不替换历史测试包。

## 最新：修正后探针 500 条可用，已核实真实启动顺序（2026-10-20）

[修正后运行 39370387308](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39370387308)，源码 `8c81d42`，**行为 PASS，探针读取 PASS**。独立模拟器分别完成 100 混合轮（五类各 20）和 100 次普通页启动；各 40 项冒烟、47 项 Java XML、39 项脚本、三个模块缺失负对照和卸载恢复通过。两份完整 39 文件 ZIP 与工作流全文已下载，SHA-256 与 GitHub 摘要一致、CRC、START/END、九项诊断退出码和字节数、全部行为记录独立核验通过。实时 logcat 为 33,811,799 / 23,243,111 字节；覆盖窗口和独立完整快照未检出目标崩溃/ANR，崩溃缓冲和 tombstones 为空，未检出所检查的内核卡顿信号。两组实际模块为单 DEX，DEX/Manifest/resources 一致。

135 / 115 个保护 PID 均各有一次构造、包回调和安装；两阶段 270 + 230 条探针全部可解析，无 unavailable。每个 PID 两阶段的 LoadedApk 标识相同，也逐一匹配框架自己的初始化对象日志，未发现读错目标对象的证据。全部进程状态一致：

| 阶段 | 类加载器已创建 | 跟踪集合成员 | 已登记回调 | 模块已收到回调 |
| --- | --- | --- | --- | --- |
| 模块构造 | false | false | 0 | false |
| 主队列 | true | false | 1 | true |

**修正前一轮的时序预期：构造时不应预设 tracked=true。** 对与两组记录 SHA 一致的固定 LSPatch release JAR 实际反汇编后确认：`Startup.bootstrapXposed()` 安装框架 Hook，随后立即加载 legacy 模块；它返回之后，`LSPApplication.onLoad()` 才调用 `trackLoadedApk`，再进入“Load modules”记录和 `realizeLoadedApk`。所以构造阶段的 false 是正常的“尚未登记”，主队列的 false 则符合 create-CL Hook 完成后的清理；不能把两次 false 当作中间从未加入过集合。250 个 PID 的日志顺序全部符合这条真实调用链。固定 JAR SHA 为 `d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165`，内部 loader DEX SHA 为 `16f544f449bb75e3147886314a5c3f66b0ef7da53e1e07715efbcbd77bbb70ac`。

这证明探针读取修复已在 Android 中生效，并建立了健康进程的可用对照，**不证明历史第 24 次回调缺失、旧第 96 轮超时或原生崩溃已修复**。当前两阶段没有直接观察跟踪集合中间加入/移除的瞬间；也尚无失败 PID 的可用状态，不能据此在“过早实现类加载器”“登记后绕过 Hook”或“Hook 内未分发”等解释中选定根因。只读诊断仍可能影响时序；不补发回调，不提前安装备用保护。

下一项是有界重复，而非重跑到绿：源码 `d00cd0517cd7053370aab011d4fa0c83ddac4c05` / [39430481021](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39430481021)。三组独立新模拟器各 100 次普通页启动，另保留一组原 100 混合轮；每组单独归档，任一失败仍保留 FAIL，互不取消。只改 CI 矩阵和工件 trial 后缀；模块、框架、探针位置、原时限、负对照及恢复规则不变。先验证可用探针下能否再次复现，再决定是否需要更靠近框架分发点的实验。尚在运行，不预报通过。

精确索引：[registry-8c81d42-index.json](evidence/registry-8c81d42-index.json)。完整日志仅保留于 Actions 与本地隔离归档；不公开混入安装包，不替换历史包，不发布稳定版，不做真机测试。

English: [Run 39370387308](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39370387308), source `8c81d42`, passed both behavior suites and probe-read health: 100 mixed cycles / 100 starts, 40 smoke assertions, 47 Java tests, 39 script tests, three module-negative controls and restoration per job. Both complete 39-file archives and full workflows were downloaded; SHA/CRC, markers, all nine diagnostics and behavior records were independently verified. All 500 probe rows from 250 protected PIDs are readable; every PID has exactly one constructor, callback and installation. Probe identities match the framework's own initialized LoadedApk record and remain stable across phases. No unexpected target crash/ANR or checked kernel-stall signal was found in these covered records. Actual pinned release bytecode explains constructed tracked=false: bootstrapXposed loads legacy modules before onLoad tracks the target; main-queue false follows cleanup. The previous expectation of constructed tracked=true was wrong. These two observations do not expose the intermediate tracker transition, and no failing-process state is yet available. Thus historical callback loss, old cycle 96 and the native crash remain unresolved; this validates instrumentation, not a product fix. A bounded [run 39430481021](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39430481021) now executes three independent 100-start trials and one unchanged 100-cycle lifecycle suite, without behavior retries, relaxed criteria, callback replay or changed module/framework code. Results pending; physical devices remain NOT RUN.

## 最新：两组行为通过，但 500 条探针状态不可用；已修正探针（2026-10-20）

[探针运行 39365232563](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39365232563)，源码 `ad9711b`。两组行为测试均 PASS：100 混合轮 / 100 次启动，各 40 项冒烟、45 项 Java、39 项脚本、三个模块缺失负对照及卸载恢复通过。两份完整 38 文件 ZIP 与工作流全文已下载，SHA-256/CRC、START/END、九项诊断退出码/字节数和行为记录独立核验通过。实时 logcat 分别为 34,652,252 与 22,091,799 字节。135 / 115 个保护 PID 各有一次构造、包回调及安装；本轮未复现回调缺失。覆盖窗口和独立快照无目标崩溃/ANR，未检出所检查的内核卡顿信号。

但**诊断目标失败**：250 个 PID 的构造/主队列两阶段共 500 条探针全部 unavailable，异常是 `CopyOnWriteArraySet.getSnapshot` 不存在。运行时回调登记表是标准集合，而我新增的探针错误地假定了框架私有方法；后续类加载器和登记状态没有输出。不能将这些读取异常忽略，也不能凭两项绿灯推断上轮保护失效的根因或修复。只读诊断也可能影响时序；没有失败进程的可用对比状态，原有两个解释仍未区分。

先修正这个已复现的探针错误：将计数改为标准 `Collection.size()`。在实际计数入口用真实 `CopyOnWriteArraySet` 写回归，用例先以相同 `NoSuchMethodException` 失败，修正后通过；增加空集合用例后两个本地 JUnit 用例通过，39 项脚本回归通过。Xposed API JAR 仅添加至测试类路径，不打包进模块。保护逻辑、作用域、框架、两个探针位置和测试时限均未改。下一轮完整 Java 预期为 47 项，不把诊断修复当作产品修复。[修正后复测 39370387308](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39370387308)，源码 `8c81d42602611e2bbbd839a84e1e66a7d7cb7306`，已完成 Android 结果及探针健康核验，见上节。精确索引：[probe-ad9711b-index.json](evidence/probe-ad9711b-index.json)。

English: [Probe run 39365232563](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39365232563) passed both behavior suites and restoration; both full archives passed SHA/CRC, coverage, diagnostics and record verification. All 250 protected PIDs have constructor/callback/install records. However, all 500 state-probe rows failed because our probe called a non-existent getSnapshot method on the runtime CopyOnWriteArraySet. Thus diagnostic outcome is FAIL and the callback-loss hypotheses remain unresolved. A real-registry counter regression reproduced this exact exception before a minimal Collection.size repair; two local JUnit cases and 39 script tests pass. The Xposed JAR is test-only. [Retest 39370387308](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39370387308) completed with all 500 probe states readable, as documented above; protection logic, scope, framework, deadlines and all cycles are unchanged. This repairs instrumentation, not the historical protection failure. No real-device or stable-release claim is made.

## 最新：独立混合通过，独立启动第 24 次确认保护失效（2026-10-20）

[独立双任务 39363717754](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39363717754)，源码 `5169129`，整体 **FAIL**。两份完整 ZIP 和工作流全文已下载；GitHub SHA-256、ZIP CRC、各一段 START/END 覆盖、九项诊断退出码/字节数、Java XML、负对照和行为记录均独立核验，日志完整不改变操作结果。

- 混合任务 **PASS**：原 100 轮（五类各 20）、40 项冒烟、45 项 Java、39 项脚本、三个缺少模块负对照和卸载恢复通过。完整实时 logcat 35,240,997 字节，135 个保护进程各一次构造/回调/安装；功能窗口和独立快照未检出目标崩溃/ANR，未见本轮内核卡顿记录。
- 启动任务 **FAIL**：前 23 次启动通过，第 24 次 PID `7068` 为 `hook=false`；不重启进程的诊断注入新鲜光线 724 和运动后，同 PID 显示 `sensorCount=2`、`events=19`、`TARGET`、`navigated=true`。这次是实际保护失效，不是普通页标记误报或启动超时。完整实时 logcat 15,477,618 字节；快照按原始字节和顺序包含实时流全部 100,507 条记录。失败 PID 有一次模块构造，但无包加载回调或安装记录；另外 38 个保护进程的三条记录各一次。两份日志未检出目标崩溃/ANR，崩溃缓冲和 tombstones 为空；退出历史是测试安排的 FORCE STOP，恢复验收未执行。只采集了前 23 个成功启动的线程列表，不能据此断言失败 PID 的线程构成。

实际模块两组均为单 DEX，DEX/Manifest/resources 与首个候选完全相同。这表明单 DEX 和独立环境仍不能消除回调漏发，不能仅归因于组合负载。观测边界已收窄到模块对象创建之后、包回调之前；更底层机制及旧第 96 轮/原始 SIGSEGV 的原因仍未证明。精确元数据见 [isolated-5169129-index.json](evidence/isolated-5169129-index.json)。

下一项[只读启动状态诊断 39365232563](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39365232563)，源码 `ad9711b9239ddd8e3094bcae6d9461dddb67760e`：在构造阶段和主线程下一次处理队列时读取现有 LoadedApk 的类加载器是否已创建、跟踪集合成员及回调登记数量。它不调用目标 `getClassLoader()`，不重放回调、不提前安装拦截、不改变原判据；读取不到的状态明确记 unavailable。用于区分“过早创建类加载器”与“已登记但未从拦截路径送达回调”。39 项脚本和本地 Java 源码编译通过，但这些不能替代 Android 回调链路验证。临时日志尚未清理，不发布稳定版，不做真机测试。

English: [Fresh-emulator run 39363717754](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39363717754) is overall FAIL. Both full archives and workflow logs were downloaded; SHA-256, CRC, coverage markers, all nine diagnostics, XML and behavior records were independently checked. Lifecycle passed 100 mixed cycles, 40 smoke assertions, 45 Java tests, 39 script tests, three module-negative controls and restoration. Startup passed 23 cycles, then failed cycle 24 in PID 7068: the same-process diagnostic observed fresh light 724, real motion events and actual navigation with Hook=false. Complete raw/snapshot records show one constructor but no package callback or hook-install message for this PID; the other 38 protected PIDs each have all three. No unexpected target crash/ANR or observed kernel stall was found in these covered windows. Single-DEX module payloads still match the first candidate, so packing and workload isolation are not a complete repair. The next read-only bootstrap-state experiment is [39365232563](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39365232563), with no callback replay, fallback hooks or relaxed deadlines. Low-level causality and the old cycle-96/native failures remain unproved. No physical-device or stable-release claim is made.

## 最新：顺序隔离混合 100 轮完成，后置启动第 99 次失败（2026-10-20）

[顺序隔离 39282982075](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39282982075)，源码 `3ce7b45`，最终 **FAIL**。完整可用工作流全文已保存，并逐条核验其中的 100 轮混合记录：五类各 20，冷/热/后台 PID 关系、新鲜光线值、保护组零运动、对照组真实运动跳转、广告关闭与普通页均符合原判据。后置的额外启动前 98 次通过，线程记录未见 ForkJoin 工作线程；32 项冒烟和 38 项脚本通过，构建/Lint/Java 任务成功。没有设备归档，不能独立重新计数 Java XML 或确认功能窗口无崩溃。

第 99 次普通页启动超过原 25 秒，Starting Intent 已保留；三条只读取证分别在原 3 秒内超时。北京时间 10 月 20 日 00:31:55 输出原异常，00:35:28 运行器收到关机信号，工件上传步骤被跳过，API 确认零工件。因此**无法下载或核验本次完整设备日志**，也不能排除原生崩溃，更不能将本次失败认定为之前已观测的内核栈。工作流本地保存文本 407,175 字节，SHA-256 和精确索引见 [order-3ce7b45-index.json](evidence/order-3ce7b45-index.json)。恢复未执行，历史第 96 轮原因仍未确认。

顺序变化使混合测试越过第 81 轮并全部完成，支持继续调查累积负载，但不构成因果证明。下一项实验为[独立模拟器双任务 39363717754](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39363717754)，源码 `5169129665c7a7eaf8989f0b139a2649a48e45bb`：每套完整 100 轮独占全新模拟器；都保留基线、模块缺失负对照、固定框架、原时限、卸载恢复和完整采集。两任务分别归档且不互相取消，任一失败仍为 FAIL。默认命令行仍支持 `--suite combined` 重放混合后启动的组合流程。无效模式在下载或设备访问前拒绝的用例已先失败后通过；全部 39 项本地脚本测试通过。这是环境隔离实验，不是已验证的产品修复。

English: [Order-isolation run 39282982075](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39282982075) remains FAIL. All 100 original mixed-cycle workflow records and 98 subsequent extra startup records were checked against PID, sensor, page and thread requirements. Extra startup 99 hit the original 25-second launch deadline; all three read-only diagnostic queries also timed out at three seconds. The runner shut down before artifact upload, leaving zero device archives. The full available workflow text is saved and hashed, but cannot replace missing crash logs or exclude a native crash. Restoration did not run; old cycle 96 remains unexplained. The next bounded [run 39363717754](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39363717754) gives each full suite its own fresh emulator and separate archive, retaining all deadlines, negative controls and restoration. Both are required; failure in one does not cancel the other. The combined CLI remains available. 39 local script tests pass, including a red-to-green invalid-suite boundary test. No product-fix, physical-device or stable-release claim is made.

## 最新：渲染对照仍失败，改为测试顺序隔离（2026-10-20）

[39189752398](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39189752398) 最终 **FAIL**。完整 37 文件 ZIP 和工作流已下载；SHA-256 与 GitHub 摘要一致、CRC 通过。独立核验了 38,965,545 字节实时 logcat 的 START/END、九项诊断的字节数和成功退出码：采集完整，但测试操作失败。45 项 Java、38 项脚本、32 项冒烟、三个模块缺失负对照、100 次额外启动和混合第 1–80 轮通过；恢复未执行。

第 81 轮仍是未保护对照应用第二次冷启动超过原 25 秒。本次新增即时诊断保留 Starting Intent、空崩溃缓冲及退出历史；PID 查询也超过只读诊断的 3 秒。内核记录 RCU 停顿、CPU#1 卡住 35 秒，RenderThread 和 binder 线程采样栈均出现 `goldfish_pipe_read_write`。这与上一轮的 66 秒 virtio 工作队列栈不同，不将两者强行合并为同一已证实根因。完整功能窗口和独立快照未检出目标崩溃/ANR；211 个保护进程各有一次构造、包回调及安装。实际模块 DEX、Manifest、resources 与首个单 DEX 候选相同。单独改渲染模式未避免超时，不能宣称产品修复。

下一项有界实验只交换测试顺序（源码 `3ce7b4569923a56ea162249966abe0f4b10e0591`）：先执行原始 100 轮混合，再执行额外 100 次启动；不删除任何一套、不增加超时、不重试，全部成功并完成卸载恢复才可通过。如果前置启动累积负载是必要条件，混合测试应越过第 81 轮；若相同序列本身触发，则仍可能在附近失败。后续启动阶段失败也保持整轮 FAIL。完整历史组合可由前述固定源码重放。该实验用于隔离环境负载，不补回原第 96 轮日志，不视为稳定版验收。

元数据见 [renderer-35d3b02-index.json](evidence/renderer-35d3b02-index.json)。

## 最新：嵌入式完整失败日志确认模拟器停顿（2026-10-19）

[取证复测 39138791733](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39138791733)，源码 `ed1fef2fc87a18fe1f1e41b60eaa7b574cc0992a`，结果 **FAIL**。已下载完整工作流和 35 文件设备归档；SHA-256 与 GitHub 摘要相同、ZIP CRC 通过。完整实时 logcat 为 39,475,137 字节，START/END 标记、九项诊断的退出码和字节数均独立核验；采集 `complete=true`，操作 `operation_succeeded=false`，不能因日志完整就判通过。45 项 Java 测试、32 项冒烟、三项缺少模块负对照、100 次额外启动及混合第 1–80 轮通过，恢复验收未执行。

本次不是第 96 轮保护组空状态，而是第 81 轮**未受保护对照组**第二次冷启动的 `am start -W` 超过原 25 秒。内核明确记录 `BUG: workqueue lockup`、通信工作队列卡住 66 秒，工作栈为 `virtio_transport_send_pkt_work` / `iowrite16`；系统主线程同时出现约 65.8 秒投递延迟，QEMU 报 CPU 线程挂起，启动请求随后才被处理。这是本次模拟器层停顿的直接证据，但尚未证明完整底层根因。崩溃缓冲为空，完整覆盖窗口未检出目标应用崩溃/ANR，退出历史最近记录是测试安排的 FORCE STOP。211 个保护组进程的构造、包回调及安装记录各一次，无遗漏；实际模块 DEX、Manifest、resources 与首次单 DEX 候选相同。以上不能补回上一轮缺失的日志，也不能认定上一轮第 96 轮已定位或修复。

发现并补齐另一个取证边界：此前即时取证只在“等待状态”失败时触发，启动命令自身超时会绕过它。新增实际 CLI + 假 ADB 传输停顿测试先失败，补丁后全部 38 项脚本测试通过；现在保留超时命令的部分输出、原异常及只读崩溃/退出/PID 诊断，不重试、不重启、不延长判据。它是取证修复，不是应用启动故障的产品修复。

单变量管道对照：[39188889405](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39188889405)，源码 `9ebff183a9e0861f43f50999de25ddc7de425da7`。仅在嵌入式 CI 设置 `ANDROID_EMULATOR_FEATURES=-VirtioVsockPipe`。官方配置将该功能描述为 goldfish pipe 的替代传输（[固定 AOSP 配置](https://android.googlesource.com/platform/external/qemu/+/ba29194f97e72ffe770bd56e4e5c5c620598004b/android/data/advancedFeatures.ini)）。本次 **FAIL**：ADB 持续 offline，原启动时限结束，未安装测试 APK、未执行应用测试或完整设备采集；12 个构建/测试文件及工作流全文已保存，工件 SHA-256/CRC 核验通过，45 项 Java 测试通过。它没有检验到混合生命周期，不能支持管道缓解假设。已撤回该设置，恢复原通信管道。

后续单变量渲染对照：[39189752398](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39189752398)，源码 `35d3b02f0adaa5818e6f79e510e40fbf8d307657`。相对原环境，仅将 `-gpu swiftshader_indirect` 改为 `-gpu swiftshader`，其他启动参数相同。原运行的模拟器是 37.2.12.0；[Android 官方说明](https://developer.android.com/studio/run/emulator-acceleration)指出旧模式自 36.4.9 弃用，并支持新模式。原日志中 GL 上下文错误与虚拟通信停顿使渲染/通信交互成为待验证解释，但“弃用”本身不是根因证明。插件/靶场源码、固定框架、100 次启动、100 轮混合及原有判据不变；38 项脚本测试通过；该运行已完整核验，最终失败见顶部。

精确哈希与结果见 [timeout-triage-ed1fef2-index.json](evidence/timeout-triage-ed1fef2-index.json)。旧失败不覆盖，不做真机测试，不发布稳定版。

## 采集修复后三组 Root 通过，嵌入式仍失败（2026-10-18）

[Root 39133520265](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39133520265)，源码 `8a2dce8ff65abd045f5b6ee9041d5c2d8618e1b3`，三组完整 ZIP 和工作流全文均已下载。每份 ZIP 475 文件，SHA-256 与 GitHub 工件摘要一致，CRC 和独立行为/采集校验全部通过：每组 100 轮混合（五类各 20）、96 项冒烟、20/60 轮作用域切换、40/80 轮重启恢复、共四次真实重启、Java/原生校准及 33 段完整采集。三组共 300 轮、288 项断言、99 段完整采集；功能窗口未检出目标应用崩溃/ANR。所有段直接使用完整实时流，本轮没有触发快照补全路径；其负对照仍由脚本回归覆盖。三组原始实时 logcat 分别约 231.34、256.06、228.67 MB。

[嵌入式 39133422677](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39133422677)，源码 `10347d011d83f0e8523c9203b4f0a06c5111409a`，**FAIL**：工作流记录 100 次额外启动通过、线程列表无 ForkJoin 工作线程，以及混合第 1–95 轮通过。第 96 轮第二次冷启动保护组时，原有 8 秒内未生成 `probe.properties`，最新状态 `{}`。14:14:54 UTC 抛出原始断言，14:15:24 运行器收到关机信号，未执行设备工件上传；可用工作流全文已保存，但完整设备日志无法恢复，不能排除原生崩溃，也不能将其归为已证明的框架或宿主机故障。没有观察到该失败进程的 Hook=false 状态。

后续只补取证、不改插件或框架：状态等待失败时，在完整采集清理前，立即把只读崩溃缓冲、应用退出历史和 PID 输出到工作流，每条诊断传输最多 3 秒；原始 8 秒判据、失败状态、传感器/页面/作用域规则均不变，不重启应用、不注入诊断运动、不重跑至通过。实际 CLI 的空状态超时用例已先失败再通过，当时 37 项脚本测试通过；这是诊断通道回归，不是 Android 故障已修复。[Android 复测 39138791733](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39138791733)，源码 `ed1fef2fc87a18fe1f1e41b60eaa7b574cc0992a`，最终失败及完整取证见顶部。

精确工件哈希与核验索引：[coverage-8a2dce8-index.json](evidence/coverage-8a2dce8-index.json)。旧失败保持 FAIL；临时 `[DEBUG-startup]` 日志尚未移除，不发布稳定版，不做真机测试。

## 单 DEX 候选首次复测（2026-10-18）

候选源码 `b151e5b768bca7aaaae23a3cce684db788bd7f62` 的[嵌入式复测](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39089887806)通过：100 次额外冷启动、100 轮混合生命周期（五类各 20 轮）、40 项冒烟断言、45 项 Java 测试和三项缺少模块负对照全部通过，卸载恢复也完成。完整 36 文件工件的 SHA-256 / ZIP CRC、九项诊断输出字节数及 START/END 覆盖标记已独立核验；完整 logcat 为 43,914,837 字节，未检出功能窗口内的目标应用崩溃/ANR。

实际模块只有 `classes.dex`。235 个进程各有且仅有一次模块构造、保护组包回调和安装成功记录，没有按 PID 核对后的遗漏或重复；100 次启动记录未见 ForkJoin 工作线程。未加载模块的诊断负对照在同一 PID 中注入新鲜光线和运动，正确观察到 TARGET / navigated=true，原始失败仍保留。这支持单 DEX 候选缓解，但一次有界通过不能证明罕见问题彻底修复，临时诊断日志也尚未移除。

[同源码 Root 三组运行](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39089919305)全部失败，不能并入 PASS：

| 组 | 额外启动 | 混合完成 | 终止与证据 |
| --- | --- | --- | --- |
| 1 | 100 | 60 | QEMU 挂起警告后运行器收到关机信号；工作流全文保留，但没有执行工件上传，无法恢复完整设备诊断 |
| 2 | 100 | 67 | 第 68 轮保护组 Launcher 恢复超时，随后模拟器传感器接口也超时；完整 ZIP 已下载，但末段采集不完整（27/28 完整） |
| 3 | 100 | 60 | QEMU 挂起警告后运行器收到关机信号；工作流全文保留，没有设备诊断工件 |

第 2 组 ZIP 完整性通过，不代表其运行时采集完整。第 1、3 组缺失的原始设备诊断不能从工作流文本重建，也不能把“没有崩溃工件”当作“没有崩溃”。没有把这些失败认定为首轮原生 SIGSEGV 的复现或消除。

完整索引和哈希见 [single-dex-b151e5b-index.json](evidence/single-dex-b151e5b-index.json)，嵌入式独立核验见 [verification](evidence/single-dex-embedded-verification.json)。完整系统日志只留在隔离测试工件和本地归档，不混入测试者安装包。

环境对照：源码 `bed9d88e188a7db4e3a457d5ea19dc7b501a33c1` 的[独立混合复测](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39091836244)。模块代码不变；额外 100 次启动诊断不再前置叠加到混合验收。同一环境内的原始 100 轮、96 项冒烟、作用域切换、四次实际重启、Java/原生崩溃校准及全部 33 段完整采集仍为必需。增加只读主机内存/磁盘/进程资源快照，不增加超时或自动重试。命令行保留 `--suite combined` 历史组合复现入口和 `--suite startup` 独立启动入口。

该环境对照三组全部 FAIL，均未进入混合循环，因此尚不能检验累积负载假设。第 1 组在框架安装后、测试 APK 安装前发生 ADB 断连，采集 0/1 完整；当时主机约 11GB 可用内存、81GB 可用磁盘，不支持“初始主机内存耗尽”的解释。第 2 组 CLI 在 90 秒内未就绪，2/2 段采集完整但操作失败，测试 APK 未安装。第 3 组完成两项崩溃校准和 32 项冒烟断言，但移除作用域后的实时流缺 END 标记，9/10 段采集完整。三份工件及工作流全文已下载，SHA-256 和 CRC 全部核验，具体哈希见索引。

### 已定位并修正的采集器问题

第 3 组原始实时流 49,297 条记录，快照 49,341 条；快照逐字节、按序包含实时流全部记录，并补含 START 和 END。没有据此把历史运行改判 PASS。先用子进程边界回归复现该失败，再修正今后的采集器：仅当实时流缺 END、快照成功且含完整标记、并且逐字节保留全部实时流记录的顺序时，记录 `coverage_file=logcat-snapshot.txt`，同时保存原实时流和 `stream_warning`。不能丢弃、改写或筛选原始日志；其余九项诊断检查不变。

新增负对照要求：有标记但丢了实时流记录的快照不能补救；仅出现在快照里的目标崩溃也必须失败；两份日志都缺标记仍失败。本地 34 项脚本回归通过。这修复的是采集判定，不是插件原生崩溃或框架 CLI 初始化本身。

实际复测：[嵌入式采集器验证 39133422677](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39133422677)，源码 `10347d011d83f0e8523c9203b4f0a06c5111409a`；[三组 Root 39133520265](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39133520265)，源码 `8a2dce8ff65abd045f5b6ee9041d5c2d8618e1b3`。Root 仅在就绪检查已经失败之后，对固定框架进程采集进程列表、原生和 Java 线程转储，最终仍抛出原始失败，不重启框架、不把失败变成通过。最终结果见顶部：Root 三组通过，嵌入式第 96 轮失败且缺少设备工件。

## 固定失败样本

- 原生故障：[首轮 Root 运行](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188810)，trial 3 第 63 轮，保护组 PID 7020 / TID 7024，SIGSEGV。完整 tombstone 显示工作线程的 ART 信号处理 / 线程创建栈；主线程当时处于 `ActivityThread.attach` 的 Binder 调用。不能仅凭最后一条模块加载日志，把模块或框架认定为根因。
- 嵌入式故障：[配套运行](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39021343697)，第 10 轮普通页 PID 7127，`hook=false`。此前没有在该失败进程注入运动，因此尚不能区分标记失效与实际保护未加载。
- 两份完整 ZIP、原生 tombstone、失败 JSONL 和哈希保留于本地，历史结果见 [100 轮记录](root-stress-testing.md)。后续 PASS 不覆盖这些失败。

## 本轮实验

诊断源码：`962820cfe8f76506369ea1227a662ca3049abb17`。

1. 保持固定 Magisk 30.7、Vector 2.2 / 3080、LSPatch v1.2 / 487 和传感器/页面判据不变。
2. 原有混合生命周期测试前增加 100 次普通页面冷启动，隔离启动回调问题；这 100 次是额外启动实验，不冒充原有五类各 20 轮的验收。
3. 页面断言失败时保存原状态与 PID，在**不强制停止进程、不删除原证据**的情况下重开探针 Activity，注入本轮独有光线值、加速度与陀螺仪输入，再核对同一 PID。
4. 保留诊断前后原始状态。只有新鲜光线、同进程和真实传感器行为同时满足时，才记录“标记为假但运动被阻断”或“标记为假且发生运动跳转”；进程退出/替换或数据不完整都记为 inconclusive。
5. 诊断不能把失败改成 PASS；原始断言仍抛出并终止测试。`[DEBUG-startup]` 只标注模块实例构造与包回调入口，定位结束后删除临时日志。

本地脚本测试：31 项通过（其中 4 项诊断边界测试）；这不是安卓运行时结果。实际运行：

- [嵌入式诊断 39042538054](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39042538054)
- [三环境 Root 诊断 39042554167](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39042554167)

Root 新增一个独立启动采集段，完整成功时预期 34 段，而非历史运行的 33 段。继续保留完整 logcat、DropBox、退出历史、内核日志与 tombstones，校准崩溃仍与非预期故障分开。

### 已确认的独立环境失败

本轮 Root trial 3 / job `117424791724` 在安装框架后的首次重启失败：系统完成启动，但 CLI 连续报告 `.cli_sock` 不存在，90 秒就绪检查超时。测试 APK 尚未安装，没有进入校准、冒烟、100 次启动或混合生命周期；不能计作原生 SIGSEGV 或 Hook=false 的复现。

其两个采集段均 complete=true，重启后 operation_succeeded=false，boot_id 实际改变。日志显示 Vector daemon 启动、创建新数据库及 system_server 注入，但没有记录 CLI 就绪；这些线索尚不能证明阻塞原因。没有延长超时或自动重试掩盖该失败。

[完整归档 12105060733](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39042554167/artifacts/12105060733) 已本地保存；SHA-256 `6b4bcb49af4898dc1e1104011a7577feb67baa783c8d31ab64065fbeb511b2fe` 与 API 一致，26 个文件的 ZIP CRC 通过。完整工作流日志另行保留。

## 2026-10-18 归档结果

以下运行均失败，不能以局部通过或后续重跑覆盖：

| 环境 | 额外冷启动 | 混合生命周期 | 失败点 |
| --- | --- | --- | --- |
| Root trial 1 | 100/100 | 60 轮 | 第 60 轮后恢复作用域，读取保护组状态超时；随后 ADB/模拟器失联，末段崩溃采集不完整 |
| Root trial 2 | 100/100 | 66 轮 | 第 67 轮对照组 `am start -W` 超时；该采集段完整，未检出目标应用崩溃 |
| Root trial 3 | 未运行 | 未运行 | 上述框架 CLI 就绪失败 |
| 嵌入式 | 100/100 | 43 轮 | 第 44 轮 missing 广告仍停留 AD，`hook=false`、`sensorCount=2`、`events=859` |

嵌入式失败 PID 16045：原始日志依次记录 GuardModule 类加载、`[DEBUG-startup] module instance constructed`、框架初始化和 Activity 启动，却没有包回调入口日志。故障已缩小到模块构造之后、包回调之前；实际运动传感器事件也说明不能把它当作标记单独失效。该 PID 未执行诊断运动脉冲，不能声称已观察到运动跳转。广告等待超时原先不在诊断捕获范围内，本轮把同进程探针覆盖到该断言；失败仍会终止测试，不转为 PASS。

完整工作流日志与 ZIP 本地保留。ZIP CRC 均通过，SHA-256 与 GitHub 工件元数据一致：

| 工件 ID | SHA-256 |
| --- | --- |
| 12105800238 / Root 1 | `bc7c81c3a3f505c2bd7af151219c7feb46ff7bea5d6d0e91400467a49f697a38` |
| 12104463830 / Root 2 | `71d6c6e3f0db6f422cd980be4624507f11c7a8a1794397eff6e726cd48883d9a` |
| 12105060733 / Root 3 | `6b4bcb49af4898dc1e1104011a7577feb67baa783c8d31ab64065fbeb511b2fe` |
| 12103914940 / 嵌入式 | `f2ba78471a09a64bdc1934fe814543b00d30edbdf6c5e0fb16742a6938f031b7` |
| 12105500550 / ART 取证文本 | `991effd5b3636525d23cceaca47a26de907d041ee73a01301e7194fb7579e5ff` |

## 原生侧的可检验解释

[只读取证运行](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39043945291) 的 libart Build ID 与原始 tombstone 完全一致：`62338b1c62e3991543c9b8b8bae2b361`。反汇编显示：原始线程启动栈涉及 GOT `0xa21858`；信号处理器随后在 `0x503641` 读取另一个 GOT 指针，寄存器 r12=0，二次访问地址 `0xd`。这不是已证实的 Java 模块异常，也不是 Thread::Current 空指针结论。

固定版本的 [Vector 多 DEX 加载器](https://github.com/JingMatrix/Vector/tree/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/xposed/src/main) 使用 `parallelStream()`；实际失败模块只有三个很小的 DEX。固定版本 [Magisk Zygisk](https://github.com/topjohnwu/Magisk/blob/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/native/src/core/zygisk/hook.cpp) 在模块加载后通过 PLT Hook 安排卸载；其固定 [LSPlt 实现](https://github.com/LSPosed/LSPlt/blob/cef80a97a73184b4def9b3e1148884365fc173fd/lsplt/src/main/jni/lsplt.cc) 先移走映射，再映射零填充页并复制内容，存在并发读取窗口。工作线程与映射替换竞态是当前领先假设，**尚非完整因果证明**。

下一项单变量候选：仅将本项目模块设为单 DEX，不修改框架、不重放包回调、不扩大作用域。`check-module-dex.py` 已对旧实际 APK 失败，准确报告三个 DEX；新构建必须通过同一检查，再执行原有负对照、额外 100 次冷启动、100 轮混合生命周期、作用域切换、重启恢复和完整崩溃采集。启动实验记录实际线程名称；保留临时模块入口日志以便比较，定位结束后移除并再做干净验收。即使全绿，也只能先称为候选缓解，不能证明罕见原生竞态彻底消失。

## 尚未证实的嵌入式解释

优先检查包回调是否实际送达，再区分模块提前返回/安装异常与标记单独失效。固定上游源码中的 LoadedApk 跟踪和回调条件是检查点，但尚无证据支持重放回调或绕过作用域。

固定 LSPatch 的 LoadedApk getter、初始化 Hook 与跟踪条件需要进一步对照；暂不改动第三方框架，也不添加 Application.attach 等绕过框架回调/作用域的后备入口。先观察单 DEX 候选是否仍出现相同回调缺失，再决定最小上游实验。

## English

Latest, 2026-10-19: run `39138791733` at `ed1fef2` is FAIL, with its complete 35-file device archive and workflow text now downloaded. API SHA-256, CRC, START/END coverage and all nine required diagnostics independently passed; 39,475,137 raw logcat bytes are retained. Capture completeness does not change the failed operation. The run passed 45 Java tests, 32 smoke assertions, three missing-module negatives, 100 extra cold starts and mixed cycles 1–80. Cycle 81 timed out on the second cold launch of the **unprotected control**, not on the protected app's old cycle 96.

The guest kernel reports a 66-second workqueue lockup in `virtio_transport_send_pkt_work` / `iowrite16`, alongside a 65.8-second system-main delivery delay and QEMU CPU-hang warnings. This directly establishes an emulator-level stall in this run, not the complete low-level cause. No unexpected target crash/ANR was detected in its fully covered window; the crash buffer is empty and the latest exit records are test-induced force stops. All 211 protected PIDs have exactly one constructor, package callback and successful hook installation. Module DEX, manifest and resources match the first single-DEX candidate. None of this reconstructs the old missing cycle-96 archive or establishes that failure's cause.

The timeout diagnostic also missed failures inside the start command itself. A real CLI/fake-ADB transport-stall regression failed before the repair; all 38 script tests pass afterwards. Command partial output, the original exception and bounded read-only triage are retained, without retry or relaxed deadlines. This repairs an evidence boundary, not application startup behavior.

The pipe experiment [39188889405](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39188889405) at `9ebff18` is FAIL before installing test APKs: ADB remained offline until the original boot deadline. Its 12-file build/test archive passed API SHA-256/CRC verification and 45 Java tests, but zero application cycles or complete device captures ran. It did not exercise mixed lifecycle behavior and cannot support the workaround hypothesis. The feature override has been removed and original transport restored.

The next renderer experiment is [39189752398](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39189752398) at `35d3b02f0adaa5818e6f79e510e40fbf8d307657`. Relative to the original environment, only `-gpu swiftshader_indirect` becomes `-gpu swiftshader`. The original emulator was 37.2.12.0; [Android's official configuration guide](https://developer.android.com/studio/run/emulator-acceleration) marks the former mode deprecated since 36.4.9 and supports the latter. Original GL-context errors plus the guest communication stall motivate this bounded test, not a proven causal explanation. Module/fixture source, pinned frameworks, 100 extra starts, 100 mixed cycles and deadlines remain unchanged; 38 script tests pass. The run subsequently failed with complete evidence verified. See [the exact failure index](evidence/timeout-triage-ed1fef2-index.json). The renderer-only experiment completed 100 additional starts and 80 mixed cycles before the unprotected control launch timed out in cycle 81. Full 37-file archive SHA/CRC, 38,965,545-byte live log coverage, all nine diagnostics and behavioral records were independently verified. Guest kernel evidence shows RCU stalls and a 35-second CPU soft lockup, with RenderThread and binder sampled in goldfish_pipe_read_write; this differs from the previous virtio workqueue stack and does not establish one shared low-level cause. Immediate read-only triage preserved partial launch output and exit history; PID lookup timed out at its three-second bound. No unexpected target crash/ANR was found in the covered window or independent snapshot scan. All 211 protected PIDs have one constructor, callback and hook-install record. The next bounded [order-only experiment 39282982075](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39282982075), source 3ce7b4569923a56ea162249966abe0f4b10e0591, retains both full suites but runs the original 100 mixed cycles before the extra 100 starts. All deadlines, assertions, restoration and full capture remain unchanged; any failure still fails the run. This tests prior-load dependence, not a verified product fix. See [renderer index](evidence/renderer-35d3b02-index.json). No physical devices or stable release are included.

Latest collector retest: all three Root jobs in run `39133520265` at `8a2dce8` passed independent archive verification, not just the workflow status. Each 475-file ZIP matches the API SHA-256 and passes CRC, 100 mixed cycles, 96 smoke assertions, scope switches after cycles 20/60, recovery after cycles 40/80, four actual reboots, both crash calibrations and 33 complete capture segments with all nine required diagnostics. All segments use the raw stream; snapshot recovery was not exercised in this Android run. Across the three trials, 300 cycles, 288 assertions and 99 complete segments passed, with no unexpected target crash/ANR detected in covered functional windows. This remains bounded mitigation evidence, not proof that the rare original native race is eliminated.

Embedded run `39133422677` at `10347d0` is FAIL. Its available workflow text records 100 extra cold starts and mixed cycles 1–95 passing, then an empty state on the protected app's second cold launch in cycle 96. The original eight-second state deadline failed at 14:14:54 UTC; the runner received a shutdown signal at 14:15:24 before uploading any device archive. Full device logs are unavailable, so a crash cannot be excluded or attributed to the framework/host. No Hook=false state was observed for this failed launch. The complete available workflow text is retained; it cannot replace missing device evidence.

The state-timeout diagnostic adds only bounded, read-only crash-buffer, exit-info and PID output before full cleanup. It neither restarts the app nor injects motion, changes the original deadline or turns failure into success. A real CLI/subprocess-boundary regression failed before this output was added and passes afterwards; 37 script tests passed at that source. [Android validation 39138791733](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39138791733) at `ed1fef2fc87a18fe1f1e41b60eaa7b574cc0992a` subsequently failed with complete evidence as recorded above. Exact archive metadata is in [coverage-8a2dce8-index.json](evidence/coverage-8a2dce8-index.json). Temporary debug logs remain; no stable release or physical-device testing is performed.

Latest single-DEX candidate: embedded run `39089887806` passed 100 extra cold starts, all 100 mixed cycles, 40 smoke assertions, 45 Java tests, three missing-module negatives and baseline restoration. Its 36-file archive passed SHA-256/CRC and full capture-manifest checks. Each of 235 PIDs has exactly one module construction, package callback and successful installation; no ForkJoin worker appeared in the 100 recorded startup thread lists. This is bounded evidence for a mitigation, not proof of a root-cause repair or a clean release.

The same-source Root run `39089919305` failed in all three environments. Trials 1 and 3 completed 100 cold starts and 60 mixed cycles before QEMU hangs and runner shutdown; no diagnostic artifacts were uploaded. Trial 2 completed 100 starts and 67 mixed cycles, then timed out restoring the protected app, lost emulator transport and retained only 27/28 complete capture segments. All available workflow logs and trial 2's CRC/SHA-verified ZIP are preserved. Missing device logs cannot be reconstructed or treated as absence of a crash.

Run `39091836244` isolated the original 100-cycle Root acceptance from the extra startup diagnostic, but all three jobs failed before mixed cycles: initial ADB loss (0/1 complete captures), CLI readiness failure (2/2 complete) and an END marker absent from the live stream after 32 successful smoke assertions (9/10 complete). All three archives and workflow logs were downloaded and SHA-256/CRC checked. The initial host had about 11GB available RAM and 81GB free disk; accumulated-load causality remains untested.

The third failure exposed a collector defect: its 49,341-record snapshot contains all 49,297 raw stream records byte-for-byte in order and both markers. A red-then-green regression now permits this strictly verified coverage source while retaining the unchanged raw stream and warning. Missing/reordered records, missing markers or a target crash found only in the snapshot still fail. All nine diagnostic-command checks remain mandatory; 34 script regressions pass. Historical failures remain FAIL.

Collector validation runs are embedded `39133422677` at `10347d0` and three-environment Root `39133520265` at `8a2dce8`. The Root addition collects native/Java framework stacks only after the original readiness deadline has failed, without restarting the framework or converting failure to success. The final results are recorded above: Root passed all three trials, while embedded failed at cycle 96 with missing device evidence. The original 100 mixed cycles, 96 smoke assertions, four reboots, scope boundaries, calibration and 33 complete capture segments remain required in stress mode.

Historical diagnostic experiment: both causes remained open. The pinned experiment added 100 ordinary-page cold starts before the unchanged mixed lifecycle suite. On a page assertion failure, it preserves the original state/PID, opens the real sensor probe without force-stopping the process, injects fresh light and motion, and requires PID continuity before classifying behavior. Missing/dead/replaced processes or incomplete evidence are inconclusive. The original assertion still fails regardless of diagnosis.

Thirty-one local script tests pass; Android results must be read separately from the linked runs and full artifacts. Temporary module-construction/package-entry logs are tagged `[DEBUG-startup]` and must be removed after diagnosis. Root now expects 34 capture segments on a complete successful run. Fixed upstream versions, scope controls, crash calibration, negative controls and original evidence are preserved. No physical-device testing or stable release is performed.

Root trial 3 failed before installing test APKs: after the framework-install reboot, Vector's CLI socket remained absent for the bounded 90-second readiness check. Both evidence segments are complete and the boot ID changed, but the operation failed. This is a separate environment failure, not reproduction of either original bug. Its complete 26-file archive was downloaded and SHA-256/CRC checked; no timeout increase or automatic retry was used to hide it.

Root trials 1 and 2 each passed the additional 100 cold starts, then stopped after 60 and 66 mixed cycles respectively. Trial 1 lost the emulator/ADB during rescoped smoke; its final crash capture is incomplete. Trial 2 timed out starting the unprotected control at cycle 67 with complete collection and no detected target crash. Embedded passed 100 cold starts and 43 mixed cycles, then failed at cycle 44: module construction was logged but package callback entry was absent, with motion sensor callbacks still delivered. No failure has been converted to PASS.

Matching-Build-ID ART disassembly and pinned Magisk/LSPlt source support a possible worker-thread versus GOT-remapping race. The next single-variable candidate disables unnecessary multi-DEX output in this small module. The actual old APK fails the new packaging check with three DEX files; the newly built APK must pass before emulator acceptance. This is a mitigation hypothesis, not a verified framework repair. No callback replay, scope bypass, framework upgrade, physical-device testing or stable release is included.
