import csv
import pandas as pd


COLUMNS = {
    "What is your Krooster username?": "username",
    "What rarities have you entered data for?": "rarities",
}


def get_df(filename: str) -> pd.DataFrame:
    """Generate Pandas dataframe from Google Forms responses"""

    df = pd.read_csv(filename)
    df.rename(columns=COLUMNS, inplace=True)

    # remove blank names
    df.dropna(subset="username", inplace=True)
    # for dupe names, only use latest submission
    df.drop_duplicates(subset="username", keep="last", inplace=True)

    # separate rarity strings into lists
    df["rarities"] = (
        df["rarities"].str.split(",").apply(lambda l: [int(x.strip(" ★")) for x in l])
    )

    return df


def generate_user_lists(df: pd.DataFrame) -> dict[int, list[str]]:
    """Generates dict of rarities to lists of users.\n
    `"{1: ['user1', 'user2' ...], ...}"`"""

    output = {}

    for rarity in range(1, 7):
        df_tmp = df[df["rarities"].apply(lambda l: rarity in l)]
        output[rarity] = list(df_tmp["username"])

    return output
