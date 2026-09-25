#!/usr/bin/env bash
set -euo pipefail
validation_dir="$(cd "$(dirname "$0")/.." && pwd)"
task_dir="$(cd "$validation_dir/../../.." && pwd)"
java_dir="${JAVA_HOME:-$task_dir/work/toolchains/jdk/Contents/Home}"
test_libs="$task_dir/work/test-libs"
test_classes="$task_dir/work/policy-test-classes"
mkdir -p "$test_classes"
sources=()
while IFS= read -r source; do sources+=("$source"); done < <(find "$validation_dir/policy/src" -name '*.java' -type f)
"$java_dir/bin/javac" --release 8 -cp "$test_libs/junit.jar" -d "$test_classes" "${sources[@]}"
"$java_dir/bin/java" -cp "$test_classes:$test_libs/junit.jar:$test_libs/hamcrest.jar" \
  org.junit.runner.JUnitCore dev.antishake.policy.MotionPolicyTest dev.antishake.policy.AdCloseRuleTest
