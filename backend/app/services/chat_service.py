import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

from app.models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from app.services.glossary_service import medical_glossary_service
from app.services.ollama_service import ollama_service, DEFAULT_OLLAMA_MODEL
from app.core.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.chat_service")

# In-memory conversation store for local testing & development without Supabase
_DEV_CONVERSATIONS_CACHE: Dict[str, Dict[str, Any]] = {}

class ChatService:
    """
    Context-aware Conversational Q&A Engine ("Ask My Report").
    Maintains multi-turn conversation memory, dynamically injects structured
    report findings and vector-retrieved medical glossary context, and applies
    strict anti-hallucination constraints with deterministic fallback.
    """

    def _get_cache_key(self, report_id: str, user_id: str) -> str:
        return f"{user_id}:{report_id}"

    def get_or_create_conversation(
        self,
        report_id: str,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves existing conversation record or initializes a new one.
        """
        cache_key = self._get_cache_key(report_id, user_id)

        # 1. Check local cache
        if cache_key in _DEV_CONVERSATIONS_CACHE:
            return _DEV_CONVERSATIONS_CACHE[cache_key]

        # 2. Check Supabase
        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                query = supabase.table("conversations").select("*").eq("report_id", report_id).eq("user_id", user_id)
                if conversation_id:
                    query = query.eq("id", conversation_id)
                res = query.order("created_at", desc=True).limit(1).execute()
                if res.data and len(res.data) > 0:
                    conv = res.data[0]
                    _DEV_CONVERSATIONS_CACHE[cache_key] = conv
                    return conv
            except Exception as e:
                logger.warning(f"Failed to query Supabase conversations: {e}")

        # 3. Initialize new conversation record
        new_conv = {
            "id": conversation_id or str(uuid.uuid4()),
            "report_id": report_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _DEV_CONVERSATIONS_CACHE[cache_key] = new_conv

        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                supabase.table("conversations").insert({
                    "id": new_conv["id"],
                    "report_id": report_id,
                    "user_id": user_id,
                    "messages": [],
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to insert new conversation in Supabase: {e}")

        return new_conv

    def get_conversation_history(
        self,
        report_id: str,
        user_id: str
    ) -> ConversationHistoryResponse:
        """
        Fetches the complete message history for a report's conversation.
        """
        conv = self.get_or_create_conversation(report_id, user_id)
        raw_msgs = conv.get("messages", [])
        chat_msgs = [ChatMessage(**m) for m in raw_msgs]
        return ConversationHistoryResponse(
            conversation_id=conv.get("id", str(uuid.uuid4())),
            report_id=report_id,
            messages=chat_msgs,
            created_at=conv.get("created_at"),
            updated_at=conv.get("updated_at"),
        )

    def clear_conversation(self, report_id: str, user_id: str) -> bool:
        """
        Resets and clears the conversation history for a given report.
        """
        cache_key = self._get_cache_key(report_id, user_id)
        if cache_key in _DEV_CONVERSATIONS_CACHE:
            _DEV_CONVERSATIONS_CACHE[cache_key]["messages"] = []
            _DEV_CONVERSATIONS_CACHE[cache_key]["updated_at"] = datetime.now(timezone.utc).isoformat()

        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                supabase.table("conversations").update({
                    "messages": [],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("report_id", report_id).eq("user_id", user_id).execute()
            except Exception as e:
                logger.error(f"Failed to clear conversation in Supabase: {e}")
                return False

        return True

    def build_chat_context(
        self,
        report_title: str,
        test_results: List[Dict[str, Any]],
        user_query: str,
        language: str = "en"
    ) -> Tuple[str, List[str], List[Dict[str, Any]]]:
        """
        Retrieves relevant biomarker values and glossary cards for the user's question.
        Returns:
            - context_text: Formatted context block for the LLM
            - relevant_biomarker_names: List of relevant biomarker canonical names
            - glossary_entries: List of retrieved glossary dictionaries
        """
        # 1. Extract out of range markers
        out_of_range = [t for t in test_results if t.get("flag") in ["HIGH", "LOW", "CRITICAL"]]

        # 2. Semantic vector search on glossary for the user's specific query
        search_results = medical_glossary_service.search(user_query, limit=4)
        
        # 3. Match biomarkers from test results against user query
        matched_results = []
        user_lower = user_query.lower()
        for t in test_results:
            raw_n = (t.get("raw_test_name") or "").lower()
            norm_n = (t.get("normalized_name") or "").lower()
            if norm_n in user_lower or raw_n in user_lower:
                matched_results.append(t)

        # Combine items to feature in prompt context
        featured_tests = list({t.get("normalized_name", t.get("raw_test_name")): t for t in (matched_results + out_of_range + test_results[:6])}.values())

        # Build formatted findings table
        findings_block = ""
        for it in featured_tests:
            name = it.get("normalized_name", it.get("raw_test_name"))
            val = it.get("value_numeric", it.get("value_text", "N/A"))
            unit = it.get("unit", "")
            ref = it.get("reference_range_raw") or f"{it.get('ref_min')} - {it.get('ref_max')}"
            flag = it.get("flag", "NORMAL")
            findings_block += f"- {name}: {val} {unit} (Ref: {ref}) -> Flag: {flag}\n"

        # Build formatted glossary block
        glossary_block = ""
        glossary_names = []
        for g in search_results:
            canon = g.get("canonical_name", "")
            glossary_names.append(canon)
            glossary_block += (
                f"- [{canon}]: {g.get('patient_friendly_summary')}. "
                f"What it measures: {g.get('what_it_measures')}. "
                f"Organs: {g.get('organs_involved')}. "
                f"Elevated: {g.get('high_value_meaning')}. "
                f"Low: {g.get('low_value_meaning')}\n"
            )

        context_text = (
            f"REPORT NAME: {report_title}\n\n"
            f"PATIENT'S VERIFIED LAB FINDINGS:\n{findings_block}\n"
            f"RELEVANT MEDICAL KNOWLEDGE BASE:\n{glossary_block}"
        )

        return context_text, glossary_names, search_results

    def generate_chat_reply(
        self,
        report_id: str,
        user_id: str,
        report_title: str,
        test_results: List[Dict[str, Any]],
        user_message: str,
        language: str = "en",
        conversation_id: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ) -> ChatResponse:
        """
        Executes a multi-turn grounded conversational interaction with Ollama or deterministic fallback.
        """
        conv = self.get_or_create_conversation(report_id, user_id, conversation_id)
        conv_id = conv.get("id", str(uuid.uuid4()))
        existing_msgs: List[Dict[str, Any]] = conv.get("messages", [])

        # Build context
        context_text, glossary_biomarkers, _ = self.build_chat_context(
            report_title=report_title,
            test_results=test_results,
            user_query=user_message,
            language=language,
        )

        # Build system prompt with anti-hallucination rules
        lang_note = {
            "ta": "Respond in polite, clear Tamil (தமிழ்).",
            "hi": "Respond in polite, clear Hindi (हिंदी).",
            "en": "Respond in polite, clear English.",
        }.get(language, "Respond in clear English.")

        system_prompt = (
            "You are 'HealthGuide AI', an empathetic, highly knowledgeable medical health-literacy assistant.\n\n"
            "STRICT CLINICAL RULES:\n"
            "1. GROUNDING: Answer the patient's questions ONLY using their verified lab findings and the medical knowledge context provided below.\n"
            "2. ACCURACY & CITATIONS: When mentioning any lab test, cite their exact numeric result, unit, and reference interval.\n"
            "3. MISSING TESTS: If the user asks about a biomarker or test not present in their report, explicitly say it was not included in this test panel.\n"
            "4. NON-DIAGNOSTIC: Do not formulate formal clinical diagnoses (e.g. do not say 'You have diabetes' or 'You have kidney disease'). State whether results are within normal limits or elevated/low, and explain possible physiological factors in calm, neutral terms.\n"
            "5. ACTIONABLE GUIDANCE: Suggest questions the patient can ask their physician during their next consultation.\n"
            "6. SAFETY & DISCLAIMER: Remind the patient that this is educational health information, not a substitute for clinical advice.\n"
            f"7. LANGUAGE: {lang_note}\n\n"
            f"REPORT CONTEXT:\n{context_text}"
        )

        # Format recent multi-turn conversation memory (last 6 messages)
        history_snippet = ""
        recent_history = existing_msgs[-6:]
        for m in recent_history:
            history_snippet += f"{m.get('role').upper()}: {m.get('content')}\n"

        prompt_with_history = (
            f"CONVERSATION HISTORY:\n{history_snippet}\n"
            f"USER QUESTION: {user_message}\n\n"
            f"ASSISTANT:"
        )

        # Try generating via local Ollama
        ollama_available, models = ollama_service.check_availability()
        reply_content: Optional[str] = None
        model_used = preferred_model or (models[0] if models else DEFAULT_OLLAMA_MODEL)
        is_mock = False

        if ollama_available:
            try:
                reply_content = ollama_service.generate(
                    prompt=prompt_with_history,
                    system_prompt=system_prompt,
                    model=model_used,
                    temperature=0.25,
                )
            except Exception as e:
                logger.warning(f"Ollama chat generation failed: {e}")

        # Fallback to deterministic clinical engine if Ollama is unavailable
        if not reply_content:
            is_mock = True
            model_used = "deterministic-clinical-qna-fallback"
            reply_content = self._generate_fallback_reply(
                user_message=user_message,
                report_title=report_title,
                test_results=test_results,
                language=language,
            )

        # Detect cited biomarkers in response
        cited_biomarkers = []
        for t in test_results:
            name = t.get("normalized_name", t.get("raw_test_name", ""))
            if name.lower() in reply_content.lower() or (t.get("raw_test_name", "").lower() in reply_content.lower()):
                if name not in cited_biomarkers:
                    cited_biomarkers.append(name)

        # Generate 2-3 dynamic suggested follow-up questions
        suggested_followups = self._generate_suggested_followups(
            user_message=user_message,
            test_results=test_results,
            language=language,
        )

        # Create message records
        now_iso = datetime.now(timezone.utc).isoformat()
        user_chat_msg = ChatMessage(
            role="user",
            content=user_message,
            timestamp=now_iso,
            sources=[],
        )
        assistant_chat_msg = ChatMessage(
            role="assistant",
            content=reply_content,
            timestamp=now_iso,
            sources=cited_biomarkers,
        )

        # Update and persist conversation history
        updated_msgs = existing_msgs + [user_chat_msg.model_dump(), assistant_chat_msg.model_dump()]
        cache_key = self._get_cache_key(report_id, user_id)
        _DEV_CONVERSATIONS_CACHE[cache_key] = {
            "id": conv_id,
            "report_id": report_id,
            "user_id": user_id,
            "messages": updated_msgs,
            "updated_at": now_iso,
        }

        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                supabase.table("conversations").upsert({
                    "id": conv_id,
                    "report_id": report_id,
                    "user_id": user_id,
                    "messages": updated_msgs,
                    "updated_at": now_iso,
                }).execute()
            except Exception as e:
                logger.error(f"Failed to persist chat messages in Supabase: {e}")

        all_chat_objects = [ChatMessage(**m) for m in updated_msgs]

        return ChatResponse(
            conversation_id=conv_id,
            report_id=report_id,
            reply=assistant_chat_msg,
            messages=all_chat_objects,
            cited_biomarkers=cited_biomarkers,
            suggested_followups=suggested_followups,
            model_used=model_used,
            is_mock_fallback=is_mock,
        )

    def _generate_fallback_reply(
        self,
        user_message: str,
        report_title: str,
        test_results: List[Dict[str, Any]],
        language: str = "en"
    ) -> str:
        """
        Deterministic, patient-friendly clinical conversational responder.
        Accurately answers common patient inquiries grounded in their actual lab values.
        """
        msg_lower = user_message.lower().strip()
        out_of_range = [t for t in test_results if t.get("flag") in ["HIGH", "LOW", "CRITICAL"]]
        normal_items = [t for t in test_results if t.get("flag") == "NORMAL"]

        # Helper to format a test item
        def fmt_item(t: Dict[str, Any]) -> str:
            name = t.get("normalized_name", t.get("raw_test_name", "Test"))
            val = t.get("value_numeric", t.get("value_text", "N/A"))
            unit = t.get("unit", "")
            ref = t.get("reference_range_raw") or f"{t.get('ref_min')} - {t.get('ref_max')}"
            flag = t.get("flag", "NORMAL")
            return f"**{name}**: Measured at **{val} {unit}** (Standard Reference Range: *{ref}* | Status: **{flag}**)"

        # 1. Out-of-range / abnormal values inquiry
        if any(w in msg_lower for w in ["abnormal", "out of range", "high", "low", "outside", "unusual", "flagged"]):
            if not out_of_range:
                if language == "ta":
                    return "உங்கள் அறிக்கையில் அனைத்து மதிப்பீடுகளும் சாதாரண வரம்பிற்குள் (Normal Range) உள்ளன. அசாதாரணமான மதிப்புகள் எதுவும் கண்டறியப்படவில்லை."
                elif language == "hi":
                    return "आपकी रिपोर्ट में सभी परीक्षण सामान्य सीमा (Normal Range) के भीतर हैं। कोई भी असामान्य मान नहीं पाया गया है।"
                return f"Great news! In your report '{report_title}', all {len(test_results)} analyzed biomarkers are currently within their standard reference intervals."

            items_list = "\n".join([f"- {fmt_item(t)}" for t in out_of_range])
            if language == "ta":
                return (
                    f"உங்கள் அறிக்கையில் பின்வரும் {len(out_of_range)} சோதனைகள் நிலையான வரம்பிற்கு வெளியே உள்ளன:\n\n"
                    f"{items_list}\n\n"
                    "இந்த முடிவுகளை உங்கள் மருத்துவரிடம் கலந்தாலோசித்து மதிப்பாய்வு செய்ய பரிந்துரைக்கப்படுகிறது."
                )
            elif language == "hi":
                return (
                    f"आपकी रिपोर्ट में निम्नलिखित {len(out_of_range)} परीक्षण मानक संदर्भ सीमा से बाहर हैं:\n\n"
                    f"{items_list}\n\n"
                    "कृपया इन परिणामों की पुष्टि और उचित सलाह के लिए अपने डॉक्टर से परामर्श करें।"
                )
            return (
                f"Based on your report '{report_title}', here are the {len(out_of_range)} biomarker(s) that are outside standard laboratory reference intervals:\n\n"
                f"{items_list}\n\n"
                "**Important Context:** A value outside the reference range does not automatically mean a disease is present. Many factors such as hydration, time of day, medications, or dietary habits can influence lab numbers. We recommend discussing these specific values with your doctor."
            )

        # 2. Normal / healthy values inquiry
        if any(w in msg_lower for w in ["normal", "healthy", "in range", "good"]):
            if not normal_items:
                return "All evaluated biomarkers in this report showed deviations outside standard bounds."
            items_list = "\n".join([f"- {fmt_item(t)}" for t in normal_items[:5]])
            return (
                f"Here are key biomarkers from your report that are within standard normal limits:\n\n"
                f"{items_list}\n\n"
                f"In total, {len(normal_items)} of your {len(test_results)} tests are currently in the healthy reference range."
            )

        # 3. Dietary / Nutrition inquiries (e.g. iron, food, diet, cholesterol, sugar)
        if any(w in msg_lower for w in ["food", "diet", "nutrition", "eat", "iron", "fruits", "vegetables", "lifestyle"]):
            if "iron" in msg_lower or any("hemoglobin" in (t.get("normalized_name", "").lower()) for t in test_results):
                return (
                    "**Dietary Information for Iron & Red Blood Cell Support:**\n\n"
                    "- **Iron-Rich Foods:** Spinach, lentils, chickpeas, beans, pumpkin seeds, tofu, fortified cereals, lean poultry, and fish.\n"
                    "- **Vitamin C Boost:** Pair plant-based iron sources with citrus fruits, bell peppers, or tomatoes to significantly enhance iron absorption.\n"
                    "- **Things to Moderate:** Tea and coffee during meals can inhibit iron absorption.\n\n"
                    "*Always consult your healthcare provider or a registered dietitian before starting new dietary supplements.*"
                )
            if any(w in msg_lower for w in ["cholesterol", "lipid", "fat"]):
                return (
                    "**Nutritional & Lifestyle Tips for Healthy Lipid Levels:**\n\n"
                    "- **Soluble Fiber:** Oats, barley, beans, lentils, apples, and flaxseeds help bind cholesterol in the digestive system.\n"
                    "- **Healthy Fats:** Choose unsaturated fats from olive oil, avocados, walnuts, and fatty fish (omega-3s) over saturated and trans fats.\n"
                    "- **Activity:** Regular aerobic exercise (e.g., 30 minutes of brisk walking 5 days a week) helps support healthy HDL levels.\n\n"
                    "*Discuss any significant dietary changes with your doctor.*"
                )
            return (
                "**General Nutritional & Lifestyle Guidelines:**\n\n"
                "- Aim for a balanced, colorful diet rich in whole grains, fresh vegetables, legumes, and lean proteins.\n"
                "- Maintain adequate daily hydration and consistent sleep hygiene.\n"
                "- For personalized guidance tailored to your specific lab numbers, speak with your physician or clinical nutritionist."
            )

        # 4. Doctor questions inquiry
        if any(w in msg_lower for w in ["question", "doctor", "physician", "ask", "appointment"]):
            q_list = []
            if out_of_range:
                for it in out_of_range[:3]:
                    name = it.get("normalized_name", it.get("raw_test_name"))
                    q_list.append(f"1. *'My {name} was measured at {it.get('value_numeric', it.get('value_text'))} {it.get('unit', '')}. What might be contributing to this level?'*")
            q_list.append("2. *'Are there any lifestyle or dietary adjustments you would recommend based on these findings?'*")
            q_list.append("3. *'When should I schedule a follow-up test to recheck these parameters?'*")
            return (
                "Here are recommended questions you can bring to your upcoming doctor's appointment:\n\n" +
                "\n".join(q_list) +
                "\n\nBringing your original lab report to the consultation will help your physician provide personalized care."
            )

        # 5. Specific Biomarker Inquiries (e.g. "What does TSH mean?", "Explain my Fasting Glucose")
        for t in test_results:
            raw_n = (t.get("raw_test_name") or "").lower()
            norm_n = (t.get("normalized_name") or "").lower()
            if (norm_n in msg_lower and len(norm_n) > 2) or (raw_n in msg_lower and len(raw_n) > 2):
                g_entry = medical_glossary_service.get_by_name(t.get("normalized_name", t.get("raw_test_name")))
                meaning = g_entry.patient_friendly_summary if g_entry else "Diagnostic biomarker."
                organs = g_entry.organs_involved if g_entry else "General Physiology"
                val = t.get("value_numeric", t.get("value_text", "N/A"))
                unit = t.get("unit", "")
                ref = t.get("reference_range_raw") or f"{t.get('ref_min')} - {t.get('ref_max')}"
                flag = t.get("flag", "NORMAL")

                status_commentary = (
                    f"Your result of **{val} {unit}** is within the normal reference range (*{ref}*)."
                    if flag == "NORMAL" else
                    f"Your result of **{val} {unit}** is flagged as **{flag}** compared to the reference range (*{ref}*)."
                )

                return (
                    f"### About **{t.get('normalized_name', t.get('raw_test_name'))}**\n\n"
                    f"- **Your Measured Value:** **{val} {unit}** (Reference: *{ref}*)\n"
                    f"- **Status:** **{flag}** ({status_commentary})\n"
                    f"- **What It Measures:** {meaning}\n"
                    f"- **Primary Organs Involved:** {organs}\n\n"
                    f"If you have questions about how this test relates to your daily energy, symptoms, or medications, discuss this result directly with your healthcare provider."
                )

        # 6. General Explanation / Summary
        if language == "ta":
            return (
                f"**அறிக்கை கண்ணோட்டம்:** உங்கள் '{report_title}' அறிக்கையில் மொத்தம் {len(test_results)} சோதனைகள் உள்ளன. "
                f"இதில் {len(normal_items)} சோதனைகள் சாதாரண வரம்பிலும், {len(out_of_range)} சோதனைகள் வரம்பிற்கு வெளியேயும் உள்ளன. "
                "எந்தவொரு குறிப்பிட்ட சோதனையைப் பற்றியும் நீங்கள் என்னிடம் கேட்கலாம்."
            )
        elif language == "hi":
            return (
                f"**रिपोर्ट अवलोकन:** आपकी '{report_title}' रिपोर्ट में कुल {len(test_results)} परीक्षण शामिल हैं। "
                f"इनमें से {len(normal_items)} सामान्य सीमा में हैं और {len(out_of_range)} सीमा से बाहर हैं। "
                "आप किसी भी विशेष परीक्षण या सुझाव के बारे में पूछ सकते हैं।"
            )

        return (
            f"### Executive Summary for **{report_title}**\n\n"
            f"- **Total Tests Evaluated:** {len(test_results)}\n"
            f"- **Within Normal Range:** {len(normal_items)}\n"
            f"- **Outside Standard Range:** {len(out_of_range)}\n\n"
            "You can ask me questions about any specific biomarker (e.g. *'What does my TSH mean?'*), "
            "ask for questions to bring to your doctor, or explore how diet and lifestyle relate to your results."
        )

    def _generate_suggested_followups(
        self,
        user_message: str,
        test_results: List[Dict[str, Any]],
        language: str = "en"
    ) -> List[str]:
        """
        Generates contextually relevant smart prompt chips for patient follow-up.
        """
        msg_lower = user_message.lower()
        out_of_range = [t for t in test_results if t.get("flag") in ["HIGH", "LOW", "CRITICAL"]]

        if "abnormal" in msg_lower or "out of range" in msg_lower:
            return [
                "What questions should I ask my doctor about these results?",
                "What lifestyle factors influence these values?",
                "Which values were completely normal?",
            ]
        elif "doctor" in msg_lower or "question" in msg_lower:
            return [
                "Which values are out of the standard range?",
                "What foods or nutrients support these organs?",
                "Explain my complete report in simple terms",
            ]
        elif "diet" in msg_lower or "food" in msg_lower or "iron" in msg_lower:
            return [
                "Which of my test results were abnormal?",
                "What questions should I ask my doctor?",
                "How often should I re-test these biomarkers?",
            ]
        else:
            chips = ["Which values are out of range?", "What questions should I ask my doctor?"]
            if out_of_range:
                first_abnormal = out_of_range[0].get("normalized_name", out_of_range[0].get("raw_test_name"))
                chips.append(f"What does {first_abnormal} measure?")
            else:
                chips.append("What dietary habits support these results?")
            return chips

# Global singleton chat service
chat_service = ChatService()
