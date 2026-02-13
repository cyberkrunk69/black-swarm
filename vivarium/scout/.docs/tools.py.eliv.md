# _module_to_path ELIV

Imagine you have a big box of toys, and inside the box, there are smaller boxes with different names on them. This function is like a helper that finds the right box for you.

It takes two things: the name of the box you're looking for, and the name of the big box where all the smaller boxes are kept.

If you ask for a box that's inside another box, or if you ask for a box that doesn't exist, it says "I couldn't find it." But if it finds the right box, it tells you where it is, like "it's in the big box, in the middle shelf."
---

# _parse_imports ELIV

Imagine you have a big box of toys, and inside the box, there are some special cards that say "get me this toy" or "get me that toy". This function is like a helper that looks at those cards and finds the toys they want.

It reads through all the cards, one by one, and checks if they say "get me this toy" or "get me that toy". If they do, it tries to find the toy in the box. If it finds the toy, it adds the toy's name to a list.

The function then looks at the list and keeps only the first 15 toys it found. That's it!
---

# query_for_deps ELIV

Imagine you have a big box of toys, and inside the box, there are some toys that you need to play with. But, you also need some other toys from outside the box to play with those toys. 

This function, 'query_for_deps', is like a helper that finds out which toys you need from outside the box. It looks at a special list of toys (called a Python file) and says, "Oh, you need these toys from outside the box to play with these toys."

It then gives you a list of the toys you need from outside the box, so you can go get them. If it can't find the list of toys or if the toys are not in the right format, it says, "Sorry, I couldn't find what you need."