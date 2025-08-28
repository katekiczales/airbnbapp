import json
import pytest

# Services under test
import properties_service as props_svc
import users_service as users_svc
import recommender_service as rec_svc


@pytest.fixture(autouse=True)
def isolate_data_paths(tmp_path, monkeypatch):
    """
    Redirect all file I/O to a temporary folder.
    """
    monkeypatch.setattr(props_svc, "PROPERTIES_DATA_PATH", tmp_path / "properties.json")
    monkeypatch.setattr(users_svc, "USERS_DATA_PATH", tmp_path / "users.json")
    monkeypatch.setattr(rec_svc, "DATA_PATH", tmp_path / "records.json")

    # Start with empty users/properties files
    (tmp_path / "users.json").write_text("[]", encoding="utf-8")
    yield


@pytest.fixture
def stub_llm(monkeypatch):
    """
    Stub the OpenRouter call
    """
    sample_props = [
        {
            "property_id": "P1",
            "location": "Tofino",
            "type": "cabin",
            "nightly_price": 150,
            "features": ["wifi"],
            "tags": ["beach"],
            "capacity": 4,
            "lat": 49.152, "lon": -125.906,
        },
        {
            "property_id": "P2",
            "location": "Kelowna",
            "type": "condo",
            "nightly_price": 200,
            "features": ["wifi", "pool"],
            "tags": ["lake"],
            "capacity": 3,
            "lat": 49.887, "lon": -119.496,
        },
    ]
    monkeypatch.setattr(props_svc, "llm_generate_properties", lambda *a, **k: sample_props)
    return sample_props


def test_end_to_end_minimal(stub_llm):
    # Generate & persist properties (using stubbed LLM)
    props = props_svc.ensure_properties()
    assert props == stub_llm

    # Create a user in budget for both properties
    user = users_svc.create_user(
        email="a@example.com", first_name="A", last_name="User",
        budget_min=0, budget_max=300, preferred_env=None,
    )

    # Run recommender and verify shape + records file written
    out = rec_svc.produce_top_matches(user, n=2)
    assert isinstance(out, list) and len(out) == 2
    assert all("property_id" in r and "score" in r for r in out)

    # Recommender writes a JSON records file; confirm it matches
    records_path = rec_svc.DATA_PATH
    saved = json.loads(records_path.read_text(encoding="utf-8"))
    assert saved == out