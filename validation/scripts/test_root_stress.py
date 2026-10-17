import unittest

from root_stress import check_chunk, check_stress


class RootStressTest(unittest.TestCase):
    def records(self):
        return [{"cycle": cycle, "kind": ("cold", "warm", "background", "ad", "normal")[(cycle - 1) % 5],
                 "result": "PASS"} for cycle in range(1, 101)]

    def test_all_100_ordinals_and_balanced_kinds_are_required(self):
        rows = self.records()
        self.assertEqual(check_stress(rows), dict.fromkeys(("cold", "warm", "background", "ad", "normal"), 20))
        for invalid in (rows[:-1], rows + rows[:1], rows[:20] * 5,
                        [dict(row, result="FAIL") if row["cycle"] == 90 else row for row in rows],
                        [dict(row, kind="cold") if row["cycle"] == 2 else row for row in rows]):
            with self.subTest(invalid=invalid[-1]), self.assertRaises(AssertionError):
                check_stress(invalid)

    def test_chunk_must_include_the_matching_summary_and_expected_range(self):
        rows = self.records()[20:40]
        summary = {"suite": "lifecycle", "result": "PASS", "cycles": 20, "startCycle": 21,
                   "counts": dict.fromkeys(("cold", "warm", "background", "ad", "normal"), 4)}
        self.assertEqual(check_chunk(rows + [summary], 21), rows)
        for invalid in (rows, rows + [dict(summary, cycles=100)],
                        rows + [dict(summary, startCycle=1)], rows[::-1] + [summary]):
            with self.subTest(length=len(invalid)), self.assertRaises(AssertionError):
                check_chunk(invalid, 21)


if __name__ == "__main__":
    unittest.main()
