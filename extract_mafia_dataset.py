import os
import csv
import json

def read_csv_as_dicts(file_path):
    data = []
    with open(file_path, 'r', newline='') as csvfile:
        csvreader = csv.DictReader(csvfile)
        for row in csvreader:
            data.append(row)
    return data

def extract_game_log(sub_dir, include_night_logs=False):
    fns = [fn for fn in os.listdir(sub_dir)]
    assert 'info.csv' in fns and 'node.csv' in fns

    print(sub_dir)
    # extract game results from node.csv.
    nodes = [
        {'id': d['id'], 'name': d['property1'], 'role': d['type'], 'survive': (d['property2'] == 'True')}
        for d in read_csv_as_dicts(os.path.join(sub_dir, 'node.csv'))
        if len(d['property1']) > 1 # remove source node.
    ]

    # The goal of the mafia was to eliminate bystanders until the number of mafia was greater than or equal to that of the bystanders. 
    # The goal of the bystanders was to identify and eliminate All of the mafia members.
    surviver_roles = [n['role'] for n in nodes if n['survive']]
    if surviver_roles.count('mafioso') == 0:
        outcome = 'bystander'

    elif surviver_roles.count('mafioso') >= surviver_roles.count('bystander'): 
        outcome = 'mafioso' 

    else: 
        outcome = None
        print('WARNING: ', sub_dir, surviver_roles.count('mafioso'), surviver_roles.count('bystander'))
        print(nodes)

    # extract game log from info.csv.
    uttrs = [uttr for uttr in read_csv_as_dicts(os.path.join(sub_dir, 'info.csv'))]
    uttrs = sorted(uttrs, key=lambda x: int(x['id']))
    game_log = ''
    is_night = None
    for uttr in uttrs:
        text = uttr["contents"]
        if uttr['type'] == 'info':
            #print('REDUNDANT', uttr)
            if game_log.endswith(f'[{text}]\n'):
                continue 

            game_log += f'[{text}]\n'
            if 'Phase Change to Nighttime' in text:
                is_night = True
            if 'Phase Change to Daytime' in text:
                is_night = False

        elif uttr['type'] == 'vote':
            voter, target = text.split(': ')
            if is_night:
                if not include_night_logs:
                    continue
                game_log += f'({voter} vote to kill {target}.)\n'
            else:
                game_log += f'({voter} vote to eliminate {target}.)\n'

        else:   # text.
            if not include_night_logs and is_night:
                continue
            game_log += text + '\n' 

    return nodes, game_log, outcome
        


if __name__ == '__main__':
    data_dir = './data/mafia/raw'

    data = []
    for root, dirs, files in os.walk(data_dir):
        for dir in dirs:
            # extract data.
            sub_dir = os.path.join(root, dir)
            nodes, log, outcome = extract_game_log(sub_dir)

            if outcome is None:
                continue
            # save.
            data.append({
                'id': dir,
                'agents': nodes, 'log': log.strip().split('\n'), 
                'win': outcome})

            print(log)
            print('Mafias:', [n for n in nodes if n['role'] == 'mafioso'])
            print(outcome)
            print()

    # save to file.
    output_fn = './mafia.json'
    with open(output_fn, 'w') as F:
        json.dump(data, F, indent=4)  # indent for pretty formatting, optional
    print(f'saved {len(data)} game logs to file: {output_fn}')