# logger ELIV


---

# _RESET ELIV


---

# _RED ELIV


---

# _CLEAR_SCREEN ELIV


---

# _INVERSE ELIV


---

# _INVERSE_OFF ELIV


---

# BudgetExceededError ELIV


---

# __init__ ELIV


---

# FileProcessResult ELIV


---

# TraceResult ELIV


---

# _get_tldr_meta_path ELIV


---

# _compute_source_hash ELIV


---

# _compute_symbol_hash ELIV


---

# _read_freshness_meta ELIV


---

# _is_up_to_date ELIV


---

# _module_to_file_path ELIV


---

# export_call_graph ELIV


---

# get_downstream_impact ELIV


---

# export_knowledge_graph ELIV


---

# find_stale_files ELIV


---

# _write_freshness_meta ELIV


---

# TLDR_MODEL ELIV


---

# DEEP_MODEL ELIV


---

# ELIV_MODEL ELIV


---

# _resolve_doc_model ELIV


---

# _DIRECTORY_PATTERNS ELIV


---

# _GROQ_SPECS_PATH ELIV


---

# get_model_specs ELIV


---

# _safe_workers_from_rpm ELIV


---

# _max_concurrent_from_rpm ELIV


---

# _default_workers ELIV


---

# extract_source_snippet ELIV


---

# _fallback_template_content ELIV


---

# validate_generated_docs ELIV


---

# write_documentation_files ELIV


---

# _generate_single_symbol_docs ELIV


---

# _merge_symbol_content ELIV


---

# _generate_docs_for_symbols ELIV

This code helps make documents for things we found in a program. 

It looks at what we've already done and what we need to do. If something hasn't changed, it uses what we already have. If something has changed, it makes new documents for it.

It does this one thing at a time, so it doesn't get stuck. It also keeps track of how long it takes to make each document.

When it's all done, it puts all the documents together in the right order and saves them so we can use them again next time.
---

# _rel_path_for_display ELIV


---

# _trace_file ELIV


---

# _TRACE_COLORS ELIV


---

# _MAX_CHAIN_LEN ELIV


---

# _ARROW ELIV


---

# _strip_ansi ELIV


---

# _build_rolling_call_trace ELIV


---

# _format_single_hop ELIV


---

# _build_chain_from_hops ELIV


---

# process_single_file_async ELIV


---

# process_single_file ELIV


---

# _gather_package_component_roles ELIV


---

# _update_module_brief_async ELIV


---

# _update_module_brief ELIV


---

# _process_file_with_semaphore ELIV


---

# _format_status_bar ELIV


---

# process_directory_async ELIV

This function helps make documents for a computer program. It looks at all the files in a special folder and makes notes about what each file does. 

Here's what it does step by step:

1. It checks if the folder exists and is a real folder. If not, it says "oops, that's not a folder!"
2. It looks at all the files in the folder and makes a list of them.
3. If some files have changed, it only looks at those files.
4. It starts a special task to show a progress bar on the screen.
5. It starts many small tasks to look at each file one by one.
6. For each file, it tries to make a document about what the file does.
7. If it runs out of money (because it costs money to make documents), it stops working.
8. When it's done, it shows a final message on the screen.
---

# process_directory ELIV


---

# _synthesize_pr_description_async ELIV


---

# synthesize_pr_description ELIV


---

# parse_python_file ELIV

