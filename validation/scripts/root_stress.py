"""Reject incomplete, duplicated or miscounted Root lifecycle evidence."""
KINDS = ("cold", "warm", "background", "ad", "normal")


def check_rows(rows, start, count):
    assert [row["cycle"] for row in rows] == list(range(start, start + count)), "Incomplete or reordered cycles"
    assert all(row["result"] == "PASS" and row["kind"] == KINDS[(row["cycle"] - 1) % 5]
               for row in rows), "Cycle failed or has the wrong lifecycle kind"
    return {kind: sum(row["kind"] == kind for row in rows) for kind in KINDS}


def check_chunk(records, start):
    assert len(records) == 21, "Expected 20 cycles and one summary"
    rows, summary = records[:-1], records[-1]
    counts = check_rows(rows, start, 20)
    assert summary == {"suite": "lifecycle", "result": "PASS", "cycles": 20,
                       "startCycle": start, "counts": counts}, summary
    return rows


def check_stress(rows):
    counts = check_rows(rows, 1, 100)
    assert counts == dict.fromkeys(KINDS, 20), counts
    return counts
