# 第二阶段真实嵌入式 Hook 测试结果

2026-09-26（北京时间），提交 `d4fe31a5ce22cda41325b88e06b38ab17016958f`。

[Actions 运行 #4](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36160645136) **全部通过**。Java 17 构建与 41 项 JVM/Robolectric 回归、Lint、APK 构建通过；Java 21 执行固定版本 LSPatch，工具 SHA-256 及嵌入模块逐字节校验通过。

环境：GitHub Ubuntu runner、Android API 35/google_apis/x86_64 模拟器、JingMatrix/LSPatch v1.2-487。目标仅为本项目靶场 v1；未修改任何商业应用。

| 阶段 | 结果 |
| --- | --- |
| 原 APK、无模块基线 | 8/8 PASS，两组运动均会跳转 |
| 无模块时运行保护验证 | 按预期失败，检查精确的未加载模块原因 |
| 嵌入真实框架与本次模块：第 1 轮 | 8/8 PASS |
| 同一环境：第 2 轮 | 8/8 PASS |
| 同一环境：第 3 轮 | 8/8 PASS |
| 移除补丁 APK、恢复原始保护组 | 8/8 PASS，两组运动均恢复跳转 |

共 40 次断言执行（包含重复场景，不是 40 种不同测试），另含未加载模块的负例检查。

每轮保护验证均观察到：对照组有真实运动事件并跳转；保护组 Hook 标记为 true、可见加速度计/陀螺仪为 0、运动事件为 0、摇动后停留探针页；两组收到 123 lux 光线事件。保护组立即/延迟按钮广告自动关闭，缺按钮返回已确认父页面，普通页面没有误点。没有通过修改传感器探针或断言来制造通过。

## 证据

- [精简原始 JSONL](evidence/embedded-hook-d4fe31a.jsonl)：从完整日志提取 45 行；顺序为前置基线、三轮 hooked、恢复基线，各 8 条断言 + 1 条汇总。
- [私有 Actions 产物](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36160645136/artifacts/10875826273)：JUnit、Lint、原始 APK、设备指纹、传感器列表、逐轮 JSONL、模块负例日志、框架日志及文件哈希。按工作流保留 7 天。
- [测试实现与固定依赖](embedded-hook-testing.md)、[双轴审查](embedded-hook-review.md)、[同类项目复用评估](reuse-research.md)。

## 仍未证明的事情

本轮是**真实 Xposed 引擎在自建 APK 内的运行验证**，不是 Root/Zygisk 系统注入或管理器作用域验证。三轮场景会重启测试进程，但不覆盖设备重启、100 次稳定性、真实 ARM 手机、厂商 ROM、NDK/direct channel、商业广告 SDK，也不证明全场景“怎么动都不会跳转”。光线检查不是所有非运动传感器的全覆盖。

没有改变模块 APK 的核心实现，也没有并入其他拦截模块。复用的是外部测试框架，节省了自行实现 Hook 运行时的工作。真实 Root 环境、竞品对照、用户体验和法律审查仍待完成；仓库维持私有。
