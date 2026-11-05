import unittest
from unittest.mock import Mock

import requests

from agents.ollama_client import (
    CHEMLLM_MODEL,
    JUDGE_MODEL,
    OllamaClient,
    OllamaModelUnavailable,
    OllamaResponseInvalid,
    OllamaUnavailable,
)


class Response:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class OllamaClientTests(unittest.TestCase):
    def test_lists_exact_models_and_shows_metadata(self):
        session = Mock()
        session.request.side_effect = [
            Response({"models": [{"name": CHEMLLM_MODEL}, {"name": JUDGE_MODEL}]}),
            Response({"details": {"parameter_size": "7.74B", "quantization_level": "Q4_K_M"}}),
        ]
        client = OllamaClient(session=session)
        self.assertEqual(client.model_names(), {CHEMLLM_MODEL, JUDGE_MODEL})
        self.assertEqual(client.show_model(CHEMLLM_MODEL)["details"]["parameter_size"], "7.74B")
        self.assertEqual(session.request.call_count, 2)

    def test_chat_uses_bounded_payload_and_preserves_raw_response(self):
        session = Mock()
        raw = {"model": JUDGE_MODEL, "message": {"role": "assistant", "content": "OK"}, "done": True}
        session.request.side_effect = [
            Response({"models": [{"name": JUDGE_MODEL}]}),
            Response(raw),
        ]
        client = OllamaClient(session=session, timeout=(3, 90), num_ctx=2048, keep_alive=0)
        result = client.chat(JUDGE_MODEL, [{"role": "user", "content": "Reply only OK"}], max_tokens=8)
        self.assertEqual(result.content, "OK")
        self.assertEqual(result.raw, raw)
        chat_call = session.request.call_args_list[1]
        self.assertEqual(chat_call.args[0], "POST")
        self.assertTrue(chat_call.args[1].endswith("/api/chat"))
        self.assertEqual(chat_call.kwargs["timeout"], (3, 90))
        self.assertEqual(chat_call.kwargs["json"]["model"], JUDGE_MODEL)
        self.assertFalse(chat_call.kwargs["json"]["stream"])
        self.assertEqual(chat_call.kwargs["json"]["options"]["num_ctx"], 2048)
        self.assertEqual(chat_call.kwargs["json"]["options"]["num_predict"], 8)

    def test_unregistered_model_fails_before_chat(self):
        session = Mock()
        session.request.return_value = Response({"models": [{"name": JUDGE_MODEL}]})
        client = OllamaClient(session=session)
        with self.assertRaises(OllamaModelUnavailable):
            client.chat(CHEMLLM_MODEL, [{"role": "user", "content": "test"}])
        self.assertEqual(session.request.call_count, 1)

    def test_service_timeout_is_reported_without_raw_request_details(self):
        session = Mock()
        session.request.side_effect = requests.Timeout("internal timeout detail")
        client = OllamaClient(session=session)
        with self.assertRaises(OllamaUnavailable) as caught:
            client.list_models()
        self.assertNotIn("internal timeout detail", str(caught.exception))

    def test_invalid_json_shape_and_missing_chat_content_fail_closed(self):
        session = Mock()
        session.request.return_value = Response({"unexpected": []})
        with self.assertRaises(OllamaResponseInvalid):
            OllamaClient(session=session).list_models()

        session = Mock()
        session.request.side_effect = [
            Response({"models": [{"name": JUDGE_MODEL}]}),
            Response({"model": JUDGE_MODEL, "message": {"role": "assistant", "content": " "}}),
        ]
        with self.assertRaises(OllamaResponseInvalid):
            OllamaClient(session=session).chat(JUDGE_MODEL, [{"role": "user", "content": "test"}])


if __name__ == "__main__":
    unittest.main()
