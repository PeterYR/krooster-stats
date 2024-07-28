import csv


OPERATORS_JSON_URL = (
    "https://raw.githubusercontent.com/neeia/ak-roster/main/src/data/operators.json"
)


FIELDS = [
    "available",
    "mod-X",
    "mod-Y",
    "mod-D",
]


def generate_flags(op_data: dict, include_cn=False) -> dict[str, bool]:
    """Generate inclusion flags for a single operator based on given params."""

    output = {f: False for f in FIELDS}

    output["available"] = True
    if not include_cn and op_data["isCnOnly"]:
        # not available in EN
        output["available"] = False

    for module in op_data["modules"]:
        if not include_cn and module["isCnOnly"]:
            # module not available in EN
            continue

        mod_letter = module["typeName"][-1]
        assert mod_letter in {"X", "Y", "D"}

        output[f"mod-{mod_letter}"] = True

    return output


def generate_all_flags(
    operators_json: dict[str, dict],
    rarities: set = None,
    include_cn=False,
) -> dict[str, dict[str, bool]]:
    """Generate inclusion flags for operators based on given params.

    - `rarities`: operators will be excluded if bad rarity, include all rarities if not given
    - `include_cn`: other flags will be set based on `isCnOnly` flags, but not excluded
    """
    output = {}

    for op_id, data in operators_json.items():
        if rarities is not None and data["rarity"] not in rarities:
            continue

        output[op_id] = generate_flags(data, include_cn=include_cn)

    return output


def write_to_csv(flags: dict[str, dict[str, bool]], filename: str):
    """Write flags to CSV file"""

    columns = ["operator_id"] + FIELDS
    rows = []
    for op_id, flag_dict in flags.items():
        row = flag_dict
        row["operator_id"] = op_id
        rows.append(row)

    with open(filename, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
