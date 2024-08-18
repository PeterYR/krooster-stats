import pandas as pd


COLUMNS = {
    "What is your Krooster username?": "username",
    "What rarities have you entered data for?": "rarities",
}


def get_df(filename: str) -> pd.DataFrame:
    """Generate Pandas dataframe from Google Forms responses"""

    df = pd.read_csv(filename)
    df.rename(columns=COLUMNS, inplace=True)
    df = df[COLUMNS.values()]  # only keep relevant columns

    # clean up usernames
    # NOTE: Krooster usernames are limited to 24 characters
    df["username"] = df["username"].str.lower().str.strip().str.slice(0, 50)

    # remove blank names
    df.dropna(subset="username", inplace=True)

    # for dupe names, only use latest submission
    df.drop_duplicates(subset="username", keep="last", inplace=True)

    return df


def generate_user_lists(df: pd.DataFrame) -> dict[int, list[str]]:
    """Generates dict of rarities to lists of users.\n
    `"{1: ['user1', 'user2' ...], ...}"`"""

    output: dict[int, list[str]] = {}

    for rarity in range(1, 7):
        df_tmp = df[df["rarities"].apply(lambda l: str(rarity) in l)]
        output[rarity] = list(df_tmp["username"])

        # detect URLs and extract usernames
        for i, username in enumerate(output[rarity]):
            if "/" in username:
                parts = username.split("/")
                if parts[-1]:
                    output[rarity][i] = parts[-1]
                else:
                    output[rarity][i] = parts[-2]  # `/` is last char
                print(f"Detected URL: {username} -> {output[rarity][i]}")

    return output
