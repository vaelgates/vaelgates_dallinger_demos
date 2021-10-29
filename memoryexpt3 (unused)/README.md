# Empirical Tests of Large-Scale Collaborative Recall

Background: 
- This experiment is examining the phenomenon of "collaborative memory", the idea that sometimes people remember things better (events, cultural history, etc.) in groups rather than by themselves. 
- Here we're dealing with the simplified problem of testing whether people remember more words when they're recalling words in groups, or by themselves. In the first part of the experiment, we test people in groups of 2,3,4,8, and 16 (the `collaborative` condition), and then test equivalent numbers of people alone (the `nominal` condition). In the `collaborative` condition, all words participants recall are sent to all other participants, whereas in the `nominal` condition, recalled words are not transmitted to anyone. In the end, we compare the number of words recalled in the `collaborative` and `nominal` conditions in the analysis. 
- This experiment builds on `memoryexpt2` by adding in Zoom, with some additional changes. (Note we are not running the network studies anymore.)

Experiment Layout:
- The experiment progresses as follows. Participants accept the ad, pass through the consent page, pass through the instructions, and then are directed to a waiting room. They wait in the waiting room until quorum has been reached-- 1 person (`nominal` condition), {2,3,4,8,or 16 people} (`collaborative` condition), or 34 people (`network` condition)-- then advance to the main experiment. 
- Having advanced, participants then see 60 words-- randomly chosen without replacement from a list of 200 words-- presented for 2 seconds each.  
- Participants then complete a distraction task (to reduce recent memory effects) where they answer 10 math questions for 30 seconds. 
- Finally, participants enter into the chatroom. They are asked to recall as many words as possible. They can type words, and these words will appear on a main thread that is visible to other participants (the participant's submitted words will appear in blue, everyone else's will appear in black). Participants are not allowed to submit words that are already present on the main thread (the submit button is disabled), and all words are converted to lower case and not allowed to use spaces.
- Participants will have Zoom open simultaneously, and in the collaborative condition are encouraged to chat with fellow participants. 
- Participants can exit the chatroom by pressing the "I can't recall any more" button, after which they get sent to a perfunctory questionnaire and are paid. 
- Any words that sent to a participant from another participant are read aloud. 
- There is a possibility of turn-taking in some conditions, in which participants can only write words when it is their turn. 

Conditions:
- There are three variables controlling condition, that are manipulatable in the config file: "mexp_topology", "mexp_turn_type", and "mexp_transmission_mode".
- There is "mexp_turn_type", which describes whether there is turn-taking in the game, or whether all participants can contribute words freely. The choices are: `free` (no turn-taking), `fixed_turns` (there's a fixed order of turns, e.g. participant 1 always goes first, participants 2 always goes second), and `random_turns` (all of the participants have a turn within a round, but the order changes between rounds). Example: mexp_turn_type = free. Turn-taking is only allowed within collaborative games, not nominal or network games.
- There is "mexp_topology", which describes whether the experiment is a collaborative experiment, a nominal experiment, or a network experiment. The choices are: `nominal`, `collaborative`, `karateclub`, and `smallworlda` where the last letters are "a" through "p", depending on what smallworld network you'd like. `baby2` and `baby4` are also available topologies, and you can define any topology you wish within the `topologies.py` file. Note that you specify the number of participants in the `experiment.py` file for each of these topologies. Example: mexp_topology = collaborative. 
- There is "mexp_transmission_mode", which describes how messages from participants are being sent to other participants (nodes). The choices are: `promiscuous` (messages are sent to all other nodes connected to the sending node) and `random` (messages are sent to a random neighboring node). The collaborative experiments usually use promiscuous sending and the network experiments usually use random sending, though both options are available for all experiment topologies. Example: mexp_transmission_mode = promiscuous.
- There is also a new variable "mexp_zoomroom", which describes which zoom link participants are given.