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

    def test_invalid_config_falls_back_to_builtin_model_definitions(self):
        invalid_config_path = "/tmp/invalid-ai-model-gateway-config.json"
        with open(invalid_config_path, "w", encoding="utf-8") as invalid_config:
            invalid_config.write("{invalid json")

        gateway = AIModelGateway(config_path=invalid_config_path)

        status = gateway.get_status()

        self.assertIn("claude", status)
        self.assertEqual(status["huggingface"]["name"], "Hugging Face")

    def test_auto_route_returns_empty_result_when_no_providers_are_configured(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        result = asyncio.run(gateway.auto_route("Hallo"))

        self.assertEqual(result["prompt"], "Hallo")
        self.assertEqual(result["responses"], {})
        self.assertIsNone(result["primary"])


if __name__ == "__main__":
    unittest.main()
