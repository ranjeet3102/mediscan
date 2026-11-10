'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { api, ReportDetail, TestResultItem, ReportExplanation, AIStatus } from '@/lib/api';
import {
  FileText,
  ScanLine,
  ArrowLeft,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  ShieldCheck,
  FileCode,
  Layers,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Edit3,
  Save,
  X,
  Plus,
  CheckCircle,
  HelpCircle,
  ShieldAlert,
  SlidersHorizontal,
  Info,
  BookOpen,
  HeartPulse,
  BrainCircuit,
  MessageSquare,
  Globe,
  Stethoscope,
  ListChecks,
  Bot,
  Pill,
} from 'lucide-react';
import ReportChatDrawer from '@/components/chat/ReportChatDrawer';

// Multilingual Localization Dictionaries for Grounded Biomarker Citations
const BIOMARKER_LOCALIZED_NAMES: Record<string, { ta: string; hi: string }> = {
  haemoglobin: { ta: 'ஹீமோகுளோபின் (Haemoglobin)', hi: 'हीमोग्लोबिन (Haemoglobin)' },
  hemoglobin: { ta: 'ஹீமோகுளோபின் (Hemoglobin)', hi: 'हीमोग्लोबिन (Hemoglobin)' },
  'total leucocyte count (wbc)': { ta: 'வெள்ளை இரத்த அணுக்கள் (WBC)', hi: 'श्वेत रक्त कोशिकाएं (WBC)' },
  'total leukocyte count': { ta: 'வெள்ளை இரத்த அணுக்கள் (WBC)', hi: 'श्वेत रक्त कोशिकाएं (WBC)' },
  wbc: { ta: 'வெள்ளை இரத்த அணுக்கள் (WBC)', hi: 'श्वेत रक्त कोशिकाएं (WBC)' },
  'platelet count': { ta: 'பிளேட்லெட் எண்ணிக்கை (Platelets)', hi: 'प्लेटलेट काउंट (Platelets)' },
  platelets: { ta: 'பிளேட்லெட் எண்ணிக்கை (Platelets)', hi: 'प्लेटलेट काउंट (Platelets)' },
  'fasting blood glucose': { ta: 'உண்ணாவிரத இரத்த சர்க்கரை (Fasting Glucose)', hi: 'फास्टिंग ब्लड ग्लूकोज (Glucose)' },
  'fasting blood sugar': { ta: 'உண்ணாவிரத இரத்த சர்க்கரை (FBS)', hi: 'फास्टिंग ब्लड शुगर (FBS)' },
  'glycated hemoglobin (hba1c)': { ta: 'சராசரி இரத்த சர்க்கரை (HbA1c)', hi: 'ग्लाइकेटेड हीमोग्लोबिन (HbA1c)' },
  hba1c: { ta: 'சராசரி இரத்த சர்க்கரை (HbA1c)', hi: 'ग्लाइकेटेड हीमोग्लोबिन (HbA1c)' },
  'serum creatinine': { ta: 'சீரம் கிரியேட்டினின் (Creatinine)', hi: 'सीरम क्रिएटिनिन (Creatinine)' },
  creatinine: { ta: 'சீரம் கிரியேட்டினின் (Creatinine)', hi: 'सीरम क्रिएटिनिन (Creatinine)' },
  'sgpt / alt': { ta: 'கல்லீரல் நொதி (SGPT / ALT)', hi: 'लिवर एंजाइम (SGPT / ALT)' },
  alt: { ta: 'கல்லீரல் நொதி (ALT)', hi: 'लिवर एंजाइम (ALT)' },
  'sgot / ast': { ta: 'கல்லீரல்/தசை நொதி (SGOT / AST)', hi: 'लिवर एंजाइम (SGOT / AST)' },
  ast: { ta: 'கல்லீரல் நொதி (AST)', hi: 'लिवर एंजाइम (AST)' },
  'total cholesterol': { ta: 'மொத்த கொலஸ்ட்ரால் (Total Cholesterol)', hi: 'कुल कोलेस्ट्रॉल (Total Cholesterol)' },
  cholesterol: { ta: 'மொத்த கொலஸ்ட்ரால் (Cholesterol)', hi: 'कुल कोलेस्ट्रॉल (Cholesterol)' },
  'ldl cholesterol': { ta: 'கெட்ட கொலஸ்ட்ரால் (LDL)', hi: 'एलडीएल खराब कोलेस्ट्रॉल (LDL)' },
  'hdl cholesterol': { ta: 'நல்ல கொலஸ்ட்ரால் (HDL)', hi: 'एचडीएल अच्छा कोलेस्ट्रॉल (HDL)' },
  triglycerides: { ta: 'டிரைகிளிசரைடுகள் (Triglycerides)', hi: 'ट्राइग्लिसराइड्स (Triglycerides)' },
  'thyroid stimulating hormone (tsh)': { ta: 'தைராய்டு ஹார்மோன் (TSH)', hi: 'थायराइड हार्मोन (TSH)' },
  tsh: { ta: 'தைராய்டு ஹார்மோன் (TSH)', hi: 'थायराइड हार्मोन (TSH)' },
  'blood urea nitrogen (bun)': { ta: 'இரத்த யூரியா நைட்ரஜன் (BUN)', hi: 'ब्लड यूरिया नाइट्रोजन (BUN)' },
  urea: { ta: 'யூரியா (Urea)', hi: 'यूरिया (Urea)' },
  'uric acid': { ta: 'யூரிக் அமிலம் (Uric Acid)', hi: 'यूरिक एसिड (Uric Acid)' },
  'rbc count': { ta: 'சிவப்பு இரத்த அணுக்கள் (RBC)', hi: 'लाल रक्त कोशिकाएं (RBC)' },
  'packed cell volume (pcv)': { ta: 'ஹெமாட்டோக்ரிட் (PCV)', hi: 'हेमाटोक्रिट (PCV)' },
  'mean corpuscular volume (mcv)': { ta: 'இரத்த அணு சராசரி அளவு (MCV)', hi: 'एमसीवी (MCV)' },
  'mean corpuscular hemoglobin (mch)': { ta: 'இரத்த அணு ஹீமோகுளோபின் (MCH)', hi: 'एमसीएच (MCH)' },
  'erythrocyte sedimentation rate (esr)': { ta: 'அழற்சி வீத சோதனை (ESR)', hi: 'ईएसआर (ESR)' },
  esr: { ta: 'அழற்சி வீத சோதனை (ESR)', hi: 'ईएसआर (ESR)' },
  'vitamin d (25-oh)': { ta: 'வைட்டமின் டி (Vitamin D)', hi: 'विटामिन डी (Vitamin D)' },
  'vitamin b12': { ta: 'வைட்டமின் பி12 (Vitamin B12)', hi: 'विटामिन बी12 (Vitamin B12)' },
  'serum calcium': { ta: 'சீரம் கால்சியம் (Calcium)', hi: 'सीरम कैल्शियम (Calcium)' },
  'bilirubin (total)': { ta: 'மொத்த பிலிரூபின் (Bilirubin)', hi: 'कुल बिलीरुबिन (Bilirubin)' },
  'alkaline phosphatase (alp)': { ta: 'அல்கலைன் பாஸ்பேடேஸ் (ALP)', hi: 'क्षारीय फॉस्फेटेस (ALP)' },
  'total protein': { ta: 'மொத்த புரதம் (Total Protein)', hi: 'कुल प्रोटीन (Total Protein)' },
  albumin: { ta: 'அல்புமின் (Albumin)', hi: 'एल्ब्यूमिन (Albumin)' },
};

const BIOMARKER_LOCALIZED_ROLES: Record<string, { ta: string; hi: string }> = {
  haemoglobin: {
    ta: 'ஹீமோகுளோபின் என்பது உங்கள் இரத்த சிவப்பணுக்களில் உள்ள ஒரு புரதமாகும், இது உடல் முழுவதும் புதிய ஆக்ஸிஜனைக் கொண்டு சென்று உங்களுக்கு ஆற்றலைத் தருகிறது.',
    hi: 'हीमोग्लोबिन आपके लाल रक्त कोशिकाओं में मौजूद प्रोटीन है जो पूरे शरीर में ताजा ऑक्सीजन पहुंचाकर ऊर्जा देता है।',
  },
  hemoglobin: {
    ta: 'ஹீமோகுளோபின் என்பது உங்கள் இரத்த சிவப்பணுக்களில் உள்ள ஒரு புரதமாகும், இது உடல் முழுவதும் புதிய ஆக்ஸிஜனைக் கொண்டு சென்று உங்களுக்கு ஆற்றலைத் தருகிறது.',
    hi: 'हीमोग्लोबिन आपके लाल रक्त कोशिकाओं में मौजूद प्रोटीन है जो पूरे शरीर में ताजा ऑक्सीजन पहुंचाकर ऊर्जा देता है।',
  },
  'total leucocyte count (wbc)': {
    ta: 'வெள்ளை இரத்த அணுக்கள் உங்கள் உடலின் நோய் எதிர்ப்பு பாதுகாப்பு படையாகும், இது தொற்று அல்லது வீக்கத்தை எதிர்த்துப் போராடுகிறது.',
    hi: 'श्वेत रक्त कोशिकाएं आपके शरीर की प्रतिरक्षा रक्षा प्रणाली हैं जो संक्रमण या सूजन से लड़ती हैं।',
  },
  'total leukocyte count': {
    ta: 'வெள்ளை இரத்த அணுக்கள் உங்கள் உடலின் நோய் எதிர்ப்பு பாதுகாப்பு படையாகும், இது தொற்று அல்லது வீக்கத்தை எதிர்த்துப் போராடுகிறது.',
    hi: 'श्वेत रक्त कोशिकाएं आपके शरीर की प्रतिरक्षा रक्षा प्रणाली हैं जो संक्रमण या सूजन से लड़ती हैं।',
  },
  wbc: {
    ta: 'வெள்ளை இரத்த அணுக்கள் உங்கள் உடலின் நோய் எதிர்ப்பு பாதுகாப்பு படையாகும், இது தொற்று அல்லது வீக்கத்தை எதிர்த்துப் போராடுகிறது.',
    hi: 'श्वेत रक्त कोशिकाएं आपके शरीर की प्रतिरक्षा रक्षा प्रणाली हैं जो संक्रमण या सूजन से लड़ती हैं।',
  },
  'platelet count': {
    ta: 'பிளேட்லெட்டுகள் என்பவை இரத்தம் உறைவதற்கும், காயம் ஏற்படும் போது இரத்தப்போக்கை நிறுத்துவதற்கும் உதவும் சிறிய செல் துண்டுகளாகும்.',
    hi: 'प्लेटलेट्स छोटे सेल टुकड़े होते हैं जो रक्त का थक्का बनाने और रक्तस्राव रोकने में मदद करते हैं।',
  },
  platelets: {
    ta: 'பிளேட்லெட்டுகள் என்பவை இரத்தம் உறைவதற்கும், காயம் ஏற்படும் போது இரத்தப்போக்கை நிறுத்துவதற்கும் உதவும் சிறிய செல் துண்டுகளாகும்.',
    hi: 'प्लेटलेट्स छोटे सेल टुकड़े होते हैं जो रक्त का थक्का बनाने और रक्तस्राव रोकने में मदद करते हैं।',
  },
  'fasting blood glucose': {
    ta: 'உண்ணாவிரத இரத்த சர்க்கரை என்பது 8-12 மணி நேரம் உணவு உண்ணாத நிலையில் உங்கள் இரத்தத்தில் உள்ள அடிப்படை குளுக்கோஸ் அளவை அளவிடுகிறது.',
    hi: 'फास्टिंग ब्लड शुगर 8-12 घंटे भूखे रहने के बाद आपके बेसलाइन ग्लूकोज स्तर को मापता है।',
  },
  'fasting blood sugar': {
    ta: 'உண்ணாவிரத இரத்த சர்க்கரை என்பது 8-12 மணி நேரம் உணவு உண்ணாத நிலையில் உங்கள் இரத்தத்தில் உள்ள அடிப்படை குளுக்கோஸ் அளவை அளவிடுகிறது.',
    hi: 'फास्टिंग ब्लड शुगर 8-12 घंटे भूखे रहने के बाद आपके बेसलाइन ग्लूकोज स्तर को मापता है।',
  },
  'glycated hemoglobin (hba1c)': {
    ta: 'HbA1c என்பது கடந்த 3 மாதங்களில் உங்கள் இரத்த சர்க்கரை அளவின் சராசரியைக் காட்டுகிறது, இது சர்க்கரை கட்டுப்பாடு எவ்வாறு உள்ளது என்பதை விளக்குகிறது.',
    hi: 'HbA1c पिछले 3 महीनों में आपके रक्त शर्करा के औसत स्तर को दर्शाता है।',
  },
  hba1c: {
    ta: 'HbA1c என்பது கடந்த 3 மாதங்களில் உங்கள் இரத்த சர்க்கரை அளவின் சராசரியைக் காட்டுகிறது, இது சர்க்கரை கட்டுப்பாடு எவ்வாறு உள்ளது என்பதை விளக்குகிறது.',
    hi: 'HbA1c पिछले 3 महीनों में आपके रक्त शर्करा के औसत स्तर को दर्शाता है।',
  },
  'serum creatinine': {
    ta: 'கிரியேட்டினின் என்பது தசைகளில் இருந்து உருவாகும் இயற்கையான கழிவுப் பொருளாகும், இதை ஆரோக்கியமான சிறுநீரகங்கள் சிறுநீரில் வடிகட்டுகின்றன.',
    hi: 'सीरम क्रिएटिनिन मांसपेशियों से निकलने वाला एक अपशिष्ट उत्पाद है जिसे स्वस्थ गुर्दे मूत्र में छानते हैं।',
  },
  creatinine: {
    ta: 'கிரியேட்டினின் என்பது தசைகளில் இருந்து உருவாகும் இயற்கையான கழிவுப் பொருளாகும், இதை ஆரோக்கியமான சிறுநீரகங்கள் சிறுநீரில் வடிகட்டுகின்றன.',
    hi: 'सीरम क्रिएटिनिन मांसपेशियों से निकलने वाला एक अपशिष्ट उत्पाद है जिसे स्वस्थ गुर्दे मूत्र में छानते हैं।',
  },
  'sgpt / alt': {
    ta: 'ALT என்பது கல்லீரல் ஆரோக்கியத்தைக் குறிக்கும் மிக முக்கியமான நொதியாகும். இது கல்லீரல் செல்களில் அழுத்தம் அல்லது வீக்கம் உள்ளதா என்பதைக் காட்டுகிறது.',
    hi: 'ALT सबसे विशिष्ट लिवर एंजाइम है। इसका बढ़ना दर्शाता है कि लिवर कोशिकाओं में तनाव या सूजन है।',
  },
  alt: {
    ta: 'ALT என்பது கல்லீரல் ஆரோக்கியத்தைக் குறிக்கும் மிக முக்கியமான நொதியாகும். இது கல்லீரல் செல்களில் அழுத்தம் அல்லது வீக்கம் உள்ளதா என்பதைக் காட்டுகிறது.',
    hi: 'ALT सबसे विशिष्ट लिवर एंजाइम है। इसका बढ़ना दर्शाता है कि लिवर कोशिकाओं में तनाव या सूजन है।',
  },
  'sgot / ast': {
    ta: 'AST என்பது கல்லீரல், இதயம் மற்றும் தசைகளில் காணப்படும் ஒரு நொதியாகும். இது திசு சேதம் அல்லது கல்லீரல் அழுத்தத்தை மதிப்பிட உதவுகிறது.',
    hi: 'AST लिवर, हृदय और मांसपेशियों में पाया जाने वाला एंजाइम है जो ऊतक तनाव को दर्शाता है।',
  },
  ast: {
    ta: 'AST என்பது கல்லீரல், இதயம் மற்றும் தசைகளில் காணப்படும் ஒரு நொதியாகும். இது திசு சேதம் அல்லது கல்லீரல் அழுத்தத்தை மதிப்பிட உதவுகிறது.',
    hi: 'AST लिवर, हृदय और मांसपेशियों में पाया जाने वाला एंजाइम है जो ऊतक तनाव को दर्शाता है।',
  },
  'total cholesterol': {
    ta: 'கொலஸ்ட்ரால் என்பது உயிரணு சவ்வுகள், வைட்டமின் டி மற்றும் ஹார்மோன்களை உருவாக்க உதவும் ஒரு மெழுகு போன்ற கொழுப்புப் பொருளாகும்.',
    hi: 'कोलेस्ट्रॉल एक मोमी वसायुक्त पदार्थ है जो कोशिका झिल्ली और हार्मोन बनाने में मदद करता है।',
  },
  cholesterol: {
    ta: 'கொலஸ்ட்ரால் என்பது உயிரணு சவ்வுகள், வைட்டமின் டி மற்றும் ஹார்மோன்களை உருவாக்க உதவும் ஒரு மெழுகு போன்ற கொழுப்புப் பொருளாகும்.',
    hi: 'कोलेस्ट्रॉल एक मोमी वसायुक्त पदार्थ है जो कोशिका झिल्ली और हार्मोन बनाने में मदद करता है।',
  },
  'ldl cholesterol': {
    ta: 'LDL "கெட்ட கொலஸ்ட்ரால்" என்று அழைக்கப்படுகிறது, ஏனெனில் அதிக அளவு தமனிகளில் படிவுகளை உருவாக்கி இதய நோய் அபாயத்தை அதிகரிக்கலாம்.',
    hi: 'LDL को "खराब कोलेस्ट्रॉल" कहा जाता है क्योंकि उच्च स्तर धमनियों में रुकावट पैदा कर सकता है।',
  },
  'hdl cholesterol': {
    ta: 'HDL "நல்ல கொலஸ்ட்ரால்" ஆகும், இது இரத்த ஓட்டத்தில் உள்ள அதிகப்படியான கொழுப்பை கல்லீரலுக்கு எடுத்துச் சென்று இதயத்தைப் பாதுகாக்கிறது.',
    hi: 'HDL "अच्छा कोलेस्ट्रॉल" है जो अतिरिक्त कोलेस्ट्रॉल को लिवर में वापस ले जाकर हृदय की रक्षा करता है।',
  },
  triglycerides: {
    ta: 'டிரைகிளிசரைடுகள் என்பவை இரத்தத்தில் உள்ள பொதுவான கொழுப்பு வகையாகும், அவை பயன்படுத்தப்படாத கலோரிகளை எதிர்கால ஆற்றலுக்காக சேமிக்கின்றன.',
    hi: 'ट्राइग्लिसराइड्स रक्त में मौजूद वसा का एक प्रकार हैं जो अप्रयुक्त कैलोरी को ऊर्जा के रूप में संग्रहीत करते हैं।',
  },
  'thyroid stimulating hormone (tsh)': {
    ta: 'TSH என்பது உங்கள் வளர்சிதை மாற்றம் மற்றும் ஆற்றல் சமநிலையைக் கட்டுப்படுத்தும் தைராய்டு சுரப்பியை ஒழுங்குபடுத்தும் ஹார்மோனாகும்.',
    hi: 'TSH थायरॉयड ग्रंथि को उत्तेजित करने वाला हार्मोन है जो मेटाबॉलिज्म और ऊर्जा को नियंत्रित करता है।',
  },
  tsh: {
    ta: 'TSH என்பது உங்கள் வளர்சிதை மாற்றம் மற்றும் ஆற்றல் சமநிலையைக் கட்டுப்படுத்தும் தைராய்டு சுரப்பியை ஒழுங்குபடுத்தும் ஹார்மோனாகும்.',
    hi: 'TSH थायरॉयड ग्रंथि को उत्तेजित करने वाला हार्मोन है जो मेटाबॉलिज्म और ऊर्जा को नियंत्रित करता है।',
  },
  'blood urea nitrogen (bun)': {
    ta: 'யூரியா நைட்ரஜன் என்பது புரத செரிமானத்தின் கழிவுப் பொருளாகும், இது சிறுநீரகங்கள் இரத்தத்தை எவ்வளவு திறம்பட வடிகட்டுகின்றன என்பதை அளவிடுகிறது.',
    hi: 'यूरिया नाइट्रोजन प्रोटीन पाचन का अपशिष्ट है जो गुर्दे की निस्पंदन क्षमता को मापता है।',
  },
  urea: {
    ta: 'யூரியா என்பது புரத முறிவின் கழிவுப் பொருளாகும், இது சிறுநீரக வடிகட்டுதல் செயல்பாட்டை பிரதிபலிக்கிறது.',
    hi: 'यूरिया प्रोटीन अपघटन का अपशिष्ट है जो गुर्दे की कार्यप्रणाली को दर्शाता है।',
  },
  'uric acid': {
    ta: 'யூரிக் அமிலம் என்பது பியூரின்கள் உடையும் போது உருவாகும் கழிவுப் பொருளாகும்; அதிக அளவு மூட்டு வலி அல்லது கீல்வாதத்தை ஏற்படுத்தலாம்.',
    hi: 'यूरिक एसिड प्यूरीन के टूटने से बनता है; उच्च स्तर जोड़ों में दर्द या गाउट पैदा कर सकता है।',
  },
  'rbc count': {
    ta: 'சிவப்பு இரத்த அணுக்கள் உங்கள் நுரையீரலில் இருந்து தசைகள் மற்றும் உறுப்புகளுக்கு ஆக்ஸிஜனை எடுத்துச் செல்லும் நுண்ணிய வாகனங்களாகும்.',
    hi: 'लाल रक्त कोशिकाएं फेफड़ों से मांसपेशियों और अंगों तक ऑक्सीजन ले जाने वाले वाहन हैं।',
  },
  'packed cell volume (pcv)': {
    ta: 'ஹெமாட்டோக்ரிட் என்பது திரவ பிளாஸ்மாவுடன் ஒப்பிடும்போது உங்கள் இரத்தத்தில் உள்ள சிவப்பு இரத்த அணுக்களின் சதவீதத்தைக் குறிக்கிறது.',
    hi: 'हेमाटोक्रिट तरल प्लाज्मा की तुलना में लाल रक्त कोशिकाओं के प्रतिशत को दर्शाता है।',
  },
  'mean corpuscular volume (mcv)': {
    ta: 'MCV உங்கள் இரத்த சிவப்பணுக்கள் சரியான அளவில் உள்ளதா அல்லது அசாதாரணமாக சிறியதாகவோ பெரியதாகவோ உள்ளதா என்பதைக் காட்டுகிறது.',
    hi: 'MCV दर्शाता है कि आपकी लाल रक्त कोशिकाएं सामान्य आकार की हैं, असामान्य रूप से छोटी हैं या बड़ी हैं।',
  },
  'mean corpuscular hemoglobin (mch)': {
    ta: 'MCH என்பது சராசரி சிவப்பு இரத்த செல்லுக்குள் எவ்வளவு ஹீமோகுளோபின் புரதம் அடைக்கப்பட்டுள்ளது என்பதை அளவிடுகிறது.',
    hi: 'MCH मापता है कि एक औसत लाल रक्त कोशिका में कितना हीमोग्लोबिन प्रोटीन भरा हुआ है।',
  },
  'erythrocyte sedimentation rate (esr)': {
    ta: 'ESR உடலில் ஏதேனும் வீக்கம், தொற்று அல்லது அழற்சி உள்ளதா என்பதைக் கண்டறியும் ஒரு பொதுவான சோதனையாகும்.',
    hi: 'ESR शरीर में सूजन या संक्रमण का पता लगाने वाला परीक्षण है।',
  },
  esr: {
    ta: 'ESR உடலில் ஏதேனும் வீக்கம், தொற்று அல்லது அழற்சி உள்ளதா என்பதைக் கண்டறியும் ஒரு பொதுவான சோதனையாகும்.',
    hi: 'ESR शरीर में सूजन या संक्रमण का पता लगाने वाला परीक्षण है।',
  },
  'vitamin d (25-oh)': {
    ta: 'வைட்டமின் டி எலும்பு வலிமை, கால்சியம் உறிஞ்சுதல் மற்றும் நோய் எதிர்ப்பு சக்தியை பராமரிக்க அவசியமானது.',
    hi: 'विटामिन डी हड्डियों की मजबूती, कैल्शियम अवशोषण और प्रतिरक्षा के लिए आवश्यक है।',
  },
  'vitamin b12': {
    ta: 'வைட்டமின் பி12 நரம்பு மண்டல ஆரோக்கியம், மூளை செயல்பாடு மற்றும் இரத்த அணுக்கள் உருவாக்கத்திற்கு இன்றியமையாதது.',
    hi: 'विटामिन बी12 तंत्रिका तंत्र के स्वास्थ्य और रक्त कोशिकाओं के निर्माण के लिए महत्वपूर्ण है।',
  },
  'serum calcium': {
    ta: 'கால்சியம் எலும்புகள், பற்கள், நரம்பு சமிக்ஞைகள் மற்றும் இதய துடிப்பை சீராக வைத்திருக்க உதவுகிறது.',
    hi: 'कैल्शियम हड्डियों, दांतों और हृदय गति को सुचारू रखने में मदद करता है।',
  },
  'bilirubin (total)': {
    ta: 'பிலிரூபின் என்பது பழைய இரத்த சிவப்பணுக்கள் உடையும் போது உருவாகும் மஞ்சள் நிற நிறமியாகும்; இது கல்லீரல் மற்றும் பித்தப்பை செயல்பாட்டை பிரதிபலிக்கிறது.',
    hi: 'बिलीरुबिन लाल रक्त कोशिकाओं के टूटने से बनता है और लिवर व पित्त स्वास्थ्य को दर्शाता है।',
  },
  'alkaline phosphatase (alp)': {
    ta: 'ALP என்பது கல்லீரல், பித்த நாளங்கள் மற்றும் எலும்புகளில் காணப்படும் ஒரு நொதியாகும்.',
    hi: 'ALP लिवर, पित्त नली और हड्डियों में पाया जाने वाला एंजाइम है।',
  },
  'total protein': {
    ta: 'மொத்த புரதம் என்பது இரத்தத்தில் உள்ள அல்புமின் மற்றும் குளோபுலின் புரதங்களின் ஒட்டுமொத்த அளவைக் குறிக்கிறது.',
    hi: 'कुल प्रोटीन रक्त में एल्ब्यूमिन और ग्लोब्युलिन के कुल स्तर को दर्शाता है।',
  },
  albumin: {
    ta: 'அல்புமின் என்பது கல்லீரலால் தயாரிக்கப்படும் முக்கிய புரதமாகும், இது இரத்தக் குழாய்களில் திரவத்தை தக்கவைத்து ஊட்டச்சத்துக்களை கடத்துகிறது.',
    hi: 'एल्ब्यूमिन लिवर द्वारा निर्मित प्रमुख प्रोटीन है जो तरल संतुलन बनाए रखता है।',
  },
};

function getLocalizedClinicalMeaning(biomarkerName: string, existingMeaning: string, lang: 'en' | 'ta' | 'hi'): string {
  if (lang === 'en') {
    const hasIndic = /[\u0B80-\u0BFF\u0900-\u097F]/.test(existingMeaning || '');
    if (!hasIndic && existingMeaning) return existingMeaning;
    return existingMeaning || 'Diagnostic laboratory biomarker evaluation.';
  }

  const isTamil = /[\u0B80-\u0BFF]/.test(existingMeaning || '');
  const isHindi = /[\u0900-\u097F]/.test(existingMeaning || '');
  if (lang === 'ta' && isTamil) return existingMeaning;
  if (lang === 'hi' && isHindi) return existingMeaning;

  const key = biomarkerName.toLowerCase().trim();
  for (const [k, v] of Object.entries(BIOMARKER_LOCALIZED_ROLES)) {
    if (k === key || key.includes(k) || k.includes(key)) {
      return v[lang];
    }
  }

  if (lang === 'ta') {
    return `${biomarkerName} என்பது உங்கள் உடல் நலம் மற்றும் உறுப்பு செயல்பாட்டை மதிப்பிடுவதற்கான ஒரு மருத்துவ பரிசோதனை அளவீடாகும்.`;
  }
  if (lang === 'hi') {
    return `${biomarkerName} आपके समग्र स्वास्थ्य और अंग प्रणाली के मूल्यांकन के लिए एक नैदानिक माप है।`;
  }
  return existingMeaning;
}

function getLocalizedBiomarkerName(name: string, lang: 'en' | 'ta' | 'hi'): string {
  if (lang === 'en') return name;
  const key = name.toLowerCase().trim();
  for (const [k, v] of Object.entries(BIOMARKER_LOCALIZED_NAMES)) {
    if (k === key || key.includes(k) || k.includes(key)) {
      return v[lang];
    }
  }
  return name;
}

export default function ReportDetailPage() {
  const params = useParams();
  const reportId = params.id as string;
  const router = useRouter();
  const { token } = useAuth();

  const [report, setReport] = useState<ReportDetail | null>(null);
  const [testResults, setTestResults] = useState<TestResultItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [ocrRunning, setOcrRunning] = useState<boolean>(false);
  const [extracting, setExtracting] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [ocrConfidence, setOcrConfidence] = useState<number>(96.5);
  const [activeTab, setActiveTab] = useState<'structured' | 'ai_explain' | 'chat' | 'ocr_text' | 'info'>('structured');
  const [filterVerification, setFilterVerification] = useState<'ALL' | 'VERIFIED' | 'NEEDS_REVIEW' | 'OUTLIERS'>('ALL');
  const [error, setError] = useState<string | null>(null);

  // Phase 8: AI Explanation State
  const [explanation, setExplanation] = useState<ReportExplanation | null>(null);
  const [explaining, setExplaining] = useState<boolean>(false);
  const [explainLanguage, setExplainLanguage] = useState<'en' | 'ta' | 'hi'>('en');
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [copiedQuestions, setCopiedQuestions] = useState<boolean>(false);

  // Phase 9: "Ask My Report" Conversational Q&A Chat State
  const [chatOpen, setChatOpen] = useState<boolean>(false);


  // Modal State for Manual Biomarker Editing
  const [editingItem, setEditingItem] = useState<TestResultItem | null>(null);
  const [editForm, setEditForm] = useState<{
    normalized_name: string;
    value_numeric: string;
    unit: string;
    reference_range_raw: string;
    flag: 'NORMAL' | 'LOW' | 'HIGH' | 'CRITICAL' | 'UNCERTAIN';
  }>({
    normalized_name: '',
    value_numeric: '',
    unit: '',
    reference_range_raw: '',
    flag: 'NORMAL',
  });
  const [savingEdit, setSavingEdit] = useState<boolean>(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const fetchReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      const activeToken = token || 'dev-user-token';
      const reportData = await api.getReport(activeToken, reportId);
      setReport(reportData);

      // Prescriptions are exclusively managed in the Prescriptions section
      if (reportData.report_type === 'prescription') {
        router.replace(`/dashboard/prescriptions?reportId=${reportId}`);
        return;
      }

      // Fetch structured test results if available
      try {
        const results = await api.getReportTestResults(activeToken, reportId);
        setTestResults(results);
      } catch {
        setTestResults([]);
      }

      // Fetch AI status
      try {
        const status = await api.getAIStatus(activeToken);
        setAiStatus(status);
      } catch {
        // AI status check non-blocking
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load report.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (reportId) {
      fetchReportData();
    }
  }, [reportId, token]);

  const handleRunOCR = async () => {
    setOcrRunning(true);
    try {
      const activeToken = token || 'dev-user-token';
      const res = await api.processReportOCR(activeToken, reportId);
      setOcrConfidence(res.data.average_confidence || 96.5);
      if (report) {
        setReport({
          ...report,
          raw_ocr_text: res.data.raw_ocr_text,
          ocr_status: 'completed',
        });
      }
      // Automatically extract structured results after OCR completes
      handleExtractStructured(activeToken);
    } catch (err: any) {
      alert(err.message || 'Failed to run OCR.');
    } finally {
      setOcrRunning(false);
    }
  };

  const handleExtractStructured = async (customToken?: string) => {
    setExtracting(true);
    setActionSuccessMsg(null);
    try {
      const activeToken = customToken || token || 'dev-user-token';
      const res = await api.extractStructuredTestResults(activeToken, reportId);
      setTestResults(res.data.results);
      setActionSuccessMsg(`Successfully parsed & verified ${res.data.total_extracted} clinical biomarkers!`);
      setTimeout(() => setActionSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to extract structured clinical values.');
    } finally {
      setExtracting(false);
    }
  };

  const handleGenerateExplanation = async (lang: 'en' | 'ta' | 'hi' = explainLanguage) => {
    setExplaining(true);
    try {
      const activeToken = token || 'dev-user-token';
      const result = await api.generateReportExplanation(activeToken, reportId, lang);
      setExplanation(result);
      setActionSuccessMsg('Grounded AI report explanation generated successfully.');
      setTimeout(() => setActionSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(err.message || 'Failed to generate explanation.');
    } finally {
      setExplaining(false);
    }
  };

  const handleQuickApprove = async (item: TestResultItem) => {
    try {
      const activeToken = token || 'dev-user-token';
      await api.updateTestResult(activeToken, item.id, {
        verification_status: 'user_corrected',
      });
      setTestResults((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, verification_status: 'user_corrected' } : it))
      );
      setActionSuccessMsg(`Approved and verified "${item.normalized_name}".`);
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to approve item.');
    }
  };

  const openEditModal = (item: TestResultItem) => {
    setEditingItem(item);
    setEditForm({
      normalized_name: item.normalized_name,
      value_numeric: item.value_numeric !== undefined ? String(item.value_numeric) : '',
      unit: item.unit || '',
      reference_range_raw: item.reference_range_raw || '',
      flag: item.flag,
    });
  };

  const handleSaveEdit = async () => {
    if (!editingItem) return;
    setSavingEdit(true);
    try {
      const activeToken = token || 'dev-user-token';
      const numVal = editForm.value_numeric !== '' ? parseFloat(editForm.value_numeric) : undefined;
      await api.updateTestResult(activeToken, editingItem.id, {
        normalized_name: editForm.normalized_name,
        value_numeric: numVal,
        unit: editForm.unit,
        reference_range_raw: editForm.reference_range_raw,
        flag: editForm.flag,
        verification_status: 'user_corrected',
      });

      // Update state locally
      setTestResults((prev) =>
        prev.map((it) =>
          it.id === editingItem.id
            ? {
                ...it,
                normalized_name: editForm.normalized_name,
                value_numeric: numVal,
                unit: editForm.unit,
                reference_range_raw: editForm.reference_range_raw,
                flag: editForm.flag,
                verification_status: 'user_corrected',
                is_outlier: false,
              }
            : it
        )
      );
      setEditingItem(null);
      setActionSuccessMsg('Biomarker measurement corrected and verified successfully.');
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to save correction.');
    } finally {
      setSavingEdit(false);
    }
  };

  const copyToClipboard = () => {
    if (report?.raw_ocr_text) {
      navigator.clipboard.writeText(report.raw_ocr_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const copyDoctorQuestions = () => {
    if (explanation?.doctor_questions) {
      navigator.clipboard.writeText(explanation.doctor_questions.join('\n'));
      setCopiedQuestions(true);
      setTimeout(() => setCopiedQuestions(false), 2000);
    }
  };

  // Biomarker Summary Metrics
  const normalCount = testResults.filter((r) => r.flag === 'NORMAL').length;
  const outOfRangeCount = testResults.filter((r) => r.flag === 'HIGH' || r.flag === 'LOW').length;
  const criticalCount = testResults.filter((r) => r.flag === 'CRITICAL').length;
  const verifiedCount = testResults.filter((r) => r.verification_status === 'verified' || r.verification_status === 'user_corrected').length;
  const needsReviewCount = testResults.filter((r) => r.verification_status === 'needs_review').length;
  const outlierCount = testResults.filter((r) => r.is_outlier).length;

  const avgCompositeScore =
    testResults.length > 0
      ? (testResults.reduce((acc, curr) => acc + (curr.composite_confidence || curr.ocr_confidence || 90), 0) / testResults.length).toFixed(1)
      : '95.0';

  // Filtered test items
  const filteredResults = testResults.filter((item) => {
    if (filterVerification === 'VERIFIED') {
      return item.verification_status === 'verified' || item.verification_status === 'user_corrected';
    }
    if (filterVerification === 'NEEDS_REVIEW') {
      return item.verification_status === 'needs_review';
    }
    if (filterVerification === 'OUTLIERS') {
      return item.is_outlier;
    }
    return true;
  });

  const getFlagBadge = (flag: string, lang: 'en' | 'ta' | 'hi' = 'en') => {
    let label = 'Normal';
    if (flag === 'HIGH') label = lang === 'ta' ? 'அதிகம் (High)' : lang === 'hi' ? 'उच्च (High)' : 'High';
    else if (flag === 'LOW') label = lang === 'ta' ? 'குறைவு (Low)' : lang === 'hi' ? 'कम (Low)' : 'Low';
    else if (flag === 'CRITICAL') label = lang === 'ta' ? 'ஆபத்தானது (Critical)' : lang === 'hi' ? 'गंभीर (Critical)' : 'Critical';
    else if (flag === 'NORMAL') label = lang === 'ta' ? 'இயல்பு (Normal)' : lang === 'hi' ? 'सामान्य (Normal)' : 'Normal';
    else label = lang === 'ta' ? 'தெளிவற்றது (Uncertain)' : lang === 'hi' ? 'अनिश्चित (Uncertain)' : 'Uncertain';

    switch (flag) {
      case 'NORMAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3" /> {label}
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <ArrowUpRight className="h-3 w-3" /> {label}
          </span>
        );
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <ArrowDownRight className="h-3 w-3" /> {label}
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 animate-pulse">
            <AlertTriangle className="h-3 w-3" /> {label}
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <HelpCircle className="h-3 w-3" /> {label}
          </span>
        );
    }
  };

  const getVerificationBadge = (item: TestResultItem) => {
    if (item.is_outlier) {
      return (
        <span
          title={item.verification_reason || 'Outlier detected'}
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40 animate-pulse"
        >
          <ShieldAlert className="h-3 w-3" /> Outlier Alert
        </span>
      );
    }

    if (item.verification_status === 'user_corrected') {
      return (
        <span
          title="Manually reviewed and approved"
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-cyan-500/15 text-cyan-300 border border-cyan-500/30"
        >
          <Check className="h-3 w-3" /> User Verified
        </span>
      );
    }

    if (item.verification_status === 'verified') {
      return (
        <span
          title={item.verification_reason || 'Verified multi-factor confidence'}
          className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
        >
          <ShieldCheck className="h-3 w-3" /> Verified ({item.composite_confidence?.toFixed(0) || '95'}%)
        </span>
      );
    }

    return (
      <span
        title={item.verification_reason || 'Review recommended'}
        className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30"
      >
        <AlertTriangle className="h-3 w-3" /> Needs Review
      </span>
    );
  };

  if (loading) {
    return (
      <div className="glass-card p-12 rounded-3xl text-center space-y-3 max-w-4xl mx-auto">
        <RefreshCw className="h-8 w-8 text-cyan-400 animate-spin mx-auto" />
        <p className="text-xs text-slate-400">Retrieving report & clinical findings...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="glass-card p-8 rounded-3xl text-center space-y-4 max-w-4xl mx-auto border-rose-500/30">
        <h2 className="text-base font-bold text-white">Report Not Found</h2>
        <p className="text-xs text-rose-300">{error || 'Requested report could not be located.'}</p>
        <Link
          href="/dashboard/reports"
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to My Reports</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Back Button & Knowledge Hub Link */}
      <div className="flex items-center justify-between">
        <Link
          href="/dashboard/reports"
          className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Back to All Reports</span>
        </Link>

        <div className="flex items-center gap-2">
          {aiStatus && (
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[11px] font-mono bg-slate-900 border border-white/10 text-slate-300">
              <BrainCircuit className="h-3.5 w-3.5 text-teal-400" />
              <span>AI Model: {aiStatus.available ? aiStatus.model : 'Grounded Fallback Engine'}</span>
            </span>
          )}
        </div>
      </div>

      {/* Success Notification */}
      {actionSuccessMsg && (
        <div className="p-4 rounded-2xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-between text-teal-300 text-xs font-semibold animate-fade-in">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 text-teal-400" />
            <span>{actionSuccessMsg}</span>
          </div>
          <button onClick={() => setActionSuccessMsg(null)} className="text-slate-400 hover:text-white">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* If prescription: do NOT show structured findings, grounded AI, ask my report, raw ocr text, or metadata */}
      {report.report_type === 'prescription' ? (
        <div className="glass-card p-10 rounded-3xl border border-purple-500/30 bg-purple-950/20 text-center space-y-5 max-w-2xl mx-auto my-8">
          <div className="h-16 w-16 rounded-3xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center mx-auto text-purple-400">
            <Pill className="h-8 w-8" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-white">{report.title}</h2>
            <p className="text-xs text-purple-300 font-medium">Doctor Prescription Document</p>
            <p className="text-xs text-slate-300 max-w-md mx-auto leading-relaxed">
              This document is a doctor&apos;s prescription. Structured findings, Grounded AI, Ask My Report Q&amp;A, raw OCR text, and metadata analysis are diagnostic lab features and are not shown for prescriptions. Prescribed medications and daily intake schedules are managed in the Prescriptions section.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <Link
              href={`/dashboard/prescriptions?reportId=${report.id}`}
              className="inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition hover:scale-105"
            >
              <Pill className="h-4 w-4" />
              <span>View Prescription &amp; Medicines</span>
            </Link>
            <Link
              href="/dashboard/reports"
              className="px-5 py-2.5 rounded-xl bg-slate-900 border border-white/10 text-white font-semibold text-xs hover:border-cyan-400 transition"
            >
              Back to Lab Reports
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Report Header Card */}
      <div className="glass-card p-6 sm:p-8 rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-slate-900/90 via-cyan-950/20 to-slate-900/90 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-xs font-semibold uppercase">
              {report.report_type.replace('_', ' ')}
            </span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold uppercase border ${
                report.ocr_status === 'completed'
                  ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                  : 'bg-teal-500/20 border-teal-500/40 text-teal-300'
              }`}
            >
              OCR: {report.ocr_status}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">{report.title}</h1>
          <p className="text-xs text-slate-400 flex items-center space-x-2">
            <Clock className="h-3.5 w-3.5 text-slate-500" />
            <span>Test Date: {report.report_date || 'Not specified'}</span>
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {report.signed_url && (
            <a
              href={report.signed_url}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2.5 rounded-xl bg-slate-900 border border-white/10 hover:border-cyan-400 text-slate-200 text-xs font-semibold flex items-center space-x-2 transition"
            >
              <ExternalLink className="h-4 w-4 text-cyan-400" />
              <span>Original File</span>
            </a>
          )}

          <button
            onClick={handleRunOCR}
            disabled={ocrRunning}
            className="px-4 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/40 hover:bg-slate-800 text-cyan-300 font-bold text-xs flex items-center space-x-2 transition disabled:opacity-50"
          >
            <ScanLine className={`h-4 w-4 ${ocrRunning ? 'animate-spin' : ''}`} />
            <span>{ocrRunning ? 'Running OCR...' : 'Re-run OCR'}</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('ai_explain');
              handleGenerateExplanation();
            }}
            disabled={explaining}
            className="px-4 py-2.5 rounded-xl bg-slate-900 border border-cyan-500/40 hover:bg-slate-800 text-cyan-300 font-bold text-xs flex items-center space-x-2 transition disabled:opacity-50"
          >
            <BrainCircuit className={`h-4 w-4 ${explaining ? 'animate-spin' : ''}`} />
            <span>{explaining ? 'Generating...' : 'Explain with AI'}</span>
          </button>

          <button
            onClick={() => setChatOpen(true)}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-teal-500/20 flex items-center space-x-2 transition"
          >
            <MessageSquare className="h-4 w-4" />
            <span>Ask My Report</span>
          </button>

          <Link
            href={`/dashboard/doctor-summary?reportId=${report.id}`}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-400 hover:to-teal-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center space-x-2 transition"
          >
            <Stethoscope className="h-4 w-4" />
            <span>Doctor Brief</span>
            <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-950/20 text-slate-950">
              Phase 12
            </span>
          </Link>
        </div>
      </div>

      {/* Confidence & Sanity Verification Summary Card */}
      {testResults.length > 0 && (
        <div className="glass-card p-5 rounded-3xl border border-teal-500/30 bg-gradient-to-r from-teal-950/30 via-slate-900/60 to-cyan-950/30 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-3 rounded-2xl bg-teal-500/20 text-teal-300">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>Confidence Verification & Medical Knowledge Grounding</span>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-teal-500/20 text-teal-300 border border-teal-500/30">
                    Phase 8 Ready
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Grounded with 100+ clinical biomarker taxonomy cards, 384-d vector embeddings, and local AI reasoning.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-2 bg-slate-950/60 p-2.5 rounded-2xl border border-white/5">
              <div className="text-right pr-2 border-r border-white/10">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Composite Score</span>
                <span className="text-lg font-extrabold text-teal-400 font-mono">{avgCompositeScore}%</span>
              </div>
              <div className="pl-2">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Verified Tests</span>
                <span className="text-lg font-extrabold text-emerald-400 font-mono">
                  {verifiedCount}/{testResults.length}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Filter Controls */}
          <div className="flex items-center justify-between pt-2 border-t border-white/5 flex-wrap gap-2 text-xs">
            <div className="flex items-center space-x-1.5">
              <SlidersHorizontal className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-slate-400 font-medium">Filter view:</span>
              <button
                onClick={() => setFilterVerification('ALL')}
                className={`px-3 py-1 rounded-lg transition font-medium ${
                  filterVerification === 'ALL'
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                All ({testResults.length})
              </button>
              <button
                onClick={() => setFilterVerification('VERIFIED')}
                className={`px-3 py-1 rounded-lg transition font-medium ${
                  filterVerification === 'VERIFIED'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Verified ({verifiedCount})
              </button>
              {needsReviewCount > 0 && (
                <button
                  onClick={() => setFilterVerification('NEEDS_REVIEW')}
                  className={`px-3 py-1 rounded-lg transition font-medium ${
                    filterVerification === 'NEEDS_REVIEW'
                      ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                      : 'text-amber-400/80 hover:text-amber-300'
                  }`}
                >
                  Needs Review ({needsReviewCount})
                </button>
              )}
              {outlierCount > 0 && (
                <button
                  onClick={() => setFilterVerification('OUTLIERS')}
                  className={`px-3 py-1 rounded-lg transition font-medium ${
                    filterVerification === 'OUTLIERS'
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                      : 'text-rose-400/80 hover:text-rose-300'
                  }`}
                >
                  Outliers ({outlierCount})
                </button>
              )}
            </div>

            <div className="text-[11px] text-slate-400 flex items-center gap-2">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-400"></span> Normal: {normalCount}
              <span className="inline-block w-2 h-2 rounded-full bg-amber-400 ml-2"></span> Out of Range: {outOfRangeCount}
              {criticalCount > 0 && (
                <span className="inline-block w-2 h-2 rounded-full bg-rose-400 ml-2"> Critical: {criticalCount}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Tabs */}
      <div className="glass-card rounded-3xl overflow-hidden border border-white/10">
        {/* Tab Navigation */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-slate-900/60 flex-wrap gap-3">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setActiveTab('structured')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition ${
                activeTab === 'structured'
                  ? 'bg-teal-500/20 text-cyan-300 border border-teal-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Activity className="h-4 w-4" />
              <span>Structured Findings ({testResults.length})</span>
            </button>
            <button
              onClick={() => {
                setActiveTab('ai_explain');
                if (!explanation && !explaining) {
                  handleGenerateExplanation();
                }
              }}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition ${
                activeTab === 'ai_explain'
                  ? 'bg-gradient-to-r from-teal-500/20 to-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <BrainCircuit className="h-4 w-4 text-cyan-400" />
              <span>Grounded AI Explanation</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-teal-500/20 text-teal-300">
                Phase 8
              </span>
            </button>
            <button
              onClick={() => setChatOpen(true)}
              className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition bg-gradient-to-r from-emerald-500/20 to-teal-500/20 hover:from-emerald-500/30 hover:to-teal-500/30 text-emerald-300 border border-emerald-500/40"
            >
              <MessageSquare className="h-4 w-4 text-emerald-400" />
              <span>Ask My Report (Q&A)</span>
              <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/30 text-emerald-200">
                Phase 9
              </span>
            </button>
            <button
              onClick={() => setActiveTab('ocr_text')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition ${
                activeTab === 'ocr_text'
                  ? 'bg-teal-500/20 text-cyan-300 border border-teal-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <FileCode className="h-4 w-4" />
              <span>Raw OCR Text</span>
            </button>
            <button
              onClick={() => setActiveTab('info')}
              className={`px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition ${
                activeTab === 'info'
                  ? 'bg-teal-500/20 text-cyan-300 border border-teal-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Layers className="h-4 w-4" />
              <span>Metadata</span>
            </button>
          </div>

          {activeTab === 'ocr_text' && report.raw_ocr_text && (
            <button
              onClick={copyToClipboard}
              className="px-3 py-1.5 rounded-lg bg-slate-900 border border-white/10 text-slate-300 hover:text-white text-xs flex items-center space-x-1.5 transition"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-teal-400" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? 'Copied!' : 'Copy Text'}</span>
            </button>
          )}
        </div>

        {/* Tab 1: Structured Clinical Biomarkers Table */}
        {activeTab === 'structured' && (
          <div className="p-6 space-y-4">
            {filteredResults.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/10 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      <th className="pb-3 pl-2">Biomarker (Normalized)</th>
                      <th className="pb-3">Measured Value</th>
                      <th className="pb-3">Reference Range</th>
                      <th className="pb-3">Clinical Flag</th>
                      <th className="pb-3">Verification & Quality</th>
                      <th className="pb-3 text-right pr-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-xs">
                    {filteredResults.map((item) => (
                      <tr key={item.id} className="hover:bg-white/[0.02] transition">
                        <td className="py-4 pl-2 font-medium text-white max-w-[200px]">
                          <div>
                            <span className="font-bold text-slate-100 text-sm">{item.normalized_name}</span>
                            {item.raw_test_name !== item.normalized_name && (
                              <p className="text-[11px] text-slate-500 font-mono truncate" title={item.raw_test_name}>
                                OCR: {item.raw_test_name}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="py-4">
                          <span className="font-extrabold text-sm text-cyan-300 font-mono">
                            {item.value_numeric !== undefined ? item.value_numeric : item.value_text || '—'}
                          </span>{' '}
                          <span className="text-slate-400 text-xs">{item.unit || ''}</span>
                        </td>
                        <td className="py-4 text-slate-300 font-mono text-xs">
                          {item.reference_range_raw ||
                            (item.ref_min !== undefined && item.ref_max !== undefined
                              ? `${item.ref_min} - ${item.ref_max}`
                              : '—')}
                        </td>
                        <td className="py-4">{getFlagBadge(item.flag)}</td>
                        <td className="py-4">
                          <div className="space-y-1">
                            <div>{getVerificationBadge(item)}</div>
                            {item.verification_reason && (
                              <p className="text-[10px] text-slate-400 max-w-[220px] truncate" title={item.verification_reason}>
                                {item.verification_reason}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="py-4 text-right pr-2">
                          <div className="flex items-center justify-end space-x-1.5">
                            {item.verification_status === 'needs_review' && (
                              <button
                                onClick={() => handleQuickApprove(item)}
                                className="p-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 transition"
                                title="Quick Approve"
                              >
                                <Check className="h-3.5 w-3.5" />
                              </button>
                            )}
                            <button
                              onClick={() => openEditModal(item)}
                              className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-cyan-300 transition"
                              title="Edit / Correct Value"
                            >
                              <Edit3 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-12 text-center space-y-3">
                <Activity className="h-10 w-10 text-cyan-400 mx-auto animate-pulse" />
                <p className="text-sm font-semibold text-white">
                  {filterVerification !== 'ALL'
                    ? 'No biomarkers matching current filter.'
                    : 'No structured test results extracted yet.'}
                </p>
                {filterVerification !== 'ALL' ? (
                  <button
                    onClick={() => setFilterVerification('ALL')}
                    className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs text-white"
                  >
                    View All Biomarkers
                  </button>
                ) : (
                  <button
                    onClick={() => handleExtractStructured()}
                    disabled={extracting}
                    className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20"
                  >
                    {extracting ? 'Parsing & Verifying...' : 'Extract & Verify Clinical Findings'}
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Grounded AI Report Explanation (Phase 8) */}
        {activeTab === 'ai_explain' && (
          <div className="p-6 sm:p-8 space-y-6">
            {/* Top Language & Generation Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/80 border border-cyan-500/20">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-cyan-500/20 text-cyan-300">
                  <BrainCircuit className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white">
                    {explainLanguage === 'ta'
                      ? 'ஆதாரப்பூர்வ AI மருத்துவ விளக்கம்'
                      : explainLanguage === 'hi'
                      ? 'प्रामाणिक AI मेडिकल व्याख्या'
                      : 'Grounded Local AI Explanation'}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {explainLanguage === 'ta'
                      ? 'மருத்துவத் தரவுகளின் அடிப்படையில் பிழையற்ற முறையில் எளிய தமிழில் விளக்கப்படுகிறது.'
                      : explainLanguage === 'hi'
                      ? 'सत्यापित पैरामीटर और क्लिनिकल संदर्भ पर आधारित स्पष्ट व्याख्या।'
                      : 'Cites all verified parameters with strict anti-hallucination bounds.'}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {/* Language Switcher */}
                <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-xl border border-white/10 text-xs">
                  <button
                    onClick={() => {
                      setExplainLanguage('en');
                      handleGenerateExplanation('en');
                    }}
                    className={`px-2.5 py-1 rounded-lg font-medium transition ${
                      explainLanguage === 'en' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    English
                  </button>
                  <button
                    onClick={() => {
                      setExplainLanguage('ta');
                      handleGenerateExplanation('ta');
                    }}
                    className={`px-2.5 py-1 rounded-lg font-medium transition ${
                      explainLanguage === 'ta' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    தமிழ்
                  </button>
                  <button
                    onClick={() => {
                      setExplainLanguage('hi');
                      handleGenerateExplanation('hi');
                    }}
                    className={`px-2.5 py-1 rounded-lg font-medium transition ${
                      explainLanguage === 'hi' ? 'bg-cyan-500 text-slate-950 font-bold' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    हिंदी
                  </button>
                </div>

                <button
                  onClick={() => handleGenerateExplanation()}
                  disabled={explaining}
                  className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-md shadow-cyan-500/20 disabled:opacity-50"
                >
                  <RefreshCw className={`h-3.5 w-3.5 ${explaining ? 'animate-spin' : ''}`} />
                  <span>
                    {explaining
                      ? explainLanguage === 'ta'
                        ? 'உருவாக்குகிறது...'
                        : explainLanguage === 'hi'
                        ? 'तैयार हो रहा है...'
                        : 'Regenerating...'
                      : explainLanguage === 'ta'
                      ? 'மீண்டும் உருவாக்கு'
                      : explainLanguage === 'hi'
                      ? 'पुनः उत्पन्न करें'
                      : 'Regenerate'}
                  </span>
                </button>
              </div>
            </div>

            {/* Explanation Content */}
            {explaining ? (
              <div className="py-16 text-center space-y-4">
                <BrainCircuit className="h-10 w-10 text-cyan-400 animate-spin mx-auto" />
                <p className="text-sm font-bold text-white">
                  {explainLanguage === 'ta'
                    ? 'மருத்துவ ரீதியிலான எளிய விளக்கத்தை உருவாக்குகிறது...'
                    : explainLanguage === 'hi'
                    ? 'सरल भाषा में व्याख्या तैयार की जा रही है...'
                    : 'Generating Grounded Plain-Language Explanation...'}
                </p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  {explainLanguage === 'ta'
                    ? `உங்கள் அறிக்கையிலுள்ள ${testResults.length} ஆய்வக அளவீடுகள் மருத்துவத் தரவுகளுடன் ஒப்பிடப்படுகின்றன.`
                    : explainLanguage === 'hi'
                    ? `आपके परीक्षण के ${testResults.length} बायोमार्कर परिणामों का मिलान किया जा रहा है।`
                    : `Cross-referencing ${testResults.length} extracted biomarker values against our clinical knowledge base.`}
                </p>
              </div>
            ) : explanation ? (
              <div className="space-y-6">
                {/* Executive Summary Card */}
                <div className="p-6 rounded-3xl bg-gradient-to-r from-teal-950/40 via-slate-900/80 to-cyan-950/40 border border-teal-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-teal-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Sparkles className="h-4 w-4" />
                      {explainLanguage === 'ta'
                        ? 'சுருக்கமான கண்ணோட்டம் (Executive Summary)'
                        : explainLanguage === 'hi'
                        ? 'संक्षिप्त सारांश (Executive Summary)'
                        : 'Executive Summary'}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400">
                      Model: {explanation.model_used}
                    </span>
                  </div>
                  <p className="text-sm text-slate-100 leading-relaxed font-medium">
                    {explanation.executive_summary}
                  </p>
                </div>

                {/* Normal vs Out-of-Range Sections */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
                  {/* Normal Findings */}
                  <div className="p-5 rounded-3xl bg-emerald-950/20 border border-emerald-500/20 space-y-2">
                    <span className="text-xs font-bold text-emerald-400 uppercase flex items-center gap-1.5">
                      <CheckCircle className="h-4 w-4" />
                      {explainLanguage === 'ta'
                        ? 'இயல்பான ஆய்வக முடிவுகள் (Normal Findings)'
                        : explainLanguage === 'hi'
                        ? 'सामान्य प्रयोगशाला परिणाम (Normal Findings)'
                        : 'Normal Laboratory Findings'}
                    </span>
                    <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {explanation.normal_findings_summary}
                    </p>
                  </div>

                  {/* Out of Range Highlights */}
                  <div className="p-5 rounded-3xl bg-amber-950/20 border border-amber-500/20 space-y-2">
                    <span className="text-xs font-bold text-amber-400 uppercase flex items-center gap-1.5">
                      <AlertTriangle className="h-4 w-4" />
                      {explainLanguage === 'ta'
                        ? 'கவனம் தேவைப்படும் அளவீடுகள் (Attention Needed)'
                        : explainLanguage === 'hi'
                        ? 'ध्यान देने योग्य परिणाम (Attention Needed)'
                        : 'Parameter Highlights & Attention'}
                    </span>
                    <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                      {explanation.abnormal_findings_summary}
                    </p>
                  </div>
                </div>

                {/* Citations "Show Your Work" Table */}
                {explanation.citations && explanation.citations.length > 0 && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <HeartPulse className="h-4 w-4 text-cyan-400" />
                        {explainLanguage === 'ta'
                          ? 'ஆதாரக் குறிப்புகள் மற்றும் எளிய விளக்கங்கள் ("Show Your Work")'
                          : explainLanguage === 'hi'
                          ? 'प्रामाणिक संदर्भ और सरल व्याख्या ("Show Your Work")'
                          : 'Grounded Parameter Citations ("Show Your Work")'}
                      </h4>
                      <span className="text-[11px] text-slate-400">
                        {explainLanguage === 'ta'
                          ? `${explanation.citations.length} மேற்கோள் அளவுகள்`
                          : explainLanguage === 'hi'
                          ? `${explanation.citations.length} संदर्भित मान`
                          : `${explanation.citations.length} cited values`}
                      </span>
                    </div>

                    <div className="overflow-x-auto rounded-2xl border border-white/5 bg-slate-950/50">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-white/10 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                            <th className="p-3 pl-4">
                              {explainLanguage === 'ta'
                                ? 'உயிரியல் குறியீடு (Biomarker)'
                                : explainLanguage === 'hi'
                                ? 'बायोमार्कर (Biomarker)'
                                : 'Biomarker'}
                            </th>
                            <th className="p-3">
                              {explainLanguage === 'ta'
                                ? 'அளவிடப்பட்ட மதிப்பு (Value)'
                                : explainLanguage === 'hi'
                                ? 'मापा गया मान (Value)'
                                : 'Measured Value'}
                            </th>
                            <th className="p-3">
                              {explainLanguage === 'ta'
                                ? 'குறிப்பு வரம்பு (Reference Interval)'
                                : explainLanguage === 'hi'
                                ? 'संदर्भ सीमा (Reference Interval)'
                                : 'Reference Interval'}
                            </th>
                            <th className="p-3">
                              {explainLanguage === 'ta'
                                ? 'நிலை (Status)'
                                : explainLanguage === 'hi'
                                ? 'स्थिति (Status)'
                                : 'Status'}
                            </th>
                            <th className="p-3 pr-4">
                              {explainLanguage === 'ta'
                                ? 'எளிய மருத்துவ விளக்கம் (Plain-Language Role)'
                                : explainLanguage === 'hi'
                                ? 'सरल भाषा में भूमिका (Plain-Language Role)'
                                : 'Plain-Language Role'}
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                          {explanation.citations.map((c, idx) => {
                            const localizedRole = getLocalizedClinicalMeaning(c.biomarker_name, c.clinical_meaning, explainLanguage);
                            const localizedName = getLocalizedBiomarkerName(c.biomarker_name, explainLanguage);
                            return (
                              <tr key={idx} className="hover:bg-white/[0.02] transition">
                                <td className="p-3 pl-4">
                                  <div className="font-bold text-white leading-snug">
                                    {localizedName}
                                  </div>
                                  {explainLanguage !== 'en' && localizedName !== c.biomarker_name && (
                                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                                      {c.biomarker_name}
                                    </div>
                                  )}
                                </td>
                                <td className="p-3 font-mono text-cyan-300 font-extrabold whitespace-nowrap">
                                  {c.measured_value} {c.unit || ''}
                                </td>
                                <td className="p-3 font-mono text-slate-400 whitespace-nowrap">
                                  {c.reference_interval || 'N/A'}
                                </td>
                                <td className="p-3 whitespace-nowrap">
                                  {getFlagBadge(c.flag, explainLanguage)}
                                </td>
                                <td className="p-3 pr-4 text-slate-200 text-[11px] leading-relaxed max-w-sm">
                                  {localizedRole}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Questions for Doctor */}
                {explanation.doctor_questions && explanation.doctor_questions.length > 0 && (
                  <div className="p-5 rounded-3xl bg-slate-900/90 border border-white/10 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <Stethoscope className="h-4 w-4 text-cyan-400" />
                        {explainLanguage === 'ta'
                          ? 'மருத்துவரிடம் கேட்க வேண்டிய கேள்விகள் (Questions for Doctor)'
                          : explainLanguage === 'hi'
                          ? 'डॉक्टर से पूछने योग्य प्रश्न (Questions for Doctor)'
                          : 'Intelligent Questions for Your Doctor'}
                      </span>
                      <button
                        onClick={copyDoctorQuestions}
                        className="px-3 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-xs flex items-center space-x-1.5 transition"
                      >
                        {copiedQuestions ? <Check className="h-3 w-3 text-teal-400" /> : <Copy className="h-3 w-3" />}
                        <span>
                          {copiedQuestions
                            ? explainLanguage === 'ta'
                              ? 'நகலெடுக்கப்பட்டது!'
                              : explainLanguage === 'hi'
                              ? 'कॉपी हो गया!'
                              : 'Copied!'
                            : explainLanguage === 'ta'
                            ? 'நகலெடு (Copy)'
                            : explainLanguage === 'hi'
                            ? 'कॉपी करें (Copy)'
                            : 'Copy Checklist'}
                        </span>
                      </button>
                    </div>

                    <ul className="space-y-2 text-xs">
                      {explanation.doctor_questions.map((q, idx) => (
                        <li key={idx} className="p-3 rounded-xl bg-slate-950/60 border border-white/5 flex items-start space-x-2.5 text-slate-200">
                          <span className="h-5 w-5 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span className="leading-relaxed">{q}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Disclaimer Banner */}
                <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-200/90 flex items-start space-x-2">
                  <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                  <p className="leading-relaxed">
                    <strong className="text-amber-300 font-semibold">
                      {explainLanguage === 'ta'
                        ? 'கல்வி விழிப்புணர்வு மறுப்பு (Disclaimer): '
                        : explainLanguage === 'hi'
                        ? 'शैक्षिक उपकरण अस्वीकरण (Disclaimer): '
                        : 'Educational Tool Disclaimer: '}
                    </strong>
                    {explanation.disclaimer}
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center space-y-3">
                <BrainCircuit className="h-10 w-10 text-cyan-400 mx-auto animate-pulse" />
                <h3 className="text-sm font-bold text-white">
                  {explainLanguage === 'ta'
                    ? 'AI எளிய மருத்துவ விளக்கத்தை உருவாக்குங்கள்'
                    : explainLanguage === 'hi'
                    ? 'सरल भाषा में AI रिपोर्ट व्याख्या बनाएं'
                    : 'Generate Plain-Language AI Explanation'}
                </h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  {explainLanguage === 'ta'
                    ? 'சிக்கலான ஆய்வக முடிவுகளை உங்கள் மொழியில் எளிதில் புரிந்துகொள்ளக்கூடிய விளக்கங்களாக மாற்றுகிறது.'
                    : explainLanguage === 'hi'
                    ? 'जटिल डायग्नोस्टिक मानों को आसानी से समझने योग्य सारांश में बदलें।'
                    : 'Translate complex diagnostic values into easy-to-understand summaries grounded strictly in your test results.'}
                </p>
                <button
                  onClick={() => handleGenerateExplanation()}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20"
                >
                  {explainLanguage === 'ta'
                    ? 'AI விளக்கத்தை இப்போதே உருவாக்கு'
                    : explainLanguage === 'hi'
                    ? 'अभी AI व्याख्या बनाएं'
                    : 'Generate AI Explanation Now'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: OCR Raw Text */}
        {activeTab === 'ocr_text' && (
          <div className="p-6">
            {report.raw_ocr_text ? (
              <div className="space-y-4">
                <div className="p-4 rounded-2xl bg-[#070a12] border border-white/5 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">
                  {report.raw_ocr_text}
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-2">
                  <span>Characters: {report.raw_ocr_text.length}</span>
                  <span>Lines: {report.raw_ocr_text.split('\n').length}</span>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center space-y-3">
                <ScanLine className="h-10 w-10 text-cyan-400 mx-auto animate-pulse" />
                <p className="text-sm font-semibold text-white">OCR has not been executed yet</p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto">
                  Click the "Run OCR" button above to preprocess the document and extract structured text.
                </p>
                <button
                  onClick={handleRunOCR}
                  disabled={ocrRunning}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20"
                >
                  Run OCR Extraction Now
                </button>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Document Metadata */}
        {activeTab === 'info' && (
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-slate-500 font-semibold uppercase">Document ID</span>
                <p className="font-mono text-slate-300">{report.id}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-slate-500 font-semibold uppercase">MIME File Type</span>
                <p className="font-mono text-slate-300">{report.file_type}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-slate-500 font-semibold uppercase">Private Storage Location</span>
                <p className="font-mono text-slate-300 truncate">{report.file_url}</p>
              </div>
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-white/5 space-y-1">
                <span className="text-slate-500 font-semibold uppercase">Created At</span>
                <p className="text-slate-300">{report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}</p>
              </div>
            </div>
          </div>
        )}
      </div>


      {/* Manual Biomarker Edit Modal */}
      {editingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card w-full max-w-md p-6 rounded-3xl border border-cyan-500/30 bg-slate-900 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white">Biomarker Correction & Verification</h3>
                <p className="text-xs text-slate-400">Raw OCR: {editingItem.raw_test_name}</p>
              </div>
              <button
                onClick={() => setEditingItem(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {editingItem.verification_reason && (
              <div className="p-3 rounded-xl bg-slate-950/80 border border-white/5 text-[11px] text-slate-300 flex items-start space-x-2">
                <Info className="h-4 w-4 text-cyan-400 shrink-0 mt-0.5" />
                <span>{editingItem.verification_reason}</span>
              </div>
            )}

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-semibold mb-1">Standard Canonical Name</label>
                <input
                  type="text"
                  value={editForm.normalized_name}
                  onChange={(e) => setEditForm({ ...editForm, normalized_name: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white focus:border-cyan-400 focus:outline-none"
                  placeholder="e.g. Haemoglobin"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Measured Value</label>
                <input
                  type="number"
                  step="any"
                  value={editForm.value_numeric}
                  onChange={(e) => setEditForm({ ...editForm, value_numeric: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white focus:border-cyan-400 focus:outline-none"
                  placeholder="e.g. 14.2"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Unit</label>
                  <input
                    type="text"
                    value={editForm.unit}
                    onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white focus:border-cyan-400 focus:outline-none"
                    placeholder="e.g. g/dL"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Clinical Flag</label>
                  <select
                    value={editForm.flag}
                    onChange={(e) => setEditForm({ ...editForm, flag: e.target.value as any })}
                    className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white focus:border-cyan-400 focus:outline-none"
                  >
                    <option value="NORMAL">NORMAL</option>
                    <option value="LOW">LOW</option>
                    <option value="HIGH">HIGH</option>
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="UNCERTAIN">UNCERTAIN</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 font-semibold mb-1">Reference Range</label>
                <input
                  type="text"
                  value={editForm.reference_range_raw}
                  onChange={(e) => setEditForm({ ...editForm, reference_range_raw: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-xl bg-slate-950 border border-white/10 text-white focus:border-cyan-400 focus:outline-none"
                  placeholder="e.g. 13.0 - 17.0"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={() => setEditingItem(null)}
                className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                disabled={savingEdit}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-cyan-500 hover:from-teal-400 hover:to-cyan-400 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 flex items-center space-x-1.5 transition disabled:opacity-50"
              >
                <Save className="h-4 w-4" />
                <span>{savingEdit ? 'Saving...' : 'Save & Verify'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Phase 9: Persistent Floating Chat Trigger Button */}
      <button
        onClick={() => setChatOpen(true)}
        className="fixed bottom-6 right-6 z-40 px-5 py-3.5 rounded-full bg-gradient-to-r from-teal-500 via-emerald-500 to-teal-400 hover:from-teal-400 hover:to-emerald-300 text-slate-950 font-extrabold text-xs shadow-2xl shadow-teal-500/40 flex items-center gap-2.5 transition-all hover:scale-105 border border-teal-300/40 group cursor-pointer"
      >
        <div className="w-6 h-6 rounded-full bg-slate-950/20 flex items-center justify-center">
          <MessageSquare className="w-3.5 h-3.5 text-slate-950 fill-current" />
        </div>
        <span className="tracking-wide">Ask My Report</span>
        <span className="w-2 h-2 rounded-full bg-emerald-950 animate-ping" />
      </button>

      {/* Phase 9: "Ask My Report" Interactive Sliding Chat Drawer */}
      <ReportChatDrawer
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        reportId={reportId}
        reportTitle={report?.title || 'Medical Lab Report'}
        testResults={testResults}
        aiStatus={aiStatus}
      />
    </>
  )}
</div>
);
}

