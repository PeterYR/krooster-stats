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


def format_csv_rows(counts: dict[str, dict[str, int]], n_users=-1, rarity=-1):
    """Add fields for final CSV output"""

    # add operator ID and name to each row
    results: list[dict[str, int]] = []
    for op_id, counts_dict in counts.items():
        csv_row = counts_dict
        csv_row["operator_id"] = op_id
        csv_row["operator_name"] = kp.operators_json[op_id]["name"]
        csv_row["n_users"] = n_users
        csv_row["rarity"] = rarity
        results.append(csv_row)

    # sort rows
    results.sort(key=lambda x: x["operator_name"])

    return results


def main(argv):
    if len(argv) < 2:
        print(f"Usage: python {argv[0]} <Google forms CSV path>")
        sys.exit()

    df = sgf.get_df(argv[1])
    user_lists = sgf.generate_user_lists(df)

    usernames = {name for sublist in user_lists.values() for name in sublist}
    uuid_map = kp.get_uuids(list(usernames), logging=True)
    roster_map = kp.get_rosters(list(uuid_map.values()), logging=True)

    # create output folder if needed
    Path("./output").mkdir(exist_ok=True)

    # rarity-specific stats
    csv_rows: list[dict[str, int]] = []
    for rarity, user_list in user_lists.items():
        if not user_list:  # list is empty
            continue

        valid_ops = op_rarities.get(rarity, set())

        rosters: list[kp.Roster] = []
        for user in user_list:
            uuid = uuid_map.get(user)
            roster = roster_map.get(uuid)
            if roster:
                rosters.append(roster)

        results = kp.count(rosters, accepted_ops=valid_ops, logging=True)

        # out_path = f"output/{rarity}.csv"
        csv_rows += format_csv_rows(results, n_users=len(rosters), rarity=rarity)

    # csv output
    columns = ["rarity", "n_users", "operator_name", "operator_id"] + kp.COUNTED_FIELDS
    out_path = "output/output.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Wrote to {out_path}")

    # existence flags
    flags = ef.generate_all_flags(kp.operators_json, include_cn=not EN_ONLY)
    out_path = "output/flags.csv"
    ef.write_to_csv(flags, out_path)
    print(f"Wrote to {out_path}")

    # overall stats
    valid_usernames = {n for n in usernames if roster_map.get(uuid_map.get(n))}
    rows = [row for _, row in df.iterrows() if row["username"] in valid_usernames]

    source_counts = {}
    for row in rows:
        source = row["source"]
        source_counts[source] = source_counts.get(source, 0) + 1

    print("\n### OVERALL STATS ###")
    print("Source counts:")
    print(f'  Discord: {source_counts.get("Discord", 0) / len(rows) * 100:.2f}%')
    print(f'  Reddit: {source_counts.get("Reddit", 0) / len(rows) * 100:.2f}%')
    print(f'  YouTube: {source_counts.get("YouTube", 0 ) / len(rows) * 100:.2f}%')


if __name__ == "__main__":
    main(sys.argv)
