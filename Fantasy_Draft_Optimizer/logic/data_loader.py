import pandas as pd

REQUIRED_COLUMNS = {
    "rank",
    "player_name",
    "team",
    "position",
    "player_projection",
    "adp",
}

def load_master_data(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df
