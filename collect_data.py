
#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import os
import sys
import time
import random
import csv

from pyboy import PyBoy
from pyboy.utils import WindowEvent 

MAX_MOVE_ID = 165 # 1-165 inclusive
REMOVED_MOVES = [20, 99, 128, 144]
moves = [x for x in range(1,MAX_MOVE_ID+1) if x not in REMOVED_MOVES] 
TYPE_IDS = [0, 1, 2, 3, 4, 5, 7, 8, 20, 21, 22, 23, 24, 25, 26]
MAX_TYPE_ID = len(TYPE_IDS) # 0-26, although i think 0 can be ignored since normal is repeated so much
MAX_MOVE_EFFECT = 86
DATA_FILE = "pokemon_data.csv"

quiet = "--quiet" in sys.argv
pyboy = PyBoy('pokemon.gb', window="null" if quiet else "SDL2", scale=3)
pyboy.set_emulation_speed(1)



def get_player_hp():
    return pyboy.memory[0xD016]

def get_player_max_hp():
    return pyboy.memory[0xD024]

def get_player_types(): # list len 2
    return pyboy.memory[0xD019:0xD01B]

def get_player_move_ids():
    return pyboy.memory[0xD01C:0xD020]

def get_player_move_details():
    # We want to list the info related to each move
    move_details = []
    for i in get_player_move_ids():
        if i == 0: # no move in the slot
            continue
        start_addr = (i - 1) * 6
        end_addr = start_addr + 6
        move_details.append(pyboy.memory[14, start_addr:end_addr])
    return move_details # list of list len 5, [move_id, effect, base_power, type, accuracy, (max?)pp]

def check_pp(move_no): # hehe
    return (pyboy.memory[(0xD02D) + move_no] > 0)
    
def maximise_pp(): # hehe
    pyboy.memory[0xD02D:0xD031] = [a.pop(5) for a in get_player_move_details()]

def get_enemy_hp():
    return pyboy.memory[0xCFE7]

def set_enemy_hp(hp):
    pyboy.memory[0xCFE7] = hp

def get_enemy_max_hp():
    return pyboy.memory[0xCFF5]

def get_enemy_types():
    return pyboy.memory[0xCFEA:0xCFEC]

def randomise_player_moves():
    pyboy.memory[0xD01C:0xD020] = random.sample(moves, 4)
    maximise_pp()
    
def randomise_player_level():
    pyboy.memory[0xD022] = random.randint(1,100)

def randomise_player_type():
    type1 = random.choice(TYPE_IDS)
    pyboy.memory[0xD019] = type1
    if random.randint(1,3) == 1:
        # same type guranteed
        pyboy.memory[0xD01A] = type1
    else:
        type2 = random.choice(TYPE_IDS)
        pyboy.memory[0xD01A] = type2

def randomise_enemy_type():
    type1 = random.choice(TYPE_IDS)
    pyboy.memory[0xCFEA] = type1
    
    if random.randint(1,3) == 1:
        # same type guranteed
        pyboy.memory[0xCFEB] = type1
    else:
        type2 = random.choice(TYPE_IDS)
        pyboy.memory[0xCFEB] = type2 

def get_player_attack():
    return pyboy.memory[0xD026]

def get_player_special():
    return pyboy.memory[0xD02C]

def get_enemy_defence():
    return pyboy.memory[0xCFF9]

def get_enemy_special():
    return pyboy.memory[0xCFFD]    

def buff_player():
    pyboy.memory[0xD024] = 225 # max hp
    pyboy.memory[0xD016] = 225 #hp

def set_stats():
    
    hp = 75
    defence = 50
    special = 50
    
    pyboy.memory[0xCFE7] = hp # enemy hp
    pyboy.memory[0xCFF5] = hp # enemy max hp
    pyboy.memory[0xCFF9] = defence # defence
    pyboy.memory[0xCFFD] = special # special
    
    pyboy.memory[0xD026] = defence # player attack
    pyboy.memory[0xD02C] = special # player special

def type_mask(v):
    t = [0] * (MAX_TYPE_ID + 1)
    t[TYPE_IDS.index(v)] = 1
    return t
    
def get_state(move_no):
    state = []
    
    # Player related state
    # state.append(get_player_attack() / 255)
    # state.append(get_player_special() / 255)
    player_types = get_player_types()
    state += type_mask(player_types[0])
    state += type_mask(player_types[1])
    
    # Enemy related state
    # state.append(get_enemy_defence() / 255)
    # state.append(get_enemy_special() / 255)
    enemy_types = get_enemy_types()
    state += type_mask(enemy_types[0])
    state += type_mask(enemy_types[1])
    
    # Moves related state
    move_details = get_player_move_details()
    # [[]] [ [move_id, effect, base_power, type, accuracy, (max?)pp],  [move_id, effect, base_power, type, accuracy, (max?)pp] ...]
    l = move_details[move_no]
    
    # state.append(l[1] / MAX_MOVE_EFFECT) # Effect state
    state.append(l[2] / 255) # Base Power
    state += type_mask(l[3]) # type
    state.append(l[4] / 255) # accuracy
    
    return state

def save_to_csv(data):
    with open(DATA_FILE, 'a', newline='') as datafile:
        writer = csv.writer(datafile)
        writer.writerow(data)
    


# print("Player types: ", get_player_types(),"Enemy types: ",  get_enemy_types())
# print("Enemy hp: ", get_enemy_hp())

# print("Random player types: ", get_player_types(),"Enemy types: ",  get_enemy_types())

# print("Player Stats ", get_player_hp(), get_player_attack(), get_player_special())
def run_battle():
    with open("pokemon.gb.state", "rb") as sav:
        pyboy.load_state(sav)

    pyboy.memory[0xD358] = 0 # no delay between text being written
    pyboy.memory[0xD355] += 0x80 # battle animation off
    run = True # can control testing here.
    pyboy.tick(120) # load the battle
    
    randomise_player_moves()
    # set_stats()
    buff_player()
    
    
    current_move = 0
    isFirstIteration = True
    chosen_move = 0

    while run:
        
        pyboy.memory[0xCFFF] = 0 # i dont want bulbasaur using growl

        run = pyboy.tick()
        # print(pyboy.memory[0xD026], end='\r') # the attack stat only seems to increase when its being printed?

        # spam 'a' button until 0xCC30 is 193 again
        if pyboy.memory[0xCC30] != 193: # maybe avoids the case where a move lasts more than one turn?
            # print("not turn", end='\r')
            pyboy.button('a', 2)
            pyboy.tick(2)
            if get_enemy_hp() <= 0 or get_player_hp() <= 0:
                
                # final reward is here
                reward = (enemy_hp_before - get_enemy_hp()) / get_enemy_max_hp()
                print("Reward: " , reward)
                output = [reward]
                input_state = get_state(chosen_move)
                print("battle done")
                if reward > 0.2: # trying to remove the cases where a really good move is used when the enemy is at low hp, which makes the move look bad since the health reduced is low
                    save_to_csv(input_state + output)
                else:
                    print("didn't save last move")
                break
            continue
        
        
        # turn finishes here any iteration after the first iteration.
        if not isFirstIteration:
            # calculate reward.
            reward = (enemy_hp_before - get_enemy_hp()) / get_enemy_max_hp()
            print("Reward: " , reward)
            output2 = [reward]
            input_state = get_state(chosen_move)
            save_to_csv(input_state + output2)            
            randomise_player_type()
            randomise_enemy_type()
            
        # ai chooses move
        move_allowed = False
        while not move_allowed:
            chosen_move = random.randint(0,3)
            move_allowed = check_pp(chosen_move)
        
        enemy_hp_before = get_enemy_hp()
        
        # code to press the move button, either through button presses or memory manip
        chosen_move_id = pyboy.memory[(0xD01C + chosen_move)]
        print("Move Chosen ID: ", chosen_move_id)
        pyboy.tick(15)
        # time.sleep(4)
        pyboy.button('a')
        pyboy.tick(15)
        
        for i in range(current_move):
            pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
            pyboy.tick(30)
            pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
            pyboy.tick(30)
            # time.sleep(0.5)
            
        
        pyboy.tick(15)
        # time.sleep(2)
        
        for i in range(chosen_move):
            pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
            pyboy.tick(30)
            pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
            pyboy.tick(30)
            # time.sleep(0.5)
            

        current_move = chosen_move
        pyboy.tick(15)
        # time.sleep(4)
        
        pyboy.button('a')
        move_used_id = pyboy.memory[0xCFD2]
        print("Move used ID: ", move_used_id)
        assert move_used_id == chosen_move_id # in this case perhaps remove any data assossiated with this battle as the training data will be wrong.
        # perhaps here assert that all of the stat changes have remained the same
        
        # determine reward based on enemy hp change.

        # repeat.
        isFirstIteration = False
    

for i in range(50):
    try:
        if pyboy.tick():
            run_battle()
    except AssertionError:
        continue

# while pyboy.tick():
#     print(f"{pyboy.memory[0xCFD3]:2f}", end='\r')
#     pass

pyboy.stop(save=False)
