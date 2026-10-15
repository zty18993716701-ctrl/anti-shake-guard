# 验证状态

2026-09-25，0.2 私有验证版；2026-09-26 增补嵌入式 Hook 与 Root / Vector 结果；2026-10-01 完成三独立环境复测。

本地 JVM / Robolectric：41 项测试通过，包括 8 项纯策略、6 项模块启用引导、3 项 Hook 回滚、24 项靶场测试。
Android 框架模拟分别使用 API 28 和 35，不执行 Xposed 注入。
模块与两个靶场均可构建，三个本地 APK 签名校验通过。Lint 为 0 错误；模块 4 项、两个靶场各 5 项 warning，未隐藏这些原型界面及配置提醒。

新增的未安装入口、未知父页面、过期版本按钮和 Activity 重建回归均观察到修改前失败、修改后通过。
传感器证据仍逐事件记录，界面读数改为手动刷新快照；新增回归确认实时证据不持续改写无障碍界面树，修改前失败、修改后通过。

| 层级 | 状态 |
| --- | --- |
| 本地策略/页面回归 | PASS |
| 本地 APK 构建 | PASS |
| 本机 Android Emulator 37.1.11 / API 35 arm64 | 启动失败，SIGILL / init_cache_info；无设备结果 |
| GitHub Linux / API 35 x86_64 基线 | PASS，8 项；未启用 Hook |
| 未加载模块时不得通过 hooked 验证 | PASS，按精确失败原因检查，不接受任意报错 |
| LSPatch v1.2 真实嵌入式 Hook | PASS，3 轮 × 8 项，随后恢复原始 APK 的 8 项基线通过；[证据](embedded-hook-results.md) |
| Root 模拟器 / Vector 拦截及自动关闭 | PASS，6 阶段 × 8 项；含内核重启、移除作用域、重新启用、停用恢复；[证据](root-results.md) |
| ARM 真机 / 厂商系统兼容性 | NOT RUN |
| Root 三独立环境重复性 | PASS，3 × 48 次场景断言、3 × 3 次日志回归；首次尝试全通过；[证据](repeatability-testing.md) |
| 2026-10-15 Node 24 构建工具与嵌入式 Hook 复测 | PASS，构建/代码回归及 40 次场景断言；解决临时 runner 磁盘不足；Root 新环境未复跑；[记录](ci-maintenance.md) |
| 竞品对照与用户体验 | NOT MEASURED |
| 法律审查 | NOT DONE |

云端基线通过只说明靶场和测试脚本在未启用 Hook 时能运行；不能证明保护生效。

## 可追溯证据

- 代码提交：`13e7690b18069f13f6e09fcca00fff4021cee398`。
- [完整成功运行 #3](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36128471909)，2026-09-25；构建、测试、Lint、设备基线及负例检查全部成功。
- [精简原始基线 JSONL](evidence/baseline-13e7690.jsonl)：从该运行日志逐行提取，保留 8 个断言和汇总。两组均收到 123 lux 光线事件，并因真实运动事件跳转；普通/延迟广告可由脚本定位真实按钮点击关闭，缺按钮广告保持不动，正常页面未被操作。
- `ci-baseline.sh` 在基线后运行 `hooked` 模式，要求它失败，且日志精确包含 `Module not loaded; refusing false positive`；该步骤成功。负例完整日志、设备指纹、传感器列表、JUnit、Lint 与 APK 在 [Actions 产物](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36128471909/artifacts/10861580083)，保留 7 天。
- 上述第一阶段证据对应其固定提交；后续阶段及测试设施变化见各自结果，不将旧运行结果归给新代码。

## 本轮修复记录

首次云端运行在 Android SDK 初始化失败，原因是 Action 默认请求已不存在的旧 `tools` 包；限定为 `platform-tools` 后通过。
第二次运行已通过运动/光线检查，但广告界面树读取返回空根节点。传感器回调持续刷新文字；改为手动显示快照、保持底层实时证据和导航后，第三次同一设备测试完整通过。一次成功复测不等于长期稳定性认证。
