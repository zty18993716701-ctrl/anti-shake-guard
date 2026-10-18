# 启动期故障定位 / Startup failure diagnosis

状态：**调查中，尚未证实修复**。只测试一次性 Android API 35 x86_64 模拟器；不测试真机或商业 App，不替换历史测试包。

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

Both failures remain open. The pinned experiment adds 100 ordinary-page cold starts before the unchanged mixed lifecycle suite. On a page assertion failure, it preserves the original state/PID, opens the real sensor probe without force-stopping the process, injects fresh light and motion, and requires PID continuity before classifying behavior. Missing/dead/replaced processes or incomplete evidence are inconclusive. The original assertion still fails regardless of diagnosis.

Thirty-one local script tests pass; Android results must be read separately from the linked runs and full artifacts. Temporary module-construction/package-entry logs are tagged `[DEBUG-startup]` and must be removed after diagnosis. Root now expects 34 capture segments on a complete successful run. Fixed upstream versions, scope controls, crash calibration, negative controls and original evidence are preserved. No physical-device testing or stable release is performed.

Root trial 3 failed before installing test APKs: after the framework-install reboot, Vector's CLI socket remained absent for the bounded 90-second readiness check. Both evidence segments are complete and the boot ID changed, but the operation failed. This is a separate environment failure, not reproduction of either original bug. Its complete 26-file archive was downloaded and SHA-256/CRC checked; no timeout increase or automatic retry was used to hide it.

Root trials 1 and 2 each passed the additional 100 cold starts, then stopped after 60 and 66 mixed cycles respectively. Trial 1 lost the emulator/ADB during rescoped smoke; its final crash capture is incomplete. Trial 2 timed out starting the unprotected control at cycle 67 with complete collection and no detected target crash. Embedded passed 100 cold starts and 43 mixed cycles, then failed at cycle 44: module construction was logged but package callback entry was absent, with motion sensor callbacks still delivered. No failure has been converted to PASS.

Matching-Build-ID ART disassembly and pinned Magisk/LSPlt source support a possible worker-thread versus GOT-remapping race. The next single-variable candidate disables unnecessary multi-DEX output in this small module. The actual old APK fails the new packaging check with three DEX files; the newly built APK must pass before emulator acceptance. This is a mitigation hypothesis, not a verified framework repair. No callback replay, scope bypass, framework upgrade, physical-device testing or stable release is included.
