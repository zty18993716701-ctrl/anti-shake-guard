# 第三阶段：Root / Vector 配置及恢复验收

仅在一次性 GitHub Linux runner 的 API 35 google_apis x86_64 模拟器执行，不对日常手机、Mac 或商业 App 获取 Root。手动触发 `root-validation.yml`，与已通过的 LSPatch 测试分开。

## 复用与固定来源

- [Magisk v30.7](https://github.com/topjohnwu/Magisk/releases/tag/v30.7)，APK SHA-256 `e0d32d2123532860f97123d927b1bb86c4e08e6fd8a48bfc6b5bee0afae9ebd5`。
- 使用官方 [build.py avd_patch](https://github.com/topjohnwu/Magisk/blob/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/build.py) 与 [host_patch.sh](https://github.com/topjohnwu/Magisk/blob/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/scripts/host_patch.sh) 修补 ramdisk 的构建目录副本，不改 SDK 原始镜像。两份脚本也固定 SHA-256。
- [Vector v2.2 / 3080 Release](https://github.com/JingMatrix/Vector/releases/tag/v2.2)，ZIP SHA-256 `9ee8323575d615f7b3f1076ff60b2a63a49390ef11881b52632311a37f6f79cc`。
- 模块开关和作用域通过框架官方 CLI 配置、读回；不直接改 Vector 数据库。Magisk 自带 `--sqlite` 设置 `zygisk`，对应官方 [settings 定义](https://github.com/topjohnwu/Magisk/blob/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/native/src/core/db.rs)。
- 上游工具均作为独立测试依赖；下载在构建目录，产物仅上传测试证据，不上传第三方框架、设备镜像或密钥。[Magisk 许可](https://github.com/topjohnwu/Magisk/blob/e8a58776f1d7bdf852072ad0baa6eceb9a1e4aac/LICENSE)、[Vector 许可](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/LICENSE)。

## 成功标准

1. Root 与框架版本实际读回；记录镜像指纹和 SELinux 状态。
2. 三个未经重打包的项目 APK 安装。未配置模块时，8 项基线通过。
3. 模块 enabled，显式 scope 只有保护组用户 0；8 项 hooked 检查通过，对照组仍能运动跳转。
4. 真正重启模拟器，内核 boot_id 改变；配置保留，8 项 hooked 再通过。
5. 移除保护组 scope，读回为空，8 项基线通过。
6. 再加入保护组，8 项 hooked 通过。
7. 停用模块，读回 disabled，8 项基线通过。

每个场景都会强制停止并重新启动靶场，避免误将旧进程中的 Hook 当成新配置。任何失败均不能报告全套通过。共 6 轮 × 8 个场景断言，不是 48 种不同测试。

Vector 对 legacy 模块还自动注入模块自身进程；本模块入口明确排除自身。因此显式 scope 与实际框架注入集合不能混称，详见[官方接口调查](root-scope-research.md)。CLI 验收不是管理器图形界面的易用性验收；模拟器不是 ARM 真机。未知父页面等策略仍由现有回归覆盖，Root 路径本次不扩张商业 App 规则。

状态：2026-09-26 固定组合首次完整运行 PASS，见[结果与证据](root-results.md)。后续日志超时修复另有本地回归，不追溯为该云端运行已覆盖。
