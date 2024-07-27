import krooster_parser as kp


OPERATORS_JSON_URL = (
    "https://raw.githubusercontent.com/neeia/ak-roster/main/src/data/operators.json"
)


def generate_flags(op_data: dict, include_cn=False):
    output = {
        "available": True,
        "mod-X": False,
        "mod-Y": False,
        "mod-D": False,
    }

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
):
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
