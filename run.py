import krooster_parser as kp
import scan_gform as sgf
import sys

# set up mapping of rarities to ops
op_rarities = {r: set() for r in range(1, 7)}
for op_name, data in kp.operators_json.items():
    rarity = data.get("rarity")
    op_rarities[rarity].add(op_name)


def main(argv):
    if len(argv) < 2:
        print(f"Usage: python {argv[0]} <Google forms CSV path>")
        sys.exit()

    user_lists = sgf.generate_user_lists(sgf.get_df(argv[1]))

    for subset_name, username in user_lists.items():
        rarity = int(subset_name[0])
        valid_ops = op_rarities.get(rarity)


if __name__ == "__main__":
    main(sys.argv)
