import pandas as pd

from src.utils.file_helpers import save_dataframe_csv


def test_save_dataframe_csv(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    file_path = save_dataframe_csv(df, tmp_path, "data")
    assert file_path.exists()
    loaded = pd.read_csv(file_path)
    pd.testing.assert_frame_equal(df, loaded)
