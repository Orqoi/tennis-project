import pandas as pd
import numpy as np
import math
from tqdm import tqdm
from datetime import datetime, timedelta
import warnings
from sklearn.metrics import brier_score_loss, log_loss
import glob
import os
warnings.simplefilter("ignore")

# Initialization
Delta = 0.08
target_year = 2018
bankroll = 10000
profit = 0
total_input = 0
num_of_win = 0
num_of_bet = 0
result = []

# Prediction by MDP, should have columns ['date', 'P1Name', 'P2Name', 'P1WinProb', 'P2WinProb']
pred_mdp = pd.read_csv('MDP_pred.csv')

# Betting data
betting_men = pd.read_excel('./betting/men/%d.xlsx' % target_year, engine='openpyxl')
betting_women = pd.read_excel('./betting/women/%d.xlsx' % target_year, engine='openpyxl')
betting = pd.concat([betting_men, betting_women], ignore_index=True)
# Filter out wrong records
betting = betting.query('Comment=="Completed"')
betting = betting.query('AvgW<2 or AvgL<2')
betting = betting.query('AvgW<=MaxW and AvgL<=MaxL')

for index, match in tqdm(pred_mdp.iterrows()):
    betonP1 = False
    betonP2 = False
    betAmount = 100
    modelChoice = None

    # find corresponding match in betting csv
    P1Name = match.P1Name.split(' ')[-1]
    P2Name = match.P2Name.split(' ')[-1]
    market = betting.query('Date==@match.date and Winner.str.contains(@P1Name) and Loser.str.contains(@P2Name)')
    if len(market) != 1 or math.isnan(market.AvgW) or math.isnan(market.AvgL):
        continue
    market = market.iloc[0]

    # mdp prediction
    P1WinProb = match.P1WinProb
    P2WinProb = 1 - P1WinProb

    # bookmaker prediction
    marketP1WinProb = 1 / market.AvgW
    marketP2WinProb = 1 / market.AvgL
    o = (marketP1WinProb + marketP2WinProb - 1) / 2  # beacuse marketP1WinProb + marketP2WinProb != 1

    # Betting strategy
    if marketP1WinProb + o + Delta < P1WinProb:   # Bet on P1 if we predict P1's win prob > bookmaker prob by delta
        betonP1 = True
    elif marketP2WinProb + o + Delta < P2WinProb: # Bet on P2 if we predict P2's win prob > bookmaker prob by delta
        betonP2 = True

    # Update bankroll and profits
    winnings = 0
    if betonP1:
        winnings += (market.AvgW - 1) * betAmount
        num_of_win += 1
        num_of_bet += 1
        total_input += betAmount
    elif betonP2:
        winnings -= betAmount
        num_of_bet += 1
        total_input += betAmount
    bankroll += winnings
    profit += winnings

    # Run out of money
    if bankroll <= 10:
        print('Run out of money in %d bets!' % (total_input/100))
        # exit(0)

print('Profits: %d, total input:%d, total win: %d, num of bet: %d' % (profit, total_input, num_of_win, num_of_bet))
print('Bank Roll: %d' % bankroll)
