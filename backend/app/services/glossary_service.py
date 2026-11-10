import logging
import difflib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from app.data.medical_glossary_data import MEDICAL_GLOSSARY_ENTRIES
from app.services.embedding_service import embedding_service
from app.core.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger("medical_ocr.glossary")

@dataclass
class GlossaryEntry:
    canonical_name: str
    aliases: List[str]
    category: str
    definition: str
    what_it_measures: str
    patient_friendly_summary: str
    organs_involved: str
    standard_unit: str
    typical_range_info: str
    high_value_meaning: str
    low_value_meaning: str
    embedding: List[float]

class MedicalGlossaryService:
    """
    Curated Medical Knowledge Base and Vector Retrieval Service.
    Provides semantic vector search, direct canonical lookup, and pgvector synchronization.
    """

    def __init__(self):
        self._entries: Dict[str, GlossaryEntry] = {}
        self._alias_map: Dict[str, str] = {}
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return

        logger.info(f"Initializing Medical Knowledge Base with {len(MEDICAL_GLOSSARY_ENTRIES)} biomarkers...")
        for raw in MEDICAL_GLOSSARY_ENTRIES:
            # Combine educational text into semantic embedding document
            doc_text = (
                f"{raw['canonical_name']}. Category: {raw['category']}. "
                f"What it measures: {raw['what_it_measures']}. "
                f"Summary: {raw['patient_friendly_summary']} "
                f"Organs: {raw['organs_involved']}. "
                f"High: {raw['high_value_meaning']} "
                f"Low: {raw['low_value_meaning']}"
            )
            emb = embedding_service.generate_embedding(doc_text)

            entry = GlossaryEntry(
                canonical_name=raw["canonical_name"],
                aliases=raw.get("aliases", []),
                category=raw["category"],
                definition=raw["definition"],
                what_it_measures=raw["what_it_measures"],
                patient_friendly_summary=raw["patient_friendly_summary"],
                organs_involved=raw.get("organs_involved", "General Physiology"),
                standard_unit=raw.get("standard_unit", ""),
                typical_range_info=raw.get("typical_range_info", ""),
                high_value_meaning=raw.get("high_value_meaning", ""),
                low_value_meaning=raw.get("low_value_meaning", ""),
                embedding=emb,
            )

            canon_key = entry.canonical_name.lower().strip()
            self._entries[canon_key] = entry
            self._alias_map[canon_key] = canon_key

            for alias in entry.aliases:
                alias_clean = alias.lower().strip()
                self._alias_map[alias_clean] = canon_key

        self._initialized = True
        logger.info(f"Medical Knowledge Base initialized ({len(self._entries)} canonical biomarkers).")

    def get_by_name(self, name: str) -> Optional[GlossaryEntry]:
        """
        Retrieves biomarker glossary entry by canonical name or alias.
        """
        self.initialize()
        clean = name.lower().strip()
        if clean in self._alias_map:
            canon = self._alias_map[clean]
            return self._entries.get(canon)

        # Fuzzy match attempt
        best_match = None
        best_score = 0.0
        for alias, canon in self._alias_map.items():
            sim = difflib.SequenceMatcher(None, clean, alias).ratio()
            if sim > best_score:
                best_score = sim
                best_match = canon

        if best_match and best_score >= 0.70:
            return self._entries.get(best_match)

        return None

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search over the medical glossary,
        augmented with exact keyword and alias matching.
        """
        self.initialize()
        if not query or not query.strip():
            return [
                {**self._entry_to_dict(e), "similarity_score": 1.0}
                for e in list(self._entries.values())[:limit]
            ]

        query_emb = embedding_service.generate_embedding(query)
        scored_results = []
        query_lower = query.lower().strip()

        for entry in self._entries.values():
            vec_sim = embedding_service.cosine_similarity(query_emb, entry.embedding)

            # Boost score if query matches canonical name or aliases directly
            boost = 0.0
            if query_lower == entry.canonical_name.lower():
                boost = 0.4
            elif query_lower in entry.canonical_name.lower() or any(query_lower in a.lower() for a in entry.aliases):
                boost = 0.25
            elif query_lower in entry.patient_friendly_summary.lower() or query_lower in entry.what_it_measures.lower():
                boost = 0.15

            total_score = min(1.0, vec_sim + boost)
            scored_results.append((total_score, entry))

        # Sort by similarity descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [
            {**self._entry_to_dict(entry), "similarity_score": round(score, 3)}
            for score, entry in scored_results[:limit]
        ]

    def get_all_categories(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Returns all biomarkers organized by their medical category.
        """
        self.initialize()
        categories: Dict[str, List[Dict[str, Any]]] = {}
        for entry in self._entries.values():
            cat = entry.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                "canonical_name": entry.canonical_name,
                "aliases": entry.aliases,
                "what_it_measures": entry.what_it_measures,
                "standard_unit": entry.standard_unit,
                "typical_range_info": entry.typical_range_info,
            })
        return categories

    def seed_supabase(self) -> int:
        """
        Seeds the PostgreSQL medical_glossary table with embeddings.
        """
        self.initialize()
        if not is_supabase_configured():
            logger.info("Supabase is not configured; glossary operating with in-memory vector index.")
            return len(self._entries)

        supabase = get_supabase_client()
        count = 0
        for entry in self._entries.values():
            try:
                row = {
                    "canonical_name": entry.canonical_name,
                    "aliases": entry.aliases,
                    "category": entry.category,
                    "definition": entry.definition,
                    "what_it_measures": entry.what_it_measures,
                    "patient_friendly_summary": entry.patient_friendly_summary,
                    "standard_unit": entry.standard_unit,
                    "typical_range_info": entry.typical_range_info,
                    "embedding": entry.embedding,
                }
                supabase.table("medical_glossary").upsert(row, on_conflict="canonical_name").execute()
                count += 1
            except Exception as e:
                logger.error(f"Failed to upsert {entry.canonical_name} in Supabase: {e}")

        logger.info(f"Successfully seeded {count} medical glossary entries into Supabase pgvector.")
        return count

    def _entry_to_dict(self, entry: GlossaryEntry) -> Dict[str, Any]:
        return {
            "canonical_name": entry.canonical_name,
            "aliases": entry.aliases,
            "category": entry.category,
            "definition": entry.definition,
            "what_it_measures": entry.what_it_measures,
            "patient_friendly_summary": entry.patient_friendly_summary,
            "organs_involved": entry.organs_involved,
            "standard_unit": entry.standard_unit,
            "typical_range_info": entry.typical_range_info,
            "high_value_meaning": entry.high_value_meaning,
            "low_value_meaning": entry.low_value_meaning,
        }

# Global singleton glossary service
medical_glossary_service = MedicalGlossaryService()
