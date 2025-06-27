import pandas as pd

from src.utils.file_helpers import save_dataframe_csv


def test_save_dataframe_csv(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    file_path = save_dataframe_csv(df, tmp_path, "data")
    assert file_path.exists()
    loaded = pd.read_csv(file_path)
    pd.testing.assert_frame_equal(df, loaded)


def test_save_dataframe_csv_empty(tmp_path):
    """Test saving an empty DataFrame."""
    df = pd.DataFrame()
    file_path = save_dataframe_csv(df, tmp_path, "empty")
    assert file_path.exists()
    loaded = pd.read_csv(file_path)
    pd.testing.assert_frame_equal(df, loaded)


def test_save_dataframe_csv_special_chars(tmp_path):
    """Test saving DataFrame with special characters."""
    df = pd.DataFrame({"col with spaces": [1, 2], "col-with-dashes": [3, 4]})
    file_path = save_dataframe_csv(df, tmp_path, "special")
    assert file_path.exists()
    loaded = pd.read_csv(file_path)
    pd.testing.assert_frame_equal(df, loaded)
