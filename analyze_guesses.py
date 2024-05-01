#!/usr/bin/env python3
import os
import json
import pandas as pd

all_data = []
for team in os.listdir('data/teams'):
    # print(team)
    with open(f'data/teams/{team}/data.json') as f:
        team_data = json.load(f)
        num_team_members = team_data.get('num_team_members')
        for x in team_data['guesses']:
            guess = x['guess']
            correct = x['correct']
            all_data.append([team, num_team_members, guess, correct])
            # print(all_data[-1])
# print(all_data)

df = pd.DataFrame(all_data, columns=['team', 'num_team_members', 'guess', 'correct'])
df.to_csv('guesses.csv', index=False)
