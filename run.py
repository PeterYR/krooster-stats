import sys

if len(sys.argv) != 2:
    print('Usage: python run.py <directory>')
    exit()

import csv
import json
import os
import requests

OPERATORS_JSON_URL = 'https://raw.githubusercontent.com/neeia/ak-roster/main/src/data/operators.json'
MAX_ELITES_AND_LEVELS = {
    1: (0, 30),
    2: (0, 30),
    3: (1, 55),
    4: (2, 70),
    5: (2, 80),
    6: (2, 90)
}


def parse_data(op_data) -> dict:
    '''Returns dict with bools for stats of interest'''
    global common_op_info
    global MAX_ELITES_AND_LEVELS
    output = {
        'owned': False,
        'E1': False,
        'E2': False,
        'max-lvl': False,
        'S1M3': False,
        'S2M3': False,
        'S3M3': False
    }

    if not op_data['owned']:
        return output
    output['owned'] = True

    # set max-lvl bool
    if (op_data.get('promotion'), op_data.get('level')) == MAX_ELITES_AND_LEVELS[op_data['rarity']]:
        output['max-lvl'] = True

    # set E1 and E2 bools
    if op_data.get('promotion') >= 1:
        output['E1'] = True
        if op_data.get('promotion') >= 2:
            output['E2'] = True

    # set S1M3 and S2M3 bools
    for skill_num in range(1, 4):
        if op_data.get(f'skill{skill_num}Mastery') == 3:
            output[f'S{skill_num}M3'] = True

    return output


# load Krooster JSONs
data = {}
for filename in os.listdir(sys.argv[1]):
    with open(os.path.join(sys.argv[1], filename), 'r', encoding='utf8') as fp:
        data[filename] = json.load(fp)
n = len(data)
print(f'Loaded {n} Krooster JSONs')

# get common info of ops
operator_json = requests.get(OPERATORS_JSON_URL).json()
print(f'Loaded operators.json from {OPERATORS_JSON_URL}')
common_op_info = {}
for op_id, op_data in operator_json.items():
    common_op_info[op_id] = {
        'name': op_data['name'], 'rarity': op_data['rarity']}

# iterate through operators and do stuff
results = []
for op_id, op_data in common_op_info.items():
    # name = op_data['name']
    totals = {
        'operator_id' : op_id,
        'operator_name' : op_data['name'],
        'owned': 0,
        'E1': 0,
        'E2': 0,
        'max-lvl': 0,
        'S1M3': 0,
        'S2M3': 0,
        'S3M3': 0
    }
    
    # iterate through JSON Krooster data
    for op_data in [x[op_id] for x in data.values()]:
        # print(name, op_id, parse_data(op_data))
        for key, val in parse_data(op_data).items():
            if val:
                totals[key] += 1

    results.append(totals)

# save CSV file
def write_to_csv(results, filename):
    '''Write results to given file'''
    columns = ['operator_name', 'owned', 'E1', 'E2', 'max-lvl', 'S1M3', 'S2M3', 'S3M3', 'operator_id']
    with open(f'output/{filename}.csv', 'w', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)
    print(f'Saved results to outout/{filename}.csv')


output_file_list = os.listdir('output')

if 'output.csv' not in output_file_list:
    write_to_csv(results, 'output')
    exit()

x = 1
while True:
    if f'output{x}.csv' not in output_file_list:
        write_to_csv(results, f'output{x}')
        break
    x += 1
