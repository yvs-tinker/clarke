# Clarke — PRD Rules (Agent Behavioural Contract)

**Version:** 1.0 | **Date:** 13 February 2026 | **Author:** Project Lead  
**Status:** Final — governs AI agent (Codex) behaviour throughout the entire build  
**Parent document:** clarke_PRD_masterplan.md  
**Scope:** Agent execution behaviour, communication, error handling, coding standards, decision-making  
**Not in scope:** What to build (technical_spec.md), build order (tasks.md), visual design (design_guidelines.md), user journey (userflow.md)

**Load this file at the start of every session. It governs how you work, not what you build.**

---

## 1. Task Execution Protocol

1. **Read each task fully before writing any code.** Never skip ahead. Never combine tasks unless tasks.md explicitly batches them.
2. **Follow this execution cycle for every task:** Read → Explain → Execute → Explain → Verify → Report.
3. **Never mark a task complete until its verification method passes.** If verification fails, fix and re-verify. Do not move on.
4. **Never silently skip a task or sub-step.** If you cannot complete something, stop and explain why.
5. **When in doubt, ask. Never guess.** If a task requires a decision not covered by the PRDs, ask the user before proceeding.

---

## 2. Communication Standards

**Before each task:** Explain in 2–3 plain sentences what you are about to do and why. A non-technical person should understand.

**After each task:** State what was done, list every file created or modified, and report the verification result (pass/fail).

**When something unexpected happens** (version conflict, deprecation warning, model behaving unexpectedly): flag it immediately and explicitly. Do not bury it in output.

**When you encounter an error:** State the error, your diagnosis, your planned fix, then execute the fix. Narrate your debugging so the user can follow.

**Formatting rules:**
- Code in code blocks. File paths in backticks. Clear separation between explanation and code output.
- Keep explanations concise. No filler. No self-praise. No unnecessary caveats. State facts.

---

## 3. Code Quality Standards

1. **Every function must have a docstring** with a one-line summary, parameter types, and return type.
2. **Comments explain why, not what.** Do not restate the code in English.
3. **Follow the directory tree in technical_spec.md §1 exactly.** Do not create files outside the defined tree without asking.
4. **Use the exact package versions in technical_spec.md §2.** Do not upgrade or substitute libraries without asking.
5. **All names (variables, functions, files) must be descriptive** and consistent with conventions established in the first tasks.
6. **Never leave TODO comments, placeholder code, or incomplete implementations** without explicitly flagging them to the user.
7. **Never use `print()` for debugging in committed code.** Use `loguru` as defined in technical_spec.md §10c:
   ```python
   from loguru import logger
   logger.bind(component="module_name").info("Message", key=value)
   ```
8. **Write tests alongside functions.** Every new testable function gets a corresponding test immediately — do not wait for a dedicated testing task.

---

## 4. Error Handling Protocol

**When a verification step fails:**

1. Read the full error message.
2. Diagnose the most likely root cause.
3. State your diagnosis to the user.
4. Implement the fix.
5. Re-run verification.
6. If it fails with a **different** error, repeat from step 1.
7. If it fails with the **same** error after **3 attempts**, STOP and ask the user for guidance. Do not loop.

**When a known risk materialises** (e.g., MedGemma 27B OOM, MedGemma 4B instruction-following failure, FHIR server setup failure): immediately reference the fallback path from implementation.md §7 and tasks.md Appendix A. State: *"Known risk triggered. Switching to Fallback Path [X]."* Do not attempt to force the original approach.

**In all code:** Never suppress, catch-and-ignore, or silently swallow errors. Every error must be logged and either handled with a specific recovery action or surfaced to the user.

---

## 5. Decision-Making Rules

1. **PRD documents are the source of truth.** If your training knowledge conflicts with a PRD specification, follow the PRD.
2. **If two PRDs conflict,** flag the conflict and ask which takes precedence. Do not resolve conflicts silently.
3. **If a task is ambiguous,** ask for clarification. Do not choose an interpretation.
4. **If you discover a better approach** (more efficient library, simpler architecture), propose it with a clear tradeoff explanation. Do NOT implement without approval.
5. **Prioritise working software over perfect software.** Ship the feature, then refine. No premature optimisation unless the task explicitly calls for it.
6. **If you are uncertain your implementation is correct** (guessing at a model's input format, unsure a library supports a method), say so explicitly: *"I'm not certain this is correct because [reason]. I recommend we verify before proceeding."* Never write confident code based on uncertain knowledge. Admitting uncertainty upfront wastes less time than fabricating plausible-looking code that doesn't work.

---

## 6. Context Management

1. **At the start of each phase** (as defined in tasks.md Appendix B), confirm which PRD files are loaded and ask for any that are missing.
2. **If your context window is getting large** and performance degrades, tell the user proactively: *"My context is getting long. I recommend starting a fresh session with [specific PRD files] loaded for the next phase."*
3. **Never hallucinate PRD contents.** If you need information from a file not in your current context, ask the user to provide it.
4. **When resuming mid-build in a new session,** before proceeding: (a) confirm which PRD files are loaded, (b) list the project directory and check key files, (c) run the full test suite, (d) report what's passing and what's not. Never assume the codebase is in a good state just because the user says "continue from Task N."

---

## 7. Regression Awareness

1. **Before modifying any existing file, read its current state first.** Do not overwrite working code with assumptions.
2. **When modifying code from previous tasks,** re-run the relevant previous tests — not just the current task's verification.
3. **At phase checkpoints,** run the full test suite as specified in tasks.md.

---

## 8. Speed and Efficiency

1. **Do not ask for confirmation on decisions clearly specified in the PRDs.** Just do them.
2. **Do not re-read or re-summarise PRD files between tasks** within the same session. Carry the context forward.
3. **Batch boilerplate work.** When creating repetitive files (e.g., multiple similar data models), create them together rather than one per conversation turn.
4. **Copy specifications verbatim** (JSON schemas, directory trees, config values) rather than retyping them — transcription errors waste time.

---

## 9. Progress Tracking

1. **At each phase checkpoint,** report: tasks complete out of total, which phase just finished, elapsed time vs. estimated time from implementation.md §3.
2. **If a phase took 50%+ over its estimate,** proactively flag it: *"Phase X took [Y] hours vs [Z] estimated. At this pace, we may need buffer week time for [remaining phases]. Consider deprioritising Polish tasks."*
3. **If the user asks "how are we tracking?",** give an honest assessment against the implementation timeline. No optimistic spin.

---

*This document governs Codex behaviour for the entire Clarke build. Re-read it at the start of every session. All execution decisions defer to this contract; all technical decisions defer to the other PRDs.*
