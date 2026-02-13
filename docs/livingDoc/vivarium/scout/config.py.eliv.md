# _path_matches ELIV

Imagine you have a lot of toys in a big box, and you want to find a specific toy. The box has many different paths to get to each toy, like "in the red box on the shelf" or "under the blue blanket".

This special helper function is like a map that helps you find the right path to the toy you want. It looks at the path you want to take (like "in the red box on the shelf") and compares it to a special code (like a key) that says what the path should look like.

The code can have special symbols like "*" (which means "any characters") and "**" (which means "any number of paths"). The function takes the code and turns it into a special key that can unlock the right path.

Then, it tries to use the key to unlock the path you want to take. If it works, it says "yes, this is the right path!" (which means True). If it doesn't work, it says "no, this isn't the right path" (which means False).
---

# logger ELIV

Imagine you have a notebook where you write down important things that happen in your day. 

The 'logger' is like a special helper that writes down important things that happen in a computer program. It helps us remember what happened, so we can fix problems if they come up.
---

# HARD_MAX_COST_PER_EVENT ELIV

Imagine you have a piggy bank where you save your money. This special number, 'HARD_MAX_COST_PER_EVENT', is like a rule that says you can't spend more than $1 from your piggy bank for something fun, like a toy or a treat. It helps keep your money safe and makes sure you don't spend too much.
---

# HARD_MAX_HOURLY_BUDGET ELIV

Imagine you have a piggy bank where you save your money. This special number, 'HARD_MAX_HOURLY_BUDGET', is like a rule that says you can only spend a certain amount of money each hour. It's like a limit that helps you not spend too much.
---

# HARD_MAX_AUTO_ESCALATIONS ELIV

Imagine you have a toy box with a special rule: you can only ask a grown-up to help you get a toy 3 times. If you ask more than 3 times, they might get a little mad.

The "HARD_MAX_AUTO_ESCALATIONS" is like a special number that says "stop asking after 3 times". It helps keep things from getting too confusing or annoying.
---

# TriggerConfig ELIV

Imagine you have a special box where you keep your toys. This box has a lock on it, and you need a key to open it. The key is like a secret code that says "yes, you can open the box".

The TriggerConfig is like a key that helps a computer decide if it can open a special box (called a file path). The key has two parts: 

1. What kind of key it is (like a special symbol that says "open now" or "don't open yet").
2. How much money you can spend to open the box (like a limit on how many cookies you can use to buy a toy).

So, the TriggerConfig helps the computer make a decision about whether to open the box or not, and how much it can cost.
---

# DEFAULT_CONFIG ELIV

Imagine you have a special box where you keep all your favorite things, like toys and snacks. This box has lots of different sections, like "toys", "snacks", and "games".

The "DEFAULT_CONFIG" is like a special key that unlocks this box. When you use this key, it opens the box and shows you all the things inside, like the toys and snacks. 

It doesn't do anything special, it just shows you what's inside the box.
---

# _max_concurrent_calls ELIV

Imagine you have a toy box with lots of toys inside. You want to take out a certain number of toys at the same time, but you don't want to take out too many or too few.

This special helper function is like a key that helps figure out how many toys to take out at the same time. It looks for a special secret code (called an "environment variable") that tells it how many toys to take out. If it can't find the secret code, it uses a default number, which is 5.

The function then makes sure the number of toys to take out is between 1 and 100. If it's not, it changes it to be between 1 and 100. That way, you can't take out too many or too few toys at the same time.
---

# get_global_semaphore ELIV

Imagine you have a toy box with lots of toys inside. But, you can only play with one toy at a time. This function is like a special key that helps you open the toy box.

When you first want to play with a toy, the key isn't there, so it makes a new key. Then, it gives you the key so you can play with the toy. If you want to play with another toy, it still gives you the key, but it's already there, so it's faster.

This key helps make sure you can only play with one toy at a time, so everything runs smoothly.
---

# ENV_TO_CONFIG ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toys with different names. But, you need to find a specific toy, like a red ball.

'ENV_TO_CONFIG' is like a special list that helps you find the right toy in the box. It tells you where the toy is, what it's called, and what kind of toy it is (like a ball or a doll).

When you use 'ENV_TO_CONFIG', it's like looking at the list and saying, "Oh, I need the red ball! Let me check the list... Ah, it's in the box, and it's called 'red ball', and it's a ball!"
---

# _deep_merge ELIV

Imagine you have two boxes, one with some toys and another with some more toys. The first box has a key that says "cars" and inside, it has a toy car. The second box also has a key that says "cars" but inside, it has a big truck.

The function _deep_merge is like a helper that takes these two boxes and puts all the toys from the second box into the first box. If the second box has a key that's already in the first box, it looks inside both boxes to see if the thing inside the second box is also a box. If it is, it uses the helper again to put all the toys from the second box into the first box. If not, it just puts the toy from the second box into the first box.
---

# _load_yaml ELIV

Imagine you have a special book that's locked with a secret code. This code is like a key that opens the door to the book.

The "_load_yaml" function is like a helper that tries to open this book. It looks for the book in a special place, and if it can't find it, it says "oh, the book is missing!" and stops.

If it finds the book, it tries to unlock it with a special tool called "yaml". If the tool works, it reads the book and shows us what's inside. But if the tool doesn't work, or if the book is broken, it says "oh no, something went wrong!" and stops.

If everything works, it shows us what's inside the book. If not, it says "the book is missing or broken" and stops.
---

# _save_yaml ELIV

Imagine you have a toy box where you keep all your favorite toys. But instead of toys, this box is for special information that computers can understand.

This function is like a key that opens the toy box and puts the information inside. It takes two things: the name of the toy box (called "path") and the information you want to put inside (called "data").

When you use the key, it tries to open the toy box and put the information inside. If it works, it says "yes, I did it!" and returns a happy face (which is like the "True" part).

But if something goes wrong, like the toy box is locked or the information is too big, it says "oh no, I couldn't do it!" and returns a sad face (which is like the "False" part).
---

# _get_nested ELIV

Imagine you have a big box with lots of smaller boxes inside. Each smaller box has a special key on it that says what's inside. 

This function is like a helper that finds a specific key inside all those smaller boxes. It looks at each box, opens it, and checks if the key is there. If it finds the key, it opens the box it's in and looks inside. If it can't find the key, it says "I couldn't find it!" and stops looking.
---

# _set_nested ELIV

Imagine you have a big box with lots of smaller boxes inside. Each smaller box has a special name, like "apple" or "banana". 

This function helps you put a new toy inside one of those smaller boxes. But first, it needs to find the right box. If the box doesn't exist, it creates a new one. Then, it puts the toy inside the box.

For example, if you want to put a toy car inside a box labeled "toys" inside a box labeled "playroom", it will create the "playroom" box if it doesn't exist, and then put the "toys" box inside it, and finally put the toy car inside the "toys" box.
---

# ScoutConfig ELIV

Imagine you have a special box where you can store your secrets, like how much money you can spend on something. This box is called "ScoutConfig".

It helps you remember three things:

1. What you wrote in a special file called "config.yaml".
2. What the computer tells you through special messages called "environment variables".
3. Some rules that are always true, like a secret password that never changes.

The box also helps you decide if you can spend money on something. It checks if the money you want to spend is less than what you're allowed to spend. If it is, the box says "yes, you can spend it!" If not, it says "no, you can't spend it!"

You can also ask the box to show you what's inside, or to change what's inside. But remember, some things in the box are secret and can't be changed!
---

# __init__ ELIV

Imagine you have a special box where you keep all your favorite things, like toys and snacks. This box is like a computer program, and it needs to know how to find all the things it needs to work properly.

The `__init__` method is like a key that opens the box and helps it find all the things it needs. It looks in a few different places to find the things it needs, like:

- A special list of things that are always there
- A box in your home that has some extra things
- A box in the project you're working on that has some more things
- Some special messages that are hidden in the computer

It takes all these things and puts them together in the box, so the program can use them to work properly.
---

# _default_search_paths ELIV

Imagine you have a special box where you keep all your favorite toys. But, you also have a big box in your room where you keep all your toys too. 

This code is like a map that shows where these two boxes are. It helps find the boxes so you can get your toys. It looks for two special places: one in your home and one in your current project. It returns the addresses of these two places, so you can find them easily.
---

# _apply_env_overrides ELIV

Imagine you have a special box where you keep your favorite toys. This box has lots of compartments, and each compartment has a special key that opens it.

This code is like a helper that checks the environment (like the air around us) for special keys. If it finds a key, it opens the right compartment in the box and puts a new toy inside.

The code looks at each key it finds and tries to understand what kind of toy it is. If it's a toy that can be counted (like a number), it puts the number in the box. If it's a toy that has words on it, it puts the words in the box. If it's a special kind of toy, it just puts the toy in the box as is.

If the code can't understand the toy, it makes a note that says "I couldn't understand this toy" and keeps looking for other keys.
---

# _ensure_hard_cap_in_limits ELIV

Imagine you have a special box where you keep important rules. This box is like a key that helps you remember what's safe and what's not.

This code is like a helper that makes sure the box has the right rule about how much money you can spend. It's like putting a sticker on the box that says "Don't spend more than this!"
---

# resolve_trigger ELIV

Imagine you have a special box where you keep your toys. Inside the box, there are some rules that say what happens when you put a certain toy in the box. 

This code is like a helper that looks at the rules and finds the right one for the toy you want to put in the box. It checks each rule one by one, and when it finds the right one, it says "aha! This is the rule for this toy!" and stops looking. 

If it can't find the right rule, it looks at a special rule that says what to do if none of the other rules match. It's like having a backup key that opens the door if the other keys don't work.
---

# effective_max_cost ELIV

Imagine you have a special box where you can put money, but there's a rule that says you can't put too much money in it. This rule is like a safety cap.

The "effective_max_cost" method is like a helper that checks how much money you can put in the box. It looks at a few things to decide:

- If you gave it a special address (like a key to a door), it checks if that address is on a list of special addresses that have a limit on how much money you can put in the box.
- If not, it looks at a special setting that you or someone else might have set to decide how much money you can put in the box.
- If it can't find any of those things, it uses a default setting that says how much money you can put in the box.

It always makes sure that the amount of money you can put in the box is not more than the safety cap, so you don't put too much money in and break the box!
---

# should_process ELIV

Imagine you have a piggy bank where you save money. This special helper, called "should_process", checks if you can spend some money from your piggy bank.

It looks at two things:

1. How much money you want to spend now (called "estimated_cost").
2. How much money you can spend in one hour (called "hourly_budget").

If you want to spend more money than you have in your piggy bank, or more than you can spend in one hour, the helper says "no". But if you can afford it, it says "yes"!
---

# to_dict ELIV

Imagine you have a big box with lots of things inside, like toys and books. But you want to show your friend what's inside the box, so you make a list of all the things in the box.

This "to_dict" method is like making that list. It takes all the things in the box (or in this case, a special place called "_raw") and puts them into a list that's easy to read. It's like a key that opens the box and shows you what's inside.
---

# get_user_config_path ELIV

Imagine you have a special box where you keep all your favorite things, like toys and stickers. But this box is hidden, and you need a special key to open it.

The "get_user_config_path" is like finding that key. It helps you figure out where the special box is, so you can open it and find what's inside. In this case, the special box is a file called "config.yaml" that's hidden in a secret place on your computer. The key helps you find it, so you can open it and see what's inside.
---

# get_project_config_path ELIV

Imagine you have a special box where you keep all your favorite toys. But, you need a key to open the box. 

This code is like finding the key to open the box. It looks for a special key (called a path) that says where the box is. 

The box is called ".scout" and inside the box, there's a special paper called "config.yaml". This code finds the path to that paper, so you can open the box and find the paper inside.
---

# get ELIV

Imagine you have a big box with lots of smaller boxes inside. Each smaller box has a special name, like "triggers" or "default".

The "get" method is like a special key that helps you find a specific box inside the big box. You tell it the name of the box you want, like "triggers.default", and it goes and finds it for you.
---

# set ELIV

Imagine you have a big box where you keep all your toys. Inside the box, there are smaller boxes with different names on them. This "set" method is like a special key that helps you put a new toy in one of those smaller boxes.

When you use the key, you tell it which box you want to put the toy in and what the toy is. It will then put the toy in the right box for you. If the box doesn't exist, it will make a new one. And if you have a special book where you keep all your favorite toys, it will write the new toy in that book too.
---

# validate_yaml ELIV

Imagine you have a special book with words and pictures that you want to read. But sometimes, the book might be broken or have mistakes in it. 

This special tool, called 'validate_yaml', checks if the book is okay or not. It looks at the book and says:

- "Yes, this book is good!" if it's okay.
- "No, this book is broken!" if it's not okay.

If you don't give it a book, it checks a special secret book that it has. If that book is okay, it says "Yes, this book is good!" If not, it says "No, this book is broken!".