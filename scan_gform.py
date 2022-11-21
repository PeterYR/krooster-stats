import csv
import pandas as pd


COLUMNS = {
    "What is your Krooster username?": "username",
    "What rarities have you entered data for?": "rarities",
    "How did you hear about this survey?": "communities",
}

COMMUNITIES = {
    "Discord",
    "Reddit",
    "YouTube",
    "Twitter",
}


def get_df(filename: str) -> pd.DataFrame:
    """Generate Pandas dataframe from Google Forms responses"""

    df = pd.read_csv(filename)
    df.rename(columns=COLUMNS, inplace=True)
    # return df

    # remove blank names
    df.dropna(subset="username", inplace=True)
    # for dupe names, only use latest submission
    df.drop_duplicates(subset="username", keep="last", inplace=True)

    # separate rarity and community strings into lists
    df["rarities"] = (
        df["rarities"].str.split(",").apply(lambda l: [int(x.strip(" ★")) for x in l])
    )
    df["communities"] = (
        df["communities"]
        .str.split(",")
        .apply(lambda l: [x.strip() for x in l] if type(l) is list else l)
    )

    return df


def generate_user_lists(df: pd.DataFrame) -> dict[str, list[str]]:
    """Generates dict where keys are lists of users.\n
    Dict values: `"{rarity}_{community}"`"""

    output = {}

    for rarity in range(1, 7):
        df_tmp = df[df["rarities"].apply(lambda l: rarity in l)]

        # # scan for all communities present for this rarity
        # communities = set()
        # for comm_list in df_tmp['communities']:
        #     for community in comm_list:
        #         communities.add(community)

        for community in COMMUNITIES:
            # dataframe filtered by rarity and community
            df_tmp2 = df_tmp[
                df_tmp["communities"].apply(
                    lambda l: type(l) is list and community in l
                )
            ]

            # set up file-safe community name
            f_comm_name = "".join([c for c in community if c.isalnum() or c == " "])
            f_comm_name = "_".join(f_comm_name.split())

            output[f"{rarity}_{f_comm_name}"] = list(df_tmp2["username"])

    return output
