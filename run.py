import csv
import sys
from pathlib import Path

import krooster_parser as kp
import scan_gform as sgf
import exist_flags as ef


EN_ONLY = True


# set up mapping of rarities to ops
op_rarities = {r: set() for r in range(1, 7)}
for op_name, data in kp.operators_json.items():
    if EN_ONLY and data.get("isCnOnly"):
        # skip CN-only operator
        continue

    rarity = data.get("rarity")
    op_rarities[rarity].add(op_name)


def write_to_csv(counts: dict[str, dict[str, int]], filename: str, n_users=-1):
    """Write results to given filename"""

    # add operator ID and name to each row
    results: list[dict[str, int]] = []
    for op_id, counts_dict in counts.items():
        csv_row = counts_dict
        csv_row["operator_id"] = op_id
        csv_row["operator_name"] = kp.operators_json[op_id]["name"]
        csv_row["n_users"] = n_users
        results.append(csv_row)

    # write to CSV
    columns = ["n_users", "operator_name"] + kp.COUNTED_FIELDS + ["operator_id"]
    with open(filename, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)


def main(argv):
    if len(argv) < 2:
        print(f"Usage: python {argv[0]} <Google forms CSV path>")
        sys.exit()

    df = sgf.get_df(argv[1])
    user_lists = sgf.generate_user_lists(df)

    # create output folder if needed
    Path("./output").mkdir(exist_ok=True)

    # rarity-specific stats
    for rarity, user_list in user_lists.items():
        if not user_list:  # list is empty
            continue

        valid_ops = op_rarities.get(rarity, set())

        rosters = kp.get_rosters(user_list)
        results = kp.count(rosters, accepted_ops=valid_ops)

        out_path = f"output/{rarity}.csv"
        write_to_csv(results, out_path, n_users=len(rosters))
        print(f"Wrote to {out_path}")

    # existence flags
    flags = ef.generate_all_flags(kp.operators_json, include_cn=not EN_ONLY)
    out_path = "output/flags.csv"
    ef.write_to_csv(flags, out_path)
    print(f"Wrote to {out_path}")


if __name__ == "__main__":
    main(sys.argv)
