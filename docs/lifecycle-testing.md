# 混合生命周期验证 / Mixed lifecycle validation

## 范围与通过条件

在常规 API 35 / x86_64 GitHub 模拟器上，用同一轮构建的模块和两个自建靶场运行。使用固定 LSPatch 将真实模块嵌入保护组；对照组保持原始 APK。不是 Root / Vector 环境，也不是物理设备测试。

100 轮按下列五种情况交替执行，每种 20 轮；一轮中的所有检查必须通过才记 PASS。运动轮分别验证对照组与保护组，不把同一轮内的多条字段检查当作不同测试场景。

| 轮次类型 | 动作与通过条件 |
| --- | --- |
| cold | 先建立探针，再强制停止并重新打开；PID 必须变化 |
| warm | 先建立探针，再清理并重开测试任务；PID 必须不变。这是同进程页面重开，不是 Activity 实例复用 |
| background | 探针 → Home → Launcher 返回原任务；PID 不变，探针恢复次数从 1 变 2 |
| ad | 交替打开即时关闭按钮、延迟按钮和无按钮广告；回到 MAIN，分别为 CLOSED / RETURNED，无运动跳转与普通按钮误点 |
| normal | 保持普通页面至少 3 秒；仍为 MAIN / NONE，无点击、无跳转 |

前三类运动轮：先确认 PROBE 未跳转；注入本轮特有光线值并确认实际光线事件；再注入运动。对照组必须收到运动事件并进入 TARGET，保护组必须有真实 Hook 标记、0 个运动传感器、0 个运动事件且留在 PROBE。PID、恢复次数和状态快照全部写入每轮 JSONL。此诊断字段不参与模块的保护或关闭决策。

测试驱动独立于 `emulator-smoke.py` 检查结果；未加载模块时必须以明确原因失败。任一断言、ADB 错误或超时使工作流失败；输出保留已完成轮次和错误，不将不完整执行补记为 100 轮成功。额外的 100 次 Robolectric 暂停/恢复循环只验证靶场监听器注销与重新注册，不能替代 Xposed 测试。

## 本轮执行

2026-10-16：首轮 [38843150188](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38843150188)，提交 `fcef681706ce8a4e57c78a3aba9b44f5927f122f`，整体 FAIL。8 项 Python 回归、Java / Robolectric、构建、Lint、8 项未启用基线与原缺模块负例通过；新的生命周期负例在启动阶段因 `Unknown option: --activity-new-task` 失败，未进入 Hook / 100 轮阶段。产物 ZIP 已下载并核对 SHA-256 `4990df59a240e53489ad9f96faf6519cacfe1a30ac1df13c4606bb7b4e78f13c`。原因由该 ZIP 中 `lifecycle-no-hook-negative.txt` 的原始堆栈确认；不是保护断言失败。

第一步修复仅将启动参数改为 `-f 0x10008000`（NEW_TASK | CLEAR_TASK），并在任务日志输出新负例的错误。数值来自本地 API 35 的 `android.content.Intent` 常量。当时尚未记 PASS；最终结果见下。本机 Gradle 因 `java.net.SocketException: Operation not permitted` 未执行，不能替代云端结果。

第二轮 [38843792000](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38843792000)，提交 `4094d6cd39c24f544df14f8f60992816d908c554`，在继续加固判据后由后继提交替代，不记整轮 PASS。补充运动后及广告/普通页等待后的 PID 存活与一致性检查，避免进程崩溃后仅凭落盘旧状态通过；原有判据均保留。

取消前的第二轮日志实际已记录三轮 Hook 冒烟通过、生命周期前两轮通过；第三轮后台恢复停在 `MAIN / resumes=0` 并超时。新启动参数被接受，但 Launcher 返回创建了首页，没有恢复探针，不算模块拦截失败。下一修复假设为：首次启动也显式指定 ACTION_MAIN / CATEGORY_LAUNCHER，使任务与随后 Launcher 返回的 Intent 匹配。通过条件仍须恢复到 PROBE、同一 PID、resumes=2，没有将后台恢复改成重开页面。

加入存活检查的第三轮 [38844253287](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38844253287)，提交 `ce2de112e3af6c0d3fa9c8a1c0bcaf1f95a78590`，实际最终状态为 FAIL；同样在后台恢复停在 MAIN 超时。它在统一 Launcher Intent 前完成，保留此失败，不按“已被替代”掩盖结果。

## 最终复测结果

**PASS，2026-10-16。** 第四轮 [38867678747](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38867678747)，提交 `cd3befcfd943d090b55d57b0511e44418967df42`，首次尝试 `run_attempt=1`，job `116864162857`，任务用时 15 分 48 秒。全新 API 35 / google_apis / x86_64 云端模拟器，LSPatch v1.2 / 487；没有使用 Root / Vector。统一 Launcher Intent 后，后台轮次实际恢复到原探针，PID 保持不变且恢复计数为 2，支持上述脚本修复假设。

| 项目 | 实际结果 |
| --- | --- |
| Python 证据判据与超时回归 | 8/8 PASS |
| JVM / Robolectric | 45/45 PASS，0 skipped / failures / errors |
| 靶场暂停/恢复循环 | 新测试在两个 APK 变体 × API 28/35 共执行 4 次，每次 100 个循环；只验证靶场框架模拟 |
| 三个原始 APK 构建与 Lint | PASS；不表示既有原型提醒或模拟器日志警告全部消失 |
| 未启用原始基线 | 8/8 PASS |
| 两套缺模块负例 | 均按预期失败；新套件明确报 Module not loaded，未误报保护成功 |
| 三轮嵌入式 Hook 冒烟 | 3 × 8/8 PASS |
| 混合生命周期 | 100/100 PASS，五类各 20 轮；其中运动轮为 60 对保护/对照检查 |
| 移除补丁、恢复原始 APK | 基线 8/8 PASS |

100 轮中，冷启动 PID 改变；同进程重开与后台恢复 PID 不变；运动注入和页面等待结束后的进程仍存在且 PID 未改变。20 轮广告由即时按钮 7 轮、延迟按钮 7 轮、无按钮返回 6 轮组成；20 轮普通页面无自动点击或跳转。非运动光线读数使用随轮次变化的值。此轮没有观察到判据内的漏拦、意外进程退出/重启或普通页面误操作，但不能将有限观测推广为“所有场景无崩溃”。

- [持久行为 JSONL](evidence/lifecycle-cd3befc.jsonl)：146 行，含 100 条生命周期结果及 1 条汇总、40 条原有场景断言及 5 条汇总。来自完整任务日志，仅增加 phase 标签；不是 140 种独立测试。
- [同轮产物](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38867678747/artifacts/12033055041)：24 个文件，包含三个原始调试 APK、JUnit XML、Lint 与设备证据，保留至 2026-10-23。ZIP 已实际下载，CRC 及 SHA-256 `999123f5d14122f903dca4946286e5956cc9a0c1fc4dd8f3614b2e07cfe1d546` 均核对通过；归档的 101 条生命周期记录与 ZIP 内原始 JSONL 完全一致（忽略新增 phase 标签）。45 项 Java 测试数量和零失败由 ZIP 内 XML 核对，不只依据绿色任务状态。

本轮没有修改模块的传感器过滤策略、权限、作用域或关闭规则；应用侧仅增加靶场恢复计数供诊断。没有更新历史 2026-10-07 测试包，也没有创建稳定版 Release。

产物中的 `lspatch-logcat.txt` 为空，不以该日志宣称“没有 Java 崩溃”。本轮进程状态结论仅来自每轮的 PID 存活/一致性检查及行为断言；完整崩溃日志采集仍可继续改进。

## 手动复测

仅在一次性模拟器已安装同轮 APK、保护组加载模块且对照组未加载模块后，从 `validation` 执行：

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/emulator-lifecycle.py --serial emulator-5554
```

脚本会强制停止、清理两个自建测试任务与诊断文件，注入虚拟传感器；拒绝非 `emulator-` 编号。不连接日常手机。CI 在原始基线后验证缺模块负例，在三轮 Hook 冒烟后执行 100 轮，最后卸载补丁恢复原 APK 再跑原始基线。模拟器步骤仍受工作流时限约束。

## 不能据此得出的结论

- 不包含设备重启；既有独立 Root 重启结果仍只属于其原测试提交。
- 不验证 NDK / direct channel、厂商 ROM、真实商业广告 SDK 或 ARM 真机。
- 没有与其他工具对照，也没有完成 5 名独立用户体验；不能宣称“更稳定”或完成产品级 100 次混合验收。
- 老测试包保持不变；本轮靶场新增恢复计数，测试应使用本轮 CI 的配套 APK，不混用历史包。

## English summary

The regular CI adds 100 alternating cycles: 20 cold process restarts, 20 same-process task reopenings, 20 Home/Launcher round trips, 20 fixture-ad closures, and 20 ordinary-page observations. Motion cycles verify both the unprotected control and the actually hooked fixture, including per-cycle light input, navigation, PID changes/preservation, and resume counts. Each cycle is one composite result, not a new distinct scenario.

Missing hooks, stale sensor evidence, unexpected process restarts, unintended ordinary-page clicks and incomplete runs fail the suite. This is embedded LSPatch validation on an API 35 x86_64 emulator, not Root/Vector or physical-device validation. It contains no device reboots and does not establish comparative reliability, commercial-ad compatibility, or product readiness.

Final run [38867678747](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38867678747), commit `cd3befcfd943d090b55d57b0511e44418967df42`, passed on 2026-10-16: 8 Python checks, 45 JVM/Robolectric executions, build/Lint, 40 existing smoke assertions across baseline/hooked/restoration phases, both missing-module negative checks, and all 100 lifecycle cycles. Each type completed 20 times. All 60 motion cycles checked both fixtures; background probes resumed twice in the same process. Final-process checks detect missing/restarted processes rather than trusting persisted screen state alone.

Two harness issues were found and retained in the history: API 35 rejected a named launch flag, and mismatched initial/return intents created a new launcher page instead of resuming the probe. Numeric Intent flags and matching MAIN/LAUNCHER intents fixed these issues without relaxing the assertions. The first and third runs failed; the second was cancelled and its partial output also recorded the background-return failure. No partial run is counted as a pass.

The downloaded final artifact passed ZIP CRC/SHA-256 checks; its 101 lifecycle records match the permanent JSONL archive, and its JUnit XML confirms 45 executions with no failures, errors, or skips. The module policy, permissions, scope and closing rules are unchanged; only fixture resume diagnostics and test infrastructure were extended. Historical tester packages remain unchanged.
