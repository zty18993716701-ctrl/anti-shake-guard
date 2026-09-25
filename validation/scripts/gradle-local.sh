#!/usr/bin/env bash
set -euo pipefail
validation_dir="$(cd "$(dirname "$0")/.." && pwd)"
task_dir="$(cd "$validation_dir/../../.." && pwd)"
export JAVA_HOME="${JAVA_HOME:-$task_dir/work/toolchains/jdk/Contents/Home}"
export ANDROID_HOME="${ANDROID_HOME:-$task_dir/work/toolchains/android-sdk}"
export ANDROID_USER_HOME="${ANDROID_USER_HOME:-$task_dir/work/android-user}"
export GRADLE_USER_HOME="${GRADLE_USER_HOME:-$task_dir/work/gradle-user}"
exec "$task_dir/work/toolchains/gradle/gradle-8.9/bin/gradle" -p "$validation_dir" --console=plain "$@"
