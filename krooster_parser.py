import requests
from functools import lru_cache

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


@lru_cache
def get_roster(username: str) -> dict:
    """Make HTTP requests and return Krooster roster JSON"""

    if not username:
        return {}

    try:
        r = requests.get(
            f"https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json"
        )
        if not r:
            return {}

        uuid = r.json()
        r2 = requests.get(
            f"https://ak-roster-default-rtdb.firebaseio.com/users/{uuid}/roster.json"
        )
        if not r2:
            return {}

        return r2.json()

    except Exception:
        return {}


def parse_data(op_data: dict) -> dict:
    """Returns dict with bools for stats of interest"""

    output = {key: False for key in COUNTED_FIELDS}

    if not op_data.get("owned"):
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
    mastery = force_mastery_schema(op_data.get("mastery", {}))
    for skill_num in range(1, 4):
        # if op_data.get(f"skill{skill_num}Mastery") == 3:
        if mastery.get(skill_num) == 3:
            output[f"S{skill_num}M3"] = True

    # check for impossible masteries/promotions
    if op_data.get("id") != "char_002_amiya":  # skip checks for caster amiya
        rarity = op_data.get("rarity")

        if rarity < 6:  # S3 doesn't exist
            output["S3M3"] = False
        if rarity < 4:  # E2 and masteries don't exist
            output["E2"] = False
            output["S2M3"] = False
            output["S1M3"] = False
        if rarity < 3:  # E1 doesn't exist
            output["E1"] = False

    return output


def force_mastery_schema(mastery) -> dict[int, int]:
    """Mastery schema is wack, this func makes it less wack"""
    output = {}
    if not mastery:
        return output

    if type(mastery) is list:
        for i, m in enumerate(mastery):
            if m:  # list entry is neither None nor 0
                output[i + 1] = m

        return output

    elif type(mastery) is dict:
        for i in range(1, 4):
            if str(i - 1) in mastery:
                output[i] = mastery.get(str(i - 1), 0)

    else:
        raise ValueError("Unrecognized mastery schema")
    return output


# TODO: logging option?
def count(
    usernames: list[str], accepted_ops: set[str] = set(), logging=False
) -> dict[str, dict[str, int]]:
    """Counts fields for all users' Kroosters.\n
    `{ operator_id: { field: count } }`
    - `usernames`: list of Krooster usernames
    - `accepted_ops`: set of operator IDs to count
    - `logging`: print intermediate statuses if enabled"""

    # use all ops if accepted_ops not given
    if not accepted_ops:
        accepted_ops = set(common_op_info.keys())

    output: dict[str, dict[str, int]] = {}
    for id in common_op_info.keys():  # initialize all fields to 0
        if id in accepted_ops:
            output[id] = {field: 0 for field in COUNTED_FIELDS}

    if logging:
        print(f"Parsing {len(usernames)} rosters...")

    n = 0
    for username in usernames:
        roster = get_roster(username)

        if not roster:
            # roster is empty, or `get_roster` failed
            if logging:
                print(f"! ROSTER REQUEST FAILED for {username[:30]}")
            continue

        n += 1
        if logging:
            print(f"  Fetched roster for {username[:30]}")

        for id, data in roster.items():  # iterate through roster JSON
            if id not in accepted_ops:
                continue
            parsed_bools = parse_data(data)
            for key, val in parsed_bools.items():
                if val:
                    output[id][key] += 1

    if logging:
        print(f"Parsed {n} rosters")
    return output
