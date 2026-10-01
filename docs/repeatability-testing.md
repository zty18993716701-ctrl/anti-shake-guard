# 第四阶段：独立环境重复性复测

## 范围与通过条件

在同一提交下创建 3 个独立 GitHub Linux runner，每个从全新模拟器开始，复用既有 Root 工作流与固定 Magisk / Vector 工具。每个环境执行 6 阶段 × 8 项断言，并运行 3 项日志超时回归。任一环境失败，则本轮不通过；不以只挑选成功重跑代替原始结果。三个任务的产物名称独立，避免互相覆盖。

目的：排除成功依赖上一轮设备残留状态，并在设备路径复验上轮诊断修复。应用代码、场景断言、权限和商业 App 范围均不变。`fail-fast: false` 保留失败后其他环境的观察结果；每任务上限 30 分钟，最多同时 3 个，不安排周期性任务。

这是 144 次场景断言，不是 144 种测试，也不是至少 100 次冷/热启动、后台/前台和重启的产品级压力测试。镜像工具链仍可能随上游更新，实际运行环境以证据包记录为准；三个环境相同架构，不算多机型兼容性。

## 验证记录

**PASS，2026-10-01。** 测试配置提交：`977e5995df1e55fe8796dacc6cf0a84d74deff2b`；实际执行提交：`ea4c4aa0a9dbb71fb1a7ae87b372b4901c4d9b99`（后者仅增补说明）。[运行 36829991457](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36829991457)，首次尝试 `run_attempt=1`，三个独立任务全部成功。先前浏览器连接失败未能启动，后由用户手动触发；此阻碍已解除。

| 任务 | 场景断言 | 日志回归 | 原始行为证据 |
| --- | --- | --- | --- |
| root-vector (1)，job 110264169340 | 48/48 PASS | 3/3 PASS | [JSONL](evidence/repeat-ea4c4aa-trial-1.jsonl) |
| root-vector (2)，job 110264169477 | 48/48 PASS | 3/3 PASS | [JSONL](evidence/repeat-ea4c4aa-trial-2.jsonl) |
| root-vector (3)，job 110264169576 | 48/48 PASS | 3/3 PASS | [JSONL](evidence/repeat-ea4c4aa-trial-3.jsonl) |

共 144 次场景断言与 9 次日志回归执行。逐个下载并核对任务文本日志：每个含 48 条 PASS 断言及 6 条汇总，顺序为 baseline、hooked、hooked、baseline、hooked、baseline，每阶段 8 项。JSONL 原结果字段保持不变，phase 字段按固定脚本执行顺序添加。没有用截图绿勾代替断言检查。

本轮覆盖了原始 APK、未配置基线、启用保护、内核重启后保持、移除作用域恢复、重新加入保护和停用恢复；也在 Linux 云端覆盖了此前仅本地验证的日志超时修复。保护组不因运动跳转、对照组仍跳转、光线保留、靶场广告关闭与普通页不误点的断言通过。基线的关闭由测试脚本点击，不算自动关闭。

三个完整证据包的上传步骤成功，保留 7 天：[trial 1](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36829991457/artifacts/11146514002)、[trial 2](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36829991457/artifacts/11146259494)、[trial 3](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/36829991457/artifacts/11146879096)。本轮未下载解压这三个 ZIP；持久归档为任务日志中提取的行为 JSONL。

### 两条警告

各任务日志均提示：`setup-java v4` 已弃用、建议迁移 v5；多个 Action 的 Node.js 20 运行时被平台强制切到 Node.js 24。全部步骤仍成功，但这些提醒不应忽略。它们是构建工具维护事项，不是本轮保护断言失败；升级应独立修改、固定新版本并重新验证，本次归档不更改已测工作流。

手动启动：[Root 工作流](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/workflows/root-validation.yml) → `Run workflow` → 选择 `main` → `Run workflow`。一次触发包含三个独立任务，无需点击三次。

后续复跑继续记录实际提交和每个任务结果；不能将这次通过追溯到未来修改或其他设备。

## 真机衔接

完成后按[真机验收表](device-acceptance.md)在已具备测试条件的专用 Android 设备上验证。没有设备时保持 NOT RUN；不要求用户给日常手机 Root，不借 iPhone 冒充 Android 结果。
