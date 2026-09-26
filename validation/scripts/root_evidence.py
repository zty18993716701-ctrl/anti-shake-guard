"""Preserve command output from disposable-emulator acceptance tests."""
import subprocess


def capture(command, path, timeout, best_effort=False):
    try:
        try:
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            output = error.output or b""
            if isinstance(output, bytes):
                output = output.decode("utf-8", errors="replace")
            path.write_text(output + f"\nTIMEOUT after {timeout} seconds\n")
            raise
        path.write_text(result.stdout)
        return result
    except (subprocess.TimeoutExpired, OSError) as error:
        if not best_effort:
            raise
        print(f"Diagnostic collection incomplete: {error}", flush=True)
