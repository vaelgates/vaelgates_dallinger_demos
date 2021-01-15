# Squares game

Game flow: 
- A participant gets recruited, reads the instructions, goes onto the main game, then receives payment, with a bonus for getting questions right. 
- The participant (Human) and the computer (Robot) iteratively choose squares on a 3x3 grid, in order to to complete a row or complete a column. 
- There are 12 trials. There are six possible rows/columns to complete (these are called "goals" or "thetas"-- row1, row2, row3, col1, col2, col3) so there are six trials. Then the number of trials is doubled because the Human will play against two types of Robots ("Schelling" and "Normal", aka "condition"), for a total of 12 trials. Trials are randomly intermixed. (The vectors in the code are often called "theta_cond_pairs" meaning the 12 goal / condition pairs.)

More detailed: 
- The participant sees a pattern they need to complete on the right of the screen (either filling in three squares in a row or three squares in a column). This is saved as the "goaltable" in the code. 
- On the left of the screen is the main grid, saved as the "maintable" in the code. In the main table, the participant (Hplayer, human player) chooses a square, and then the computer (Rplayer, robot player) chooses a square. The Human and Robot play iteratively until the goal pattern is achieved. The Human always goes first.
- The cover story is that only the Human knows the end goal, while the Robot has to infer what the end goal is from the Human's first action. 
- The Human will play against two different Robots-- one a "Schelling Robot", and one a "Normal Robot". The actions of the "Schelling Robot" and the "Normal Robot" are described in two matrices which are included in the javascript code. The "Schelling Robot" is better at inferring the Human's goal from the Human's first action then the "Normal Robot" is. (Though right now I don't actually have the correct matrices, just random numbers, so both Robots are taking dumb actions and can in fact choose the same squares that have already been chosen. This will not be true in the real game.)
- To incentive the Human to accurately convey their intent, if the Human and Robot complete the pattern in the minimum number of turns (3 turns), the participant gets a bonus of .05 dollars every time they successfully complete a grid.

