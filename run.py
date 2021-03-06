import sys
import csv
import json
import os
import requests


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
    with open(f'output/{filename}.csv', 'w', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    print(f'Saved results to output/{filename}.csv')


def main():
    if len(sys.argv) != 2:
        print('Usage: python run.py <username list file path>')
        sys.exit()


    # get common info of ops (operators.json)
    operators_json: dict = requests.get(OPERATORS_JSON_URL).json()
    print(f'Loaded operators.json from {OPERATORS_JSON_URL}')


    common_op_info = {}
    for op_id, op_data in operators_json.items():
        common_op_info[op_id] = {
            'name': op_data['name'],
            'rarity': op_data['rarity']
        }


    counts = {} # operator ID to dict with counts
    for key in common_op_info.keys():
        counts[key] = {key: 0 for key in COUNTED_FIELDS}


    # iterate through Krooster usernames and count
    with open(sys.argv[1]) as fp:
        for txt_line in fp:
            username = txt_line.strip(' \t\n\r')
            roster_json = get_roster(username)

            for op_id, op_data in roster_json.items():
                # parse roster JSON for operator and increment counts dict
                parsed_bools = parse_data(op_data)
                for key, val in parsed_bools.items():
                    if val:
                        counts[op_id][key] += 1


if __name__ == '__main__':
    main()




# # save to output

# output_file_list = os.listdir('output')

# if 'output.csv' not in output_file_list:
#     write_to_csv(results, 'output')
# else:
#     x = 1
#     while True:
#         if f'output{x}.csv' not in output_file_list:
#             write_to_csv(results, f'output{x}')
#             break
#         x += 1
