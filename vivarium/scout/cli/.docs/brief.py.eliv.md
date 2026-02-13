# ESTIMATED_EXPENSIVE_MODEL_COST ELIV

Imagine you have a big box of toys, and some toys are very expensive. This special number, 0.85, is like a secret code that helps figure out if a toy is very expensive or not. It's like a key that helps the computer understand how much things cost.
---

# COMPLEXITY_THRESHOLD ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toys with different sizes. The COMPLEXITY_THRESHOLD is like a special ruler that says, "If a toy is bigger than this ruler, it's too big for the box."

In this case, the ruler is set to 0.7. So, if something is more than 0.7, it's too big and might not work properly. It helps keep things simple and safe.
---

# NavResult ELIV

Imagine you're on a treasure hunt and you need to find the right path to get to the treasure. The NavResult is like a map that helps you find the way.

It has some important information on it, like:

- Where the treasure is (target_file)
- What you need to do to get it (target_function)
- How long it will take to get there (line_estimate)
- What the treasure looks like (signature)
- How much it will cost to get it (cost)
- Who is helping you on the hunt (session_id)
- Why you think this is the right path (reasoning)
- What you should do next (suggestion)
- How sure you are that this is the right path (confidence)

It's like a key that helps you unlock the door to the treasure!
---

# GitContext ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toys that you've played with over time. 

The 'GitContext' is like a special card that helps us remember some important things about the toys in the box. It tells us:

- Who last played with the toys (last_author)?
- When they last played with the toys (last_modified)?
- What they said when they played with the toys (last_commit_msg)?
- How many toys they changed (churn_score)?
- Which toys they changed together (files_changed_together)?

This card helps us keep track of all these things, so we can see what's been happening with the toys in the box.
---

# DepGraph ELIV

Imagine you have a big box of toys, and inside the box, there are lots of smaller boxes with different toys in them. 

The DepGraph is like a map that shows which toys are inside which boxes, and how they're connected to each other. It helps us figure out what we need to do first, and what we can do later.

It keeps track of three things:

- Direct: These are the toys that are right inside the big box.
- Transitive: These are the toys that are inside the smaller boxes, but we can get to them by opening other boxes first.
- Callers: These are the toys that are asking for other toys to be opened.

It's like a key that helps us open the right boxes in the right order, so we can play with all the toys!
---

# _generate_session_id ELIV

Imagine you're at a big playground with lots of kids. You want to play on a special slide, but it's locked. To unlock it, you need a special key. 

The `_generate_session_id` function is like making a special key. It creates a unique key that helps keep track of who's playing on the slide (or in this case, using a computer program). This key is like a secret code that only works for that one person.
---

# _run_git ELIV

Imagine you have a special box where you keep all your toys. This box is like a secret place where only you can go. But sometimes, you need help from a friend to get into the box. 

The "_run_git" function is like a special key that helps you open the box. It's a key that talks to the box (called "git") and says "Hey, can you do something for me?" 

The function tries to open the box, do what it's asked, and then tells you if it was successful or not. If it was successful, it also tells you what happened inside the box. If it wasn't successful, it says "Sorry, I couldn't open the box."
---

# gather_git_context ELIV

Imagine you have a big box of toys, and inside the box, there are lots of little notes that say who played with the toys, when they played with them, and what they did. This function is like a special tool that helps find those notes for a specific toy.

It looks for the last note that was written, who wrote it, and what they did. It also tries to figure out how long ago the note was written. If it can't find the note, it says "I don't know".

Then, it looks at all the notes from the last 90 days and counts how many times the toy was played with. It gives a score from 0 to 10 based on how many times it was played with.

Finally, it finds out which other toys were played with at the same time as the special toy. It only looks at the first 5 toys it finds.

The function puts all this information together into a special package called "GitContext" that we can use later.
---

# _module_to_path ELIV

Imagine you have a big box of toys, and inside the box, there are lots of smaller boxes with different names on them. This function is like a helper that finds the right box for you.

It takes two things: the name of the box you're looking for, and the name of the big box where all the smaller boxes are kept.

The helper looks at the name of the box you want, and it tries to find it in the big box. If it can't find it, it looks for a special box called "__init__" inside the box you want. 

If it finds the box, it tells you where it is, like "it's in the blue box!" If it can't find it, it says "I couldn't find it!"
---

# _parse_imports ELIV

Imagine you have a big box of toys, and inside the box, there are lots of smaller boxes with different toys in them. This function is like a helper that finds the names of those smaller boxes and tells you where they are in the big box.

It looks at each line in a special list of instructions, and if it finds a word that says "import" or "from", it tries to find the name of the smaller box. If it can find the name, it checks if it's already found that box before, and if not, it adds the name to a list of boxes it's found.

Finally, it gives you the list of box names, but only the first 15 boxes it found.
---

# _find_callers ELIV

Imagine you have a big library with lots of books. Each book has a special name, like "Math Book" or "Science Book". 

This function is like a helper that finds all the books in the library that have a special key (called a "target module") that unlocks a specific book (the "target file"). 

It looks at every book in the library, one by one, and checks if the key is in that book. If it finds the key, it writes down the name of that book. 

But it only writes down the name of the book if it's not the same book that has the key (because that's not very helpful!). And it stops writing down names after it finds 10 books (because that's a good number to start with!). 

Finally, it gives you a list of all the books that have the key, so you can see which books are connected to the special book you're looking for.
---

# _resolve_target_to_file ELIV

Imagine you have a big box of toys, and inside the box, there are lots of smaller boxes and toys. This function is like a helper that finds a specific toy in the box.

It takes two things: the name of the toy you're looking for, and the name of the big box where the toy might be. 

The helper looks for the toy in the big box and its smaller boxes. If it finds the toy, it tells you where it is in the box. If it can't find the toy, it says "I couldn't find it."

The toy can be a small toy, or it can be a whole box of toys. And the helper knows how to find the toy even if it's hidden inside another box.
---

# build_dependencies ELIV

Imagine you have a big box of toys, and inside the box, there are smaller boxes with toys too. This function helps find all the smaller boxes that are connected to the big box.

It starts with a special file (like a key) that we want to look at. It reads the file and finds all the other files that it uses (like a list of friends that the file talks to).

Then, it looks at those friends and finds their friends too (like a big family tree). It only looks at the friends of friends that are close to the special file (like the first cousins).

Finally, it finds all the files that use the special file (like a list of people who have the key).

The function puts all this information together into a special report, like a map of the toy box, so we can see how all the files are connected.
---

# calculate_complexity ELIV

Imagine you have a big box of toys, and you want to know how hard it is to clean up. This function is like a special tool that helps figure out how messy the box is.

It looks at four things:

1. How many toys are in the box (like how many dependencies there are).
2. How often you play with the toys (like how much the code is changing).
3. How many toys you play with at the same time (like how many files are changed together).
4. How many other kids are playing with the same toys (like how many other parts of the code are using the same things).

It adds up how messy each of these things makes the box, and then it gives you a score from 0 to 1. If the score is over 0.7, it's like the box is too messy, so it needs a special helper to make it cleaner!
---

# _get_groq_api_key ELIV

Imagine you have a special key that lets you talk to a super smart computer. This key is called the "GROQ API Key". 

This function is like a helper that tries to find this key for you. It looks in one place first, and if it can't find it there, it looks in another place. 

If it finds the key, it gives it back to you. If it can't find the key anywhere, it says "I couldn't find it" and gives you nothing.
---

# _call_groq ELIV

Imagine you have a special machine that can talk to another machine on the other side of the world. This machine is called Groq. 

The special machine in our code is like a messenger who helps us talk to Groq. It takes a message (like a question) and sends it to Groq. Then, it gets the answer back from Groq and brings it back to us.

The messenger also keeps track of how much it costs to talk to Groq. It's like counting how many coins we need to pay for the conversation.

So, the code is like a helper that makes it easy for us to talk to Groq and get answers back.
---

# _format_structure_prompt ELIV

Imagine you have a big box of toys, and you want to tell someone how to find a specific toy inside the box. You need to give them a map or a list of clues to help them find it.

This special function is like making a map or a list of clues. It takes some information about the toy (like its name, where it's located, and what it looks like) and uses it to create a special message that helps someone find the toy.

The message is like a key that opens a door to a secret place where the toy is hidden. In this case, the secret place is a special report that helps someone understand what's going on with the toy.

The function takes some information from different places, like a special book that keeps track of changes (called "Git context") and a list of things that are connected to the toy (called "dependencies"). It uses this information to create the special message that helps someone find the toy.

The message is written in a special way called "Markdown" that makes it easy to read and understand. It's like a treasure map that leads someone to the treasure (the report) and helps them understand what's going on with the toy.
---

# generate_structure_8b ELIV

Imagine you have a special machine that can help you write a report. This machine is like a super smart friend who can understand what you want to say and write it down for you.

The "generate_structure_8b" function is like a key that tells this machine what to write. It gives the machine some information, like what the report is about, and what other things it needs to know.

Then, the machine writes the report and tells us how long it took to write it. The function takes this report and the time it took, and gives it back to us. It's like getting a finished report from our super smart friend!
---

# enhance_with_70b ELIV

Imagine you have a big box of LEGOs, and you want to make it even better. You want to add more details and make it more interesting.

This special tool, called "enhance_with_70b", helps you do that. It's like a magic key that opens a special door to a super smart computer.

When you give it a task and some information, it asks the computer to make the information better. The computer looks at what you gave it and adds more details, like a special helper.

Then, it gives you back the improved information, like a new and exciting LEGO creation!
---

# generate_deep_prompt_section ELIV

Imagine you have a special machine that can help you with a big task. This machine needs a special message to understand what to do. 

This function is like a helper that writes that special message. It takes some information from you, like what the task is, where the problem is, and what changes were made recently. 

Then, it uses that information to create a message that says something like: "Hey machine, I need you to look at this task. Check this part of the code and see what's going on. Also, remember that some changes were made recently."

It's like a key that opens the door to the machine, so it knows what to do.
---

# generate_cost_section ELIV

Imagine you have a toy box with lots of toys inside. You want to know how much it costs to play with all the toys, and how much it would cost if you had a special helper to pick out the toys for you.

The "generate_cost_section" function is like a tool that helps you make a chart to compare the costs. It takes two numbers: how much it costs to play with all the toys, and how much it costs to have the helper pick out the toys.

It then makes a chart that shows:

- How much it costs to play with all the toys
- How much it costs to have the helper pick out the toys
- How much money you save by having the helper

The chart also shows how much time it takes to play with all the toys, and how much time it takes to have the helper pick out the toys. It's like a key that helps you understand which way is more efficient!
---

# build_header ELIV

Imagine you're a superhero who needs to write a report about a secret mission. This function is like a special tool that helps you write the title and introduction of your report.

It takes four things: the name of the mission, some information about how the mission went, how much money it cost, and how hard it was. Then it uses this information to create a special header for your report.

The header says things like when the report was made, how much money the mission cost, and how much money you saved by doing it a certain way. It's like a key that opens the door to your report, and it helps people understand what your report is about.
---

# build_target_section ELIV

Imagine you're on a treasure hunt and you found a map that shows you where to go. This special function is like a tool that helps make a report about where you're going.

It takes a map (called "nav_result") and uses it to write a special section in the report. This section says things like:

- Where you're going (the target location)
- What file you need to look at
- What function you need to use
- What line of code you need to look at

It's like writing a key that opens a door to the treasure!
---

# build_change_context_section ELIV

Imagine you have a special report about changes made to a computer program. This report is like a key that helps people understand what happened.

The "build_change_context_section" function is like a helper that makes this report. It takes some information about the changes, like who made them, what they changed, and how much they changed it.

The function puts all this information together in a nice, easy-to-read format, like a list with headings. It's like writing a summary of what happened, so people can understand it easily.

When it's all done, the function gives you a special string (like a sentence) that you can use to show the report.
---

# build_dependency_section ELIV

Imagine you have a big box of toys, and inside the box, there are some toys that you need to play with first, and some toys that those toys need to play with. This function helps make a list of all those toys.

It takes two things: a list of toys that you need to play with first (called "direct dependencies"), and a list of all the toys that those toys need to play with (called "transitive dependencies").

Then, it makes a special report that says:

- What toys you need to play with first (direct dependencies)
- What toys those toys need to play with (transitive dependencies)

This report is like a map that helps you know what toys you need to play with, and how they all fit together.
---

# _resolve_pr_task ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toys with numbers on them. This function is like a special key that helps find the name of the toy when you know its number.

It looks at the box (called a "repository") and uses a special tool (called "gh CLI") to find the name of the toy with the number you gave it. If it can't find the name, it says "I couldn't find the toy with that number" instead.
---

# get_navigation ELIV

Imagine you have a big library with lots of books. You want to find a specific book, but you don't know where it is. 

This special function, called "get_navigation", is like a librarian who helps you find the book. It takes some information from you, like the title of the book and where you think it might be.

The librarian uses a special map to figure out where the book is. If it finds the book, it gives you the book's title, the page number, and how long it will take to read it. If it can't find the book, it says "I couldn't find it".

It's like having a key that opens a door to the book you want to read!
---

# generate_brief ELIV

Imagine you have a big project with lots of files and code. This special tool, called `generate_brief`, helps you make a short report about your project.

It's like a key that opens a door to your project. It goes through a few steps to get all the information it needs:

1. It looks at your project and finds the important parts.
2. It checks the code and sees what's changed.
3. It looks at the files and sees what's inside.
4. If your project is very complicated, it gets some extra help from a special computer.
5. It adds some extra information to the report, like how much time it took and how hard it was.
6. It puts all the information together into a short report.

When it's done, it gives you a report that's easy to read and understand. You can even save it to a file if you want!
---

# parse_args ELIV

Imagine you have a special box with lots of buttons and levers. This box is like a computer program. 

When you want to use the program, you need to tell it what to do. You do this by pressing the right buttons and turning the right levers. 

The "parse_args" function is like a helper that looks at the buttons and levers you pressed. It figures out what you want the program to do and makes it happen.

It's like a key that opens a door. You give it the key (the buttons and levers you pressed), and it opens the door (makes the program do what you want).
---

# _main_async ELIV

Imagine you have a special box that can do lots of things. This box is like a computer program. 

The "_main_async" part is like a key that opens the box. When you use the key, the box starts doing its job.

First, the box checks if it's in the right place. If it's not, it says "oops, you need to move me to the right spot!" and stops.

Next, the box looks at what you want it to do. You can tell it to do something special, like "make a report" or "check a picture". If you don't tell it what to do, it says "oops, you need to tell me what to do!" and stops.

Then, the box tries to do the thing you told it to do. If it can't, it says "oops, something went wrong!" and stops.

If everything goes well, the box does its job and says "yay, I'm done!"
---

# main ELIV

Imagine you have a big box of toys, and inside the box, there are lots of fun things to play with. But, you need a special key to open the box.

The "main" function is like that special key. It helps open the box, and when it does, it lets other things inside the box start working together.

When you use the key (or run the "main" function), it makes sure everything inside the box is ready and working properly. Then, it lets the other things inside the box do their jobs, like finding the right toys to play with or making sure everything is safe.

The "main" function is like a helper that makes sure everything runs smoothly, and it's very important because it's the first thing that happens when you open the box.