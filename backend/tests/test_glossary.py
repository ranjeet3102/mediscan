import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.glossary_service import medical_glossary_service
from app.services.embedding_service import embedding_service

client = TestClient(app)

def test_embedding_generation_and_cosine_similarity():
    # Test vector dimensionality
    vec1 = embedding_service.generate_embedding("Haemoglobin oxygen transport protein")
    assert len(vec1) == 384

    vec2 = embedding_service.generate_embedding("Hemoglobin red blood cells oxygen")
    assert len(vec2) == 384

    vec3 = embedding_service.generate_embedding("Thyroid stimulating hormone TSH metabolism")
    assert len(vec3) == 384

    sim_related = embedding_service.cosine_similarity(vec1, vec2)
    sim_unrelated = embedding_service.cosine_similarity(vec1, vec3)

    # Similar concepts should have higher cosine similarity than unrelated ones
    assert sim_related > sim_unrelated

def test_direct_biomarker_lookup():
    # Direct canonical lookup
    entry_hb = medical_glossary_service.get_by_name("Haemoglobin")
    assert entry_hb is not None
    assert entry_hb.canonical_name == "Haemoglobin"
    assert "oxygen" in entry_hb.definition.lower()
    assert entry_hb.category == "Complete Blood Count (CBC)"

    # Alias lookup
    entry_tsh = medical_glossary_service.get_by_name("TSH")
    assert entry_tsh is not None
    assert entry_tsh.canonical_name == "Thyroid Stimulating Hormone (TSH)"

    # Glycemic alias lookup
    entry_a1c = medical_glossary_service.get_by_name("HbA1c")
    assert entry_a1c is not None
    assert entry_a1c.canonical_name == "Glycated Hemoglobin (HbA1c)"

def test_semantic_vector_search():
    # Semantic search: concept description without mentioning the exact canonical name
    results = medical_glossary_service.search("3-month average blood sugar level for diabetes", limit=3)
    assert len(results) > 0
    top_match = results[0]
    assert "Glycated Hemoglobin (HbA1c)" in [r["canonical_name"] for r in results]

    # Semantic search for kidney filtration
    results_kidney = medical_glossary_service.search("kidney waste filtration rate", limit=3)
    assert len(results_kidney) > 0
    matched_names = [r["canonical_name"] for r in results_kidney]
    assert any(k in matched_names for k in ["Serum Creatinine", "eGFR (Estimated Glomerular Filtration Rate)", "Blood Urea"])

def test_glossary_search_api():
    headers = {"Authorization": "Bearer dev-test-token"}
    response = client.get("/api/v1/glossary/search?q=cholesterol", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["results"]) > 0
    assert any("Cholesterol" in r["canonical_name"] for r in data["data"]["results"])

def test_glossary_item_api():
    headers = {"Authorization": "Bearer dev-test-token"}
    response = client.get("/api/v1/glossary/item/Serum Creatinine", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["canonical_name"] == "Serum Creatinine"
    assert "muscle" in data["data"]["patient_friendly_summary"].lower()

def test_glossary_categories_api():
    headers = {"Authorization": "Bearer dev-test-token"}
    response = client.get("/api/v1/glossary/categories/all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    categories = data["data"]["categories"]
    assert "Complete Blood Count (CBC)" in categories
    assert "Liver Function Tests (LFT)" in categories
    assert "Lipid Profile" in categories
