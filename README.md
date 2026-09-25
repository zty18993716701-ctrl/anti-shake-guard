# 屏蔽摇一摇跳转插件

基于 Sensor Disabler 的 Android 防运动触发跳转实验工程，当前为 **0.2 私有验证版**。

**不是免 Root 成品，不支持 iPhone。真实 Hook 兼容性、与现有工具的对比测试和法律审查尚未完成。GitHub 托管、免费或开源都不能消除法律风险。**

## 当前能做什么

- 模块首页提供安装检查、保护组/对照组探针入口、测试广告入口和停用说明。未安装、停用或版本不匹配时禁用测试入口；不会把“已安装”显示成“保护已生效”。
- 在用户明确配置的 Xposed 作用域内隐藏列出的 Java 运动传感器并拒绝监听注册。保护持续到进程结束，包括后台；不修改全机传感器开关。
- 自动关闭只针对本项目靶场 v1：包名、版本、页面、父页面、焦点和按钮标记必须满足规则。不会为真实商业 App 自动点击或结束广告页。
- 光线、距离等非运动传感器不在屏蔽策略中；普通页面即使出现同名按钮也不应被操作。

## 最短验证路径

1. 在专用 Android 测试环境准备兼容 legacy Xposed API 82 的框架。这里不提供一键 Root，也尚无经本项目实测的框架版本可声明兼容。
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
- [安全与发布边界](SECURITY.md)
- [上游来源与许可证](NOTICE.md)

GitHub Actions 检查 JVM/Robolectric 测试、Lint、APK 构建，以及**未启用 Hook**的 Android 模拟器基线。即使 CI 全绿，也不代表 Xposed 拦截有效；`hooked` 模式必须在实际启用框架的设备上另行验收。

“更容易启用、更少误伤、更稳定”是待证明的目标，不是已经胜过其他工具的宣传结论。当前不公开发布、不提供商业 App 兼容承诺，不替换广告、不重定向流量、不伪造广告展示/点击事件。
