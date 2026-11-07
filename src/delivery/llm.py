"""LLM client for a local Ollama server (free, no API key). One request per plan,
no retries to fix mistakes; only transport errors are retried (fixed policy)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMReply:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    done_reason: str
    attempts: int


class TransportError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, llm_cfg: dict, host: str = "http://localhost:11434"):
        self.model = llm_cfg["model"]
        self.temperature = llm_cfg["temperature"]
        self.max_tokens = llm_cfg["max_output_tokens"]
        self.seed = llm_cfg.get("seed", 0)
        self.num_ctx = llm_cfg.get("num_ctx", 8192)
        self.transport_retries = llm_cfg["retries_on_transport_error"]
        self.host = host

    def _post(self, path: str, payload: dict, timeout: float = 600) -> dict:
        req = urllib.request.Request(self.host + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())

    def model_info(self) -> dict:
        """Exact model identity (name + digest) for the reproducibility log."""
        tags = json.loads(urllib.request.urlopen(self.host + "/api/tags", timeout=30).read())
        for m in tags.get("models", []):
            if m["name"] == self.model:
                return {"name": m["name"], "digest": m["digest"], "size": m["size"]}
        raise TransportError(f"model {self.model} not found on server")

    def generate(self, system: str, user: str) -> LLMReply:
        payload = {
            "model": self.model, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": self.temperature, "seed": self.seed,
                        "num_predict": self.max_tokens, "num_ctx": self.num_ctx},
        }
        last = None
        for attempt in range(1, self.transport_retries + 2):
            t0 = time.time()
            try:
                d = self._post("/api/chat", payload)
                return LLMReply(
                    text=d["message"]["content"], input_tokens=d.get("prompt_eval_count", 0),
                    output_tokens=d.get("eval_count", 0), latency_s=time.time() - t0,
                    done_reason=d.get("done_reason", ""), attempts=attempt)
            except (urllib.error.URLError, TimeoutError, ConnectionError, KeyError, json.JSONDecodeError) as e:
                last = e
                time.sleep(2 ** attempt)
        raise TransportError(f"transport failed after {self.transport_retries + 1} attempts: {last}")
