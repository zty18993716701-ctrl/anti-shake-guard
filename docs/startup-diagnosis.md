# 启动期故障定位 / Startup failure diagnosis

状态：**调查中，尚未证实修复**。只测试一次性 Android API 35 x86_64 模拟器；不测试真机或商业 App，不替换历史测试包。

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
