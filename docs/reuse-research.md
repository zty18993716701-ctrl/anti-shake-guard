# 同类项目复用评估

核查日期：2026-09-26。范围：官方 GitHub 仓库、固定提交源码与许可证；未运行这些项目的 APK，未验证其宣传效果。本报告是工程选型及许可证筛查，不是法律意见。

## 结论

可以复用现成生态，但不应把多个传感器拦截实现直接叠加。当前最值得优先复用的是测试基础设施和对比基线，而非替换已经具备类型过滤、作用域与回滚的核心。以下三项分别代表 Xposed、Shizuku 和无障碍路线；它们解决的问题、权限和失效方式不同。

## 1. pwh-pwh/fuck_shake：适合作为对比基线，不替换核心

- 固定提交 `34a20bad084fbc54ce4a776acbf0809defe8d02b`，默认分支最后提交时间为 2023-11-15；仓库未归档。仓库 `pushed_at` 为 2024-08-02，不能把它误当默认分支最近代码变更。维护频率偏低是本次观察，不代表作者明确停止维护。[提交](https://github.com/pwh-pwh/fuck_shake/commit/34a20bad084fbc54ce4a776acbf0809defe8d02b)、[仓库元数据](https://api.github.com/repos/pwh-pwh/fuck_shake)
- MIT 许可证，版权人为 coderpwh。若以后复制实质代码，需保留版权及许可文本；本轮没有复制。[许可证](https://github.com/pwh-pwh/fuck_shake/blob/34a20bad084fbc54ce4a776acbf0809defe8d02b/LICENSE)
- 核心使用 YukiHookAPI，匹配 `SensorManager.registerListener` 的三参数方法并直接返回 `true`。源码没有检查传入传感器类型，也没有完整覆盖其他参数个数的注册入口。[HookEntry.kt](https://github.com/pwh-pwh/fuck_shake/blob/34a20bad084fbc54ce4a776acbf0809defe8d02b/app/src/main/java/dev/coderpwh/fuck/hook/HookEntry.kt)
- 工程推断：使用该入口的光线/距离监听也可能被阻断；返回成功但实际未注册也会改变调用方预期。它不能证明“无论怎么动都不跳转”，更不能据此保证自动关闭广告。现有项目已经在更底层入口按类型过滤，直接合并没有明显新增收益。[同一实现依据](https://github.com/pwh-pwh/fuck_shake/blob/34a20bad084fbc54ce4a776acbf0809defe8d02b/app/src/main/java/dev/coderpwh/fuck/hook/HookEntry.kt)
- 可复用方式：在独立模拟器快照中构建该固定版本作竞品对照，记录三参数/其他重载、光线事件、运动跳转及启用步骤；不要和本模块同时启用，否则难以归因。此项是建议，尚未执行。

## 2. WeiyePlayer/no-shakingAD：恢复设计值得参考，全局限制不适合当前目标

- 固定提交 `761638826db6d053f138490b5025c19c0264ad2e`，提交时间 2026-07-13；未归档。仓库 API 的 `license` 为 `null`，递归树中没有发现 LICENSE/COPYING/NOTICE 文件。不能把“源码可见”当成明确的复制分发授权，本轮不复制。[提交](https://github.com/WeiyePlayer/no-shakingAD/commit/761638826db6d053f138490b5025c19c0264ad2e)、[元数据](https://api.github.com/repos/WeiyePlayer/no-shakingAD)、[固定版本文件树](https://api.github.com/repos/WeiyePlayer/no-shakingAD/git/trees/761638826db6d053f138490b5025c19c0264ad2e?recursive=1)
- README 描述 Shizuku + 无障碍前台检测，进入目标应用后限制传感器、默认 5 秒恢复；同时明确其底层为 SensorService 的全局受限模式，白名单之外的应用受影响。它不是逐个 App 的系统权限开关。[README](https://github.com/WeiyePlayer/no-shakingAD/blob/761638826db6d053f138490b5025c19c0264ad2e/README.md)
- UserService 代码用参数数组调用 `dumpsys sensorservice restrict <filter>`，另调 `enable` 恢复；恢复任务运行在独立进程，有 generation 防旧任务、重试和 destroy 清理。这些是可参考的恢复场景，不等于进程崩溃或所有设备上都能恢复的实测保证。[SensorControlUserService.kt](https://github.com/WeiyePlayer/no-shakingAD/blob/761638826db6d053f138490b5025c19c0264ad2e/app/src/main/java/com/shizukucontrol/service/SensorControlUserService.kt)
- 工程判断：全局限制与本项目“不误伤其他应用和非运动传感器”目标存在冲突；固定 5 秒也不能覆盖任意时刻的广告。加入 Shizuku、无障碍和全局恢复状态会扩大权限与故障面，因此不作为当前验证版的后备拦截器。将来如单独探索免 Root 路线，应先测全局副作用与异常恢复，并取得明确许可。

## 3. gkd-kit/gkd：自动关闭路线可利用现成工具，但不是传感器防护

- 固定提交 `677c1388b12cbbc976bd08b9753ab1b5c3acc62a`，提交时间 2026-09-24；未归档。相比上述项目，观察到近期代码维护；这不是稳定性优劣的实测结论。[提交](https://github.com/gkd-kit/gkd/commit/677c1388b12cbbc976bd08b9753ab1b5c3acc62a)、[仓库元数据](https://api.github.com/repos/gkd-kit/gkd)
- 项目采用无障碍、自定义选择器和订阅规则执行屏幕点击；它不是运动传感器屏蔽模块，关闭按钮被发现以前仍可能发生摇动跳转。[项目介绍](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/README.md)
- `RuleScopePolicy` 包含应用版本、Activity 包含/排除、系统应用及桌面作用域；`RuleLimitations` 能解释规则被版本或排除项阻止的原因。可借鉴“规则为什么没有执行”的用户反馈，避免把没有点击误报成保护失败。[作用域代码](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/gkd-app/src/main/kotlin/li/gkd/app/domain/rule/RuleScopePolicy.kt)、[解释代码](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/gkd-app/src/main/kotlin/li/gkd/app/domain/rule/RuleLimitations.kt)
- 根许可证为 GPLv3，不能把拷贝的 GPL 实现仅标成 MIT。引入源码/链接库前必须明确组合分发、对应源码与第三方规则各自许可；本轮没有并入代码或订阅。优先考虑使用独立安装的工具配合自建靶场规则验证，保持模块职责分离。[许可证](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/LICENSE)
- 另一个必须先澄清的问题：README 同时写有 `GPL-3.0-only` 与“禁止用于商业或非法用途”，不能擅自将这段措辞解释为已获得明确商业授权。默认也不提供规则；配套试验需要自建规则，并在任何代码整合/商业分发前澄清许可表述。[README 声明与订阅说明](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/README.md)
- 其规则具有通用匹配能力，未知应用信息及默认作用域的行为不等同于本项目的严格白名单。不能直接照搬默认值；本项目仍应坚持未知版本/页面不执行动作。[作用域代码](https://github.com/gkd-kit/gkd/blob/677c1388b12cbbc976bd08b9753ab1b5c3acc62a/gkd-app/src/main/kotlin/li/gkd/app/domain/rule/RuleScopePolicy.kt)

## 仅推荐的两项具体复用

1. **固定版本对比测试**：将 `fuck_shake` 作为隔离的可选对照，不合并 Hook。用同一靶场、同一系统镜像、同一输入轨迹测运动与非运动事件，并增加不同注册重载。实际收益是避免凭印象宣称“更少误伤”，不是节省几十行 Hook 代码。
2. **自动关闭功能复用现成独立工具**：真实 Root/Xposed 防跳转先验收，再评估 GKD 与本模块独立配合的靶场实验；先只写本项目靶场规则，不装第三方大规则包、不授权商业应用自动点击。若验证有效，再决定是否将它作为可选配套，而不是重写完整无障碍规则引擎。独立运行不能替代对具体分发与许可关系的审查。

本轮没有引入新的运行时依赖、外部 APK 或规则，没有扩大任何真实商业 App 的作用域。Root/Xposed 实测由下一阶段测试记录独立报告，不将本研究当作通过证据。
