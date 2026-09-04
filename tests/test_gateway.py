import asyncio
import unittest

from gateway import AIModelGateway


class AIModelGatewayTests(unittest.TestCase):
    def test_missing_default_config_uses_builtin_model_definitions(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        status = gateway.get_status()

        self.assertEqual(
            set(status),
            {"claude", "openrouter", "groq", "huggingface"},
        )
        self.assertFalse(status["claude"]["available"])
        self.assertEqual(status["openrouter"]["name"], "OpenRouter")

    def test_auto_route_returns_empty_result_when_no_providers_are_configured(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        result = asyncio.run(gateway.auto_route("Hallo"))

        self.assertEqual(result["prompt"], "Hallo")
        self.assertEqual(result["responses"], {})
        self.assertIsNone(result["primary"])


if __name__ == "__main__":
    unittest.main()
