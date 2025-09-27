#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import tensorflow as tf
import sys
import csv
from pyboy import PyBoy
from pyboy.utils import WindowEvent
import numpy as np

quiet = "--quiet" in sys.argv
pyboy = PyBoy('pokemon.gb', window="null" if quiet else "SDL2", scale=3)
pyboy.set_emulation_speed(1)

TYPE_IDS = [0, 1, 2, 3, 4, 5, 7, 8, 20, 21, 22, 23, 24, 25, 26]
MAX_TYPE_ID = len(TYPE_IDS) # 0-26, although i think 0 can be ignored since normal is repeated so much
MAX_MOVE_EFFECT = 86

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

def check_pp(move_no):
    return (pyboy.memory[(0xD02D) + move_no] > 0)
    
def get_enemy_hp():
    return pyboy.memory[0xCFE7]

def get_enemy_max_hp():
    return pyboy.memory[0xCFF5]

def get_enemy_types():
    return pyboy.memory[0xCFEA:0xCFEC]
    
def type_mask(v):
    t = [0] * (MAX_TYPE_ID + 1)
    t[TYPE_IDS.index(v)] = 1
    return t
    
def get_state(move_no):
    state = []
    
    # Player related state
    player_types = get_player_types()
    state += type_mask(player_types[0])
    state += type_mask(player_types[1])
    
    # Enemy related state
    enemy_types = get_enemy_types()
    state += type_mask(enemy_types[0])
    state += type_mask(enemy_types[1])
    
    # Moves related state
    move_details = get_player_move_details()
    l = move_details[move_no]
    
    state.append(l[2] / 255) # Base Power
    state += type_mask(l[3]) # type
    state.append(l[4] / 255) # accuracy
    
    return state

DATA_FILE = "pokemon_data_parallel.csv"
INPUT_LENGTH = 0
with open(DATA_FILE, newline='') as f:
    reader = csv.reader(f)
    INPUT_LENGTH = len(next(reader)) - 1

model = tf.keras.models.Sequential([
  tf.keras.layers.Normalization(input_shape=[INPUT_LENGTH]),
  tf.keras.layers.Dense(128, activation='relu'),
  tf.keras.layers.Dropout(0.2),
  tf.keras.layers.Dense(64, activation='relu'),
  tf.keras.layers.Dense(16, activation='relu'),
  tf.keras.layers.Dense(1)
])

model.load_weights('pokmonmodel.weights.h5')

with open("pokemon.gb.state", "rb") as sav:
        pyboy.load_state(sav)

pickingMove = False
while pyboy.tick():
    if not pickingMove and pyboy.memory[0xCC30] == 193:
        # pick move

        num_moves = len(get_player_move_details())
        
        best_move = 0
        highest_output = 0.0
        
        for i in range(num_moves):
            if check_pp(i):
                # output from nn
                inp = get_state(i)
                inp_batch = [inp]
                output = model.predict(np.array(inp_batch))
                if output > highest_output:
                    best_move = i
                    highest_output = output
        
        print(f"Suggested Move: {best_move}")
        
        pickingMove = True
        
    if pyboy.memory[0xCC30] != 193:
        pickingMove = False
    