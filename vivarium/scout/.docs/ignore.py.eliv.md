# BUILT_IN_IGNORES ELIV

Imagine you have a big box full of toys, and you want to keep some of them safe from getting mixed up. 'BUILT_IN_IGNORES' is like a list of special words that tell the computer which toys to keep safe.

When the computer is looking at all the things in the box, it sees these special words and says, "Oh, don't touch those ones! They're special and need to be kept safe." It's like a key that opens a door to keep certain things from getting changed.
---

# _glob_to_regex ELIV

Imagine you have a special key that can open a door to find a toy. The key is like a secret code that says where the toy might be. This code is called a "glob pattern".

The function `_glob_to_regex` is like a helper that takes this special key and turns it into a new code that computers can understand. This new code is called a "regex".

The helper looks at the key and says things like:

- If the key says "**", it means the toy might be anywhere in a big box, so it adds a special code that says "look anywhere in the box".
- If the key says "*", it means the toy might have any name, so it adds a special code that says "look for any name".
- If the key says "?", it means the toy might have a special mark, so it adds a special code that says "look for that mark".

Then, the helper puts all these special codes together to make a new key that computers can understand. This new key is like a map that shows where the toy might be.
---

# _normalize_path ELIV

Imagine you have a special key that can open any door in your house. But, sometimes the key might have a little mistake in it, like a wrong letter or a missing letter. 

This special function is like a helper that takes your key (called a "path") and makes sure it's correct so it can open the right door. 

It does a few things:

- If your key starts with a special symbol (~), it changes it to the right symbol so it can open the door.
- If you have a special map (called "repo_root") that shows where all the doors are, it uses that map to find the right door.
- If the key doesn't have the right address (like a street name), it adds the right address so it can open the door.
- Finally, it changes any backslashes in the key to forward slashes, like a special code that says "open the door now!"

Now, your key is perfect, and you can open the right door!
---

# IgnorePatterns ELIV

Imagine you have a big box full of toys, and you want to keep some of them hidden from your friends. You need a special list of rules to tell the box what toys to hide.

The "IgnorePatterns" class is like a magic list of rules that helps the box decide which toys to hide. It looks at two kinds of rules:

1. Built-in rules: These are like the box's default rules that always apply. They're like a special key that opens the door to hiding some toys.
2. User rules: These are like the rules you write down in a special book called ".livingDocIgnore". You can write rules like "hide all the toys that start with 'car'" or "don't hide the toy that's called 'my favorite'".

The "IgnorePatterns" class looks at both kinds of rules and decides which toys to hide based on what you've written. It's like a helper that makes sure the box hides the right toys for you!
---

# __init__ ELIV

Imagine you have a toy box, and you want to put all your toys inside it. But before you can put the toys in, you need to make sure the box is ready. That's kind of like what the `__init__` method does.

It's like a special key that opens the box and gets it ready for you to use. When you use the key, it makes sure the box has a special place to put your toys, and it's all set up and ready to go.
---

# _load_patterns ELIV

Imagine you have a special box where you keep things you don't want to see. This box has three parts: one for things you always want to ignore, one for things you want to ignore in a special place, and one for things you want to ignore in a different special place.

This code is like a helper that fills up these boxes. It first empties the boxes and then adds some things to the "always ignore" box. 

Then, it looks at a special file on your computer. If the file exists, it reads what's inside and adds some things to the boxes. If it can't read the file, it just moves on.

It's like a key that opens a door to the special file, and then it uses what it finds inside to fill up the boxes.
---

# matches ELIV

Imagine you have a big box of toys, and you want to know if a certain toy should be played with or not. This special tool, called "matches", helps you decide.

It looks at three things:

1. Some special rules that come with the box (like a secret code).
2. Rules that you, the player, made to ignore certain toys (like a "don't touch" sign).
3. Rules that you, the player, made to make sure some toys are played with (like a "play with" sign).

It checks these rules in a certain order, and if any of them say "don't play with this toy", it will say "yes, don't play with this toy". If none of them say that, it will say "yes, play with this toy".
---

# reload ELIV

Imagine you have a big box full of toys, and you want to add some new toys to the box. But, you can't just add them without looking inside the box first. 

The "reload" method is like a special button that says, "Hey, let's look inside the box again!" It helps the computer find the new toys (or patterns) that were added, so it can use them. It's like a key that opens the box and shows you what's inside.