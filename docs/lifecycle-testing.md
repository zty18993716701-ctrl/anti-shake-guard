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

修复仅将启动参数改为 `-f 0x10008000`（NEW_TASK | CLEAR_TASK），并在任务日志输出新负例的错误。数值来自本地 API 35 的 `android.content.Intent` 常量。复测结果待执行；此处尚未记 PASS。本机 Gradle 因 `java.net.SocketException: Operation not permitted` 未执行，不能替代上述云端结果。

第二轮 [38843792000](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38843792000)，提交 `4094d6cd39c24f544df14f8f60992816d908c554`，在继续加固判据后由后继提交替代，不记整轮 PASS。补充运动后及广告/普通页等待后的 PID 存活与一致性检查，避免进程崩溃后仅凭落盘旧状态通过；原有判据均保留。

取消前的第二轮日志实际已记录三轮 Hook 冒烟通过、生命周期前两轮通过；第三轮后台恢复停在 `MAIN / resumes=0` 并超时。新启动参数被接受，但 Launcher 返回创建了首页，没有恢复探针，不算模块拦截失败。下一修复假设为：首次启动也显式指定 ACTION_MAIN / CATEGORY_LAUNCHER，使任务与随后 Launcher 返回的 Intent 匹配。通过条件仍须恢复到 PROBE、同一 PID、resumes=2，没有将后台恢复改成重开页面。加入存活检查的过渡运行 [38844253287](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/38844253287) 也由此修复替代，不记整轮 PASS。

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

Missing hooks, stale sensor evidence, unexpected process restarts, unintended ordinary-page clicks and incomplete runs fail the suite. This is embedded LSPatch validation on an API 35 x86_64 emulator, not Root/Vector or physical-device validation. It contains no device reboots and does not establish comparative reliability, commercial-ad compatibility, or product readiness. Current cloud results are pending; do not interpret the test plan as a pass record.
