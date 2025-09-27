
#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import os
import sys
import time

from pyboy import PyBoy
from pyboy.utils import WindowEvent 

quiet = "--quiet" in sys.argv
pyboy = PyBoy('pokemon.gb', window="null" if quiet else "SDL2", scale=3)
pyboy.set_emulation_speed(1)

with open("pokemon.gb.state", "rb") as f:
    pyboy.load_state(f)

print(pyboy.memory[0xD014]) # Prints pokemon number
print(pyboy.memory[0xD015:0xD017]) # Prints pokemon hp
print(pyboy.memory[0xD023:0xD025]) # prints max hp
print(pyboy.memory[0xD019:0xD01B]) # Prints pokemons 2 types
print(pyboy.memory[0xD01C:0xD020]) # Prints the list of move IDs in decimal.

# We want to list the info related to each move
move_ids = pyboy.memory[0xD01C:0xD020]
move_ids = range(1,165)
for i in move_ids:
    if i == 0: # no move in the slot
        continue
    # print("id: " + str(i))
    start_addr = (i - 1) * 6
    end_addr = start_addr + 6
    # print(start_addr, end_addr)
    print(pyboy.memory[14, start_addr:end_addr][3]) # gives 5 vals eg: [39, 0, 35, 0, 242, 35] => [move_id, effect, base_power, type, accuracy, (max?)pp], assumed the position of effect and type based on Battle RAM
                    # moves are stored in bank E  maybe effect is physical/special
print("done")

print(pyboy.memory[0xD015:0xD017]) # current HP player
print(pyboy.memory[0xD023:0xD025]) # max HP player
# pyboy.memory[0xD016] = 100, pyboy.memory[0xD024] = 100 so this sets current and max hp to 100
# pyboy.memory[0xD024] = 100 this one changes max hp
# pyboy.memory[0xD023] = 0 not sure abt this one..

print(pyboy.memory[0xCFE6:0xCFE8]) # enemy hp
print(pyboy.memory[0xCFF4:0xCFF6]) # max enemy hp
print(pyboy.memory[0xCFEA:0xCFEC]) # enemy 2 types


# pyboy.memory[0xD018] = 0x10 this burns the players current pokemon :O 
# pyboy.memory[0xD01C] = 0x3F # this sets squirtles move 1 to thunderpunch
pyboy.memory[0xD358] = 0 # no delay between text being written

print(pyboy.memory[0xD18F:0xD191]) # attack to 200?
# pyboy.memory[0xD026] = 200
# pyboy.memory[0xD02C] = 200
# pyboy.memory[0xD190] = 200
# pyboy.memory[0xD196] = 200

while pyboy.tick():
    
    # CCDB - Move menu type : 0 is regular, 1 is mimic, other are text boxes (learn, PP-refill...)
    # FFF3 - Battle turn (0-1 = player-opponent)
    # if pyboy.memory[0xFFF3] != 0:
    #     pyboy.button_press('a')
    # print(pyboy.memory[0xD026], end='\r') # the attack stat only seems to increase when its being printed?
    print(f"{pyboy.memory[0xCC30]:2f}", end='\r') # 193 is fight menu button, so after picking a move perhaps it can spam 'a' until it becomes 193 again.
    
    # ai chooses move
    
    # code to press the move button, either through button presses or memory manip
    
    # spam 'a' button until 0xCC30 is 193 again
    
    # determine reward based on enemy hp change.
    
    # repeat.
    
    
    pass

pyboy.stop(save=False)
