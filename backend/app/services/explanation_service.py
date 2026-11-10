import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.models.schemas import (
    ReportExplanationResponse,
    GroundedBiomarkerCitation,
)
from app.services.glossary_service import medical_glossary_service
from app.services.ollama_service import ollama_service
from app.core.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.explanation_service")

BIOMARKER_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "haemoglobin": {
        "ta": "ஹீமோகுளோபின் என்பது உங்கள் இரத்த சிவப்பணுக்களில் உள்ள ஒரு புரதமாகும், இது உடல் முழுவதும் புதிய ஆக்ஸிஜனைக் கொண்டு சென்று உங்களுக்கு ஆற்றலைத் தருகிறது.",
        "hi": "हीमोग्लोबिन आपके लाल रक्त कोशिकाओं में मौजूद प्रोटीन है जो पूरे शरीर में ताजा ऑक्सीजन पहुंचाकर ऊर्जा देता है।",
    },
    "hemoglobin": {
        "ta": "ஹீமோகுளோபின் என்பது உங்கள் இரத்த சிவப்பணுக்களில் உள்ள ஒரு புரதமாகும், இது உடல் முழுவதும் புதிய ஆக்ஸிஜனைக் கொண்டு சென்று உங்களுக்கு ஆற்றலைத் தருகிறது.",
        "hi": "हीमोग्लोबिन आपके लाल रक्त कोशिकाओं में मौजूद प्रोटीन है जो पूरे शरीर में ताजा ऑक्सीजन पहुंचाकर ऊर्जा देता है।",
    },
    "total leucocyte count (wbc)": {
        "ta": "வெள்ளை இரத்த அணுக்கள் உங்கள் உடலின் நோய் எதிர்ப்பு பாதுகாப்பு படையாகும், இது தொற்று அல்லது வீக்கத்தை எதிர்த்துப் போராடுகிறது.",
        "hi": "श्वेत रक्त कोशिकाएं आपके शरीर की प्रतिरक्षा रक्षा प्रणाली हैं जो संक्रमण या सूजन से लड़ती हैं।",
    },
    "wbc": {
        "ta": "வெள்ளை இரத்த அணுக்கள் உங்கள் உடலின் நோய் எதிர்ப்பு பாதுகாப்பு படையாகும், இது தொற்று அல்லது வீக்கத்தை எதிர்த்துப் போராடுகிறது.",
        "hi": "श्वेत रक्त कोशिकाएं आपके शरीर की प्रतिरक्षा रक्षा प्रणाली हैं जो संक्रमण या सूजन से लड़ती हैं।",
    },
    "platelet count": {
        "ta": "பிளேட்லெட்டுகள் என்பவை இரத்தம் உறைவதற்கும், காயம் ஏற்படும் போது இரத்தப்போக்கை நிறுத்துவதற்கும் உதவும் சிறிய செல் துண்டுகளாகும்.",
        "hi": "प्लेटलेट्स छोटे सेल टुकड़े होते हैं जो रक्त का थक्का बनाने और रक्तस्राव रोकने में मदद करते हैं।",
    },
    "platelets": {
        "ta": "பிளேட்லெட்டுகள் என்பவை இரத்தம் உறைவதற்கும், காயம் ஏற்படும் போது இரத்தப்போக்கை நிறுத்துவதற்கும் உதவும் சிறிய செல் துண்டுகளாகும்.",
        "hi": "प्लेटलेट्स छोटे सेल टुकड़े होते हैं जो रक्त का थक्का बनाने और रक्तस्राव रोकने में मदद करते हैं।",
    },
    "fasting blood glucose": {
        "ta": "உண்ணாவிரத இரத்த சர்க்கரை என்பது 8-12 மணி நேரம் உணவு உண்ணாத நிலையில் உங்கள் இரத்தத்தில் உள்ள அடிப்படை குளுக்கோஸ் அளவை அளவிடுகிறது.",
        "hi": "फास्टिंग ब्लड शुगर 8-12 घंटे भूखे रहने के बाद आपके बेसलाइन ग्लूकोज स्तर को मापता है।",
    },
    "fasting blood sugar": {
        "ta": "உண்ணாவிரத இரத்த சர்க்கரை என்பது 8-12 மணி நேரம் உணவு உண்ணாத நிலையில் உங்கள் இரத்தத்தில் உள்ள அடிப்படை குளுக்கோஸ் அளவை அளவிடுகிறது.",
        "hi": "फास्टिंग ब्लड शुगर 8-12 घंटे भूखे रहने के बाद आपके बेसलाइन ग्लूकोज स्तर को मापता है।",
    },
    "glycated hemoglobin (hba1c)": {
        "ta": "HbA1c என்பது கடந்த 3 மாதங்களில் உங்கள் இரத்த சர்க்கரை அளவின் சராசரியைக் காட்டுகிறது, இது சர்க்கரை கட்டுப்பாடு எவ்வாறு உள்ளது என்பதை விளக்குகிறது.",
        "hi": "HbA1c पिछले 3 महीनों में आपके रक्त शर्करा के औसत स्तर को दर्शाता है।",
    },
    "hba1c": {
        "ta": "HbA1c என்பது கடந்த 3 மாதங்களில் உங்கள் இரத்த சர்க்கரை அளவின் சராசரியைக் காட்டுகிறது, இது சர்க்கரை கட்டுப்பாடு எவ்வாறு உள்ளது என்பதை விளக்குகிறது.",
        "hi": "HbA1c पिछले 3 महीनों में आपके रक्त शर्करा के औसत स्तर को दर्शाता है।",
    },
    "serum creatinine": {
        "ta": "கிரியேட்டினின் என்பது தசைகளில் இருந்து உருவாகும் இயற்கையான கழிவுப் பொருளாகும், இதை ஆரோக்கியமான சிறுநீரகங்கள் சிறுநீரில் வடிகட்டுகின்றன.",
        "hi": "सीरम क्रिएटिनिन मांसपेशियों से निकलने वाला एक अपशिष्ट उत्पाद है जिसे स्वस्थ गुर्दे मूत्र में छानते हैं।",
    },
    "creatinine": {
        "ta": "கிரியேட்டினின் என்பது தசைகளில் இருந்து உருவாகும் இயற்கையான கழிவுப் பொருளாகும், இதை ஆரோக்கியமான சிறுநீரகங்கள் சிறுநீரில் வடிகட்டுகின்றன.",
        "hi": "सीरम क्रिएटिनिन मांसपेशियों से निकलने वाला एक अपशिष्ट उत्पाद है जिसे स्वस्थ गुर्दे मूत्र में छानते हैं।",
    },
    "sgpt / alt": {
        "ta": "ALT என்பது கல்லீரல் ஆரோக்கியத்தைக் குறிக்கும் மிக முக்கியமான நொதியாகும். இது கல்லீரல் செல்களில் அழுத்தம் அல்லது வீக்கம் உள்ளதா என்பதைக் காட்டுகிறது.",
        "hi": "ALT सबसे विशिष्ट लिवर एंजाइम है। इसका बढ़ना दर्शाता है कि लिवर कोशिकाओं में तनाव या सूजन है।",
    },
    "alt": {
        "ta": "ALT என்பது கல்லீரல் ஆரோக்கியத்தைக் குறிக்கும் மிக முக்கியமான நொதியாகும். இது கல்லீரல் செல்களில் அழுத்தம் அல்லது வீக்கம் உள்ளதா என்பதைக் காட்டுகிறது.",
        "hi": "ALT सबसे विशिष्ट लिवर एंजाइम है। इसका बढ़ना दर्शाता है कि लिवर कोशिकाओं में तनाव या सूजन है।",
    },
    "sgot / ast": {
        "ta": "AST என்பது கல்லீரல், இதயம் மற்றும் தசைகளில் காணப்படும் ஒரு நொதியாகும். இது திசு சேதம் அல்லது கல்லீரல் அழுத்தத்தை மதிப்பிட உதவுகிறது.",
        "hi": "AST लिवर, हृदय और मांसपेशियों में पाया जाने वाला एंजाइम है जो ऊतक तनाव को दर्शाता है।",
    },
    "ast": {
        "ta": "AST என்பது கல்லீரல், இதயம் மற்றும் தசைகளில் காணப்படும் ஒரு நொதியாகும். இது திசு சேதம் அல்லது கல்லீரல் அழுத்தத்தை மதிப்பிட உதவுகிறது.",
        "hi": "AST लिवर, हृदय और मांसपेशियों में पाया जाने वाला एंजाइम है जो ऊतक तनाव को दर्शाता है।",
    },
    "total cholesterol": {
        "ta": "கொலஸ்ட்ரால் என்பது உயிரணு சவ்வுகள், வைட்டமின் டி மற்றும் ஹார்மோன்களை உருவாக்க உதவும் ஒரு மெழுகு போன்ற கொழுப்புப் பொருளாகும்.",
        "hi": "कोलेस्ट्रॉल एक मोमी वसायुक्त पदार्थ है जो कोशिका झिल्ली और हार्मोन बनाने में मदद करता है।",
    },
    "cholesterol": {
        "ta": "கொலஸ்ட்ரால் என்பது உயிரணு சவ்வுகள், வைட்டமின் டி மற்றும் ஹார்மோன்களை உருவாக்க உதவும் ஒரு மெழுகு போன்ற கொழுப்புப் பொருளாகும்.",
        "hi": "कोलेस्ट्रॉल एक मोमी वसायुक्त पदार्थ है जो कोशिका झिल्ली और हार्मोन बनाने में मदद करता है।",
    },
    "ldl cholesterol": {
        "ta": "LDL 'கெட்ட கொலஸ்ட்ரால்' என்று அழைக்கப்படுகிறது, ஏனெனில் அதிக அளவு தமனிகளில் படிவுகளை உருவாக்கி இதய நோய் அபாயத்தை அதிகரிக்கலாம்.",
        "hi": "LDL को 'खराब कोलेस्ट्रॉल' कहा जाता है क्योंकि उच्च स्तर धमनियों में रुकावट पैदा कर सकता है।",
    },
    "hdl cholesterol": {
        "ta": "HDL 'நல்ல கொலஸ்ட்ரால்' ஆகும், இது இரத்த ஓட்டத்தில் உள்ள அதிகப்படியான கொழுப்பை கல்லீரலுக்கு எடுத்துச் சென்று இதயத்தைப் பாதுகாக்கிறது.",
        "hi": "HDL 'अच्छा कोलेस्ट्रॉल' है जो अतिरिक्त कोलेस्ट्रॉल को लिवर में वापस ले जाकर हृदय की रक्षा करता है।",
    },
    "triglycerides": {
        "ta": "டிரைகிளிசரைடுகள் என்பவை இரத்தத்தில் உள்ள பொதுவான கொழுப்பு வகையாகும், அவை பயன்படுத்தப்படாத கலோரிகளை எதிர்கால ஆற்றலுக்காக சேமிக்கின்றன.",
        "hi": "ट्राइग्लिसराइड्स रक्त में मौजूद वसा का एक प्रकार हैं जो अप्रयुक्त कैलोरी को ऊर्जा के रूप में संग्रहीत करते हैं।",
    },
    "thyroid stimulating hormone (tsh)": {
        "ta": "TSH என்பது உங்கள் வளர்சிதை மாற்றம் மற்றும் ஆற்றல் சமநிலையைக் கட்டுப்படுத்தும் தைராய்டு சுரப்பியை ஒழுங்குபடுத்தும் ஹார்மோனாகும்.",
        "hi": "TSH थायरॉयड ग्रंथि को उत्तेजित करने वाला हार्मोन है जो मेटाबॉलिज्म और ऊर्जा को नियंत्रित करता है।",
    },
    "tsh": {
        "ta": "TSH என்பது உங்கள் வளர்சிதை மாற்றம் மற்றும் ஆற்றல் சமநிலையைக் கட்டுப்படுத்தும் தைராய்டு சுரப்பியை ஒழுங்குபடுத்தும் ஹார்மோனாகும்.",
        "hi": "TSH थायरॉयड ग्रंथि को उत्तेजित करने वाला हार्मोन है जो मेटाबॉलिज्म और ऊर्जा को नियंत्रित करता है।",
    },
    "blood urea nitrogen (bun)": {
        "ta": "யூரியா நைட்ரஜன் என்பது புரத செரிமானத்தின் கழிவுப் பொருளாகும், இது சிறுநீரகங்கள் இரத்தத்தை எவ்வளவு திறம்பட வடிகட்டுகின்றன என்பதை அளவிடுகிறது.",
        "hi": "यूरिया नाइट्रोजन प्रोटीन पाचन का अपशिष्ट है जो गुर्दे की निस्पंदन क्षमता को मापता है।",
    },
    "urea": {
        "ta": "யூரியா என்பது புரத முறிவின் கழிவுப் பொருளாகும், இது சிறுநீரக வடிகட்டுதல் செயல்பாட்டை பிரதிபலிக்கிறது.",
        "hi": "यूरिया प्रोटीन अपघटन का अपशिष्ट है जो गुर्दे की कार्यप्रणाली को दर्शाता है।",
    },
    "uric acid": {
        "ta": "யூரிக் அமிலம் என்பது பியூரின்கள் உடையும் போது உருவாகும் கழிவுப் பொருளாகும்; அதிக அளவு மூட்டு வலி அல்லது கீல்வாதத்தை ஏற்படுத்தலாம்.",
        "hi": "यूरिक एसिड प्यूरीन के टूटने से बनता है; उच्च स्तर जोड़ों में दर्द या गाउट पैदा कर सकता है।",
    },
    "rbc count": {
        "ta": "சிவப்பு இரத்த அணுக்கள் உங்கள் நுரையீரலில் இருந்து தசைகள் மற்றும் உறுப்புகளுக்கு ஆக்ஸிஜனை எடுத்துச் செல்லும் நுண்ணிய வாகனங்களாகும்.",
        "hi": "लाल रक्त कोशिकाएं फेफड़ों से मांसपेशियों और अंगों तक ऑक्सीजन ले जाने वाले वाहन हैं।",
    },
    "packed cell volume (pcv)": {
        "ta": "ஹெமாட்டோக்ரிட் என்பது திரவ பிளாஸ்மாவுடன் ஒப்பிடும்போது உங்கள் இரத்தத்தில் உள்ள சிவப்பு இரத்த அணுக்களின் சதவீதத்தைக் குறிக்கிறது.",
        "hi": "हेमाटोक्रिट तरल प्लाज्मा की तुलना में लाल रक्त कोशिकाओं के प्रतिशत को दर्शाता है।",
    },
    "mean corpuscular volume (mcv)": {
        "ta": "MCV உங்கள் இரத்த சிவப்பணுக்கள் சரியான அளவில் உள்ளதா அல்லது அசாதாரணமாக சிறியதாகவோ பெரியதாகவோ உள்ளதா என்பதைக் காட்டுகிறது.",
        "hi": "MCV दर्शाता है कि आपकी लाल रक्त कोशिकाएं सामान्य आकार की हैं, असामान्य रूप से छोटी हैं या बड़ी हैं।",
    },
    "mean corpuscular hemoglobin (mch)": {
        "ta": "MCH என்பது சராசரி சிவப்பு இரத்த செல்லுக்குள் எவ்வளவு ஹீமோகுளோபின் புரதம் அடைக்கப்பட்டுள்ளது என்பதை அளவிடுகிறது.",
        "hi": "MCH मापता है कि एक औसत लाल रक्त कोशिका में कितना हीमोग्लोबिन प्रोटीन भरा हुआ है।",
    },
    "erythrocyte sedimentation rate (esr)": {
        "ta": "ESR உடலில் ஏதேனும் வீக்கம், தொற்று அல்லது அழற்சி உள்ளதா என்பதைக் கண்டறியும் ஒரு பொதுவான சோதனையாகும்.",
        "hi": "ESR शरीर में सूजन या संक्रमण का पता लगाने वाला परीक्षण है।",
    },
    "esr": {
        "ta": "ESR உடலில் ஏதேனும் வீக்கம், தொற்று அல்லது அழற்சி உள்ளதா என்பதைக் கண்டறியும் ஒரு பொதுவான சோதனையாகும்.",
        "hi": "ESR शरीर में सूजन या संक्रमण का पता लगाने वाला परीक्षण है।",
    },
    "vitamin d (25-oh)": {
        "ta": "வைட்டமின் டி எலும்பு வலிமை, கால்சியம் உறிஞ்சுதல் மற்றும் நோய் எதிர்ப்பு சக்தியை பராமரிக்க அவசியமானது.",
        "hi": "विटामिन डी हड्डियों की मजबूती, कैल्शियम अवशोषण और प्रतिरक्षा के लिए आवश्यक है।",
    },
    "vitamin b12": {
        "ta": "வைட்டமின் பி12 நரம்பு மண்டல ஆரோக்கியம், மூளை செயல்பாடு மற்றும் இரத்த அணுக்கள் உருவாக்கத்திற்கு இன்றியமையாதது.",
        "hi": "विटामिन बी12 तंत्रिका तंत्र के स्वास्थ्य और रक्त कोशिकाओं के निर्माण के लिए महत्वपूर्ण है।",
    },
    "serum calcium": {
        "ta": "கால்சியம் எலும்புகள், பற்கள், நரம்பு சமிக்ஞைகள் மற்றும் இதய துடிப்பை சீராக வைத்திருக்க உதவுகிறது.",
        "hi": "कैल्शियम हड्डियों, दांतों और हृदय गति को सुचारू रखने में मदद करता है।",
    },
    "bilirubin (total)": {
        "ta": "பிலிரூபின் என்பது பழைய இரத்த சிவப்பணுக்கள் உடையும் போது உருவாகும் மஞ்சள் நிற நிறமியாகும்; இது கல்லீரல் மற்றும் பித்தப்பை செயல்பாட்டை பிரதிபலிக்கிறது.",
        "hi": "बिलीरुबिन लाल रक्त कोशिकाओं के टूटने से बनता है और लिवर व पित्त स्वास्थ्य को दर्शाता है।",
    },
    "alkaline phosphatase (alp)": {
        "ta": "ALP என்பது கல்லீரல், பித்த நாளங்கள் மற்றும் எலும்புகளில் காணப்படும் ஒரு நொதியாகும்.",
        "hi": "ALP लिवर, पित्त नली और हड्डियों में पाया जाने वाला एंजाइम है।",
    },
    "total protein": {
        "ta": "மொத்த புரதம் என்பது இரத்தத்தில் உள்ள அல்புமின் மற்றும் குளோபுலின் புரதங்களின் ஒட்டுமொத்த அளவைக் குறிக்கிறது.",
        "hi": "कुल प्रोटीन रक्त में एल्ब्यूमिन और ग्लोब्युलिन के कुल स्तर को दर्शाता है।",
    },
    "albumin": {
        "ta": "அல்புமின் என்பது கல்லீரலால் தயாரிக்கப்படும் முக்கிய புரதமாகும், இது இரத்தக் குழாய்களில் திரவத்தை தக்கவைத்து ஊட்டச்சத்துக்களை கடத்துகிறது.",
        "hi": "एल्ब्यूमिन लिवर द्वारा निर्मित प्रमुख प्रोटीन है जो तरल संतुलन बनाए रखता है।",
    },
}

def get_biomarker_clinical_meaning(norm_name: str, language: str, default_meaning: str) -> str:
    """Returns patient-friendly clinical meaning localized to requested language."""
    if language in ["ta", "hi"]:
        clean_k = norm_name.lower().strip()
        for k, tr_map in BIOMARKER_TRANSLATIONS.items():
            if k == clean_k or k in clean_k or clean_k in k:
                if language in tr_map:
                    return tr_map[language]
        if language == "ta":
            return f"{norm_name} என்பது உங்கள் உடல் நலம் மற்றும் உறுப்பு செயல்பாட்டை மதிப்பிடுவதற்கான ஒரு மருத்துவ பரிசோதனை அளவீடாகும்."
        elif language == "hi":
            return f"{norm_name} आपके समग्र स्वास्थ्य और अंग प्रणाली के मूल्यांकन के लिए एक नैदानिक माप है।"
    return default_meaning

# In-memory explanation cache for local development / testing
_DEV_EXPLANATION_CACHE: Dict[str, Dict[str, Any]] = {}

class GroundedExplanationService:
    """
    Orchestration service for generating and retrieving grounded, anti-hallucinatory
    patient-friendly medical report explanations.
    """

    def generate_explanation(
        self,
        report_id: str,
        report_title: str,
        test_results: List[Dict[str, Any]],
        language: str = "en",
        preferred_model: Optional[str] = None,
    ) -> ReportExplanationResponse:
        """
        Generates grounded explanation for a report by combining structured results
        with Phase 7 glossary cards and executing Ollama with strict citation prompting.
        """
        if not test_results:
            return ReportExplanationResponse(
                report_id=report_id,
                title=report_title,
                language=language,
                executive_summary=f"No structured test results available for report '{report_title}'. Please run OCR and clinical extraction first.",
                normal_findings_summary="None",
                abnormal_findings_summary="None",
                doctor_questions=["Please review the original laboratory report."],
                citations=[],
                disclaimer="Educational health literacy summary.",
                model_used="none",
                is_mock_fallback=True,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )

        # 1. Build Citation and Context map from Phase 7 Glossary
        citations: List[GroundedBiomarkerCitation] = []
        glossary_context: List[Dict[str, Any]] = []
        glossary_map: Dict[str, Any] = {}

        for it in test_results:
            raw_name = it.get("raw_test_name", "")
            norm_name = it.get("normalized_name", raw_name)
            val = str(it.get("value_numeric", it.get("value_text", "N/A")))
            unit = it.get("unit")
            ref_raw = it.get("reference_range_raw") or (
                f"{it.get('ref_min')} - {it.get('ref_max')}"
                if it.get("ref_min") is not None and it.get("ref_max") is not None
                else "N/A"
            )
            flag = it.get("flag", "NORMAL")

            # Fetch glossary entry
            g_entry = medical_glossary_service.get_by_name(norm_name)
            meaning = ""
            organs = None
            if g_entry:
                english_meaning = g_entry.patient_friendly_summary
                organs = g_entry.organs_involved
                g_dict = medical_glossary_service._entry_to_dict(g_entry)
                glossary_context.append(g_dict)
                glossary_map[norm_name.lower()] = g_dict
            else:
                english_meaning = "Diagnostic investigation measurement."

            meaning = get_biomarker_clinical_meaning(norm_name, language, english_meaning)

            citations.append(
                GroundedBiomarkerCitation(
                    biomarker_name=norm_name,
                    measured_value=val,
                    unit=unit,
                    reference_interval=ref_raw,
                    flag=flag,
                    clinical_meaning=meaning,
                    organs_involved=organs,
                )
            )

        # 2. Check Ollama availability
        ollama_online, models = ollama_service.check_availability()
        explanation_data: Optional[Dict[str, Any]] = None

        if ollama_online:
            chosen_model = preferred_model or (models[0] if models else "llama3:latest")
            system_p, user_p = ollama_service.construct_grounded_prompt(
                report_title=report_title,
                test_items=test_results,
                glossary_context=glossary_context,
                language=language,
            )
            raw_response = ollama_service.generate(prompt=user_p, system_prompt=system_p, model=chosen_model)
            if raw_response:
                normal_txt = "See detailed citations below for confirmed normal values."
                abnormal_txt = "See detailed citations below for highlighted out-of-range parameters."
                doc_q = [
                    "Are any follow-up tests recommended for my out-of-range markers?",
                    "What lifestyle or dietary modifications would be beneficial?",
                ]
                disc = "This explanation is generated by local AI for health literacy purposes only and is not medical diagnosis."

                if language == "ta":
                    normal_txt = "உறுதிப்படுத்தப்பட்ட இயல்பான முடிவுகளுக்கு கீழே உள்ள விரிவான ஆதாரக் குறிப்புகளைப் பார்க்கவும்."
                    abnormal_txt = "இயல்பு வரம்பிற்கு அப்பாற்பட்ட அளவீடுகளுக்கு கீழே உள்ள சிறப்பம்சங்களைக் கவனிக்கவும்."
                    doc_q = [
                        "இயல்பு வரம்பை மீறிய எனது அளவீடுகளுக்கு கூடுதல் பரிசோதனைகள் தேவையா?",
                        "எனது ஆரோக்கியத்தை மேம்படுத்த என்ன உணவுமுறை மற்றும் வாழ்க்கைமுறை மாற்றங்கள் தேவை?",
                        "அடுத்த பரிசோதனையை எப்போது செய்து கொள்ள வேண்டும்?"
                    ]
                    disc = "இந்த விளக்கம் சுகாதார விழிப்புணர்வு மற்றும் கல்விக்காக மட்டுமே உருவாக்கப்பட்டது. இது மருத்துவ சிகிச்சை அல்லது நோய் கண்டறிதல் ஆலோசனை அல்ல."
                elif language == "hi":
                    normal_txt = "पुष्टि किए गए सामान्य परिणामों के लिए नीचे दिए गए विस्तृत संदर्भ देखें।"
                    abnormal_txt = "सामान्य सीमा से बाहर के परिणामों के लिए नीचे दिए गए महत्वपूर्ण बिंदुओं पर ध्यान दें।"
                    doc_q = [
                        "क्या असामान्य बायोमार्कर के लिए आगे के परीक्षण आवश्यक हैं?",
                        "स्वास्थ्य सुधार के लिए क्या आहार या जीवनशैली में बदलाव उपयोगी होंगे?",
                        "अगला परीक्षण कब कराना चाहिए?"
                    ]
                    disc = "यह व्याख्या केवल स्वास्थ्य साक्षरता और रोगी शिक्षा के लिए तैयार की गई है। यह चिकित्सीय सलाह या निदान नहीं है।"

                explanation_data = {
                    "executive_summary": raw_response[:400].strip(),
                    "normal_findings_summary": normal_txt,
                    "abnormal_findings_summary": abnormal_txt,
                    "doctor_questions": doc_q,
                    "disclaimer": disc,
                    "model_used": chosen_model,
                    "is_mock_fallback": False,
                }

        # 3. Use Clinical Deterministic Generator if Ollama offline or output empty
        if not explanation_data:
            explanation_data = ollama_service.generate_fallback_explanation(
                report_title=report_title,
                test_items=test_results,
                glossary_map=glossary_map,
                language=language,
            )

        response = ReportExplanationResponse(
            report_id=report_id,
            title=report_title,
            language=language,
            executive_summary=explanation_data["executive_summary"],
            normal_findings_summary=explanation_data["normal_findings_summary"],
            abnormal_findings_summary=explanation_data["abnormal_findings_summary"],
            doctor_questions=explanation_data["doctor_questions"],
            citations=citations,
            disclaimer=explanation_data["disclaimer"],
            model_used=explanation_data["model_used"],
            is_mock_fallback=explanation_data["is_mock_fallback"],
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # 4. Cache & Persist explanation
        cache_key = f"{report_id}_{language}"
        _DEV_EXPLANATION_CACHE[cache_key] = response.model_dump()

        if is_supabase_configured():
            try:
                supabase = get_supabase_client()
                supabase.table("reports").update({
                    "summary": response.executive_summary
                }).eq("id", report_id).execute()
            except Exception as e:
                logger.error(f"Error persisting explanation in Supabase: {e}")

        return response

    def get_cached_explanation(self, report_id: str, language: str = "en") -> Optional[ReportExplanationResponse]:
        """
        Retrieves cached explanation for a report if already generated.
        """
        cache_key = f"{report_id}_{language}"
        if cache_key in _DEV_EXPLANATION_CACHE:
            return ReportExplanationResponse(**_DEV_EXPLANATION_CACHE[cache_key])
        return None

# Global singleton explanation service
grounded_explanation_service = GroundedExplanationService()
