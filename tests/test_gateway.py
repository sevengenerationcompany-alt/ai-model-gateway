import asyncio
import tempfile
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
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as invalid_config:
            invalid_config.write("{invalid json")
            invalid_config.flush()

            gateway = AIModelGateway(config_path=invalid_config.name)

        status = gateway.get_status()

        self.assertIn("claude", status)
        self.assertEqual(status["huggingface"]["name"], "Hugging Face")

    def test_directory_config_path_falls_back_to_builtin_model_definitions(self):
        with tempfile.TemporaryDirectory() as config_dir:
            gateway = AIModelGateway(config_path=config_dir)

        status = gateway.get_status()

        self.assertIn("groq", status)
        self.assertEqual(status["claude"]["name"], "Claude")

    def test_auto_route_returns_empty_result_when_no_providers_are_configured(self):
        gateway = AIModelGateway(config_path="/tmp/does-not-exist-config.json")

        result = asyncio.run(gateway.auto_route("Hallo"))

        self.assertEqual(result["prompt"], "Hallo")
        self.assertEqual(result["responses"], {})
        self.assertIsNone(result["primary"])


if __name__ == "__main__":
    unittest.main()
