# Vector Root 作用域自动配置调查

调查日期：2026-09-26。只读审查，以下命令尚不代表设备实测通过。

## 结论

可直接复用 Vector 自带的 Root CLI 配置模块，不必编造数据库字段、复制管理器代码或自动点击管理器。选定稳定版 **v2.2 / 3080**，固定源码提交 **88f8e1faa8b4e7ce20aefabe9c295cd746ea038e**。该版本有 legacy `de.robv.android.xposed` 兼容层，支持 `assets/xposed_init` 与 `IXposedHookLoadPackage`。[发布版本](https://github.com/JingMatrix/Vector/releases/tag/v2.2)、[固定源码 legacy 说明](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/legacy/README.md)

模块 ID 是 `zygisk_vector`，安装脚本会解包 `cli`、`daemon.apk` 并赋予 CLI Root 执行权限。常规 Magisk 模块安装路径下入口为 `/data/adb/modules/zygisk_vector/cli`；脚本也支持 Magisk 镜像挂载目录。CLI 强制 UID 0，JSON 输出含 `success`、`data`、`error`。[模块 ID](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/zygisk/module/module.prop)、[安装脚本](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/zygisk/module/customize.sh)、[入口脚本](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/zygisk/module/cli)、[CLI 定义](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/Cli.kt)

## 可复现操作接口

仅针对一次性、明确指定的测试模拟器。在模块和三个未重新打包 APK 已安装、重启后框架就绪的前提下，以 Root 执行：

```sh
/data/adb/modules/zygisk_vector/cli --json status
/data/adb/modules/zygisk_vector/cli --json modules enable dev.antishake.guard
/data/adb/modules/zygisk_vector/cli --json scope set dev.antishake.guard dev.antishake.fixture.protectedapp/0
/data/adb/modules/zygisk_vector/cli --json modules ls
/data/adb/modules/zygisk_vector/cli --json scope ls dev.antishake.guard
```

`scope set` 替换该模块的完整显式作用域，而不是追加；`/0` 指目标 Android 用户 0。返回 scope 列表字段是 `APP_PACKAGE`、`USER_ID`。停用命令是 `modules disable dev.antishake.guard`；移除目标作用域命令是 `scope rm dev.antishake.guard dev.antishake.fixture.protectedapp/0`。[CLI 定义](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/Cli.kt)、[命令处理](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/ipc/CliHandler.kt)

测试必须读回验证，而不是只看进程退出码：

- `modules enable/disable` 的总体 `success: true` 仍可能附带非空 `data.Failed`；要求失败列表为空，成功列表含目标包。
- `scope set` 的 handler 没有检查数据库方法的布尔返回值；必须要求 `scope ls` 恰好返回 protected 包与用户 0，不含 control、system 或其他 App。
- 缓存更新异步执行。配置读回并不证明目标进程已被 Hook；需重新启动目标进程，再运行现有严格的 hook marker、传感器和关闭页面验收。

以上行为来自 [CliHandler](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/ipc/CliHandler.kt)、[ModuleDatabase](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/data/ModuleDatabase.kt)、[ConfigCache](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/data/ConfigCache.kt)。

## 必须披露的边界

Vector 会在缓存中为已加载 legacy 模块自动加入**模块自身进程**，用于传统激活状态检测；它不显示为数据库显式 scope 行。因此不能声称实际注入仅发生于 protected 进程。应检查本项目入口对模块自身的处理，且通过对照组证明 control 未被注入／拦截。[ConfigCache 的 legacy 自身作用域派生](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/daemon/src/main/kotlin/org/matrix/vector/daemon/data/ConfigCache.kt)

在核查的固定版本官方 Core workflow 中，没有发现可直接复用的模拟器 Root Hook 集成测试：它执行构建 `zipAll`、打包和发布。因此本项目仍需自己的设备行为测试，不能把上游构建成功当作拦截成功。[官方 Core workflow](https://github.com/JingMatrix/Vector/blob/88f8e1faa8b4e7ce20aefabe9c295cd746ea038e/.github/workflows/core.yml)

建议测试矩阵：启用后保护组／对照组 → 重启后重复 → 移除作用域后恢复基线 → 恢复作用域后再次保护 → 停用模块后恢复基线。所有阶段均保留官方 CLI 配置读回与本项目行为证据；不修改框架数据库，不将框架源码合入 MIT 项目。
