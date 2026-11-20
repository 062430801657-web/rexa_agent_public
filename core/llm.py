import time
import urllib.request
import json
from openai import OpenAI
import config

class LLMRouter:
    def __init__(self):
        if not config.API_KEY:
            raise ValueError("REXA_API_KEY belum diatur.")
        self.client = OpenAI(
            base_url=config.API_BASE_URL,
            api_key=config.API_KEY,
            timeout=60.0
        )
        self.fast_pool = [
            "ag/gemini-4-argon-medium",
            "ag/gemini-3.8-flash-high",
            "ag/claude-sonnet-5-5-medium",
            "ag/gemini-3.8-flash"
        ]
        self.deep_pool = [
            "ag/claude-sonnet-5-5-high",
            "ag/gemini-4-argon-medium",
            "ag/claude-opus-5-5-high",
            "ag/claude-sonnet-4-6",
            "ag/gemini-3.8-flash-high"
        ]
        self.fallback_pool = [
            "ag/gemini-3.8-flash",
            "ag/claude-sonnet-5-5-low",
            "ag/gpt-oss-120b-medium"
        ]
        # Blacklist tracking: {model_name: timestamp_unhealthy}
        self.model_cooldowns = {}
        self.cooldown_seconds = 180  # 3 menit cooldown jika model 503/404

    def is_model_healthy(self, model_name):
        now = time.time()
        if model_name in self.model_cooldowns:
            if now - self.model_cooldowns[model_name] < self.cooldown_seconds:
                return False
            else:
                del self.model_cooldowns[model_name]
        return True

    def mark_model_unhealthy(self, model_name, reason=""):
        self.model_cooldowns[model_name] = time.time()

    def get_candidate_models(self, deep=False):
        pool = self.deep_pool if deep else self.fast_pool
        # Urutkan model yang masih sehat di depan
        candidates = [m for m in pool if self.is_model_healthy(m)]
        # Jika semua di pool utama cooldown, masukkan sisa pool dan fallback
        if not candidates:
            candidates = [m for m in pool]
        for fb in self.fallback_pool:
            if fb not in candidates:
                candidates.append(fb)
        return candidates

    def complete(self, messages, tools=None, deep=False, temperature=0.3, on_status=None):
        candidates = self.get_candidate_models(deep=deep)
        last_error = None
        recovery_logs = []

        for model in candidates:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            try:
                if on_status:
                    if recovery_logs:
                        on_status("Rexa sedang mengalihkan penalaran...")
                    else:
                        on_status("Rexa sedang berpikir...")

                response = self.client.chat.completions.create(**kwargs)
                if not response.choices or len(response.choices) == 0:
                    raise ValueError(f"Model {model} mengembalikan choices kosong.")

                msg = response.choices[0].message
                has_tools = bool(getattr(msg, "tool_calls", None) and len(msg.tool_calls) > 0)
                has_content = bool(msg.content and str(msg.content).strip())
                has_reasoning = bool(getattr(msg, "reasoning_content", None) and str(msg.reasoning_content).strip())

                # Proteksi Respons Kosong: Jika tidak ada tool calls, tidak ada content, dan tidak ada reasoning
                if not has_tools and not has_content and not has_reasoning:
                    raise ValueError(f"Model {model} mengembalikan respons kosong (content None/empty).")

                return msg

            except Exception as e:
                err_str = str(e)
                self.mark_model_unhealthy(model, err_str)
                recovery_logs.append(f"Model {model} gagal ({err_str[:40]}...)")

                # Cek jika error terkait format tools: coba panggil sekali tanpa tools sebagai fallback
                if "tool" in err_str.lower() and tools:
                    try:
                        if on_status:
                            on_status("Rexa sedang menyederhanakan alur instruksi...")
                        kwargs_no_tools = {
                            "model": model,
                            "messages": messages,
                            "temperature": temperature
                        }
                        resp_fallback = self.client.chat.completions.create(**kwargs_no_tools)
                        return resp_fallback.choices[0].message
                    except Exception:
                        pass

                last_error = e
                continue

        # Jika semua kandidat gagal, coba deteksi live model dari 9Router secara darurat
        try:
            if on_status:
                on_status("Rexa sedang memulihkan koneksi...")
            discovered = self.discover_live_model()
            if discovered:
                if on_status:
                    on_status("Rexa sedang menyambungkan kembali...")
                resp = self.client.chat.completions.create(
                    model=discovered,
                    messages=messages,
                    temperature=temperature
                )
                return resp.choices[0].message
        except Exception as e:
            last_error = e

        error_summary = " | ".join(recovery_logs[-2:]) if recovery_logs else str(last_error)
        raise RuntimeError(f"Semua model gagal merespons. Diagnosis: {error_summary}")

    def discover_live_model(self):
        try:
            req = urllib.request.urlopen(f"{config.API_BASE_URL}/models", timeout=3)
            data = json.loads(req.read().decode())
            models = [m['id'] for m in data.get('data', [])]
            for pref in ["ag/gemini-3.8-flash", "ag/claude-sonnet-4-6", "ag/gpt-oss-120b-medium"]:
                if pref in models:
                    return pref
            return models[0] if models else None
        except Exception:
            return None
