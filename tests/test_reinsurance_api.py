import pytest
import pandas as pd
from app.services.reinsurance_api import ReinsuranceDataAPI

# --- Fixtures ---


@pytest.fixture
def dummy_csv_path(tmp_path):
    """Creates a temporary CSV file with mock reinsurance data."""
    data = {
        "policy_id": ["POL-001", "POL-002", "POL-003", "POL-004", "POL-005"],
        "uwy": [2022, 2022, 2023, 2023, 2024],
        "pipeline_premium": [10000.50, 25000.00, 5000.00, 15000.75, 0.00],
        "recoverable": [1500.00, 0.00, 250.50, 5000.00, 1000.00],
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "dummy_portfolio.csv"
    df.to_csv(file_path, index=False)

    return str(file_path)


@pytest.fixture
def api_client(dummy_csv_path):
    """Instantiates the API class with the dummy data."""
    return ReinsuranceDataAPI(dummy_csv_path)


# --- Tests ---


def test_initialization_failure():
    """Test that the class raises a ValueError if the file doesn't exist."""
    with pytest.raises(ValueError, match="Failed to load reinsurance data"):
        ReinsuranceDataAPI("non_existent_file.csv")


def test_get_portfolio_summary(api_client):
    """Test the summary aggregation logic."""
    response = api_client.get_portfolio_summary()

    assert response["status_code"] == 200
    data = response["data"]

    assert data["total_policies"] == 5
    # 10000.50 + 25000.00 + 5000.00 + 15000.75 + 0.00 = 55001.25
    assert data["total_pipeline_premium"] == 55001.25
    # 1500.00 + 0.00 + 250.50 + 5000.00 + 1000.00 = 7750.50
    assert data["total_recoverables"] == 7750.50
    assert data["unique_uwys"] == 3  # 2022, 2023, 2024


def test_get_policies_by_uwy_found(api_client):
    """Test filtering by Underwriting Year when records exist."""
    response = api_client.get_policies_by_uwy(2022)

    assert response["status_code"] == 200
    assert len(response["data"]) == 2
    assert response["data"][0]["policy_id"] == "POL-001"
    assert response["data"][1]["policy_id"] == "POL-002"


def test_get_policies_by_uwy_not_found(api_client):
    """Test filtering by Underwriting Year when no records exist."""
    response = api_client.get_policies_by_uwy(2099)

    assert response["status_code"] == 200
    assert response["data"] == []  # Should return empty list, not a 404


def test_get_policy_details_found(api_client):
    """Test retrieving a single policy by ID."""
    response = api_client.get_policy_details("POL-003")

    assert response["status_code"] == 200
    assert response["data"]["uwy"] == 2023
    assert response["data"]["pipeline_premium"] == 5000.00


def test_get_policy_details_not_found(api_client):
    """Test retrieving a single policy that does not exist."""
    response = api_client.get_policy_details("POL-999")

    assert response["status_code"] == 404
    assert "error" in response["data"]


def test_get_top_recoverables(api_client):
    """Test sorting and limiting top recoverables."""
    response = api_client.get_top_recoverables(limit=2)

    assert response["status_code"] == 200
    assert len(response["data"]) == 2
    # The highest recoverable is POL-004 with 5000.00
    assert response["data"][0]["policy_id"] == "POL-004"
    # The second highest is POL-001 with 1500.00
    assert response["data"][1]["policy_id"] == "POL-001"
