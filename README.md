# 屏蔽摇一摇跳转插件

基于 Sensor Disabler 的 Android 防运动触发跳转实验工程，当前为 **0.2 私有验证版**。

**不是免 Root 成品，不支持 iPhone。Root 整机兼容性、与现有工具的对比测试和法律审查尚未完成。GitHub 托管、免费或开源都不能消除法律风险。**

2026-09-25 验证：41 项 JVM/Robolectric 测试通过；[云端构建与 8 项未启用 Hook 的设备基线通过](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36128471909)。未加载模块时的保护测试按预期失败，没有将基线通过冒充真实拦截成功。详见[验证证据](docs/verification.md)。

2026-09-26：复用 LSPatch v1.2 的真实 Xposed 引擎，自建靶场三轮保护测试及移除后的恢复基线全部通过。仅此固定组合，不代表 Root 管理器或商业 App 兼容性。[第二阶段结果](docs/embedded-hook-results.md) · [开源项目复用取舍](docs/reuse-research.md)

第三阶段：复用 Magisk v30.7 官方模拟器工具与 Vector v2.2 官方 CLI，原始 APK 在 Root 模拟器上六阶段共 48 次断言通过，包含真正重启、移除作用域和停用恢复。[结果及边界](docs/root-results.md)。

## 当前能做什么

- 模块首页提供安装检查、保护组/对照组探针入口、测试广告入口和停用说明。未安装、停用或版本不匹配时禁用测试入口；不会把“已安装”显示成“保护已生效”。
- 在用户明确配置的 Xposed 作用域内隐藏列出的 Java 运动传感器并拒绝监听注册。保护持续到进程结束，包括后台；不修改全机传感器开关。
- 自动关闭只针对本项目靶场 v1：包名、版本、页面、父页面、焦点和按钮标记必须满足规则。不会为真实商业 App 自动点击或结束广告页。
- 光线、距离等非运动传感器不在屏蔽策略中；普通页面即使出现同名按钮也不应被操作。

## 最短验证路径

1. 在专用 Android 测试环境准备兼容 legacy Xposed API 82 的框架。固定 API 35 x86_64 模拟器已验证 Magisk v30.7 + Vector v2.2；不提供一键 Root，不据此承诺真机兼容。
2. 安装同一次构建生成的模块、保护组、对照组三个 APK。
3. 打开模块首页，按清单设置作用域：仅勾选 `dev.antishake.fixture.protectedapp`，不要勾选对照组或其他 App。
4. 强制停止两个靶场后重开。先验证对照组会因运动跳转，再验证保护组；严格结果以黑盒测试脚本为准。
5. 恢复时先停用模块或取消作用域，然后强制停止并重新打开目标 App。仅退出模块界面不会解除已经注入的 Hook。

## 构建

Java 17、Android SDK `platforms;android-35` 和 `build-tools;34.0.0`；设置 `JAVA_HOME` 和 `ANDROID_HOME`：

```sh
cd validation
./gradlew :policy:test :guard:testDebugUnitTest \
  :fixture:testProtectedAppDebugUnitTest :fixture:testControlDebugUnitTest \
  :guard:assembleDebug :fixture:assembleDebug \
  :guard:lintDebug :fixture:lintProtectedAppDebug :fixture:lintControlDebug
```

模块 APK 在 `validation/guard/build/outputs/apk/debug/`；两个靶场 APK 在 `validation/fixture/build/outputs/apk/` 各自变体目录。
CI 生成的调试 APK 签名可能随全新 runner 改变，不能承诺跨构建覆盖安装；请使用同次构建的一组 APK。不要上传私钥或调试 keystore。

## 证据与边界

- [验收标准与对比计划](docs/acceptance.md)
- [构建与设备黑盒复测](validation/README.md)
- [验证状态](docs/verification.md)
- [三环境重复性复测（144 次场景断言通过）](docs/repeatability-testing.md)
- [专用 Android 真机验收表（未执行）](docs/device-acceptance.md)
- [安卓测试者安装包说明](docs/tester-kit.md)
- [Node 24 构建工具维护与复测](docs/ci-maintenance.md)
- [双轴代码审查](docs/review.md)
- [安全与发布边界](SECURITY.md)
- [上游来源与许可证](NOTICE.md)

GitHub Actions 常规检查 JVM/Robolectric、Lint、APK 构建、无 Hook 基线、LSPatch 嵌入式真实 Hook 三轮测试及恢复基线。独立手动 Root 工作流验证 Vector CLI 作用域与重启恢复。CI 全绿只证明固定框架和靶场组合；管理器图形界面和真机仍须另行验收。框架工具及打补丁后的 APK 不进入交付产物。

“更容易启用、更少误伤、更稳定”是待证明的目标，不是已经胜过其他工具的宣传结论。当前不公开发布、不提供商业 App 兼容承诺，不替换广告、不重定向流量、不伪造广告展示/点击事件。
