# 来源与许可

基于 [Wardell Bagby / Sensor Disabler](https://github.com/wardellbagby/sensor-disabler/tree/ac2dda13bea421be2bf1bd2715e02de54a5ffdf9)，固定提交 `ac2dda13bea421be2bf1bd2715e02de54a5ffdf9`。

本仓库不是官方续作，也不代表上游作者背书。`validation/guard` 的复制列表再过滤实现改编自上游 `RemoveSensorModificationMethod.java`；该原始文件和上游 README 保存在 `upstream/` 供查阅。旧界面、计费和 Tasker 工程没有纳入这个精简验证仓库。MIT 许可证及原版权声明保留在根目录 `LICENSE`，新增代码也按该许可证提供，不影响独立依赖的许可。

`app/libs/de.robv.android.xposed-api-82.jar` 来自同一上游提交，仅用于 `compileOnly` 编译，不打包进 APK。XposedBridge 的许可为 Apache-2.0，版权与许可文本见 `licenses/`。Gradle wrapper 由 Gradle 8.9 生成，按 Apache-2.0 许可，wrapper 下载文件校验值已固定。

许可证声明不是产品合法性审查，也不保证修改其他软件行为的合法性。

第二阶段测试以固定版本 [JingMatrix/LSPatch v1.2](https://github.com/JingMatrix/LSPatch/tree/0dc50f42503711b14f5e2bb217c2bdd6321ce5be) 作为外部 GPLv3 测试工具。框架 JAR 和嵌入框架后的自建靶场 APK 仅存于临时构建目录，不纳入本仓库、交付包或 Actions 产物；没有将其源码重新标记为 MIT。工具来源、哈希和使用范围见 [测试方案](docs/embedded-hook-testing.md)。其他同类项目只做源码与许可证研究，未合并其实现。
