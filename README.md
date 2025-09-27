# PokemonRedBattleAI
Model to predict what move in a gen 1 battle would deal the most damage.

Video of it working: TODO

main.py -> original script used to experiment with pyboy
collect_data.py -> original data collection script
parallel_data.py -> data collection with concurrency, many times faster
train.py -> trains the model
play.py -> allows playing of the game and outputs its chosen move in each round of a battle in the terminal

Description:
The data collection script runs many battles, in each battle the moves of the player are randomised and in each round of the battle the types of the player and enemy are randomised.
The script chooses moves at random and after each move is used the result is saved to a csv.
The row of data saved includes data about the type of the player, type of the enemy, move data including type, power and accuracy then the percentage of enemy hp that was reduced.
A model is then trained to predict hp reduction.
The model in the video had ~700k rows of data that it trained on. It showed understanding of 1) using moves that do damage 2) type effectiveness 3) STAB (boosted damage for using the same type move as the player is)
The way I have trained it is to only focus on one round of battle rather than long term strategy. A very greedy strategy, as a new player would use.

More detailed log of development:
The original model took info about the stats of each pokemon, this proved to be unnessessary and would have lead to it taking much longer to learn. I switched to focusing on trying to get it to understand type effectiveness.
The original neural net would have taken 4 moves and outputted the values for all 4 in one go. After trying to figure out how to handle the missing data of the 3 non-chosen moves with custom loss function I realised its much simpler to just handle one move at a time.
The quick realisation about pokemon is that there is endless nuance in the game. From watching the collecting script run I removed moves from the random selection that messed with the timings. These were identified by using an assertion to check that the move that was being used (seen in the games memory) is the same as the intended move to be used. Along with that a timeout error was added as occasionaly the program would infinitely loop.
Adding concurrency was probably the best move, the amount of data I could gather went up dramatically.

I really enjoyed having to deal with the emulators memory directly. I had to experiment with what data is where and build an understanding on how the game represented different values. Getting data out of the games ROM, say for move IDs to know which ones were problematic or type IDs, felt very sophisticated.
