# Networked chatroom-based coordination game

This is a networked coordination game where players broadcast messages to each other and try to make the same decision as others.

MORE DETAILS ON THE MEMORYEXPTS:

-----------First, `memoryexpt v1`:

Background: 
- This experiment is examining the phenomenon of "collaborative memory", the idea that sometimes people remember things (events, cultural history, etc.) in groups rather than by themselves. 
- Here we're dealing with the simplified problem of testing whether people remember more words when they're recalling words in groups, or by themselves. In the first part of the experiment, we test people in groups of 2,3,4,8, and 16 (the `collaborative` condition), and then test equivalent numbers of people alone (the `nominal` condition). In the `collaborative` condition, all words participants recall are sent to all other participants, whereas in the `nominal` condition, recalled words are not transmitted to anyone. In the end, we compare the number of words recalled in the `collaborative` and `nominal` conditions in the analysis. 
- In the second part of the experiment, we're interested in how word recall is affected by putting people in networks (`network` condition). Thus, we put people in two types of networks (34 people in each KarateClub network and 34 people in each SmallWorld network), and have them recall words, but their recalled words are only shared with randomly-chosen people in their network. The end goal is to see whether other people's words "trigger" the participant's memory and increase their own word recall. 

Experiment Layout:
- The experiment progresses as follows. Participants accept the ad, pass through the consent page, pass through the instructions, and then are directed to a waiting room. They wait in the waiting room until quorum has been reached-- 1 person (`nominal` condition), {2,3,4,8,or 16 people} (`collaborative` condition), or 34 people (`network` condition)-- then advance to the main experiment. 
- Having advanced, participants then see 60 words-- randomly chosen without replacement from a list of 200 words-- presented for 2 seconds each. (I normally have this set to a lower number for testing purposes because 60 words takes a while. This is set in `experiment.py`, line `expt_wordlist = random.sample(wordlist,60)`.) 
- Participants then complete a distraction task (to reduce recent memory effects) where they answer 10 math questions for 30 seconds. I call this `fillertask` in the code-- you can find it in `exp.html` as `<div id="fillertask-form" style="display:none;">`, and you can adjust the amount of time the fillertask is shown in `experiment.js` on the line with `showFillerTask = function() `. The results from the fillertask are logged in `question.csv`.
- Finally, participants are dumped into the chatroom. They are asked to recall as many words as possible. They can type words, and these words will appear on a main thread that is visible to other participants (the participant's submitted words will appear in blue, everyone else's will appear in black). Participants are not allowed to submit words that are already present on the main thread (we disable the submit button), and all words are converted to lower case and not allowed to use spaces. Results are logged in `infos.csv`: the original wordlist from the source, and then all of the words submitted by participants. With regards to who sees which words... If I'm running a `collaborative` condition, I set up a FullyConnected network here, if I'm running a `nominal` condition, I set up an Empty network here, and if I'm running a `network` condition, I start with an Empty network and manually add in the desired links in `experiment.py`. 
- Participants can exit the chatroom by pressing the "I can't recall any more" button, after which they get sent to a perfunctory questionnaire and are paid. 
- Standard chatroom rules apply: I usually overrecruit 2x or 3x, and those participants get directed to the end of the experiment and paid anyway (and not logged on qualifications, I believe :)). Qualifications are important, since the total number of participants ~2000 and people like repeating this one.

Summary:
- That's `memoryexpt v1`. I want to keep this version as a separate, working copy since I anticipate running 2000 participants on this version of the experiment, and another 2000 participants on the second version of the experiment. 
- Code is at: `https://github.com/mongates/mongates_dallinger_demos/tree/master/memoryexpt`. This is currently running using python 2, on the master branch, dallinger 4.0.0

-----------Second, `memoryexpt v2`:

Background:
- `memoryexpt v2` is very similar to `memoryexpt v1`, but while `memoryexpt v1` was based on a modeling paper (Luhmann and Rajaram 2015), `memoryexpt v2` is going to be based more on the empirical papers in the collaborative memory literature. Thus, `memoryexpt v2` incorporates two changes: 1) possibility of turn-taking, and 2) words being read aloud. 

Experiment:
-  `memoryexpt v2` is identical to `memoryexpt v1` except for the following changes: 1) allowing turn-taking in chatrooms for FullyConnected networks, and 2) words being read aloud within chatrooms.

--- Turn-taking. 
- Instead of letting participants write in the chatroom whenever they'd like, in the `collaborative` condition, force participants to take turns submitting words. 
- In `nominal` conditions (Empty networks), there is no need to do turn-taking, since there is only one person in each network.
- In `collaborative` conditions (FullyConnected networks), enforce turn-taking. 
- In `network` conditions (custom-designed Networks in which some nodes are more highly connected than others), disable turn-taking and allow free-response, because I have no idea how you'd enforce turn-taking when you basically have individuals in a bunch of overlapping networks. 
--> Specifically, disable each participant's "Send" button in the chatroom until it is their turn. As soon as a) it has been been five seconds, or b) they've attempted to submit a word by pressing the "Send" button or hitting Enter on the keyboard, re-disable the "Send" button. 
- If they attempted to submit a word but didn't actually (because participants can't submit words that are repetitions of previous words, or contain spaces)... I think the desired behavior is that you count that as their turn (so disable their submit button), but don't display their attempt on the main thread or in the info table (this is already true that failed attempts don't get sent and don't displayed in the info table.) However, if it's easier to implement the following solution-- ignore the attempt and let it be their turn for the full five seconds-- then that seems fine as desirable behavior; I'm not firmly committed either way.
- Also put in a "Pass" button so that participants can skip their turn if they want.
--> Procedurally, turn-taking should happen in random order within each round. So we should be doing random sampling for the nodes, without replacement, and when all nodes have been selected restart that loop. Participants are going to be systematically dropping out throughout the experiment, so we should be sampling randomly from the REMAINING nodes, if that's possible. I'm not sure how feasible the above is... the thing I'm trying to avoid with this "remaining nodes" idea is this scenario: it's a 16-person experiment, 15 participants have dropped out so the last person is waiting for their turn to submit words, and they have to wait 15x5 seconds every time they want to submit a new one. 
--> To avoid participants dropping out, create a bonus variable that's awarded based on the number of words submitted by the `collaborative` condition group (from my notes, the Slack thread here on performance-based bonuses is here: https://dallinger.slack.com/archives/C4F24KPNC/p1528062461000050). This should be added on top of the existing time-based bonus for sitting in the waiting room (that should be easy, just adding those two bonus types together). 
- I don't think there needs to be a bonus for "words recalled" in the `nominal` condition (which would be easy to implement) and the `network` condition (seems annoying to implement), though if it makes sense to do across experiments that's fine too. 
- It'd be super lovely if there was a fix on the time-based chatroom bonuses, such that if people were _in the chatroom_ they got paid, rather than the current version which is "paid as long as they are _in the chatroom + doing the rest of the experiment_". I don't really expect that to be fixed anytime soon... (Though maybe it already is? Or is in the works or something? That'd be great because I can see the possibility that people are just going to let this experiment hang for ages and then get paid a LOT, depending on how fast I have the experiment expire.)
- Note to self: edit the instructions and payment accounts to account for a new bonus, and all of the changes above and below.
--> (Optional) Text that says "It's your turn!" appropriately

--- Reading words aloud.
--> In reading words aloud, if a participant types a word, read it aloud to all of the destination_ids (but not to the origin_id). 
- Attempt to read all submitted words aloud, even if they are nonsense. This implies some javascript plug-in that does text to speech (I actually like the settings on the following link, and it seems to read all of my words okay and quickly. https://codepen.io/SteveJRobertson/pen/emGWaR).
- Continue writing words visually to the main thread, as exists already. 
- If words are being received quickly, enforce a 1 second pause between the reading of each word. 
--> The above rules apply for all conditions (`nominal`, `collaborative`, and `network`). Details if you'd like to read: 
- In the `nominal` condition, no words need to be read out loud because there are no destination_ids. (Continue writing the words visually to the main thread, as exists already.) 
- In the `collaborative` condition, all words received (...which is going to be all words since it's a FullyConnected network) should be read out loud. Submitted words should not be read out loud to that participant. (Continue writing the words visually to the main thread, as exists already.) 
- In the `network` condition, it's the same situation as in the `collaborative` condition, where all words received should be read out loud, submitted words should not, and words should continue being written visually as well. (I don't have full confidence in the recorded voice, so I think that it's fine that things are also written visually, but hearing words audibly forces participants to acknowledge the words.) We might have the problem here of words coming in very quickly-- enforce a 1 second pause between received words. (Alternatively, there's an argument to be made that the words shouldn't be displayed, especially in this condition, to give participants incentive to listen instead of just read, and then we'd allow participants to write down words they heard. This seems bad (and also annoying to implement), so I think we ignore this possibility.)
--> Have a sound check in the beginning of the experiment, to check that participants' speakers are working, probably on the instructions page. I think I?m hoping for something like a button that says ?Click here to listen to the sentence. Please type the sentence you heard? and only if they type the sentence correctly do they advance to the next screen.
--> (Optional) Maybe test participants at the end with a sentence that was read aloud, to enforce that they kept their speakers on.
