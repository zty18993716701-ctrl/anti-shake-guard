# 非预期原生崩溃 / Unexpected native crash — OPEN

[Run 39020188810](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188810), trial 3 / job 117360286441, commit `d218bf41097424a29889af64522b1e06b015b7d9`, cycle 63 startup. Not a calibration crash.

这里两个文件从完整原始 ZIP 的 `stress-061-080/` 直接提取，内容未改写：

- [完整 crash 缓冲 / raw crash buffer](logcat-crash.txt)：SIGSEGV、PID 7020、ART backtrace；debuggerd 名称为 `<pre-initialized>`。
- [保护组退出历史 / raw protected-process exit history](dev.antishake.fixture.protectedapp-exit-info.txt)：对应 PID 的 reason=5 / APP CRASH(NATIVE)、status=11；同时保留其他预期 FORCE STOP 历史，不能混为一类。

`am_proc_start` / `am_crash` / `am_proc_died` 原始事件把 PID 7020、UID 10211 关联到 `dev.antishake.fixture.protectedapp`。栈位于 Android ART，单凭该栈无法确定模块、Vector、模拟器或它们交互中哪一处是根因。没有修改框架，也没有将此问题标为修复。后续改动只使判据能识别这类未初始化进程名称下的系统崩溃事件。

完整 [ZIP 12097110799](https://github.com/zty18993716701-ctrl/anti-shake-guard/actions/runs/39020188810/artifacts/12097110799)（包括 tombstone 原文与 protobuf、完整 logcat、DropBox、kernel、退出历史等）已下载并通过 ZIP CRC 与 SHA-256 `de3a3d86e9fb5e50341c8f42106950e204ffc5159ccd9735f45bae29c90d366b` 校验。Actions 文件保留至 2026-10-24；完整 ZIP 另留在任务本地证据目录，不只依赖此临时链接。

These are unmodified diagnostic files from the failed startup, not intentional calibration. System events associate PID 7020 / UID 10211 with the protected fixture despite debuggerd's `<pre-initialized>` command line. The stack and exit record establish an unexpected native crash, **not its root cause**. The new exact-package system-event classifier detects it; that detection repair does not fix or exonerate any runtime component. The full original archive, including native tombstone/protobuf and all diagnostics, is retained locally as well as the time-limited Actions artifact.
