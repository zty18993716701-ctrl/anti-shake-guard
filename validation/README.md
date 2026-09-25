# Sensor Disabler 防摇一摇验证版

基于上游 `wardellbagby/sensor-disabler` 提交
`ac2dda13bea421be2bf1bd2715e02de54a5ffdf9`（2022-03-15）。
本目录是独立验证构建，不依赖旧界面、付费或 Tasker 功能。
工作区保留完整上游；GitHub 精简仓库仅保留所需 API jar、原过滤实现参考和版权声明。
`guard` 中的传感器列表过滤改编自上游 `RemoveSensorModificationMethod.java`，
保留仓库根目录的 MIT 许可证及 Wardell Bagby 版权声明。

## 本轮验收范围

- 用户通过 Xposed/LSPosed 兼容管理器的作用域选择受保护 App，默认只推荐测试靶场。
- 受保护进程从加载开始持续隐藏明确列出的运动传感器，并拒绝 Java 层监听注册。
  本验证版的保护持续到进程结束，**包括后台**；不实现前后台切换恢复。
- 光线、距离等非运动传感器保留；未选中应用保持原行为。
- 自动关闭只针对本仓库靶场的固定包名、版本、广告 Activity 和标记控件。
  无论点击还是返回，都必须确认由靶场内容页启动；父页面未知时不操作。
  最多等待约两秒；持续无焦点的页面不会被操作，超时后停止，避免误点后台页面。
- 两个靶场 APK 使用相同源码：一个加入模块作用域，另一个不加入，用于对照。
- Java API 原型，不承诺 NDK、共享内存 direct channel、厂商私有接口或真实广告 SDK 的覆盖。
- 不适用于 iPhone；没有完成 Root 环境运行验证前，不将 APK 编译成功视为拦截成功。

## 工程约束

首次固定 Android API 35 构建、minSdk 26、Java 17 和 Gradle 8.9。
传感器策略和关闭决策通过 `policy` 的 JVM 测试；跨进程真实 Hook 效果由靶场验证。
模块不申请网络、无障碍服务或全局传感器控制权限。无真实商业 App 关闭规则。

## 构建与测试

安装 Java 17 和 Android SDK（platforms;android-35、build-tools;34.0.0、platform-tools），
设置 `JAVA_HOME`、`ANDROID_HOME`。在**本目录**执行（不要使用上一级旧工程的 wrapper）：

```sh
./gradlew :policy:test :guard:testDebugUnitTest :fixture:testProtectedAppDebugUnitTest :fixture:testControlDebugUnitTest \
  :guard:assembleDebug :fixture:assembleDebug :guard:lintDebug :fixture:lintProtectedAppDebug :fixture:lintControlDebug
```

本任务工作区已经准备好隔离工具链，可直接执行（此启动脚本不适用于单独解压的源码包）：

```sh
bash scripts/gradle-local.sh :policy:test :guard:testDebugUnitTest :fixture:testProtectedAppDebugUnitTest \
  :fixture:testControlDebugUnitTest :guard:assembleDebug :fixture:assembleDebug
```

`scripts/test-policy.sh` 是本工作区内的小型 TDD 快速循环，依赖 `work/test-libs`；
在其他电脑请优先使用 wrapper 的 `:policy:test`，它自动下载 JUnit。

生成文件：

| APK | 相对本目录的位置 |
| --- | --- |
| 模块 | `guard/build/outputs/apk/debug/guard-debug.apk` |
| 保护组 | `fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk` |
| 对照组 | `fixture/build/outputs/apk/control/debug/fixture-control-debug.apk` |

Robolectric 页面测试分别执行 API 28 和 API 35 的框架模拟；**它不会执行 Xposed**。
纯策略测试覆盖运动类型过滤、非保护应用不变、版本/页面限定、关闭优先、安全返回和焦点等待。
静态检查仍有原型界面国际化、图标、备份规则和跨应用资源查找的 warning，详见报告。

## 模拟器上的完整闭环（需要另行跑通）

准备 API 35 Android 模拟器，启用加速度计、陀螺仪和光线传感器。
将以下 `emulator-5580` 改为**明确指定的测试模拟器**编号。不要连接日常使用的手机跑此脚本。

```sh
adb -s emulator-5580 install -r guard/build/outputs/apk/debug/guard-debug.apk
adb -s emulator-5580 install -r fixture/build/outputs/apk/protectedApp/debug/fixture-protectedApp-debug.apk
adb -s emulator-5580 install -r fixture/build/outputs/apk/control/debug/fixture-control-debug.apk
python3 scripts/emulator-smoke.py --serial emulator-5580 --mode baseline
```

基线期不启用模块，两个靶场都应因运动而跳转，广告只能手动关闭。
随后在同一模拟器安装并启用兼容 legacy Xposed API 82 的 Root Hook 框架；
本交付没有替你完成或验证 Root / 框架安装，`adb root` 本身不代表具备 Xposed。
在框架管理器启用本模块，**仅勾选 `dev.antishake.fixture.protectedapp`**，
保持 `dev.antishake.fixture.control` 未选中。重新启动目标进程后执行：

```sh
python3 scripts/emulator-smoke.py --serial emulator-5580 --mode hooked
```

必须全部通过：

1. 对照组有运动事件且跳转。
2. 保护组真实 Hook 标记为 true，运动事件为 0，晃动后仍停留在探针页。
3. 两组均能收到 123 lux 的光线事件（防止误禁所有传感器）。
4. 保护组广告页及延迟按钮广告页自动关闭；缺按钮时返回已确认的父页面。
5. 普通页面即使有同名、同 ID 和同标记按钮，也不被自动操作。

脚本会强制停止两个测试包、清理各自旧探针记录并注入虚拟运动/光线值。
`hooked` 模式在框架未激活时必须失败，不能用基线通过代替保护验证。
模块作用域只约束注入目标，不是 Android 系统传感器权限；更改作用域后重启目标 App。

## 本机模拟器启动记录

工具已安装在工作区 `work/toolchains`，AVD 在 `work/avd`。
Emulator 37.1.11 / API 35 arm64 在此 macOS 环境启动失败：
无界面引擎为 `SIGILL` / `init_cache_info`；图形引擎报告 Qt 要求的 `neon` 不可用。
因此没有本机模拟器端到端结果，也没有真实广告 SDK 兼容结果。
保留 APK 和上述严格检查脚本，供可运行的 Root 模拟器环境复验。
GitHub 工作流另行运行 Linux x86_64 未启用 Hook 的基线；请查看对应提交的运行结果。

## 0.2 启用与保护边界

模块首页增加两个测试包的安装/版本/停用检查、固定测试入口和恢复说明。
这些检查只帮助配置，不将安装状态伪装成有效保护。入口点击时再次检查版本。
必须传感器 Hook 安装失败时尝试回滚本次已经安装的 Hook；清理失败会附在原始异常中记录。
靶场启动页因旋转等原因重建时不重复启动测试场景。
探针文字显示为快照，点击“刷新探针读数”更新；底层事件证据及运动跳转继续实时处理。
新增代码尚不支持免 Root，不增加真实商业 App 自动关闭规则。
