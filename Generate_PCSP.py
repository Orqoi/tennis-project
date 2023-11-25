import pandas as pd
import numpy as np
import glob
from tqdm import tqdm as tqdm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import math
import warnings
import requests
import json
import os
warnings.simplefilter("ignore")


# generate pcsp file
def generate_pcsp(params, date, ply1_name, ply2_name, hand1, hand2):
    VAR = 'var.txt'
    HAND = '%s_%s.txt' % (hand1, hand2)
    file_name = '%s_%s_' % (hand1, hand2)
    file_name += '%s_%s_%s.pcsp' % (date, ply1_name.replace(' ', '-'), ply2_name.replace(' ', '-'))
    # write to file
    lines = []
    with open(VAR) as f:
        lines_1 = f.readlines()
    lines_2 = []
    for i, p in enumerate(params):
        lines_2.append('#define p%d %d;\n' % (i, p))
    # print(f"{len(params)} probabilities")
    with open(HAND) as f:
        lines_3 = f.readlines()
    lines = lines_1 + lines_2 + lines_3
    with open(file_name, 'w') as f:
        for line in lines:
            f.write(line)


# obtain parameters
def get_params(df, hand):
    # Serve 
    De_Serve = df.query('shot_type==1 and from_which_court==1')
    De_Serve_2nd = df.query('shot_type==2 and from_which_court==1')
    Ad_Serve = df.query('shot_type==1 and from_which_court==3')
    Ad_Serve_2nd = df.query('shot_type==2 and from_which_court==3')
    # Return
    De_ForeHandR = df.query('shot_type==3 and prev_shot_from_which_court==1 and shot<=20')
    Ad_ForeHandR = df.query('shot_type==3 and prev_shot_from_which_court==3 and shot<=20')
    De_BackHandR = df.query('shot_type==3 and prev_shot_from_which_court==1 and shot<=40 and shot>20')
    Ad_BackHandR = df.query('shot_type==3 and prev_shot_from_which_court==3 and shot<=40 and shot>20')

    # Stroke
    De_Stroke = df.query('shot_type==4 and from_which_court==1')
    Mid_Stroke = df.query('shot_type==4 and from_which_court==2')
    Ad_Stroke = df.query('shot_type==4 and from_which_court==3')

    results = []
    # Serve
    for Serve in [De_Serve, De_Serve_2nd, Ad_Serve, Ad_Serve_2nd]:
        ServeT = Serve.query('direction==6')
        ServeB = Serve.query('direction==5')
        ServeW = Serve.query('direction==4')
        serve_in = [len(x.query('shot_outcome==7')) for x in [ServeT, ServeB, ServeW]]
        serve_win = [len(Serve.query('shot_outcome in [1, 5, 6]'))]
        serve_err = [len(Serve.query('shot_outcome in [2, 3, 4]'))]
        results.append(serve_in + serve_win + serve_err)
    # print("serve")
    # print(len(sum(results, [])))

    # Return
    if hand == 'RH':  # RH
        directions = [[[[1], [1]], [[1], [3]], [[1], [2]]],                    # FH_[CC, DL, DM]
                      [[[2, 3], [3]], [[3], [1]], [[2], [1]], [[2, 3], [2]]],  # FH_[IO, II, CC, DM]
                      [[[2], [3]], [[1], [3]], [[1, 2], [1]], [[1, 2], [2]]],  # BH_[CC, II, IO, DM]
                      [[[3], [3]], [[3], [1]], [[3], [2]]]]                    # BH_[CC, DL, DM]
    else:  # LH
        directions = [[[[1, 2], [1]], [[1], [3]], [[2], [3]], [[1, 2], [2]]],  # FH_[IO, II, CC, DM]
                      [[[3], [3]], [[3], [1]], [[3], [2]]],                    # FH_[CC, DL, DM]
                      [[[1], [1]], [[1], [3]], [[1], [2]]],                    # BH_[CC, DL, DM]
                      [[[2], [1]], [[3], [1]], [[2, 3], [3]], [[2, 3], [2]]]]  # BH_[CC, II, IO, DM]
    for i, Return in enumerate([De_ForeHandR, Ad_ForeHandR, De_BackHandR, Ad_BackHandR]):
        shots = [Return.query('from_which_court in @dir[0] and to_which_court in @dir[1]') for dir in directions[i]]
        return_in = [len(x.query('shot_outcome==7')) for x in shots]
        return_win = [len(Return.query('shot_outcome in [1, 5, 6]'))]
        return_err = [len(Return.query('shot_outcome in [2, 3, 4]'))]
        results.append(return_in + return_win + return_err)
    # print("return")
    # print(len(sum(results, [])))

    # Rally
    if hand == 'RH':  # RH
        directions = [[[1, 3, 2], [3, 1, 2]], # de - FHCC, FHDL, FHDM, BHII, BHIO, BHDM
                      [[3, 1, 2], [1, 3, 2]], # mid - FHIO, FHCC, FHDM, BHIO, BHCC, BHDM
                      [[3, 1, 2], [3, 1, 2]]] # ad - FHIO, FHII, FHDM, BHCC, BHDL, BHDM

    else:  # LH
        directions = [[[1, 3, 2], [1, 3, 2]],  # de - FHIO, FHII, FHDM, BHCC, BHDL, BHDM
                      [[1, 3, 2], [3, 1, 2]],  # mid - FHIO, FHCC, FHDM, BHIO, BHCC, BHDM
                      [[3, 1, 2], [1, 3, 2]]]  # ad - FHCC, FHDL, FHDM, BHII, BHIO, BHDM
        
    # Handlers
    for i, Stroke in enumerate([De_Stroke, Mid_Stroke, Ad_Stroke]):
        # Regular, Smash, Lob
        Regular_Shallow = Stroke.query('prev_shot not in [3, 24] and hit_at_depth in [1,99]')
        Slice_Shallow = Stroke.query('prev_shot in [3, 24] and hit_at_depth in [1,99]')
        Regular_Deep = Stroke.query('prev_shot not in [3, 24] and hit_at_depth in [2,99]')
        Slice_Deep = Stroke.query('prev_shot in [3, 24] and hit_at_depth in [2,99]')
        for curr in [Regular_Shallow, Slice_Shallow, Regular_Deep, Slice_Deep]:
            react_regular_shallow = [len(curr.query('shot not in [3, 24] and depth in [1,99]'))]
            react_slice_shallow = [len(curr.query('shot in [3, 24] and depth in [1,99]'))]
            react_regular_deep = [len(curr.query('shot not in [3, 24] and depth in [2,3,99]'))]
            react_slice_deep = [len(curr.query('shot in [3, 24] and depth in [2,3,99]'))]
            results.append(react_regular_shallow + react_slice_shallow + react_regular_deep + react_slice_deep)
    # print("handlers")
    # print(len(sum(results, [])))
        
    # SHALLOW
    De_Stroke_Shallow = De_Stroke.query('depth==1 or depth==99')
    Mid_Stroke_Shallow = Mid_Stroke.query('depth==1 or depth==99')
    Ad_Stroke_Shallow = Ad_Stroke.query('depth==1 or depth==99')

    # Regular played by current player

    for i, Stroke in enumerate([De_Stroke_Shallow, Mid_Stroke_Shallow, Ad_Stroke_Shallow]):
        # (0, DE), (1, MID), (2, AD)
        FH_Stroke = Stroke.query('shot<=20 and shot not in [3]')
        BH_Stroke = Stroke.query('shot<=40 and shot>20 and shot not in [24]')
        FH_shots = [FH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][0]]
        BH_shots = [BH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][1]]
        shots = FH_shots + BH_shots
        FH_stroke_in = [len(x.query('shot_outcome==7')) for x in FH_shots]
        BH_stroke_in = [len(x.query('shot_outcome==7')) for x in BH_shots]
        stroke_win = [len(Stroke.query('shot_outcome in [1, 5, 6]'))]
        stroke_err = [len(Stroke.query('shot_outcome in [2, 3, 4]'))]
        results.append(FH_stroke_in + BH_stroke_in + stroke_win + stroke_err)
    
    # Slice played by current player
    for i, Stroke in enumerate([De_Stroke_Shallow, Mid_Stroke_Shallow, Ad_Stroke_Shallow]):
        # (0, DE), (1, MID), (2, AD)
        FH_Stroke = Stroke.query('shot==3')
        BH_Stroke = Stroke.query('shot==24')
        FH_shots = [FH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][0]]
        BH_shots = [BH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][1]]
        shots = FH_shots + BH_shots
        FH_stroke_in = [len(x.query('shot_outcome==7')) for x in FH_shots]
        BH_stroke_in = [len(x.query('shot_outcome==7')) for x in BH_shots]
        stroke_win = [len(Stroke.query('shot_outcome in [1, 5, 6]'))]
        stroke_err = [len(Stroke.query('shot_outcome in [2, 3, 4]'))]
        results.append(FH_stroke_in + BH_stroke_in + stroke_win + stroke_err)
    
    # print("shallow")
    # print(len(sum(results, [])))
    

    # DEEP

    De_Stroke_Deep = De_Stroke.query('depth==2 or depth==3 or depth==99')
    Mid_Stroke_Deep = Mid_Stroke.query('depth==2 or depth==3 or depth==99')
    Ad_Stroke_Deep = Ad_Stroke.query('depth==2 or depth==3 or depth==99')
    for i, Stroke in enumerate([De_Stroke_Deep, Mid_Stroke_Deep, Ad_Stroke_Deep]):
        # (0, DE), (1, MID), (2, AD)
        FH_Stroke = Stroke.query('shot<=20 and shot not in [3]')
        BH_Stroke = Stroke.query('shot<=40 and shot>20 and shot not in [24]')
        FH_shots = [FH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][0]]
        BH_shots = [BH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][1]]
        shots = FH_shots + BH_shots
        FH_stroke_in = [len(x.query('shot_outcome==7')) for x in FH_shots]
        BH_stroke_in = [len(x.query('shot_outcome==7')) for x in BH_shots]
        stroke_win = [len(Stroke.query('shot_outcome in [1, 5, 6]'))]
        stroke_err = [len(Stroke.query('shot_outcome in [2, 3, 4]'))]
        results.append(FH_stroke_in + BH_stroke_in + stroke_win + stroke_err)
    
    # Slice played by current player
    for i, Stroke in enumerate([De_Stroke_Deep, Mid_Stroke_Deep, Ad_Stroke_Deep]):
        # (0, DE), (1, MID), (2, AD)
        FH_Stroke = Stroke.query('shot==3')
        BH_Stroke = Stroke.query('shot==24')
        FH_shots = [FH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][0]]
        BH_shots = [BH_Stroke.query('to_which_court==@to_dir') for to_dir in directions[i][1]]
        shots = FH_shots + BH_shots
        FH_stroke_in = [len(x.query('shot_outcome==7')) for x in FH_shots]
        BH_stroke_in = [len(x.query('shot_outcome==7')) for x in BH_shots]
        stroke_win = [len(Stroke.query('shot_outcome in [1, 5, 6]'))]
        stroke_err = [len(Stroke.query('shot_outcome in [2, 3, 4]'))]
        results.append(FH_stroke_in + BH_stroke_in + stroke_win + stroke_err)
    
    # print("deep")
    # print(len(sum(results, [])))

    return results


def generate_transition_probs(data, date, ply1_name, ply2_name, ply1_hand, ply2_hand):
    prev_date = (pd.to_datetime(date) - relativedelta(years=2)).strftime('%Y-%m-%d')

    data_ply1 = data.query('date>=@prev_date and date<@date and ply1_name==@ply1_name')
    data_ply2 = data.query('date>=@prev_date and date<@date and ply1_name==@ply2_name')

    # number of matches played
    num_ply1_prev_n = len(data_ply1.date.unique())
    num_ply2_prev_n = len(data_ply2.date.unique())

    # get players params
    ply1_params = get_params(data_ply1, ply1_hand)
    ply2_params = get_params(data_ply2, ply2_hand)

    # sample
    params = sum(ply1_params, []) + sum(ply2_params, [])

    # print('# P1 matches:', num_ply1_prev_n)
    # print('# P2 matches:', num_ply2_prev_n)
    if (num_ply1_prev_n + num_ply2_prev_n >= 5):
        print("File generated")
        generate_pcsp(params, date, ply1_name, ply2_name, ply1_hand, ply2_hand)
   


date = '2020-01-01'
ply1_name = 'Roger Federer'
ply2_name = 'Novak Djokovic'
ply1_hand = 'RH'
ply2_hand = 'RH'
gender = 'M'

# obtain shot-by-shot data
file = 'tennisabstract-v2-combined.csv'
data = pd.read_csv(file, names=['ply1_name', 'ply2_name', 'ply1_hand', 'ply2_hand', 'ply1_points',
                                'ply2_points', 'ply1_games', 'ply2_games', 'ply1_sets', 'ply2_sets', 'date',
                                'tournament_name', 'shot_type', 'from_which_court', 'shot', 'direction',
                                'to_which_court', 'depth', 'touched_net', 'hit_at_depth', 'approach_shot',
                                'shot_outcome', 'fault_type', 'prev_shot_type', 'prev_shot_from_which_court',
                                'prev_shot', 'prev_shot_direction', 'prev_shot_to_which_court', 'prev_shot_depth',
                                'prev_shot_touched_net', 'prev_shot_hit_at_depth', 'prev_shot_approach_shot',
                                'prev_shot_outcome', 'prev_shot_fault_type', 'prev_prev_shot_type',
                                'prev_prev_shot_from_which_court', 'prev_prev_shot', 'prev_prev_shot_direction',
                                'prev_prev_shot_to_which_court', 'prev_prev_shot_depth',
                                'prev_prev_shot_touched_net', 'prev_prev_shot_hit_at_depth',
                                'prev_prev_shot_approach_shot', 'prev_prev_shot_outcome',
                                'prev_prev_shot_fault_type', 'url', 'description'])
rhand = set()
lhand = set()
for ind in data.index:
    p1_hand = data['ply1_hand'][ind]
    p1_name = data['ply1_name'][ind]
    rhand.add(p1_name) if p1_hand == 'RH' else lhand.add(p1_name)

    p2_hand = data['ply2_hand'][ind]
    p2_name = data['ply2_name'][ind]
    rhand.add(p2_name) if p2_hand == 'RH' else lhand.add(p2_name)

p_df = pd.read_csv("MDP_pred.csv")

for ind in p_df.index:
    date = p_df['date'][ind] # mm dd yyyy
    
    ply1_name = p_df['P1Name'][ind]
    if ply1_name in rhand:
        ply1_hand = 'RH'
    else:
        ply1_hand = 'LH'
    ply2_name = p_df['P2Name'][ind]
    if ply2_name in rhand:
        ply2_hand = 'RH'
    else:
        ply2_hand = 'LH'
    print(f"{date}, {ply1_name}, {ply2_name}")
    generate_transition_probs(data, date, ply1_name, ply2_name, ply1_hand, ply2_hand)
