# Competition Overview

Google has released open-weight models designed to help developers more efficiently create novel healthcare and life science applications. Many clinical environments can’t rely on large, closed models that require constant internet access or centralized infrastructure. They need adaptable, privacy-focused tools that can run anywhere care is delivered.

MedGemma and the rest of the HAI-DEF collection gives developers a starting point for building powerful tools while allowing them full control over the models and associated infrastructure.

The competition requires us to use these models to build full fledged demonstration applications that can enhance healthcare. Examples include apps to streamline workflows, support patient communication, or facilitate diagnostics.

## Minimum requirements

To be considered a valid contribution, your submission should include:

* a high-quality writeup describing use of a specific HAI-DEF model,  
* associated reproducible code for your initial results, and  
* a video for judging.

Your complete submission consists of a single package containing your video (3 minutes or less) and write-up (3 pages or less). This single entry can be submitted to the main competition track, and one special technology award, so separate submissions are not required. Read the section *Submission Instructions* for more details. Please follow the provided write-up template and refer to the judging criteria for all content requirements.

## Judging Criteria

1. Effective use of HAI-DEF models (weighting \= 20%)  
   1. Are HAI-DEF models used appropriately?  
   2. Are HAI-DEF models used to their fullest potential?  
   3. Why is this solution and its use of HAI-DEF models superior to other ones?  
   4. At least one of HAI-DEF models such as MedGemma is mandatory  
2. Problem Domain (weighting \= 15%)  
   1. How important is this problem to solve?  
   2. How plausible is it that AI is the right solution?  
   3. Is your storytelling unbeliably captivating and inspiring?  
   4. Is your problem definition clear?  
   5. Is the unmet need true and clear?  
   6. Is the problem of large magnitude in severity and ubiquity?  
   7. Who is the target user?  
   8. Does the solution genuinely improve the user journey?  
3. Impact potential (weighting \= 15%)  
   1. If the solution works, what impact would it have?  
   2. Have you clearly and honestly articulated the real and/or anticipated impact of the application within the given problem domain?  
   3. Have you honestly and accurately calculated your estimates, and what are those estimates?  
4. Product feasibility (weighting \= 20%)  
   1. Is the technical solution clearly feasible?  
   2. Have you accurately and completely detailed model fine-tuning, model’s performance analysis, user-facing application stack, deployment challenges and how you plan on overcoming them?  
   3. Have you communicated exactly how a product might be used in practice?  
5. Execution and communication (weighting \= 30%)  
   1. Is the quality of your project world-class?  
   2. Is the communication of your work concise (using as few words as possible to most completely and comprehensibly communicate information)?  
   3. Does the submission package follow the provided template, including a video demo and a write-up with links to source material?  
      1. Do you have a public interactive live demo app?  
      2. Open-weight Hugging Face model tracing to a HAI-DEF model?   
   4. Is your communication in the video of maximal clarity?  
   5. Is the video polished and stylish?  
   6. Does the video effectively communicate and demonstrate your application?  
   7. Is your technical write-up easy-to-read?  
   8. Is your source code organised, annotated and reusable?  
   9. Do you have a cohesive and compelling narrative across all submitted materials that effectivley articulates how you meet the rest of the judging criteria?

## Dataset Description

Welcome to the MedGemma Impact Challenge

This is a Hackathon with no provided dataset.

Please refer to the following resources, and note that use of HAI-DEF and MedGemma are subject to the [HAI-DEF Terms of Use](https://developers.google.com/health-ai-developer-foundations/terms):

* Hugging Face model collections:  
  * [Complete HAI-DEF collection](https://huggingface.co/collections/google/health-ai-developer-foundations-hai-def)  
  * [MedGemma collection](https://huggingface.co/collections/google/medgemma-release)  
* [Developer forum](https://discuss.ai.google.dev/c/hai-def)  
* [HAI-DEF concept apps for inspiration](https://huggingface.co/collections/google/hai-def-concept-apps)  
* [HAI-DEF main site](https://goo.gle/hai-def)

# Goal

1. Win the Main Track 1st place prize ($30,000)  
   1. this prizes are awarded to the best overall project that demonstrate exceptional vision, technical execution, and potential for real-world impact.  
2. Wins one of the special track prizes ($$5000)  
   1. Agentic Workflow Prize \- It is awarded for the project that most effectively reimagines a complex workflow by deploying HAI-DEF models as intelligent agents or callable tools. The winning solution will demonstrate a significant overhaul of a challenging process, showcasing the power of agentic AI to improve efficiency and outcomes.  
   2. Novel Task Prize \- Awarded for the most impressive fine-tuned model that successfully adapts a HAI-DEF model to perform a useful task for which it was not originally trained on pre-release.  
   3. The Edge AI Prize \- This prize is awarded to the most impressive solution that brings AI out of the cloud and into the field. It will be awarded to the team that best adapts a HAI-DEF model to run effectively on a local device like a mobile phone, portable scanner, lab instrument, or other edge hardware.

# Constraints

1. Complete the product in 3 days (using an AI tool like Claude or Codex to do this successfully)  
   * Assuming I have 8 hours per day to complete the product (24 hours in total)  
2. Writeup structure  
   * \#\#\# Project name   
   * \[A concise name for your project.\]  
   *   
   * \#\#\# Your team   
   * \[Name your team members, their speciality and the role they played.\]  
   *   
   * \#\#\# Problem statement  
   * \[Your answer to the “Problem domain” & “Impact potential” criteria\]  
   *   
   * \#\#\# Overall solution:   
   * \[Your answer to “Effective use of HAI-DEF models” criterion\]   
   *   
   * \#\#\# Technical details   
   * \[Your answer to “Product feasibility” criterion\]

# Target Timeline

**Thursday 12 February**

1. Conjecture the best possible ideas to maximise chance of winning the competition within the constraints and pick the best one  
   1. Use Claude Opus 4.6, ChatGPT 5.2 Thinking, Gemini 3 Pro, and Grok Thinking to conjecture ideas and pick the best one  
2. Use OpenClaw to compile all the useful information as context (saved to a Google Docs titled “Additional Competition Context”) to use to create PRDs (Project Requirement Documents) along with “MedGemma High-Level Context.md”  
3. Use Claude Opus 4.6 Extended to create first-draft version of the PRDs  
4. Review and edit the PRDs as needed  
5. Feed preliminary PRDs to Lovable PRD Generator along with “MedGemma High-Level Context.md”, “Additional Competition [Context.md](http://Context.md)”, and “Clarke\_Product\_Specifcation\_V1.md” and any other requests/context   
6. Use Lovable PRD Generator to create new and improved PRDs  
7. Select, review and edit the final PRDs as needed  
8. Complete planning and preparation of guiding Project-Requirements-Documents (PRDs)  
   1. clarke\_PRD\_masterplan.md   
      1. This file should provide a complete, high-level overview of what we’re building, why we’re building it, the goals, and the constraints  
         1. What are we building?  
         2. Why are we building it?  
         3. Why is it important?  
         4. What are the goals?  
         5. What are the constraints?  
         6. What must be fulfilled to guarantee a successful outcome?  
   2. clarke\_PRD\_implementation.md  
      1. This file should outline the order in which we should build and integrate components of the product to ensure there is a clean, understandable sequence  
         1. What steps must we take to ensure a successful outcome?  
         2. What is the optimal order for us to take those steps to guarantee a successful outcome with the constraints?  
   3. clarke\_PRD\_design\_guidelines.md  
      1. This file should detail the visual aesthetics of the product and how it should make the user feel when using it  
         1. What should the product look like?  
         2. What should the product feel like?  
         3. Give examples using Mobbin or Dribbble or anything else about the aesthetics and vibe I want to cultivate  
   4. clarke\_PRD\_userflow.md  
      1. This file should detail the intended user experience and journey, optimising for ease of use and navigation  
         1. What is the optimal the step-by-step description of the idea user navigation journey from very start to finish?  
   5. clarke\_PRD\_technical\_spec.md  
      1. **Folder/file structure** — the exact project directory tree Codex should create  
      2. **Technology stack** — every framework, library, and version (e.g., Gradio 4.x, transformers 4.45, torch 2.x)  
      3. **Data models/schemas** — what objects exist in the system (Patient, Consultation, Transcript, ClinicalDocument), their fields, types, and relationships  
      4. **API contracts** — what each backend endpoint accepts and returns  
      5. **Model serving specification** — how each HAI-DEF model is loaded, called, and what input/output format it expects  
      6. **Synthetic data spec** — exact format of demo data (FHIR resources, sample transcripts, lab reports) so Codex can generate it  
   6. clarke\_PRD\_tasks.md  
      1. This file should very explicitly detail every single, step-by-step task that the AI tool (e.g. Codex) should execute on to culminate in a product that completely, without fail, achieves the goal within the constraints  
         1. What are the specific tasks the AI should execute on to successfully build a world-class product and fulfil our goal?  
         2. for each task, specify what "done" looks like. For example, "Task 3 is done when the /transcribe endpoint accepts a .wav file and returns JSON with a transcript field."  
   7. clarke\_PRD\_rules.md  
      1. This file should convey how the LLM/AI tool should behave, communicate and execute actions and correct errors to ensure maximal speed, accuracy, effectiveness, transparency and efficiency  
         1. What information can I communicate to the AI to ensure the best possible comprehension and communication of information and execution of action?

**Friday 13 February to Sunday 15th February**

1. Complete building of the product  
   1. AI tool should first read and understand all the files. There should be some sort of test to check and ensure the AI has read and understood all the files before starting.  
   2. The AI should then execute one task at a time (using tasks.md), making sure to explain everything and every step that it is doing in a way that a layman could understand as well as testing or creating a way to test that the task has indeed been completed successfully  
      1. The AI should also correct any errors that arise in the execution

**Monday 16th February**

1. Complete the 3-page write up for the competition submission  
   1. The writeup should use the “Propose Writeup template”  
   2. The writeup should ensure that it completely satisfies and exceeds the judging criteria to maximise chance of achieving the goal  
   3. The writeup should be as high-level and easy-to-read as possible

**Tuesday 17th February to Saturday 21st February**

1. Complete the 3-minute video  
   1. The video will be the main, attention-grabbing medium of communication so should be optimised to exceed every aspect of the judging criteria 

**Sunday 22nd February**

1. Submit everything  
   1. 3-page writeup  
   2. Video (3 mins or less)  
   3. Public code repository  
   4. PUblic interactive live demo app  
   5. Open-weight Hugging Face model tracing to a HAI-DEF model