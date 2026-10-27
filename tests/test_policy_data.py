
from pathlib import Path
import pandas as pd

DATA_FILE = (
    Path(__file__).parent.parent
    / "data"
    / "policies.csv"
)

REQUIRED_COLUMNS = {
    "Country",
    "Year",
    "Policy",
    "Type",
    "Topic",
    "Status",
    "Summary",
    "Source",
}


def load_policies():
    return pd.read_csv(DATA_FILE)


def test_policy_file_exists():
    assert DATA_FILE.exists()


def test_required_columns_exist():
    df = load_policies()
    assert REQUIRED_COLUMNS.issubset(df.columns)


def test_dataset_is_not_empty():
    df = load_policies()
    assert not df.empty


def test_required_values_are_present():
    df = load_policies()

    for column in ["Country", "Policy", "Year", "Source"]:
        assert df[column].notna().all()
        assert df[column].astype(str).str.strip().ne("").all()


def test_years_are_valid_integers():
    df = load_policies()
    years = pd.to_numeric(df["Year"], errors="raise")

    assert years.between(1900, 2100).all()
    assert (years % 1 == 0).all()


def test_source_links_use_http():
    df = load_policies()

    assert df["Source"].str.startswith(
        ("https://", "http://")
    ).all()


def test_policy_records_are_unique():
    df = load_policies()

    assert not df.duplicated(
        subset=["Country", "Policy"]
    ).any()
