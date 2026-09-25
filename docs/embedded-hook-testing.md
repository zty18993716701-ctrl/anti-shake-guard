# 第二阶段：复用真实 Xposed 引擎测试

本阶段使用 [JingMatrix/LSPatch v1.2](https://github.com/JingMatrix/LSPatch/releases/tag/v1.2)，源提交 `0dc50f42503711b14f5e2bb217c2bdd6321ce5be`，仅作为自建靶场的外部测试工具。不改商业 APK，不改变产品的 Root/Xposed 路线。

框架通过修改单个 APK 嵌入真实 Hook 引擎，支持 legacy Xposed 模块；这不同于在 Root 设备通过管理器配置作用域。[框架说明](https://github.com/JingMatrix/LSPatch/tree/0dc50f42503711b14f5e2bb217c2bdd6321ce5be)

## 固定依赖及边界

- 工具：`lspatch-v1.2-487-release.jar`，SHA-256 `d238fdc414d121b7fa454d8b4ccf420df3a8c97d563761861ff92bd9c5da2165`，与发布 API 的 digest 一致。执行前校验。
- CLI 需要 Java 21（Java 17 实际启动报 class version 65/61 不兼容）；项目仍用 Java 17 构建。
- `-m` 嵌入本次构建模块，`-d` 保留自建靶场的调试证据读取，`-l 0` 不启用签名绕过，`--version-code 1` 保留靶场白名单版本；不降低 target SDK。[参数源码](https://github.com/JingMatrix/LSPatch/blob/0dc50f42503711b14f5e2bb217c2bdd6321ce5be/patch/src/main/java/org/lsposed/patch/LSPatch.java)
- 上游采用 GPLv3；不将框架源码复制进 MIT 模块，不把框架 JAR 或打补丁后的 APK 纳入本项目发布包或 Actions 产物。只下载到临时构建目录供测试，保留来源及许可边界。[上游许可证](https://github.com/JingMatrix/LSPatch/blob/0dc50f42503711b14f5e2bb217c2bdd6321ce5be/LICENSE)

## 执行顺序

1. 同一 API 35 x86_64 模拟器运行现有 8 项基线及未加载模块负例。
2. 只重装自建保护组；对照组不打补丁。比对嵌入模块与本次模块 APK 字节完全一致。
3. 原 `hooked` 黑盒脚本连续执行三轮：控制组运动跳转，保护组运动事件为 0 且不跳转，两组光线事件保留；广告立即/延迟关闭、缺按钮安全返回、普通页面不误点。
4. 卸载仅测试用保护组并恢复原 APK，再跑 8 项基线，确认移除后行为恢复。

脚本：`validation/scripts/ci-lspatch.sh`。结果以对应提交的 Actions 证据为准，未运行完成前不声明 PASS。

即使通过，也只证明这一版本框架、镜像和自建靶场组合。Root/管理器作用域、真实手机/厂商 ROM、NDK 路径、商业 App、长期稳定性和法律审查仍未验收。三轮不是 100 次稳定性认证。
