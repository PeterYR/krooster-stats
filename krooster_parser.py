import grequests
import requests
from typing import Any


CHUNK_SIZE = 500


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
    "all-M3",
    "mod-X3",
    "mod-Y3",
    "mod-D3",
    "pot-6",
]

MAX_ELITES_AND_LEVELS = {
    1: (0, 30),
    2: (0, 30),
    3: (1, 55),
    4: (2, 70),
    5: (2, 80),
    6: (2, 90),
}

# modules unlock at E2, with levels depending on rarity
MODULE_UNLOCKS = {
    4: 40,
    5: 50,
    6: 60,
}

type Roster = dict[str, dict[str, Any]]
"""operator ID -> data"""

# load general operator data from operators.json
operators_json: dict[str, dict] = requests.get(OPERATORS_JSON_URL).json()
common_op_info: dict[str, dict] = {}
for id, data in operators_json.items():
    # find module order
    mod_order = []
    for module in data["modules"]:
        if module["typeName"] == "ISW-A":  # skip IS modules for now
            # TODO: handle IS modules
            continue

        mod_letter = module["typeName"][-1:]

        assert len(module["stages"]) == 3
        assert mod_letter in {"X", "Y", "D"}

        mod_order.append(mod_letter)

    common_op_info[id] = {
        "name": data["name"],
        "rarity": data["rarity"],
        "mod_order": mod_order,
    }


def split_list(ls: list, size: int):
    """Split list into chunks of size `size`"""
    return (ls[i : i + size] for i in range(0, len(ls), size))


def get_uuids(usernames: list[str], logging=False) -> dict[str, str | None]:
    """Returns dict of usernames to UUIDs (`None` if invalid)"""
    output: dict[str, str] = {}

    for chunk in split_list(usernames, CHUNK_SIZE):
        reqs = (
            grequests.get(
                f"https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json"
            )
            for username in chunk
        )
        responses: list[requests.Response] = grequests.map(reqs)

        uuids_chunk: list[str | None] = []
        for r in responses:
            uuid = None
            # https://stackoverflow.com/a/69312334
            if r and r.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    uuid = r.json()
                except requests.exceptions.JSONDecodeError:
                    pass

            uuids_chunk.append(uuid)

        assert len(chunk) == len(uuids_chunk)
        for username, uuid in zip(chunk, uuids_chunk):
            output[username] = uuid

    return output


def get_rosters(usernames: list[str], logging=False) -> list[Roster]:
    # find UUIDs
    uuids: list[str] = []

    for chunk in split_list(usernames, CHUNK_SIZE):
        reqs = (
            grequests.get(
                f"https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json"
            )
            for username in chunk
        )
        responses: list[requests.Response] = grequests.map(reqs)

        for r in responses:
            # https://stackoverflow.com/a/69312334
            if r and r.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    roster = r.json()
                except requests.exceptions.JSONDecodeError:
                    continue

                if roster:  # uuid is null/None if bad username
                    uuids.append(roster)

        if logging:
            print(f"Found {len(uuids)} UUIDs...")

    # get rosters from UUIDs
    rosters: list[dict[str, dict]] = []
    for chunk in split_list(uuids, CHUNK_SIZE):
        reqs = (
            grequests.get(
                f"https://ak-roster-default-rtdb.firebaseio.com/users/{uuid}/roster.json"
            )
            for uuid in chunk
        )
        responses: list[requests.Request] = grequests.map(reqs)

        for r in responses:
            # https://stackoverflow.com/a/69312334
            if r and r.headers.get("Content-Type", "").startswith("application/json"):
                try:
                    roster = r.json()
                except requests.exceptions.JSONDecodeError:
                    continue

                if roster:  # uuid is null/None if bad username
                    rosters.append(roster)

        if logging:
            print(f"Found {len(rosters)} rosters...")

    return rosters


def parse_data(op_data: dict) -> dict[str, bool]:
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
    mastery = force_mastery_mod_schema(op_data.get("mastery", {}))
    for skill_num in range(1, 4):
        if mastery.get(skill_num, -1) == 3:
            output[f"S{skill_num}M3"] = True

    # set M6/M9 bool
    if (
        op_data["rarity"] >= 4
        and output["S1M3"]
        and output["S2M3"]
        and (output["S3M3"] or op_data["rarity"] < 6)
    ):
        output["all-M3"] = True

    # set mod3 bools
    if (
        op_data["rarity"] >= 4  # 4-star and above
        and op_data["promotion"] >= 2  # e2
        and op_data["level"] >= MODULE_UNLOCKS[op_data["rarity"]]  # leveled enough
        and "module" in op_data  # module data in roster entry
    ):
        mod_data = convert_mod_schema(
            force_mastery_mod_schema(op_data["module"]),
            common_op_info[op_data["id"]]["mod_order"],
        )
        for mod_letter, mod_level in mod_data.items():
            if mod_level == 3:
                assert f"mod-{mod_letter}3" in output
                output[f"mod-{mod_letter}3"] = True

    # set pot6 bool
    if op_data["potential"] == 6:
        output["pot-6"] = True

    # check for impossible masteries/promotions
    if op_data["id"] != "char_002_amiya":  # skip checks for caster amiya
        rarity = op_data.get("rarity")

        if rarity < 6:  # S3 doesn't exist
            output["S3M3"] = False
        if rarity < 4:  # E2 and masteries don't exist
            output["E2"] = False
            output["S2M3"] = False
            output["S1M3"] = False
        if rarity < 3:  # E1 doesn't exist
            output["E1"] = False
    if op_data.get("skillLevel", 0) < 7:  # skill level too low for masteries
        output["S1M3"] = False
        output["S2M3"] = False
        output["S3M3"] = False
        output["all-M3"] = False

    return output


def force_mastery_mod_schema(data: list[int | None] | dict[str, int]) -> dict[int, int]:
    """Mastery/mod schema is wack, this func makes it less wack

    - Masteries: key is skill number
    - Modules: key is nth module (1-indexed, order matches game data)

    `[None, 3] -> {2: 3}`

    `{'0': 1, '1': 2} -> {1: 1, 2: 2}`
    """
    output = {}
    if not data:
        return output

    if type(data) is list:
        for i, m in enumerate(data):
            if m:  # list entry is neither None nor 0
                output[i + 1] = m

        return output

    elif type(data) is dict:
        for i in range(1, 4):
            if str(i - 1) in data:
                output[i] = data.get(str(i - 1), 0)

    else:
        raise ValueError("Unrecognized mastery schema")
    return output


def convert_mod_schema(mod: dict[int, int], mod_order: list[str]) -> dict[str, int]:
    """Converts mod schema to dict with mod letter keys

    `{X: 3, Y: 3, D: 3}`

    `0` if not unlocked, or doesn't exist
    """
    output = {"X": 0, "Y": 0, "D": 0}
    for idx, letter in enumerate(mod_order):
        output[letter] = mod.get(idx + 1, 0)

    return output


def count(
    rosters: list[dict[str, dict]], accepted_ops: set[str] = None, logging=False
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
    for id in common_op_info.keys():
        if id in accepted_ops:
            # initialize all fields to 0
            output[id] = {field: 0 for field in COUNTED_FIELDS}

    # rosters = get_rosters(usernames)
    if logging:
        print(f"Parsing {len(rosters)} rosters...")

    for roster in rosters:
        for id, data in roster.items():  # iterate through roster JSON
            if id not in accepted_ops:
                continue

            parsed_bools = parse_data(data)
            for key, val in parsed_bools.items():
                output[id][key] += int(val)

    return output
