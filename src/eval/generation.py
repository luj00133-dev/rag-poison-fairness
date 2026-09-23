"""
Multi-provider chat client, and the NLI-based scorer that replaces the
self-report attribution probe.

Why this module exists
----------------------
Two problems with the first generation-stage evaluation, both of which a
reviewer would raise:

1. **One generator.** A propagation claim measured on a single model is a
   property of that model. We need at least two independent model *families*
   (not two checkpoints from one family, which is what `deepseek-chat` and
   `deepseek-reasoner` amount to: R1 is V3 fine-tuned with RL).

2. **The attribution probe was broken, and we failed to notice.** The original
   probe asked the generator itself "does the Answer rely on information from
   the Passage? YES/NO" and averaged the YES rate. That judge answers YES to
   essentially everything, so the reported EAE-D saturated at 1.000 in every
   condition -- a constant, which we reported honestly as a failed metric but
   did not replace. A self-report is the wrong instrument: it measures the
   judge's agreeableness, not the answer's provenance.

The fix is to stop asking a model and start measuring entailment. A small
NLI model decides, per (passage, answer) pair, whether the passage entails the
answer, and the same model scores stance without a prompt at all:

    stance(answer, group)  =  P(entailment | answer, favourable_statement(group))
                              - P(entailment | answer, unfavourable_statement(group))

Both are local, deterministic, free of API cost, and -- unlike a prompted
judge -- produce a continuous score rather than a saturated binary.

Providers
---------
Any OpenAI-compatible `/chat/completions` endpoint is accepted. Credentials are
read from the environment under a caller-supplied variable name, never stored.

Environment
-----------
    <provider>_API_KEY   e.g. DEEPSEEK_API_KEY, DASHSCOPE_API_KEY
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #


@dataclass
class Provider:
    """An OpenAI-compatible chat endpoint."""

    name: str
    base_url: str
    model: str
    key_env: str
    #: key in the per-record pricing table, purely for cost reporting
    label: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"{self.name}:{self.model}"


#: The generator panel. Deliberately spans two independent families:
#: Qwen (Alibaba) and DeepSeek. `qwen3-235b-a22b` is a different architecture
#: generation from `qwen-plus` (MoE, newer training), so it counts as a third
#: generator rather than a checkpoint of the first.
PROVIDERS: Dict[str, Provider] = {
    "qwen-max": Provider(
        name="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-max",
        key_env="DASHSCOPE_API_KEY",
    ),
    "qwen-plus": Provider(
        name="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
        key_env="DASHSCOPE_API_KEY",
    ),
    "qwen-turbo": Provider(
        name="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-turbo",
        key_env="DASHSCOPE_API_KEY",
    ),
    "qwen3-235b": Provider(
        name="qwen",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3-235b-a22b",
        key_env="DASHSCOPE_API_KEY",
    ),
    "deepseek-chat": Provider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        model="deepseek-chat",
        key_env="DEEPSEEK_API_KEY",
    ),
    "deepseek-reasoner": Provider(
        name="deepseek",
        base_url="https://api.deepseek.com",
        model="deepseek-reasoner",
        key_env="DEEPSEEK_API_KEY",
    ),
}


class ProviderError(RuntimeError):
    pass


@dataclass
class ChatClient:
    """Minimal OpenAI-compatible chat client with a disk cache.

    The cache is keyed on (provider label, system, user) so that a re-run after
    a crash or a config change costs nothing for prompts already answered, and
    so that two providers can never share an entry.
    """

    provider: Provider
    api_key: str
    cache_path: Optional[str] = "results/attribution_cache.json"
    temperature: float = 0.0
    max_tokens: int = 256
    timeout: float = 120.0
    max_retries: int = 4
    dry_run: bool = False

    _cache: Dict[str, str] = field(default_factory=dict, init=False)
    n_calls: int = field(default=0, init=False)
    n_cache_hits: int = field(default=0, init=False)
    n_errors: int = field(default=0, init=False)
    prompt_tokens: int = field(default=0, init=False)
    completion_tokens: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, encoding="utf-8") as fh:
                    self._cache = json.load(fh)
            except Exception:
                self._cache = {}

    # -- persistence ------------------------------------------------------- #

    def flush(self) -> None:
        if not self.cache_path:
            return
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as fh:
            json.dump(self._cache, fh, ensure_ascii=False)

    @property
    def usage(self) -> Dict[str, object]:
        return {
            "provider": self.provider.label,
            "calls": self.n_calls,
            "cache_hits": self.n_cache_hits,
            "errors": self.n_errors,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    # -- the one call ------------------------------------------------------ #

    def chat(self, system: str, user: str) -> str:
        key = "\x00".join((self.provider.label, system, user))
        if key in self._cache:
            self.n_cache_hits += 1
            return self._cache[key]
        if self.dry_run:
            return "A"

        payload = {
            "model": self.provider.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        url = self.provider.base_url.rstrip("/") + "/chat/completions"
        last = ""
        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    body = json.loads(r.read().decode("utf-8"))
                usage = body.get("usage") or {}
                self.prompt_tokens += int(usage.get("prompt_tokens") or 0)
                self.completion_tokens += int(
                    usage.get("completion_tokens") or 0
                )
                self.n_calls += 1
                text = body["choices"][0]["message"]["content"] or ""
                self._cache[key] = text
                return text
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:160]
                last = f"HTTP {exc.code}: {detail}"
                # 4xx other than rate-limiting will not succeed on retry
                if exc.code in (400, 401, 403, 404):
                    break
                time.sleep(1.5 * (attempt + 1))
            except Exception as exc:  # network hiccups, timeouts
                last = f"{type(exc).__name__}: {exc}"
                time.sleep(1.5 * (attempt + 1))
        self.n_errors += 1
        raise ProviderError(f"{self.provider.label}: {last}")

    @staticmethod
    def from_name(name: str, **kw) -> "ChatClient":
        if name not in PROVIDERS:
            raise KeyError(
                f"unknown provider {name!r}; known: {sorted(PROVIDERS)}"
            )
        prov = PROVIDERS[name]
        key = os.environ.get(prov.key_env, "")
        if not key and not kw.get("dry_run"):
            raise ProviderError(
                f"{prov.key_env} is not set (needed for {prov.label})"
            )
        return ChatClient(provider=prov, api_key=key, **kw)


# --------------------------------------------------------------------------- #
# Local open-weight generator
# --------------------------------------------------------------------------- #

#: Open-weight generators, run locally rather than through an API.
#:
#: Why this exists: the API panel spans two *families* (Alibaba's Qwen, DeepSeek),
#: and a reviewer is entitled to object that a propagation result measured only on
#: hosted models says nothing about the open-weight systems most RAG deployments
#: actually run. Mistral-7B-Instruct is the largest 7B-class instruct model that
#: needs no gated access, and it is a third family rather than another checkpoint
#: of the first two.
#:
#: The machine has an RTX 5060 (Blackwell, sm_120, 8.5 GB). A 7B model fits only in
#: 4-bit, which `analysis/test_4bit_gpu.py` verified works on this device before
#: any download was attempted; the loaded model occupies 4.14 GB and 3 repeated
#: greedy calls returned byte-identical text, which the protocol requires.
#:
#: The value may be a HuggingFace id or a local directory, because the weights were
#: fetched with a resumable HTTP downloader rather than through huggingface_hub
#: (see analysis/fetch_mistral.py for why).
LOCAL_MODELS: Dict[str, str] = {
    "mistral-7b": os.environ.get(
        "MISTRAL_LOCAL_PATH",
        r"D:\HaizeiwangPingshu\models\mistral-7b-v0.3"),
    "phi-3.5-mini": "microsoft/Phi-3.5-mini-instruct",
}


@dataclass
class LocalGenerator:
    """A local instruct model behind the same ``chat`` interface as ChatClient.

    Deliberately mirrors :class:`ChatClient` (``chat``, ``usage``, ``flush``,
    ``from_name``) so the evaluation driver does not need to know which kind of
    generator it is holding. Responses are cached on disk with the same key
    scheme, so a local and an API run can share nothing and collide never.
    """

    model_id: str
    label: str = ""
    cache_path: Optional[str] = "results/attribution_cache.json"
    max_new_tokens: int = 256
    load_in_4bit: bool = True

    _model: object = field(default=None, init=False, repr=False)
    _tokenizer: object = field(default=None, init=False, repr=False)
    _cache: Dict[str, str] = field(default_factory=dict, init=False)
    n_calls: int = field(default=0, init=False)
    n_cache_hits: int = field(default=0, init=False)
    n_errors: int = field(default=0, init=False)
    prompt_tokens: int = field(default=0, init=False)
    completion_tokens: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = f"local:{self.model_id.split('/')[-1]}"
        if self.cache_path and os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, encoding="utf-8") as fh:
                    self._cache = json.load(fh)
            except Exception:
                self._cache = {}

    # -- loading ----------------------------------------------------------- #

    def _ensure(self):
        if self._model is not None:
            return
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if not torch.cuda.is_available():
            raise ProviderError(
                "local generation needs a CUDA build of torch; the environment "
                "used for the retrieval results is CPU-only by design"
            )
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        kwargs = {"device_map": "cuda"}
        if self.load_in_4bit:
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
            )
        else:
            kwargs["torch_dtype"] = torch.float16
        self._model = AutoModelForCausalLM.from_pretrained(self.model_id, **kwargs)
        self._model.eval()

    # -- interface --------------------------------------------------------- #

    def flush(self) -> None:
        if not self.cache_path:
            return
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as fh:
            json.dump(self._cache, fh, ensure_ascii=False)

    @property
    def usage(self) -> Dict[str, object]:
        return {
            "provider": self.label,
            "calls": self.n_calls,
            "cache_hits": self.n_cache_hits,
            "errors": self.n_errors,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
        }

    def chat(self, system: str, user: str) -> str:
        key = "\x00".join((self.label, system, user))
        if key in self._cache:
            self.n_cache_hits += 1
            return self._cache[key]
        try:
            self._ensure()
            import torch

            messages = [{"role": "system", "content": system},
                        {"role": "user", "content": user}]
            prompt = self._tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            enc = self._tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = self._model.generate(
                    **enc, max_new_tokens=self.max_new_tokens,
                    do_sample=False,  # greedy, for the same determinism an API
                                      # run gets from temperature 0
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            text = self._tokenizer.decode(
                out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
            self.prompt_tokens += int(enc["input_ids"].shape[1])
            self.completion_tokens += int(out.shape[1] - enc["input_ids"].shape[1])
            self.n_calls += 1
            self._cache[key] = text
            return text
        except Exception as exc:
            self.n_errors += 1
            raise ProviderError(f"{self.label}: {type(exc).__name__}: {exc}")

    @staticmethod
    def from_name(name: str, **kw) -> "LocalGenerator":
        if name not in LOCAL_MODELS:
            raise KeyError(
                f"unknown local model {name!r}; known: {sorted(LOCAL_MODELS)}"
            )
        return LocalGenerator(model_id=LOCAL_MODELS[name], **kw)


def make_generator(name: str, **kw):
    """Return a generator for an API provider or a local open-weight model.

    One entry point so the driver does not carry the distinction.
    """
    if name in PROVIDERS:
        return ChatClient.from_name(name, **kw)
    if name in LOCAL_MODELS:
        return LocalGenerator.from_name(name, **kw)
    raise KeyError(
        "unknown generator %r; API: %s  local: %s"
        % (name, sorted(PROVIDERS), sorted(LOCAL_MODELS))
    )


# --------------------------------------------------------------------------- #
# NLI scorer: stance and attribution without asking a model to judge itself
# --------------------------------------------------------------------------- #

#: Default local NLI checkpoint. DeBERTa-v3-base is small enough for CPU and
#: scores ~60 (premise, hypothesis) pairs per second here.
DEFAULT_NLI = "cross-encoder/nli-deberta-v3-base"


@dataclass
class NliScorer:
    """Local NLI model used for stance scoring and entailment attribution.

    Lazily loads `transformers` so that nothing that does not need NLI pays for
    it, and holds the model for the process lifetime (loading costs ~100 s on
    CPU, inference microseconds).
    """

    model_id: str = DEFAULT_NLI
    batch_size: int = 32
    _pipe: object = field(default=None, init=False, repr=False)

    def _ensure(self):
        if self._pipe is None:
            os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
            from transformers import pipeline

            self._pipe = pipeline(
                "text-classification", model=self.model_id, device=-1
            )
            self._labels = {
                int(k): str(v).lower()
                for k, v in self._pipe.model.config.id2label.items()
            }
        return self._pipe

    def entailment(self, premises: Sequence[str],
                   hypotheses: Sequence[str]) -> List[float]:
        """P(entailment | premise) for each aligned (premise, hypothesis) pair."""
        assert len(premises) == len(hypotheses)
        if not premises:
            return []
        pipe = self._ensure()
        pairs = [{"text": p, "text_pair": h}
                 for p, h in zip(premises, hypotheses)]
        raw = pipe(pairs, batch_size=self.batch_size, top_k=None)
        out: List[float] = []
        for item in raw:
            # top_k=None returns a list of {label, score} per input
            scores = {str(d["label"]).lower(): float(d["score"]) for d in item}
            out.append(scores.get("entailment", 0.0))
        return out

    def stance(self, answers: Sequence[str],
               fav_statement: str, unfav_statement: str) -> List[float]:
        """Continuous stance score in [-1, 1] per answer.

        ``P(entail | answer, favourable) - P(entail | answer, unfavourable)``.
        Positive means the answer leans favourable, negative unfavourable, and
        values near zero mean the answer does not commit either way. This
        replaces the forced-choice probe's binary A/B selection, which saturates
        as soon as the context is decisive.

        The answer must be the PREMISE. Calibrated in analysis/calibrate_nli.py:
        with a favourable answer this returns +0.997 and with an unfavourable
        answer -0.997, whereas the reversed convention returns +/-0.002 for both
        and therefore cannot separate anything. The direction is not
        interchangeable and the reversed one fails silently by returning zeros.
        """
        ans = list(answers)
        pos = self.entailment(ans, [fav_statement] * len(ans))
        neg = self.entailment(ans, [unfav_statement] * len(ans))
        return [p - n for p, n in zip(pos, neg)]
