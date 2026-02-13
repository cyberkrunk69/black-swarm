# logger ELIV

Imagine you have a notebook where you write down important things that happen in your day. Like, "I ate a sandwich" or "I played outside."

The 'logger' is like a special helper that writes down important things that happen in a computer program. It helps us remember what happened, so we can fix problems or make the program better.
---

# _run_git ELIV

Imagine you have a special tool called "Git" that helps you keep track of your drawings or pictures. This tool has many commands, like "show me all your pictures" or "delete a picture".

The "_run_git" function is like a helper that makes sure you can use the Git tool. It takes some instructions (called "args") and says "okay, let's run this command". If the command works, it shows you what happened. But if the command doesn't work, it tells you what went wrong and stops the helper from working.

It's like having a key that opens a door. If the key works, the door opens. But if the key doesn't work, the door stays closed and you can't go inside.
---

# get_changed_files ELIV

Imagine you have a big box of toys, and you want to know which toys have changed since yesterday. 

This function is like a special tool that helps you find out which toys have changed. It looks at the box and says, "Oh, this toy is new!" or "This toy has been changed!"

It can look at two kinds of changes:

1. Changes that are already in the box (like toys you've already put away).
2. Changes that are in the box, but not yet put away (like toys you're still playing with).

If you want to see only the changes that are already in the box, it will show you those. If you want to see all the changes, it will show you everything.

It also has a special key (called a "branch") that helps it understand which changes are new and which ones are old. It's like a key that opens a door to a special room where it can find the changes.

When it's all done, it will give you a list of the changed toys, so you can see what's new and what's changed!
---

# get_diff_for_file ELIV

Imagine you have a special box where you keep all your drawings. You want to see what's different between the drawing you made today and the one you made yesterday. 

This function is like a helper that looks at your drawing and tells you what's changed. It takes a few things from you: 

- The name of the drawing you want to look at.
- If you want to see the changes that are already saved (like a special "save" button).
- Where the box with your drawings is (like the address of your house).

It then looks at your drawing and tells you what's different. If it can't find the drawing or something goes wrong, it says "I couldn't find it."
---

# get_current_branch ELIV

Imagine you have a big box of toys, and inside the box, there are lots of different toy collections. Each collection is like a special group of toys that you can play with together.

The "get_current_branch" function is like a special tool that helps you find out which toy collection you're playing with right now. It looks at the box and says, "Oh, you're playing with the 'cars' collection!" or "You're not playing with any collection right now."

If you're not playing with any collection, it says, "I don't see any collection you're playing with." And if it can't find the collection, it says, "I couldn't find the collection you're looking for."
---

# get_base_branch ELIV

Imagine you're in a big library with lots of books. Each book has a special name, and some books are connected to other books in a special way.

This function, called `get_base_branch`, helps find the main book that all the other books are connected to. It looks for this main book in a few different places:

1. It checks if there's a special connection to another book that says what the main book is.
2. If not, it looks for a book called "main", then "master", and finally "develop".
3. If it can't find any of these, it says "I don't know" and stops looking.

It's like trying to find the main door in the library that all the other doors are connected to. If it finds it, it tells you the name of the main door. If it can't find it, it says it can't help you.