# DEFAULT_BASE_BRANCH ELIV

Imagine you have a special folder with lots of files inside, like a big box of toys. This folder is like a special place where you keep all your important work.

The "DEFAULT_BASE_BRANCH" is like a special key that helps find the main room in the box. It's like saying, "Hey, I want to go to the main room where all the important toys are kept." 

It helps some other helpers (like the ones in vivarium/scout/audit.py, vivarium/scout/git_analyzer.py, and vivarium/scout/ignore.py) know where to look for the main room, so they can do their jobs correctly.
---

# DEFAULT_HOURLY_SPEND_LIMIT ELIV

Imagine you have a piggy bank where you save your money. This special number, 5.0, is like a rule that says how much money you can spend in one hour. It's like a key that helps decide if you can buy something or not.
---

# DEFAULT_MIN_CONFIDENCE ELIV

Imagine you have a special tool that helps you find things you want. It's like a super smart magnifying glass. 

This tool has a special setting that says "I only want to show you things that are really sure about". And it sets that setting to 70%. 

So, when the tool looks for things, it only shows you the ones that are 70% or more sure about what they found. It's like a filter that helps you see only the things that are really certain.
---

# _check_tldr_coverage ELIV

Imagine you have a big box of toys, and inside the box, there are lots of small boxes with different toys in them. This function is like a helper that checks each small box to see if it has a special note called a ".tldr.md" note.

If the small box has a note, it's okay. But if it doesn't have a note, the helper writes down a message saying "Hey, this small box is missing a note!" and puts it in a list.

Then, the helper looks at the list and says, "If there are no messages in the list, everything is okay!" But if there are messages, it means some small boxes are missing notes, and the helper returns those messages so we can fix the problem.
---

# _check_draft_confidence ELIV

Imagine you have a special box where you keep track of things that happen. This box is like a diary. 

This function is like a helper that checks the diary to see if there are any problems. 

It looks at the diary for a certain amount of time (like the last day or last week). 

It checks each thing that happened in that time to see if it's a problem. 

If it finds a problem, it writes it down in a list. 

Then, it tells you if there are any problems or not, and shows you the list of problems. 

It's like a key that helps you find out if everything is okay or not.
---

# _check_hourly_spend ELIV

Imagine you have a piggy bank where you save your money. This special helper checks if you spent too much money in one hour. 

It looks at how much money you spent in the last hour and compares it to a special number called the "limit". If you spent more than the limit, it says "no" and tells you how much you spent and what the limit was. If you didn't spend too much, it says "yes" and doesn't tell you anything.
---

# _check_draft_events_recent ELIV

Imagine you have a special box where you keep track of all the things that happen in a project. This box is like a diary where you write down every little thing that happens.

This function is like a helper that checks the diary to see if anything important happened in the last few hours. It's looking for a special kind of note called "commit_draft". If it finds one, it says "yes, everything is okay!" If it doesn't find one, it says "oh no, something might be broken!"
---

# run_ci_guard ELIV

Imagine you have a big box of toys, and you want to make sure everything inside the box is okay before you open it. This special tool, called "run_ci_guard", helps you do that.

It checks three things:

1. Are there any toys that are broken or missing?
2. Are there any toys that are not in the right place?
3. Are there any toys that you haven't played with in a long time?

If you want to make sure that all the toys you haven't played with recently are still in the box, this tool will also check that.

If everything is okay, it says "yes, the box is fine!" If not, it tells you what's wrong.
---

# main ELIV

Imagine you have a special tool that helps you check if everything is okay with your project. This tool is like a key that opens a door to make sure everything is working correctly.

The "main" function is like the key that opens the door. It's the first thing that happens when you use the tool. It asks you some questions, like:

- What's the name of the special branch in your project?
- How much money can we spend on this project each hour?
- How confident are we that our project is good enough?
- Did we make any changes to our project recently?

It then uses the answers to these questions to check if everything is okay. If it finds any problems, it tells you what's wrong. If everything is okay, it says "yes, everything is fine!"

The "main" function is like a guardian that makes sure your project is healthy and working correctly.