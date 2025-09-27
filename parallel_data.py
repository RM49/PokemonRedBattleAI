
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

import threading

MAX_MOVE_ID = 165 # 1-165 inclusive
REMOVED_MOVES = [20, 99, 128, 144]
moves = [x for x in range(1,MAX_MOVE_ID+1) if x not in REMOVED_MOVES] 
TYPE_IDS = [0, 1, 2, 3, 4, 5, 7, 8, 20, 21, 22, 23, 24, 25, 26]
MAX_TYPE_ID = len(TYPE_IDS) # 0-26, although i think 0 can be ignored since normal is repeated so much
MAX_MOVE_EFFECT = 86
DATA_FILE = "pokemon_data_parallel.csv"
quiet = "--quiet" in sys.argv
data_to_save = []
list_lock = threading.Lock()
time_started = time.time()

def save_to_csv(data):
        with open(DATA_FILE, 'a', newline='') as datafile:
            writer = csv.writer(datafile)
            writer.writerow(data)

class TimeoutException(Exception):
    def __init__(self, message="Timeout"):            
        # Call the base class constructor with the parameters it needs
        super().__init__(message)


class battle(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.pyboy = PyBoy('pokemon.gb', window="null")
        self.pyboy.set_emulation_speed(0)
        self.data_buffer = []
    
    def get_player_hp(self):
        return self.pyboy.memory[0xD016]

    def get_player_max_hp(self):
        return self.pyboy.memory[0xD024]

    def get_player_types(self): # list len 2
        return self.pyboy.memory[0xD019:0xD01B]

    def get_player_move_ids(self):
        return self.pyboy.memory[0xD01C:0xD020]

    def get_player_move_details(self):
        # We want to list the info related to each move
        move_details = []
        for i in self.get_player_move_ids():
            if i == 0: # no move in the slot
                continue
            start_addr = (i - 1) * 6
            end_addr = start_addr + 6
            move_details.append(self.pyboy.memory[14, start_addr:end_addr])
        return move_details # list of list len 5, [move_id, effect, base_power, type, accuracy, (max?)pp]

    def check_pp(self, move_no): # hehe
        return (self.pyboy.memory[(0xD02D) + move_no] > 0)
        
    def maximise_pp(self): # hehe
        self.pyboy.memory[0xD02D:0xD031] = [a.pop(5) for a in self.get_player_move_details()]

    def get_enemy_hp(self):
        return self.pyboy.memory[0xCFE7]

    def set_enemy_hp(self, hp):
        self.pyboy.memory[0xCFE7] = hp

    def get_enemy_max_hp(self):
        return self.pyboy.memory[0xCFF5]

    def get_enemy_types(self):
        return self.pyboy.memory[0xCFEA:0xCFEC]

    def randomise_player_moves(self):
        self.pyboy.memory[0xD01C:0xD020] = random.sample(moves, 4)
        self.maximise_pp()
        
    def randomise_player_level(self):
        self.pyboy.memory[0xD022] = random.randint(1,100)

    def randomise_player_type(self):
        type1 = random.choice(TYPE_IDS)
        self.pyboy.memory[0xD019] = type1
        if random.randint(1,3) == 1:
            # same type guranteed
            self.pyboy.memory[0xD01A] = type1
        else:
            type2 = random.choice(TYPE_IDS)
            self.pyboy.memory[0xD01A] = type2

    def randomise_enemy_type(self):
        type1 = random.choice(TYPE_IDS)
        self.pyboy.memory[0xCFEA] = type1
        
        if random.randint(1,3) == 1:
            # same type guranteed
            self.pyboy.memory[0xCFEB] = type1
        else:
            type2 = random.choice(TYPE_IDS)
            self.pyboy.memory[0xCFEB] = type2 

    def get_player_attack(self):
        return self.pyboy.memory[0xD026]

    def get_player_special(self):
        return self.pyboy.memory[0xD02C]

    def get_enemy_defence(self):
        return self.pyboy.memory[0xCFF9]

    def get_enemy_special(self):
        return self.pyboy.memory[0xCFFD]    

    def buff_player(self):
        self.pyboy.memory[0xD024] = 225 # max hp
        self.pyboy.memory[0xD016] = 225 #hp

    def type_mask(self, v):
        t = [0] * (MAX_TYPE_ID + 1)
        t[TYPE_IDS.index(v)] = 1
        return t
        
    def get_state(self, move_no):
        state = []
        
        # Player related state
        player_types = self.get_player_types()
        state += self.type_mask(player_types[0])
        state += self.type_mask(player_types[1])
        
        # Enemy related state
        enemy_types = self.get_enemy_types()
        state += self.type_mask(enemy_types[0])
        state += self.type_mask(enemy_types[1])
        
        # Moves related state
        move_details = self.get_player_move_details()
        # [[]] [ [move_id, effect, base_power, type, accuracy, (max?)pp],  [move_id, effect, base_power, type, accuracy, (max?)pp] ...]
        l = move_details[move_no]
        
        # state.append(l[1] / MAX_MOVE_EFFECT) # Effect state
        state.append(l[2] / 255) # Base Power
        state += self.type_mask(l[3]) # type
        state.append(l[4] / 255) # accuracy
        
        return state

    def run(self):
        with open("pokemon.gb.state", "rb") as sav:
            self.pyboy.load_state(sav)

        self.pyboy.memory[0xD358] = 0 # no delay between text being written
        self.pyboy.memory[0xD355] += 0x80 # battle animation off
        loop = True # can control testing here.
        self.pyboy.tick(120) # load the battle
        
        self.randomise_player_moves()
        self.buff_player()
        
        current_move = 0
        isFirstIteration = True
        chosen_move = 0

        while loop:
            
            self.pyboy.memory[0xCFFF] = 0 # i dont want bulbasaur using growl, sets growl pp to 0

            loop = self.pyboy.tick()

            # spam 'a' button until 0xCC30 is 193 again
            if self.pyboy.memory[0xCC30] != 193: # avoids the case where a move lasts more than one turn
                
                if time.time() > time_started + 30: # sometimes ends up in endless loop of clicking and exiting items
                    raise TimeoutException()
                
                self.pyboy.button('a', 2)
                self.pyboy.tick(2)
                if self.get_enemy_hp() <= 0 or self.get_player_hp() <= 0:
                    
                    # final reward is here
                    reward = (enemy_hp_before - self.get_enemy_hp()) / self.get_enemy_max_hp()
                    # print("Reward: " , reward)
                    output = [reward]
                    input_state = self.get_state(chosen_move)
                    print("battle done")
                    if reward > 0.2: # trying to remove the cases where a really good move is used when the enemy is at low hp, which makes the move look bad since the health reduced is low
                        self.data_buffer.append(input_state + output)
                    else:
                        print("didn't save last move")
                    break
                continue
            
            
            # turn finishes here any iteration after the first iteration.
            if not isFirstIteration:
                # calculate reward.
                reward = (enemy_hp_before - self.get_enemy_hp()) / self.get_enemy_max_hp()
                output2 = [reward]
                input_state = self.get_state(chosen_move)
                self.data_buffer.append(input_state + output2)            
                self.randomise_player_type()
                self.randomise_enemy_type()
                
            # ai chooses move
            move_allowed = False
            while not move_allowed:
                chosen_move = random.randint(0,3)
                move_allowed = self.check_pp(chosen_move)
                any_allowed = False
                for i in range(4):
                    if self.check_pp(chosen_move):
                        any_allowed = True
                if not any_allowed:
                    raise TimeoutException()
            
            enemy_hp_before = self.get_enemy_hp()
            
            # code to press the move button, either through button presses or memory manip
            chosen_move_id = self.pyboy.memory[(0xD01C + chosen_move)]
            # print("Move Chosen ID: ", chosen_move_id)
            self.pyboy.tick(15)
            # time.sleep(4)
            self.pyboy.button('a')
            self.pyboy.tick(15)
            
            for i in range(current_move):
                self.pyboy.send_input(WindowEvent.PRESS_ARROW_UP)
                self.pyboy.tick(30)
                self.pyboy.send_input(WindowEvent.RELEASE_ARROW_UP)
                self.pyboy.tick(30)
                
            
            self.pyboy.tick(15)
            
            for i in range(chosen_move):
                self.pyboy.send_input(WindowEvent.PRESS_ARROW_DOWN)
                self.pyboy.tick(30)
                self.pyboy.send_input(WindowEvent.RELEASE_ARROW_DOWN)
                self.pyboy.tick(30)
                
            current_move = chosen_move
            self.pyboy.tick(15)
            
            self.pyboy.button('a')
            move_used_id = self.pyboy.memory[0xCFD2]
            # This assertion is just a way to ensure nothing has gone wrong with the user choosing the move. It happens from time to time and in that case its output is just ignored as the data would be wrong.
            assert move_used_id == chosen_move_id # in this case remove any data assossiated with this battle as the training data will be wrong.
            
            # repeat.
            isFirstIteration = False
            
        self.pyboy.stop(save=False)
        global data_to_save
        with list_lock:
            data_to_save += self.data_buffer

for i in range(100):
    time_started = time.time()
    threads = []

    for i in range(100):
        threads.append(battle())
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for d in data_to_save:
        save_to_csv(d)

    d = []
    
print("done!!")