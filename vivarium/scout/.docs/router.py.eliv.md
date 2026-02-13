# logger ELIV

Imagine you have a big notebook where you write down important messages. The 'logger' is like a special pen that helps you write those messages in the notebook.

It's job is to write down things that happen in the program, like "I did this" or "I found a problem". This way, you can see what the program is doing and fix any mistakes.

The 'logger' talks to many other parts of the program, like different rooms in a big house. It helps them work together and share information.
---

# TOKENS_PER_SMALL_FILE ELIV

Imagine you have a big box of toys, and inside the box, there are lots of small bags of toys. Each bag can hold a certain number of toys before it gets too full.

'TOKENS_PER_SMALL_FILE' is like a rule that says how many toys can fit in each small bag. In this case, the rule says each small bag can hold 500 toys. It helps keep track of things so they don't get too messy or hard to manage.
---

# COST_PER_MILLION_8B ELIV

Imagine you have a big box of toys that cost a lot of money. The box has 1 million toys in it, and each toy costs a little bit of money. 

The 'COST_PER_MILLION_8B' is like a secret code that tells us how much money we need to buy all the toys in the box. It's like a key that helps us figure out the total cost. 

In this case, the key says that if we have 1 million toys, we need to spend 20 cents to buy them all.
---

# COST_PER_MILLION_70B ELIV

Imagine you have a big box of toys that cost a lot of money. This number, 'COST_PER_MILLION_70B', is like a secret code that helps figure out how much money each toy costs. It's like a key that helps unlock the price of each toy.
---

# BRIEF_COST_PER_FILE ELIV

Imagine you have a piggy bank where you save money. This special number, 'BRIEF_COST_PER_FILE', is like a tiny coin that gets added to your piggy bank every time someone looks at a file. It's like a small fee for checking the file.
---

# TASK_NAV_ESTIMATED_COST ELIV

Imagine you have a big box of toys, and you want to know how much it will cost to buy all the toys in the box. 

The "TASK_NAV_ESTIMATED_COST" is like a special number that helps figure out how much money it will cost. It's like a key that helps open the door to the answer.

This special number is used in many different places to help calculate the cost of things. It's like a helper that makes sure everyone gets the right answer.
---

# DRAFT_COST_PER_FILE ELIV

Imagine you have a big box of toys, and each toy costs a little bit of money. 'DRAFT_COST_PER_FILE' is like a special number that tells us how much money each toy costs. It's used to figure out how much money we need to buy all the toys in the box.
---

# NavResult ELIV

Imagine you have a special box that helps you find the best way to do something. This box is like a helper that gives you answers.

The "NavResult" box has some important information inside it. It's like a key that opens a door to show you:

- What the helper suggested (like a map to a treasure)
- How much time it took to find the answer (like a clock)
- If the helper changed something important (like a light switch)
- If it found something new (like a new toy)

This box helps other parts of the system work together to make things easier and faster.
---

# SymbolDoc ELIV

Imagine you have a big box full of toys, and you want to tell your friends what's inside the box. You write a little note that says "Toys: cars, dolls, blocks, etc." so they know what to expect.

The SymbolDoc is like that note. It helps people understand what something is and what it does. It's like a key that opens a door to understanding.

It keeps two things: what the thing says (like the note), and how hard it was to make that note (like how long it took to write it).
---

# _notify_user ELIV

Imagine you have a friend who wants to tell you something important. This function is like a messenger that helps your friend tell you the message.

When your friend wants to tell you something, they give the messenger a note with the message. The messenger then goes and tells you what's on the note. 

It's like a key that opens a door to your attention, so you know something important is happening.
---

# TriggerRouter ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toys that you want to play with. But, you don't want to play with all of them at the same time. You want to pick the ones that are the most fun and play with those first.

The "TriggerRouter" is like a special helper that helps you pick the toys to play with. It looks at all the toys in the box and decides which ones are the most fun and which ones you should play with first.

Here's what it does:

1. It looks at all the toys in the box and decides which ones are the most fun.
2. It makes sure you don't play with too many toys at the same time. It's like a rule that says "you can only play with 5 toys at a time."
3. It makes sure you don't get stuck in a loop where you keep playing with the same toy over and over again.
4. It helps you write notes about the toys you play with, so you can remember what was fun and what wasn't.

The TriggerRouter works with lots of other helpers to make sure everything runs smoothly. It's like a team of helpers that work together to make sure you have the best time playing with your toys!
---

# __init__ ELIV

Imagine you're building a big Lego castle. You need to put all the pieces together, like the walls, the towers, and the door. The `__init__` method is like a special key that helps you put all those pieces together.

When you use this key, it makes sure you have everything you need to build the castle. It checks if you have a plan (called `config`), a way to keep track of what you've done (called `audit`), a way to make sure everything is correct (called `validator`), and a place to build the castle (called `repo_root`). 

If you don't have any of these things, the key helps you create them. It's like having a magic box that gives you what you need to build your castle.
---

# should_trigger ELIV

Imagine you have a big box of toys, and some of them are special toys that you don't want to play with. This special method is like a helper that looks at all the toys in the box and says, "Oh, these ones are special, let's put them aside."

It takes all the toys (files) and checks if they're special (ignored). If they're not special, it keeps them. If they are special, it puts them away. Then it gives you the toys that are not special.
---

# _quick_token_estimate ELIV

Imagine you have a big box of toys, and you want to know how many toys are inside. This special tool, called `_quick_token_estimate`, helps you guess how many toys are in the box.

It looks at the box (called a "path") to see if it's empty. If it is, it says there are a few toys inside. If it's not empty, it reads the box's contents (like looking inside the box). Then, it tries to guess how many toys are inside by counting the words (like counting the toys). It's like using a special key to open the box and see how many toys are inside. If it can't open the box, it says there are a few toys inside.
---

# estimate_cascade_cost ELIV

Imagine you have a big box of toys, and you want to know how much it will cost to buy more toys. This special tool, called "estimate_cascade_cost", helps you guess how much money you'll need.

It looks at all the toys you have, and it adds up how many special tokens each toy has. Then, it multiplies that number by a secret number that tells us how much each million tokens cost. 

Finally, it adds a little extra money, like a safety net, so you don't run out of money when you buy more toys. That's it!
---

# on_file_save ELIV

Imagine you're working on a big project with lots of files. When you save one of those files, this special helper does a few things to make sure everything runs smoothly.

First, it checks if the file is important or not. If it's not important, it says "oh, I don't need to do anything with that one" and moves on.

If the file is important, it estimates how much time and effort it will take to work with it. If it's too much, it says "no, I don't have time for that" and stops.

If it's okay to work with the file, it sends a message saying "I'm going to work on this file now" and then starts working on it. It's like sending a key to open a door, and then going through the door to do the work.
---

# on_git_commit ELIV

Imagine you have a special box where you keep all your toys. When you make changes to your toys, like adding a new one or fixing a broken one, you need to tell the box what you did. This is like a special message that says "Hey, I made some changes!"

The "on_git_commit" method is like a key that opens the box and says "Hey, I got a message! Let me check what's inside." It looks at the changes you made and decides what to do next.

If you didn't make any changes, it just says "No changes, no problem!" and closes the box.

If you did make changes, it checks if it's okay to open the box and do some work. If it's not okay, it says "Sorry, I'm not allowed to open the box right now" and closes it.

If it's okay, it opens the box and starts working on the changes. It's like a little worker that says "Okay, I got the message! Let me fix this toy for you."

It also keeps track of how much time it spends working on the changes, so it doesn't get too tired. If it gets too tired, it says "I need a break!" and closes the box.

That's what the "on_git_commit" method does!
---

# prepare_commit_msg ELIV

Imagine you're working on a big project with lots of files. When you want to save your changes, your computer needs to know what changes you made. This is like writing a note to yourself about what you did.

This special tool, called `prepare_commit_msg`, helps write that note. It looks at all the files you changed and decides what to write in the note. If you wrote a special note, it will add it to the note. Then, it will save the note so you can see it later.

If something goes wrong, it will still save the note, but it will also tell someone that something went wrong. It's like having a helper that makes sure your note gets saved, even if something goes wrong.
---

# estimate_task_nav_cost ELIV

Imagine you have a big box of toys, and you want to know how much it will cost to get a new toy from the box. This special tool, called "estimate_task_nav_cost", helps figure out the cost.

It's like having a magic key that opens a special door to a secret room where the cost is kept. When you use the key, it shows you the cost, and that's what this tool does!
---

# _list_python_files ELIV

Imagine you have a big box full of toys, and inside the box, there are lots of smaller boxes with different toys in them. This code is like a helper that finds all the boxes with toys inside that have a special name on them, like "ball" or "doll".

It looks at the box you tell it to look in, and then it searches all the smaller boxes inside that one to find the ones with the special name. If it finds too many, it stops looking.

Then, it makes a list of all the special boxes it found, and it gives you that list. But it only gives you the first 50 boxes it found, because that's all you can carry in your hands.
---

# _parse_nav_json ELIV

Imagine you have a big box of toys, and inside the box, there's a special note that says "open me to find the toys". But sometimes, the note is wrapped in a special paper that says "don't open yet".

This code is like a key that opens the box and finds the note. It looks at the note to see if it's wrapped in that special paper. If it is, it removes the paper. Then, it tries to read the note to find the toys inside. If it can't read the note, it says "I couldn't find the toys" and gives up. But if it can read the note, it shows you what's inside the box!
---

# navigate_task ELIV

Imagine you have a big library with lots of books. You want to find a specific book, but you don't know where it is. This code is like a helper that tries to find the book for you.

It first looks in a special index that's like a map of the library. If it finds the book, it tells you where it is and what page to look at.

If it can't find the book in the index, it asks a smart computer (called a "LLM") for help. The LLM is like a super-smart librarian who can look through all the books and tell you where the one you want is.

The code keeps asking the LLM until it finds the book or until it gets tired of asking. If it still can't find the book, it gives up and tells you that it couldn't find it.

The code also keeps track of how long it takes to find the book and how much it costs (like how much it costs to ask the LLM for help). It's like a report card that says how well the code did and how much it cost to find the book.
---

# on_manual_trigger ELIV

Imagine you have a special tool that helps you find and fix problems in your computer files. This tool has a special button that says "Go!" When you press the "Go!" button, the tool starts working.

The "on_manual_trigger" is like a key that opens the door to make the tool start working. When you press the "Go!" button, the tool checks if it should work on the files you chose. If it says "no", it writes a note saying "I'm not going to work on these files today."

If it says "yes", it estimates how much time and energy it will take to fix the problems. If it says it's too much time and energy, it writes another note saying "I'm not going to work on these files today."

If it says it's okay to work on the files, it starts fixing the problems one by one. It keeps track of what it's doing and how much time and energy it's using.
---

# _quick_parse ELIV

Imagine you have a big box of toys, and you want to find a special toy inside. This method is like a helper that looks inside the box for you.

It takes a file (like a piece of paper) as input, and it tries to open it. If it can't open it, it says "oh no, I couldn't find it!" and stops.

If it can open it, it reads what's inside the file, but only looks at the first 2000 words. It's like taking a peek inside the box, but only looking at the top part.

Then, it gives you what it found, like a little summary of what's inside the box.
---

# _scout_nav ELIV

Imagine you have a big box of toys, and you want to find a specific toy. This special helper, called `_scout_nav`, is like a map that shows you where the toy might be.

It looks at the toy (called a "file") and tries to find its home in the box. If it can't find the home, it just says where the toy is.

Then, it gives you some information about the toy, like what it's called and where it is. It also tells you how hard it was to find the toy, like a score out of 100.

This helper is like a key that helps you find the toy you're looking for, and it gives you some extra information to help you understand what you found.
---

# _affects_module_boundary ELIV

Imagine you have a big box of toys, and inside the box, there are special toys that you can play with outside the box too. This special method is like a key that checks if a toy has been changed in a way that might affect how people play with it outside the box.

It looks at three things:

1. If someone changed the way the toy is introduced (like a new name or a new way to play with it).
2. If someone added new toys that can be played with outside the box.
3. If someone made a toy that was meant to be played with outside the box, but now it's not.

If any of these things happened, the key says "yes, the toy has been changed in a way that might affect how people play with it outside the box."
---

# _is_public_api ELIV

Imagine you have a big library with many books. Some books are for everyone to read, and some are just for special people who are working on the library.

This special helper, called `_is_public_api`, checks if a book is for everyone or just for the special people. It looks at the book's title and says "yes" if it's a book for everyone, and "no" if it's just for the special people.

It's like a key that opens the door to the public books. If the book is in the right place, the key works, and you can read it. If it's not in the right place, the key doesn't work, and you can't read it.
---

# _detect_module ELIV

Imagine you have a big library with lots of books. Each book has a title and a shelf number. This special helper looks at the shelf number and the title of a book to figure out what kind of book it is.

It tries to find the shelf number first. If it can find it, it uses that to decide what kind of book it is. If it can't find the shelf number, it looks at the title instead. If it still can't figure it out, it says "I don't know what kind of book this is."
---

# _critical_path_files ELIV

Imagine you have a big box of toys, and inside the box, there are some very special toys that you really want to keep safe. This special helper, called `_critical_path_files`, is like a key that finds those special toys in the box.

It looks at all the files (like toys) in the box, and it makes a list of the ones that are super important. When it finds those important toys, it says, "Oh, I found the special ones! Let's keep them safe!"

This list of special toys is what the helper returns. It's like giving you a list of the toys that you really need to keep safe.
---

# _generate_symbol_doc ELIV

Imagine you have a big box of toys, and you want to write a special card to tell people what's inside the box. This special card is like a symbol doc.

This code is like a helper that makes that special card. It takes three things: the name of the box (file), some information about what's inside (nav_result), and if the box is okay or not (validation).

The helper then makes a special card with the box's name and some words that say it was generated. It's like putting a label on the box that says "Generated doc."
---

# _write_draft ELIV

Imagine you have a big box of toys, and inside the box, you have a special folder where you keep your drawings. This special folder is like a secret place where you can store your ideas.

The `_write_draft` method is like a helper that puts your ideas into the secret folder. It takes two things: a special paper with your drawing on it, and a key that says what your drawing is about.

The helper looks at the paper and the key, and then it puts your drawing into the secret folder. It makes sure the folder is ready, and then it writes your drawing on the paper in the folder. Finally, it gives you the address of where your drawing is, so you can find it later.
---

# _update_module_brief ELIV

Imagine you have a big box of toys, and inside the box, there are lots of small boxes with different toys in each one. This code is like a special helper that updates the labels on the small boxes.

It takes three things: the name of the small box, a special file that tells it what to do, and a secret code that helps it remember what it's doing.

When it's done, it puts a new label on the small box with the name and a message that says who updated it. It also keeps track of how long it took to do this job, like a timer.

The timer is what the code returns at the end, so it can remember how long it took to update the label.
---

# _create_human_ticket ELIV

Imagine you have a special box where you keep important notes. This box is like a safe where you can write down things that need to be fixed.

This code is like a key that opens the safe. When you use this key, it writes down a note that says something like "We need to fix this file because it has a problem."

The note also says what kind of problem it is and which file it is. This way, someone can come and look at the note and fix the problem.
---

# _create_pr_draft ELIV

Imagine you're writing a letter to your friend to ask for help with something very important. You want to make sure your friend knows exactly what you need, so you write a special kind of letter that says "Please help me with this!" and explains what you need.

This special letter is like a "pull request draft". It's a way to ask for help from other people to fix something that's very important. This code helps create that special letter, so people can see what needs to be fixed and help you fix it.
---

# _load_symbol_docs ELIV

Imagine you have a big box of toys, and inside the box, there are special papers that tell you what each toy does. This special code is like a helper that finds those papers and puts them together for you.

It looks for papers in two special places: one next to the toy, and another in a special folder called ".docs". If it finds papers in either place, it reads what's written on them and puts it all together in a nice order. If it can't find any papers, it says "oh well, nothing to show you!"
---

# _generate_commit_draft ELIV

Imagine you have a big box of toys, and you want to tell your friends what you did with the toys. You want to write a note that says "I fixed the broken toy" or "I added a new toy".

This special tool, called `_generate_commit_draft`, helps you write that note. It looks at the toys you changed and tries to guess what you did with them. Then, it asks a super smart computer to write a nice note for you.

The computer reads what you changed and writes a note that says something like "I fixed the broken toy" or "I added a new toy". The tool then saves that note in a special place so you can find it later.

If the tool can't guess what you did, or if something goes wrong, it will try to fix the problem and save the note anyway.
---

# _generate_pr_snippet ELIV

Imagine you have a big box of LEGOs, and you want to tell your friend what you changed in the box. This special helper, called `_generate_pr_snippet`, makes a short note about what you changed.

It looks at the box (called a "file") and sees what's different (called a "diff"). If nothing is different, it doesn't write anything.

Then, it asks a special computer (called a "LLM") to write a short note about what you changed. The computer reads what's different and what the LEGOs (or code) used to look like.

The computer writes a short note, and this helper saves it in a special folder (called a "draft"). It also tells another helper (called an "audit") that it wrote a note, and how much it cost to write it.
---

# _generate_impact_summary ELIV

Imagine you made some changes to a file in a big project. This special tool helps figure out what those changes might do to the project.

It's like a detective who looks at the changes you made and says, "Okay, let me check what's changed." Then it talks to a super smart computer that says, "I think this might break this, and this person might be affected, and we should change this setting."

The detective writes down what the smart computer said and puts it in a special place where people can read it later. It's like putting a note on a door that says, "Be careful, this might break something!"

This tool also keeps track of how much money it cost to talk to the smart computer and what changes it made. It's like keeping a record of how much money you spent on a special tool that helps you fix things.
---

# _process_file ELIV

Imagine you have a big box of toys, and you want to find the right toy to play with. This special helper, called `_process_file`, is like a guide that helps you find the right toy.

First, it looks at the toy (file) and tries to understand what it is. It's like looking at a picture and trying to guess what it is.

Next, it talks to a special friend (nav) that helps it figure out what the toy is. The friend gives it some answers, and the guide writes down what it learned.

Then, it checks if the answers are correct. If they're not, it tries again with a different friend (nav) that can give better answers.

If it still can't get the right answers, it asks a human for help. It's like saying, "I need your help to find the right toy!"

If it does get the right answers, it creates a special report (draft) that tells you what the toy is and what it does. It's like writing a note that says, "This toy is a car, and it goes 'vroom'!"

Finally, it checks if the toy is special and needs extra help. If it does, it creates another report that says, "This toy is important, and we need to tell everyone about it!"

That's what `_process_file` does! It helps find the right toy, creates reports, and makes sure everything is okay.