"""Static deployment contracts; these do not claim a live Azure deployment."""

import re
import unittest
from pathlib import Path


TEMPLATE = Path(__file__).resolve().parents[1] / "infra" / "metaculus-job.bicep"


class MetaculusAzureConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = TEMPLATE.read_text()

    def test_optional_secrets_filtered_before_resource_configuration(self):
        self.assertIn(
            "var configuredSecrets = filter(allSecrets, secret => !empty(secret.value))",
            self.text,
        )
        self.assertRegex(self.text, r"secrets: concat\(\s*configuredSecrets,")
        secret_names = set(re.findall(r"\{ name: '([^']+)', value:", self.text))
        references = set(re.findall(r"secretRef: '([^']+)'", self.text))
        self.assertTrue(references <= secret_names)
        self.assertIn("filter(envMap, m => m.has)", self.text)

    def test_schedule_is_explicit_opt_in_and_configs_share_one_condition(self):
        self.assertIn("param scheduleCronExpression string = ''", self.text)
        self.assertIn("var isScheduled = !empty(scheduleCronExpression)", self.text)
        self.assertIn("triggerType: isScheduled ? 'Schedule' : 'Manual'", self.text)
        self.assertRegex(
            self.text,
            r"manualTriggerConfig: !isScheduled \? \{[^}]+\} : null",
        )
        self.assertRegex(
            self.text,
            r"scheduleTriggerConfig: isScheduled \? \{\s*"
            r"cronExpression: scheduleCronExpression[^}]+\} : null",
        )

    def test_schedule_docs_require_fresh_writer_handover_check(self):
        self.assertIn("freshly recheck Railway", self.text)
        self.assertIn("stop the old writer/scheduler", self.text)
        self.assertIn("obtain handover approval", self.text)

    def test_single_replica_and_no_automatic_retry(self):
        self.assertIn("replicaRetryLimit: 0", self.text)
        self.assertEqual(self.text.count("replicaCompletionCount: 1"), 2)
        self.assertEqual(self.text.count("parallelism: 1"), 2)

    def test_existing_environment_does_not_deploy_logging_resources(self):
        self.assertIn("param useExistingEnvironment bool = false", self.text)
        for resource in ("logAnalytics", "containerAppEnvironment"):
            self.assertRegex(
                self.text,
                rf"resource {resource} '[^']+' = if \(!useExistingEnvironment\)",
            )
        self.assertRegex(
            self.text,
            r"resource existingEnvironment '[^']+' existing = if \(useExistingEnvironment\)"
            r" \{\s*name: environmentName\s*\}",
        )
        self.assertIn(
            "environmentId: useExistingEnvironment ? existingEnvironment.id : containerAppEnvironment.id",
            self.text,
        )

    def test_default_mode_discloses_external_writes(self):
        self.assertIn("param mode string = 'test_questions'", self.text)
        self.assertIn("test_questions also makes provider calls and publishes forecasts", self.text)
        self.assertIn("external writes and provider charges", self.text)


if __name__ == "__main__":
    unittest.main()
