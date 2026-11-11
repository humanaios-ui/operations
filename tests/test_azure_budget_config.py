"""Bounded static contract checks; no claim of ARM compilation or live alerts."""

import re
import unittest
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "infra" / "azure-research-budget.bicep"


class AzureBudgetConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text()

    def test_requires_amount_recipients_dates_and_currency_without_defaults(self):
        for name, kind in (
            ("budgetName", "string"),
            ("monthlyAmountUsd", "int"),
            ("confirmedBillingCurrency", "string"),
            ("startDate", "string"),
            ("endDate", "string"),
            ("notificationEmails", "array"),
        ):
            self.assertRegex(self.text, rf"(?m)^param {name} {kind}$")
        self.assertIn("@minValue(1)\nparam monthlyAmountUsd int", self.text)
        self.assertRegex(
            self.text,
            r"@minLength\(1\)\s*@maxLength\(5\)\s*param notificationEmails array",
        )
        self.assertIn("@allowed(['USD'])", self.text)

    def test_resource_group_budget_has_only_four_enabled_email_alerts(self):
        self.assertIn("targetScope = 'resourceGroup'", self.text)
        self.assertEqual(
            re.findall(r"(?m)^resource \w+ '([^']+)'", self.text),
            ["Microsoft.Consumption/budgets@2026-06-01"],
        )
        alerts = re.findall(
            r"(?m)^      (\w+): \{\s*enabled: true\s*"
            r"operator: 'GreaterThanOrEqualTo'\s*threshold: (\d+)\s*"
            r"thresholdType: '(Actual|Forecasted)'\s*"
            r"contactEmails: notificationEmails\s*\}",
            self.text,
        )
        self.assertEqual(
            alerts,
            [
                ("actual50", "50", "Actual"),
                ("actual80", "80", "Actual"),
                ("actual100", "100", "Actual"),
                ("forecast100", "100", "Forecasted"),
            ],
        )
        self.assertEqual(self.text.count("enabled:"), 4)
        self.assertIn("timeGrain: 'Monthly'", self.text)
        self.assertIn("amount: monthlyAmountUsd", self.text)
        self.assertIn("startDate: startDate", self.text)
        self.assertIn("endDate: endDate", self.text)

    def test_documents_scope_currency_and_non_enforcement(self):
        self.assertIn("Budget alerts do not stop costs", self.text)
        self.assertIn("billing currency; they do not convert", self.text)
        self.assertIn("resource group only", self.text)
        self.assertIn("not a fetched or verified billing record", self.text)


if __name__ == "__main__":
    unittest.main()
