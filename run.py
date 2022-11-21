import krooster_parser as kp
import scan_gform as sgf
import sys
import csv

# set up mapping of rarities to ops
op_rarities = {r: set() for r in range(1, 7)}
for op_name, data in kp.operators_json.items():
    if kp.EN_ONLY and data.get("isCnOnly"):
        # op is CN_only but kparser set to EN only
        continue

    rarity = data.get("rarity")
    op_rarities[rarity].add(op_name)


def write_to_csv(counts: dict[str, dict[str, int]], filename: str):
    """Write results to given filename"""

    # add operator ID and name to each row
    results: list[dict[str, int]] = []
    for op_id, counts_dict in counts.items():
        csv_row = counts_dict
        csv_row["operator_id"] = op_id
        csv_row["operator_name"] = kp.operators_json.get(op_id).get("name")
        results.append(csv_row)

    # write to CSV
    columns = ["operator_name"] + kp.COUNTED_FIELDS + ["operator_id"]
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

    # rarity/community specific stats
    for subset_name, user_list in user_lists.items():  # for each rarity/community pair
        if not user_list:  # list is empty
            continue

        rarity = int(subset_name[0])
        valid_ops = op_rarities.get(rarity)

        results = kp.count(user_list, accepted_ops=valid_ops)

        out_path = f"output/{subset_name}.csv"
        write_to_csv(results, out_path)
        print(f"Wrote to {out_path}")

    # find overall stats (all communities) for each rarity
    for rarity in range(1, 7):
        df_tmp = df[df['rarities'].apply(lambda l: rarity in l)]
        user_list = list(df_tmp['username'])

        valid_ops = op_rarities.get(rarity)

        results = kp.count(user_list, accepted_ops=valid_ops)

        out_path = f"output/ALL_{rarity}.csv"
        write_to_csv(results, out_path)
        print(f"Wrote to {out_path}")


if __name__ == "__main__":
    main(sys.argv)
