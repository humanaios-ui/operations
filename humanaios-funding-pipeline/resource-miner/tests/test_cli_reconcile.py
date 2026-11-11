import unittest

from resource_miner.cli import build_parser


class ReconcileCommandTests(unittest.TestCase):
    def test_reconcile_subcommand_is_registered(self):
        args = build_parser().parse_args(
            ["reconcile", "--snapshot", "snap.jsonl", "--receipts", "receipts.jsonl"]
        )
        self.assertEqual(args.command, "reconcile")
        self.assertEqual(args.snapshot, "snap.jsonl")
        self.assertEqual(args.receipts, "receipts.jsonl")
        self.assertIsNone(args.out)


if __name__ == "__main__":
    unittest.main()
