# _MODULE_MD_NAME ELIV


---

# _stem_for_file ELIV


---

# _find_package_root ELIV


---

# _read_module_summary ELIV


---

# assemble_pr_description ELIV


---

# _call_graph_summary_for_scope ELIV

This function helps us make a list of how different parts of a program talk to each other. 

It does this by reading a special file that has information about how the program parts talk to each other. 

It then looks at this information and makes a list of the parts that talk to each other. 

If a part of the program is inside a special area, it only looks at the parts that talk to other parts inside that area. 

It then shows us the list of parts that talk to each other, but only shows us the first 50 parts.
---

# assemble_pr_description_from_docs ELIV

This function helps make a special text for a computer program. It looks for some special files in a folder called ".docs". 

First, it checks if the ".docs" folder exists. If it doesn't, it says there's no folder.

Then, it finds all the files that end with ".tldr.md" inside the ".docs" folder. If there are no files, it says there are no files.

Next, it reads the text from each file and makes a list of the text. It also adds the name of the file (without the ".tldr.md" part) to the text.

After that, it puts all the text together with some special lines in between.

If we want to see a special graph, it looks for a file called "call_graph.json" in two places: in a folder called "vivarium/.docs" and in the ".docs" folder. If it finds the file, it adds the graph to the text.

Finally, it returns the text we made.
---

# assemble_commit_message ELIV

