import requests
from functools import cache

EN_ONLY = True

OPERATORS_JSON_URL = (
    "https://raw.githubusercontent.com/neeia/ak-roster/main/src/data/operators.json"
)

COUNTED_FIELDS = [
    "owned",
    "E1",
    "E2",
    "max-lvl",
    "S1M3",
    "S2M3",
    "S3M3",
]

MAX_ELITES_AND_LEVELS = {
    1: (0, 30),
    2: (0, 30),
    3: (1, 55),
    4: (2, 70),
    5: (2, 80),
    6: (2, 90),
}

# load general operator data from operators.json
operators_json: dict[str, dict] = requests.get(OPERATORS_JSON_URL).json()
common_op_info = {}
for id, data in operators_json.items():
    if EN_ONLY and data.get("isCnOnly"):  # skip CN-only ops if flag set
        continue

    common_op_info[id] = {
        "name": data["name"],
        "rarity": data["rarity"],
    }


@cache
def get_roster(username: str) -> dict:
    """Make HTTP requests and return Krooster roster JSON"""

    if not username:
        return {}
    uuid = requests.get(
        f"https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json"
    ).json()
    if not uuid:
        raise ValueError(f"Invalid username: {username}")
    return requests.get(
        f"https://ak-roster-default-rtdb.firebaseio.com/users/{uuid}/roster.json"
    ).json()


def parse_data(op_data: dict) -> dict:
    """Returns dict with bools for stats of interest"""

    output = {key: False for key in COUNTED_FIELDS}

    if not op_data["owned"]:
        return output
    output["owned"] = True

    # set max-lvl bool if operator is at max elite and level
    if (op_data.get("promotion"), op_data.get("level")) == MAX_ELITES_AND_LEVELS[
        op_data["rarity"]
    ]:
        output["max-lvl"] = True

    # set E1 and E2 bools
    if op_data.get("promotion") >= 1:
        output["E1"] = True
        if op_data.get("promotion") >= 2:
            output["E2"] = True

    # set M3 bools
    for skill_num in range(1, 4):
        if op_data.get(f"skill{skill_num}Mastery") == 3:
            output[f"S{skill_num}M3"] = True

    return output


def count(
    usernames: list[str], accepted_ops: set[str] = None
) -> dict[str, dict[str, int]]:
    """Counts fields for all users' Kroosters.\n
    `{ operator_id: { field: count } }`
    - `usernames`: list of Krooster usernames
    - `accepted_ops`: set of operator IDs to count"""

    # use all ops if accepted_ops not given
    if accepted_ops is None:
        accepted_ops = set(common_op_info.keys())

    output: dict[str, dict[str, int]] = {}
    for id in common_op_info.keys():  # initialize all fields to 0
        if id in accepted_ops:
            output[id] = {field: 0 for field in COUNTED_FIELDS}

    for username in usernames:
        roster = get_roster(username)
        if not roster:
            # print(f"Roster for {username} is empty")
            continue
        # print(f"Fetched roster for {username}")

        for id, data in roster.items():  # iterate through roster JSON
            if id not in accepted_ops:
                continue
            parsed_bools = parse_data(data)
            for key, val in parsed_bools.items():
                if val:
                    output[id][key] += 1

    return output
