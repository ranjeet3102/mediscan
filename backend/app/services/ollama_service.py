import os
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Tuple, Any
import time
import threading

from app.core.config import settings

logger = logging.getLogger("medical_ocr.llm")

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
DEFAULT_OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", getattr(settings, "OLLAMA_MODEL", "llama3:latest"))
DEFAULT_GROQ_MODEL = getattr(settings, "GROQ_MODEL", "qwen/qwen3.8-27b")

GROQ_RECOMMENDED_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
]

class OllamaService:
    """
    Hybrid LLM client interface supporting:
    1. Groq Cloud (Free Tier, ultra-fast LPU inference with 10-key round-robin rotation & rate-limit auto-failover)
    2. Local Ollama daemon (Offline / Private, e.g. Llama-3, Mistral, Qwen)
    3. Grounded Deterministic Clinical Fallback (Zero-failure rule engine)
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, default_model: str = DEFAULT_OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.default_groq_model = DEFAULT_GROQ_MODEL
        self._cached_status: Optional[Tuple[bool, List[str]]] = None
        self._last_check_time: float = 0.0
        self._key_index: int = 0
        self._key_lock = threading.Lock()
        self._key_cooldowns: Dict[str, float] = {}

    def get_all_groq_keys(self) -> List[str]:
        """
        Discovers all available Groq API keys from environment variables and settings.
        Supports groq1..groq20, GROQ_API_KEYS (comma separated), and GROQ_API_KEY.
        Returns a list of unique, valid keys.
        """
        keys: List[str] = []
        
        # 1. Check numbered keys: groq1 to groq20 (case-insensitive)
        for i in range(1, 21):
            for pattern in [f"groq{i}", f"GROQ{i}", f"groq_{i}", f"GROQ_{i}"]:
                val = os.getenv(pattern) or getattr(settings, pattern, None)
                if val and isinstance(val, str) and val.strip().startswith("gsk_"):
                    if val.strip() not in keys:
                        keys.append(val.strip())
                    break

        # 2. Check comma-delimited GROQ_API_KEYS
        env_multi = os.getenv("GROQ_API_KEYS", "") or getattr(settings, "GROQ_API_KEYS", "")
        if env_multi and isinstance(env_multi, str):
            for part in env_multi.split(","):
                part_clean = part.strip()
                if part_clean.startswith("gsk_") and part_clean not in keys:
                    keys.append(part_clean)

        # 3. Check single GROQ_API_KEY
        single_key = os.getenv("GROQ_API_KEY", "") or getattr(settings, "GROQ_API_KEY", "")
        if single_key and isinstance(single_key, str) and single_key.strip().startswith("gsk_"):
            if single_key.strip() not in keys:
                keys.append(single_key.strip())

        return keys

    def get_next_groq_key(self) -> Optional[str]:
        """
        Round-robin selection of an available Groq key, skipping any keys currently in rate-limit cooldown.
        """
        all_keys = self.get_all_groq_keys()
        if not all_keys:
            return None

        now = time.time()
        with self._key_lock:
            # Clean expired cooldowns
            expired = [k for k, exp in self._key_cooldowns.items() if now >= exp]
            for k in expired:
                del self._key_cooldowns[k]

            # Filter candidates not in cooldown
            active_candidates = [k for k in all_keys if k not in self._key_cooldowns]
            
            # If all keys are in cooldown, pick the one with earliest cooldown expiration
            if not active_candidates:
                earliest_key = min(self._key_cooldowns.keys(), key=lambda k: self._key_cooldowns[k])
                logger.warning("All Groq keys currently cooling down; reusing earliest cooling key.")
                return earliest_key

            # Round robin over active candidates
            self._key_index = (self._key_index + 1) % len(active_candidates)
            return active_candidates[self._key_index]

    def record_key_rate_limit(self, key: str, cooldown_seconds: float = 60.0):
        """Places a key on cooldown when a 429 RateLimitError is received."""
        with self._key_lock:
            self._key_cooldowns[key] = time.time() + cooldown_seconds
            active_count = len(self.get_all_groq_keys()) - len(self._key_cooldowns)
            logger.warning(
                f"Groq API key {key[:8]}... hit rate limit! Cooldown for {int(cooldown_seconds)}s. "
                f"Remaining active keys: {active_count}"
            )

    def get_groq_api_key(self) -> str:
        """Compatibility helper: returns next active key or empty string."""
        return self.get_next_groq_key() or ""

    def get_provider(self) -> str:
        """Returns the active LLM provider name: 'groq', 'ollama', or 'fallback'."""
        if self.get_all_groq_keys():
            return "groq"
        ollama_ok, _ = self.check_availability()
        if ollama_ok:
            return "ollama"
        return "fallback"

    def get_active_model(self) -> str:
        """Returns the active model name based on provider."""
        if self.get_all_groq_keys():
            return os.getenv("GROQ_MODEL", "") or getattr(settings, "GROQ_MODEL", "") or self.default_groq_model
        return self.default_model

    def check_availability(self) -> Tuple[bool, List[str]]:
        """
        Verifies LLM connectivity:
        - If GROQ keys are configured, returns Groq Cloud availability and supported models.
        - Otherwise, pings local Ollama server at /api/tags (cached 30 seconds).
        """
        # Tier 1: Check Groq Cloud
        if self.get_all_groq_keys():
            return True, GROQ_RECOMMENDED_MODELS

        # Tier 2: Check Local Ollama
        now = time.time()
        if self._cached_status is not None and (now - self._last_check_time) < 30.0:
            return self._cached_status

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=0.3) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    self._cached_status = (True, models)
                    self._last_check_time = now
                    return True, models
        except Exception:
            pass

        self._cached_status = (False, [])
        self._last_check_time = now
        return False, []

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2
    ) -> Optional[str]:
        """
        Generates text using Groq Cloud with multi-key round-robin rotation and automatic 429 failover.
        Falls back to local Ollama if Groq is unavailable or all keys exhausted.
        """
        all_keys = self.get_all_groq_keys()

        # Tier 1: Groq Multi-Key Pool Execution
        if all_keys:
            from groq import Groq, RateLimitError

            # Determine target model
            active_model = model or self.get_active_model()
            # If caller requested an Ollama-only or invalid tag, map to current active Groq model
            if any(tag in active_model.lower() for tag in ["llama3:latest", "llama3:8b", "llama3", "llama-3", ":latest"]):
                active_model = self.get_active_model()

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Attempt across available keys with failover
            max_attempts = min(len(all_keys), 5)
            for attempt in range(max_attempts):
                chosen_key = self.get_next_groq_key()
                if not chosen_key:
                    break

                try:
                    client = Groq(api_key=chosen_key, timeout=15.0)
                    completion = client.chat.completions.create(
                        model=active_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=1500,
                    )
                    if completion.choices and completion.choices[0].message.content:
                        text = completion.choices[0].message.content.strip()
                        if text:
                            return text
                except RateLimitError as rle:
                    logger.warning(f"Groq RateLimitError on key attempt {attempt + 1}/{max_attempts}: {rle}")
                    self.record_key_rate_limit(chosen_key, cooldown_seconds=60.0)
                    continue
                except Exception as e:
                    logger.warning(f"Groq generation error on attempt {attempt + 1} with key {chosen_key[:8]}...: {e}")
                    if "429" in str(e) or "rate" in str(e).lower():
                        self.record_key_rate_limit(chosen_key, cooldown_seconds=60.0)
                    continue

            logger.warning("All Groq key attempts failed or were rate-limited; attempting local Ollama fallback.")

        # Tier 2: Local Ollama daemon
        active_model = model or self.default_model
        payload: Dict[str, Any] = {
            "model": active_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30.0) as response:
                if response.status == 200:
                    res_json = json.loads(response.read().decode("utf-8"))
                    return res_json.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama generation failed ({e}); engaging grounded fallback generator.")
        return None

    def construct_grounded_prompt(
        self,
        report_title: str,
        test_items: List[Dict[str, Any]],
        glossary_context: List[Dict[str, Any]],
        language: str = "en"
    ) -> Tuple[str, str]:
        """
        Builds a strict anti-hallucination system prompt and context envelope.
        """
        system_prompt = (
            "You are an expert, compassionate Medical Health-Literacy Communicator. "
            "Your goal is to explain laboratory test findings to a patient in clear, plain language.\n\n"
            "STRICT RULES TO PREVENT MEDICAL MISINFORMATION & HALLUCINATION:\n"
            "1. CITE THE FACTS: Every biomarker you discuss MUST cite the exact measured value, unit, and reference interval.\n"
            "2. DO NOT DIAGNOSE: Do not say 'You have disease X'. Instead say 'This value is within normal limits' or 'This value is slightly elevated, which can occur for several reasons'.\n"
            "3. USE THE GLOSSARY: Ground your explanations solely in the provided report values and clinical glossary context.\n"
            "4. CLEAR STRUCTURE: Output a clear 4-part summary: Executive Overview, Normal Findings, Out-of-Range Highlights, and Questions for Your Doctor.\n"
            "5. TONE: Calm, reassuring, educational, and precise."
        )

        # Format findings table for prompt
        findings_text = ""
        for it in test_items:
            findings_text += (
                f"- Biomarker: {it.get('normalized_name', it.get('raw_test_name'))} | "
                f"Value: {it.get('value_numeric', it.get('value_text'))} {it.get('unit', '')} | "
                f"Reference Range: {it.get('reference_range_raw', 'N/A')} | "
                f"Flag: {it.get('flag', 'NORMAL')}\n"
            )

        # Format glossary knowledge context
        glossary_text = ""
        for g in glossary_context:
            glossary_text += (
                f"[{g.get('canonical_name')}]: {g.get('patient_friendly_summary')} "
                f"Organs: {g.get('organs_involved')}. "
                f"High: {g.get('high_value_meaning')} "
                f"Low: {g.get('low_value_meaning')}\n"
            )

        lang_instruction = ""
        if language == "ta":
            lang_instruction = "Respond entirely in clear, respectful Tamil (தமிழ்) suitable for a patient."
        elif language == "hi":
            lang_instruction = "Respond entirely in clear, respectful Hindi (हिंदी) suitable for a patient."
        else:
            lang_instruction = "Respond in clear, patient-friendly English."

        user_prompt = (
            f"REPORT TITLE: {report_title}\n\n"
            f"EXTRACTED LABORATORY VALUES:\n{findings_text}\n\n"
            f"CLINICAL BIOMARKER KNOWLEDGE CONTEXT:\n{glossary_text}\n\n"
            f"LANGUAGE REQUIREMENT: {lang_instruction}\n\n"
            "Please provide a structured, grounded explanation following the required sections:\n"
            "1. Executive Summary\n"
            "2. Normal Findings\n"
            "3. Out-of-Range Findings\n"
            "4. 3-4 Thoughtful Questions to Ask the Doctor"
        )

        return system_prompt, user_prompt

    def generate_fallback_explanation(
        self,
        report_title: str,
        test_items: List[Dict[str, Any]],
        glossary_map: Dict[str, Any],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Deterministic, strictly grounded clinical explanation generator.
        Used when local Ollama runtime is offline or during automated testing.
        """
        normal_items = [it for it in test_items if it.get("flag") == "NORMAL"]
        out_of_range_items = [it for it in test_items if it.get("flag") in ["HIGH", "LOW", "CRITICAL"]]

        # Executive summary
        total = len(test_items)
        if not out_of_range_items:
            exec_summary = (
                f"Your medical report '{report_title}' shows that all {total} evaluated biomarkers are currently within their standard reference intervals. "
                "Overall, these results reflect stable baseline physiological function."
            )
        else:
            oor_names = ", ".join([it.get("normalized_name", it.get("raw_test_name")) for it in out_of_range_items[:3]])
            exec_summary = (
                f"Your report '{report_title}' includes {total} measured clinical parameters. "
                f"While {len(normal_items)} tests are within standard target ranges, {len(out_of_range_items)} biomarker(s) ({oor_names}) were found outside standard reference bounds and merit discussion with your physician."
            )

        # Normal findings summary
        if normal_items:
            normal_names = [f"{it.get('normalized_name', it.get('raw_test_name'))} ({it.get('value_numeric', it.get('value_text'))} {it.get('unit', '')})" for it in normal_items]
            normal_summary = (
                f"The following {len(normal_items)} parameters are within normal laboratory ranges: {', '.join(normal_names)}. "
                "These values indicate healthy organ function and balance in these specific pathways."
            )
        else:
            normal_summary = "All recorded values in this specific panel showed variations from baseline reference bounds."

        # Out-of-range findings summary
        if out_of_range_items:
            abnormal_parts = []
            for it in out_of_range_items:
                name = it.get("normalized_name", it.get("raw_test_name"))
                val = f"{it.get('value_numeric', it.get('value_text'))} {it.get('unit', '')}"
                ref = it.get("reference_range_raw", "standard range")
                flag = it.get("flag", "HIGH")
                g_info = glossary_map.get(name.lower(), {})
                meaning = g_info.get("high_value_meaning" if flag == "HIGH" else "low_value_meaning", "")
                
                part = f"• {name} was measured at {val} (reference interval: {ref}, status: {flag})."
                if meaning:
                    part += f" Context: {meaning}"
                abnormal_parts.append(part)
            abnormal_summary = "\n".join(abnormal_parts)
        else:
            abnormal_summary = "No out-of-range or critical biomarker readings were identified in this report."

        # Questions for doctor
        questions = [
            f"Based on my overall results, are there any dietary or lifestyle adjustments you recommend?",
            f"When would you like me to schedule a follow-up test to monitor these values?",
        ]
        if out_of_range_items:
            for it in out_of_range_items[:2]:
                name = it.get("normalized_name", it.get("raw_test_name"))
                questions.append(f"Could my {name} reading be influenced by recent hydration, stress, or medications?")

        # Multilingual translations for deterministic fallback
        if language == "ta":
            exec_summary = (
                f"உங்கள் மருத்துவ அறிக்கை '{report_title}' இல் {total} சோதனைகள் ஆய்வு செய்யப்பட்டன. "
                f"{len(normal_items)} சோதனைகள் இயல்பான அளவில் உள்ளன; {len(out_of_range_items)} சோதனைகள் குறித்து உங்கள் மருத்துவரிடம் ஆலோசனை பெற பரிந்துரைக்கப்படுகிறது."
            )
            normal_summary = f"{len(normal_items)} சோதனைகள் இயல்பான மருத்துவ வரம்பிற்குள் உள்ளன."
            abnormal_summary = "இயல்பான வரம்பிற்கு அப்பாற்பட்ட சோதனைகள் மருத்துவ ஆலோசனையை நாடுகின்றன."
            questions = [
                "இந்த முடிவுகளின் அடிப்படையில் நான் ஏதேனும் உணவுமுறை மாற்றங்களை செய்ய வேண்டுமா?",
                "அடுத்த பரிசோதனையை எப்போது செய்ய வேண்டும்?",
                "இந்த முடிவுகள் ஏதேனும் மருந்துகளால் பாதிக்கப்பட வாய்ப்புள்ளதா?"
            ]
        elif language == "hi":
            exec_summary = (
                f"आपकी मेडिकल रिपोर्ट '{report_title}' में {total} बायोमार्कर की जांच की गई है। "
                f"{len(normal_items)} पैरामीटर सामान्य सीमा के भीतर हैं, जबकि {len(out_of_range_items)} पर डॉक्टर से परामर्श की आवश्यकता है।"
            )
            normal_summary = f"{len(normal_items)} परीक्षण सामान्य सीमा में हैं और स्वस्थ कार्यप्रणाली दर्शाते हैं।"
            abnormal_summary = "सामान्य सीमा से बाहर के परिणामों पर डॉक्टर से मार्गदर्शन लें।"
            questions = [
                "क्या मुझे अपनी जीवनशैली या आहार में कोई बदलाव करना चाहिए?",
                "अगला फॉलो-अप टेस्ट कब कराना उचित होगा?",
                "क्या कोई दवा या तनाव इन परिणामों को प्रभावित कर सकता है?"
            ]

        disc = "This explanation is generated solely for health literacy and patient education. It does not constitute medical advice, diagnosis, or clinical management."
        if language == "ta":
            disc = "இந்த விளக்கம் சுகாதார விழிப்புணர்வு மற்றும் நோயாளி கல்விக்காக மட்டுமே உருவாக்கப்பட்டது. இது மருத்துவ சிகிச்சை அல்லது நோய் கண்டறிதல் ஆலோசனை அல்ல."
        elif language == "hi":
            disc = "यह व्याख्या केवल स्वास्थ्य साक्षरता और रोगी शिक्षा के लिए तैयार की गई है। यह चिकित्सीय सलाह या निदान नहीं है।"

        return {
            "executive_summary": exec_summary,
            "normal_findings_summary": normal_summary,
            "abnormal_findings_summary": abnormal_summary,
            "doctor_questions": questions,
            "disclaimer": disc,
            "model_used": "Grounded-Clinical-Engine-v2.0",
            "is_mock_fallback": True,
        }

# Global singleton ollama service
ollama_service = OllamaService()
