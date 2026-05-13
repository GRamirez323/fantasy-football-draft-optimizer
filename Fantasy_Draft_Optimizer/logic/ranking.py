import pandas as pd

def calculate_vor(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    replacement_points = (
        df.groupby("position")["player_projection"]
        .min()
        .to_dict()
    )

    df["replacement_points"] = df["position"].map(replacement_points)
    df["vor"] = df["player_projection"] - df["replacement_points"]

    df = df.sort_values(by="vor", ascending=False).reset_index(drop=True)
    return df
