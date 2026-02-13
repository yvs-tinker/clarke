# **Additional Competition Context — MedGemma Impact Challenge**

*Compiled 2026-02-12 from systematic review of Kaggle competition pages, discussions, rules, and HAI-DEF developer documentation.*

### **Key NEW findings not in Clarke spec:**

1. **Submission is a Kaggle Writeup (not a file upload)** — created via the Writeups tab, with a Submit button. One submission per team, can re-submit.  
2. **3 pages \= \~1,500 words** (host clarification). With images, aim for 1,000-1,200 words.  
3. **12 named judges** — all Google Research/Health AI staff. Profiles documented.  
4. **Judged as DEMO, not production** — Yun Liu explicitly said regulatory pathway is NOT the focus. Focus is technical demonstration.  
5. **Non-commercial training data is OK** — Daniel Golden confirmed. Model weights release is BONUS not required.  
6. **MedGemma 4B has known instruction-following bugs** — leaks system prompts, generates meta-commentary. Risk for Clarke's EHR pipeline.  
7. **MedGemma 27B deployment is very hard** — needs \~54GB VRAM, Vertex AI A100 quotas being rejected. Unsloth GGUF quantizations available via Ollama (Q8\_0 \= 31.8GB).  
8. **MedGemma 1.5 4B adds EHR understanding** — directly relevant to Clarke. Should use 1.5 not 1.0.  
9. **MedASR runs in-browser via ONNX/WebGPU** — someone built it, could strengthen Edge AI track claim.  
10. **Only 129 submissions from 5,855 entrants** — competitive field may be smaller than expected.  
11. **Google explicitly suggests agentic orchestration** in their MedGemma docs — validates Clarke's architecture.

---

## **1\. Submission Requirements**

### **Submission Format: Kaggle Writeup (NOT a file upload)**

* Your submission is a **Kaggle Writeup** attached to the competition's Writeups page — not a PDF or file upload. Create via the "New Writeup" button at: [https://www.kaggle.com/competitions/med-gemma-impact-challenge/writeups](https://www.kaggle.com/competitions/med-gemma-impact-challenge/writeups)  
* After saving your Writeup, click the **"Submit"** button in the top right corner.  
* Each team gets **one (1) Writeup submission only**, but it can be un-submitted, edited, and re-submitted unlimited times before the deadline.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Submission Instructions section)

### **3-Page Limit Clarification**

* The "3 pages" translates to **\~1,500 words** single-spaced. If using charts/images/code blocks, aim for **1,000–1,200 words** of text.  
* **Source:** Fereshteh Mahvar (Competition Host) at [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671156](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671156)

### **Required Links in Writeup**

* **Required:** Video (3 min or less)  
* **Required:** Public code repository  
* **Bonus:** Public interactive live demo app  
* **Bonus:** Open-weight Hugging Face model tracing to a HAI-DEF model  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Submission Instructions)

### **Track Selection**

* All submissions automatically compete in the **Main Track**.  
* You may select **one** special award prize (Agentic Workflow, Novel Task, or Edge AI).  
* If you select multiple special awards, only one will be considered (randomly selected).  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Choosing a Track)

### **Writeup Template (exact structure required)**

\#\#\# Project name  
\#\#\# Your team \[Name members, speciality, role\]  
\#\#\# Problem statement \[Problem domain \+ Impact potential criteria\]  
\#\#\# Overall solution \[Effective use of HAI-DEF models criterion\]  
\#\#\# Technical details \[Product feasibility criterion\]

* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Proposed Writeup template)

### **Private Resources Warning**

* If you attach a **private** Kaggle Resource to your public Writeup, it will be **automatically made public** after the deadline.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview)

### **Submissions Must Be in English**

* Confirmed by María Cruz (Kaggle Staff).  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660)

---

## **2\. Judging Details**

### **Full Judge Panel (12 judges)**

| Judge | Role |
| ----- | ----- |
| Fereshteh Mahvar | Staff Medical Software Engineer & Solutions Architect, Google Health AI |
| Omar Sanseviero | Developer Experience Lead, Google DeepMind |
| Glenn Cameron | Sr. PMM, Google |
| Can "John" Kirmizi | Software Engineer, Google Research |
| Andrew Sellergren | Software Engineer, Google Research |
| Dave Steiner | Clinical Research Scientist, Google |
| Sunny Virmani | Group Product Manager, Google Research |
| Liron Yatziv | Research Engineer, Google Research |
| Daniel Golden | Engineering Manager, Google Research |
| Yun Liu | Research Scientist, Google Research |
| Rebecca Hemenway | Health AI Strategic Partnerships, Google Research |
| Fayaz Jamil | Technical Program Manager, Google Research |

**Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Judges section)

### **Evaluation is Through Demonstration Application Lens**

* Judges evaluate through the lens of a **demonstration application, NOT a finished product**.  
* Regulatory pathway, HIPAA/GDPR compliance, etc. are **not the focus** of evaluation criteria — though you may include them.  
* Quote from Yun Liu (Competition Host): *"The focus of the evaluation criteria is the technical aspects of the demonstration application. Each evaluation criteria will be judged through the lens of a demonstration application and not a finished product."*  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/668280](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/668280)

### **Execution & Communication is the Highest-Weighted Category (30%)**

* Judges look for a **"cohesive and compelling narrative across all submitted materials"** that articulates how you meet the rest of the criteria.  
* Assess: clarity/polish/effectiveness of video demo, completeness/readability of writeup, quality of source code (organization, comments, reusability).  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Evaluation Criteria table)

---

## **3\. Rules & Restrictions**

### **Team Size**

* Maximum **5 members** per team.  
* Team mergers allowed before Team Merger Deadline.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.1)

### **One Submission Per Team**

* For Hackathons, each team is allowed **one (1) Submission**.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.2)

### **Winner License: CC BY 4.0**

* Winning submissions must be licensed under **CC BY 4.0** (code and demos).  
* For generally commercially available software you used but don't own, you don't need to grant that license.  
* For input data or pretrained models with incompatible licenses used to generate your winning solution, you **don't need to grant** open source license for that data/model.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.5)

### **Non-Commercial Data is Allowed for Training**

* Using public, research-only / non-commercial external datasets during development is **permitted**.  
* Participation in a Kaggle challenge is **not considered commercial use**.  
* Releasing final model weights is a **bonus, not a requirement**.  
* Daniel Golden (Competition Host) quote: *"You are permitted to use data and other code sources during development that are governed under other, potentially more restrictive licenses."*  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671596](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671596)

### **External Data & Tools**

* External data allowed if **publicly available and equally accessible** to all participants at no cost, or meets the "Reasonableness Standard".  
* Use of HAI-DEF and MedGemma subject to **HAI-DEF Terms of Use**: [https://developers.google.com/health-ai-developer-foundations/terms](https://developers.google.com/health-ai-developer-foundations/terms)  
* Automated ML tools (AutoML, H2O, etc.) are permitted with appropriate licensing.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.6)

### **HAI-DEF Terms Key Restrictions**

* **"Clinical Use"** (diagnosis/treatment of patients) requires Health Regulatory Authorization — this doesn't apply to a demo/competition context.  
* HAI-DEF source code licensed under **Apache 2.0**.  
* Models are free for research and commercial use.  
* **Source:** [https://developers.google.com/health-ai-developer-foundations/terms](https://developers.google.com/health-ai-developer-foundations/terms)

### **Mandatory HAI-DEF Model Usage**

* Use of **at least one HAI-DEF model** (such as MedGemma) is **mandatory**.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Effective use of HAI-DEF models criterion)

### **Eligibility**

* Must be 18+, registered on Kaggle, not resident of sanctioned countries.  
* Competition Entities (Google, Kaggle employees) can participate but **cannot win prizes**.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.7, 3.1)

### **Winner's Obligations**

* Deliver final model's software code \+ documentation.  
* Code must be capable of generating the winning submission.  
* Must describe resources required to build/run.  
* For hackathons, deliverables are as described on the competition website (may not be software code).  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.8)

### **No Cloud Credits Provided**

* Multiple competitors asked about GCP credits / Colab compute — no response from organizers confirming any credits.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660)

---

## **4\. Winning Patterns & Insights from Discussions**

### **Focus on Demonstration, Not Production**

* The organizers repeatedly emphasize this is about **demonstration applications** with impact potential, not production-ready systems. Keep the writeup high-level; use the video to convey concepts.  
* *"Less is more\! You should take advantage of the video to convey most of the concepts and keep the write-up as high level as possible."*  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Submission Instructions)

### **Storytelling is Explicitly Scored**

* Problem Domain criterion explicitly mentions **"storytelling"** alongside clarity of problem definition.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Evaluation Criteria)

### **Use HAI-DEF Models "to Their Fullest Potential"**

* The criterion asks whether your application uses HAI-DEF models *"to their fullest potential, where other solutions would likely be less effective"*.  
* Clarke's multi-model approach (MedASR \+ MedGemma 4B \+ MedGemma 27B) is well-aligned with this.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Evaluation Criteria)

### **Agentic Orchestration is Officially Suggested**

* Google's own MedGemma documentation explicitly suggests agentic orchestration: using MedGemma as a tool within an agentic system, coupled with FHIR generators/interpreters, Gemini Live for bidirectional audio, or Gemini 2.5 Pro for function calling.  
* MedGemma can **"parse private health data locally before sending anonymized requests to centralized models"** — directly supports Clarke's privacy-preserving architecture.  
* **Source:** [https://developers.google.com/health-ai-developer-foundations/medgemma](https://developers.google.com/health-ai-developer-foundations/medgemma)

### **Competition Scale: Low Submissions So Far**

* 5,855 entrants but only **129 submissions** (134 participants, 129 teams) as of Feb 12 2026\.  
* This suggests many entrants haven't submitted yet — the field may be smaller than expected.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview](https://www.kaggle.com/competitions/med-gemma-impact-challenge/overview) (Participation stats)

### **MedGemma 1.5 is the Latest Version**

* MedGemma 1.5 4B (google/medgemma-1.5-4b-it) was released in Jan 2026 with improved capabilities:  
  * High-dimensional medical imaging (CT, MRI, histopathology)  
  * Longitudinal medical imaging (chest X-ray time series)  
  * Medical document understanding (structured extraction from lab reports)  
  * EHR understanding (interpretation of text-based EHR data)  
  * Improved medical text reasoning accuracy  
* **Source:** [https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/](https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/)

---

## **5\. Technical Resources**

### **Official Notebooks & Code**

| Resource | URL |
| ----- | ----- |
| Quick start (Hugging Face) | [https://github.com/google-health/medgemma/blob/main/notebooks/quick\_start\_with\_hugging\_face.ipynb](https://github.com/google-health/medgemma/blob/main/notebooks/quick_start_with_hugging_face.ipynb) |
| Quick start (Model Garden) | [https://github.com/google-health/medgemma/blob/main/notebooks/quick\_start\_with\_model\_garden.ipynb](https://github.com/google-health/medgemma/blob/main/notebooks/quick_start_with_model_garden.ipynb) |
| Fine-tuning with LoRA | [https://github.com/google-health/medgemma/blob/main/notebooks/fine\_tune\_with\_hugging\_face.ipynb](https://github.com/google-health/medgemma/blob/main/notebooks/fine_tune_with_hugging_face.ipynb) |
| Reinforcement Learning | [https://github.com/Google-Health/medgemma/blob/main/notebooks/reinforcement\_learning\_with\_hugging\_face.ipynb](https://github.com/Google-Health/medgemma/blob/main/notebooks/reinforcement_learning_with_hugging_face.ipynb) |
| MedGemma GitHub repo | [https://github.com/google-health/medgemma](https://github.com/google-health/medgemma) |
| HAI-DEF developer forum | [https://discuss.ai.google.dev/c/hai-def/](https://discuss.ai.google.dev/c/hai-def/) |

### **MedASR Resources**

| Resource | URL |
| ----- | ----- |
| MedASR model (HuggingFace) | [https://huggingface.co/google/medasr](https://huggingface.co/google/medasr) |
| MedASR developer docs | [https://developers.google.com/health-ai-developer-foundations/medasr/](https://developers.google.com/health-ai-developer-foundations/medasr/) |
| MedASR in-browser (ONNX/WebGPU) | [https://medasr.ainergiz.com/](https://medasr.ainergiz.com/) |
| MedASR in-browser source | [https://github.com/ainergiz/medasr-web](https://github.com/ainergiz/medasr-web) |
| MedASR MLX (Apple Silicon) | Discussion: [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/672879](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/672879) |
| MedASR ONNX export script | In ainergiz/medasr-web repo at /scripts/export\_onnx.py |

### **MedGemma 27B GGUF Quantizations (Unsloth)**

* Available at: [https://huggingface.co/unsloth/medgemma-27b-it-GGUF/tree/main](https://huggingface.co/unsloth/medgemma-27b-it-GGUF/tree/main)  
* Can run locally via Ollama: ollama run hf.co/unsloth/medgemma-27b-it-GGUF:Q8\_0 (31.8 GB)  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091)

### **HuggingFace Collections**

| Collection | URL |
| ----- | ----- |
| MedGemma release | [https://huggingface.co/collections/google/medgemma-release-680aade845f90bec6a3f60c4](https://huggingface.co/collections/google/medgemma-release-680aade845f90bec6a3f60c4) |
| HAI-DEF collection | [https://huggingface.co/collections/google/health-ai-developer-foundations-hai-def](https://huggingface.co/collections/google/health-ai-developer-foundations-hai-def) |
| Community fine-tunes | [https://huggingface.co/models?other=or:base\_model:finetune:google/medgemma-4b-it,base\_model:finetune:google/medgemma-4b-pt,base\_model:finetune:google/medgemma-27b-it,base\_model:finetune:google/medgemma-27b-text-it](https://huggingface.co/models?other=or:base_model:finetune:google/medgemma-4b-it,base_model:finetune:google/medgemma-4b-pt,base_model:finetune:google/medgemma-27b-it,base_model:finetune:google/medgemma-27b-text-it) |

### **Key Blog Posts**

| Title | URL |
| ----- | ----- |
| MedGemma 1.5 \+ MedASR announcement | [https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/](https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/) |
| Original MedGemma blog | [https://research.google/blog/medgemma-our-most-capable-open-models-for-health-ai-development/](https://research.google/blog/medgemma-our-most-capable-open-models-for-health-ai-development/) |
| HAI-DEF launch blog | [https://research.google/blog/helping-everyone-build-ai-for-healthcare-applications-with-open-foundation-models/](https://research.google/blog/helping-everyone-build-ai-for-healthcare-applications-with-open-foundation-models/) |
| AskCPG concept integration | [https://discuss.ai.google.dev/t/sharing-our-product-integration-with-medgemma-askcpg/94556](https://discuss.ai.google.dev/t/sharing-our-product-integration-with-medgemma-askcpg/94556) |

### **Notable Competition Notebooks (for inspiration)**

| Notebook | Theme |
| ----- | ----- |
| MedFlow AI (24 upvotes) | Top-voted notebook |
| MedGemma Navigator: DICOMweb ↔ FHIR (16 upvotes) | FHIR/DICOM integration — similar to Clarke's EHR focus |
| MedGemma Medical AI Chatbot \+ 5 Test Scenarios (14 upvotes) | Medical chatbot with test scenarios |
| MedAssist Edge Offline Medical AI (7 upvotes) | Offline/edge deployment |
| Spasht AI — Bridging India's "Last Mile" Health Gap (6 upvotes) | Community health focus |
| RadAssist-MedGemma: AI Radiology Triage Assistant (4 upvotes) | Radiology triage |
| CRSA — Clinical Reasoning Stability Auditor | Reasoning evaluation |

**Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/code](https://www.kaggle.com/competitions/med-gemma-impact-challenge/code)  
---

## **6\. Gaps & Risks**

### **MedGemma 4B Instruction Following Issues**

* Multiple competitors report MedGemma 4B (medgemma-1.5-4b-it) **leaking system prompts, generating meta-commentary, and outputting chain-of-thought training artifacts** (critique responses, constraint checklists, special tokens).  
* One user reports running with Ollama locally works well; the issues may be prompt/framework dependent.  
* **Risk for Clarke:** If using MedGemma 4B for EHR extraction, we need thorough prompt engineering and output parsing to handle instruction-following failures.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091)

### **MedGemma 27B Deployment is Extremely Challenging**

* Requires \~54GB VRAM — won't run on Apple M3 Max 64GB (MPS buffer limit), won't fit on 2x L4 GPUs (48GB).  
* Vertex AI A100 quota requests being **rejected by Google**.  
* Quantized GGUF versions (Unsloth Q8\_0 \= 31.8GB) can run via Ollama on local hardware.  
* **Risk for Clarke:** The 24-hour build plan assumes MedGemma 27B for letter generation. If deploying on Kaggle/cloud is blocked by GPU quota, we need a fallback (quantized 27B via Ollama, or enhanced 4B with heavy prompt engineering).  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/673091)

### **MedGemma 1.5 Only Available as 4B**

* MedGemma 1.5 is only released as 4B multimodal. The 27B model is still MedGemma 1 (text-only and multimodal).  
* **Risk for Clarke:** Clarke spec references "MedGemma 27B" — should clarify we're using MedGemma 1 27B, not 1.5.  
* **Source:** [https://developers.google.com/health-ai-developer-foundations/medgemma](https://developers.google.com/health-ai-developer-foundations/medgemma)

### **No Provided Dataset \= You Must Source Your Own**

* Competition provides **zero data**. All data must be sourced externally.  
* For Clarke: synthetic NHS consultation data or publicly available clinical note datasets needed. Non-commercial academic datasets are acceptable per organizer clarification.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules](https://www.kaggle.com/competitions/med-gemma-impact-challenge/rules) (Section 2.4)

### **Model Weights Release is Bonus, Not Required**

* Releasing fine-tuned model weights on HuggingFace is listed as a **bonus** submission element, not mandatory.  
* However, it could significantly strengthen the "Effective use of HAI-DEF models" score.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671596](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/671596) (Daniel Golden's response)

### **EHR/FHIR Understanding is a New MedGemma 1.5 Capability**

* MedGemma 1.5 4B specifically adds **"EHR understanding for the interpretation of text-based EHR data"** — this directly supports Clarke's EHR navigation component.  
* Consider using MedGemma 1.5 4B (instead of 1.0 4B) for the EHR extraction pipeline.  
* **Source:** [https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/](https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/)

### **Official Discord Exists But Not Monitored by Staff**

* Kaggle Discord at [http://discord.gg/kaggle](http://discord.gg/kaggle) — additional discussion channel, but organizers don't monitor it.  
* **Source:** [https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660](https://www.kaggle.com/competitions/med-gemma-impact-challenge/discussion/667660)

---

## **Pages That Could Not Be Accessed**

| URL | Issue |
| ----- | ----- |
| Kaggle discussion threads via web\_fetch | JS-rendered, required browser automation |
| Kaggle Code notebooks (content) | Would require login/browser to read notebook code cells |
| AskCPG concept app details | [https://discuss.ai.google.dev/t/sharing-our-product-integration-with-medgemma-askcpg/94556](https://discuss.ai.google.dev/t/sharing-our-product-integration-with-medgemma-askcpg/94556) — not fetched |
| MedGemma model card | [https://developers.google.com/health-ai-developer-foundations/medgemma/model-card](https://developers.google.com/health-ai-developer-foundations/medgemma/model-card) — not fetched |
| MedASR developer docs | [https://developers.google.com/health-ai-developer-foundations/medasr/](https://developers.google.com/health-ai-developer-foundations/medasr/) — not fetched |
| HAI-DEF Terms of Use (full) | [https://developers.google.com/health-ai-developer-foundations/terms](https://developers.google.com/health-ai-developer-foundations/terms) — truncated at Section 3 |

