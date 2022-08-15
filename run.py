import sys
import csv
import requests


EN_ONLY = True

OPERATORS_JSON_URL = 'https://raw.githubusercontent.com/neeia/ak-roster/main/src/data/operators.json'

COUNTED_FIELDS = [
    'owned',
    'E1',
    'E2',
    'max-lvl',
    'S1M3',
    'S2M3',
    'S3M3'
]

MAX_ELITES_AND_LEVELS = {
    1: (0, 30),
    2: (0, 30),
    3: (1, 55),
    4: (2, 70),
    5: (2, 80),
    6: (2, 90)
}


def get_roster(username: str) -> dict:
    '''Make HTTP requests and return Krooster roster JSON'''

    uuid = requests.get(f'https://ak-roster-default-rtdb.firebaseio.com/phonebook/{username.lower()}.json').json()
    if not uuid:
        raise ValueError(f'Invalid username: {username}')
    return requests.get(f'https://ak-roster-default-rtdb.firebaseio.com/users/{uuid}/roster.json').json()


def parse_data(op_data: dict) -> dict:
    '''Returns dict with bools for stats of interest'''

    output = {key: False for key in COUNTED_FIELDS}

    if not op_data['owned']:
        return output
    output['owned'] = True

    # set max-lvl bool if operator is at max elite and level
    if (op_data.get('promotion'), op_data.get('level')) == MAX_ELITES_AND_LEVELS[op_data['rarity']]:
        output['max-lvl'] = True

    # set E1 and E2 bools
    if op_data.get('promotion') >= 1:
        output['E1'] = True
        if op_data.get('promotion') >= 2:
            output['E2'] = True

    # set M3 bools
    for skill_num in range(1, 4):
        if op_data.get(f'skill{skill_num}Mastery') == 3:
            output[f'S{skill_num}M3'] = True

    return output


def write_to_csv(results: list[dict[str, str]], filename: str):
    '''Write results to given file'''

    columns = ['operator_name'] + COUNTED_FIELDS + ['operator_id']
    with open(f'{filename}', 'w', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)


def main():
    if len(sys.argv) < 2:
        print('Usage: python run.py <username list path> [rarity]')
        sys.exit()
    

    rarity = 0
    if len(sys.argv) >= 3:  # rarity specified
        rarity = int(sys.argv[2])
        if not 1 <= rarity <= 6:
            print('Rarity must be between 1 and 6')
            sys.exit()
    

    # get common info of ops (operators.json)
    operators_json: dict = requests.get(OPERATORS_JSON_URL).json()
    print(f'Loaded operators.json from {OPERATORS_JSON_URL}')


    common_op_info = {}
    for op_id, op_data in operators_json.items():
        common_op_info[op_id] = {
            'name': op_data['name'],
            'rarity': op_data['rarity'],
            'isCnOnly': op_data['isCnOnly']
        }


    counts = {}  # operator ID to dict with counts
    for key, val in common_op_info.items():
        if rarity and val['rarity'] != rarity:
            # skip if rarity specified but doesn't match
            continue
        if EN_ONLY and val['isCnOnly']:
            # use only EN ops
            continue
        counts[key] = {key: 0 for key in COUNTED_FIELDS}


    # iterate through Krooster usernames and count
    users_ct = 0
    with open(sys.argv[1]) as fp:
        for txt_line in fp:
            username = txt_line.strip(' \t\n\r')
            if not username:
                continue

            roster_json = get_roster(username)
            if not roster_json:  # roster empty or smth
                print(f'Roster for {username} is empty')
                continue
            print(f'Fetched roster for {username}')

            for op_id, op_data in roster_json.items():
                if rarity and op_data['rarity'] != rarity:
                    # skip if rarity specified but doesn't match
                    continue
                if EN_ONLY and operators_json[op_id]['isCnOnly']:
                    # use only EN ops
                    continue

                # parse roster JSON for operator and increment counts dict
                parsed_bools = parse_data(op_data)
                for key, val in parsed_bools.items():
                    if val:
                        counts[op_id][key] += 1
            users_ct += 1


    # convert counts to CSV columns
    output = []
    for op_id, counts_dict in counts.items():
        csv_row = counts_dict
        csv_row['operator_id'] = op_id
        csv_row['operator_name'] = operators_json.get(op_id).get('name')
        output.append(csv_row)

    write_to_csv(output, 'output.csv')
    print(f'Saved results for {users_ct} users to output.csv')


if __name__ == '__main__':
    main()
