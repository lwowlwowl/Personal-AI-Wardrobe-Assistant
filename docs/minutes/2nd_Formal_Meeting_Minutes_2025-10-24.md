# 2nd Formal Meeting Minutes

**Date:** Friday, 2025-10-24
**Time:** 13:30 – 14:30 
**Place:** IEB 520



## Abstract 

The second formal meeting focused on consolidating research directions and defining technical tasks for the next stage of the project. The meeting reviewed the progress of the four model research directions and discussed model inference efficiency, platform selection justification, and the logical design of aesthetic-based outfit recommendations.

Further plans were made to extend research on Qwen3 deployment (local, API, AutoDL), data storage security, and user experience design. The team agreed to produce comprehensive UML diagrams, finalize background and requirement documentation, and complete backend implementation before the midterm report.

The meeting concluded with confirmed deadlines, assigned research responsibilities, and a reaffirmed emphasis on user-centered design and system scalability.



## 1. Participants

|    Member    |   Role    | Present / Apology |
| :----------: | :-------: | :---------------: |
| Haochen Wang |   /   |      Present      |
|  Jilin Song  |     Secretary     |Present|
|  Ruixi Yang  |     /     |      Present      |
|  Yuchen Fan  |     /     |      Present      |
| Jiajun Chen  | Chair |      Present      |



## 2. Agenda

- Confirm the full checklist and sign.
- Briefly summarize the four model research directions discussed in the previous week.
- Extend existing research.
  - Model deployment schemes (local, API, or AutoDL).
- Further research required.
  - Aesthetic-based outfit matching.
  - Justification for platform selection (e.g., WeChat Mini Program).
  - Project background and requirement specification.
  - Data storage and privacy protection design.
- Confirm the project timeline and key milestones.



## 3. Main Discussion Points

- In-depth Research Required

  - Comparison between **models** in terms of inference time and quality.
  - Evaluation of LLMs for **deployment strategy** and their **functionalities** within the project (e.g., recommendation tasks).
  - **Platform evaluation:** software/hardware justification, backend support libraries, and specific technologies to be adopted.
  - **Project background:** analysis of current systems, user evaluations, performance, and the rationale for developing our system.
  - Aesthetic recommendation logic

- Post-Research Deliverables

  - Creation of all **UML diagrams**.

- System Expandability (e.g. quality assessment regression module)

- Timeline and Deliverables

  | Milestone                               | Deliverables                                                 |
  | --------------------------------------- | ------------------------------------------------------------ |
  | Before the midterm report               | Complete all design work, background research, requirement documentation, and backend development |
  | Before the start of the spring semester | Achieve a 90% functional prototype                           |
  | During the spring semester              | Enhance UI design, add functionalities, conduct testing, distribute questionnaires, and finalize the report. |

- Strong emphasis on **user experience** (user-friendly interface and smooth visual interaction)



## 4. Possible Encounter and Utilize

- Insufficient GPU Resources
  - Deploy large-scale models on AutoDL during the testing phase only.
- High API Cost and Token Control
  - Maintain a quantized local Qwen3 version as a low-cost alternative.
- Unclear User Needs
  -  Integrate user satisfaction questionnaires during the testing phase.



## 5. Action Points

### 5.1 General

| Task                                                         | Responsible  | Deadline |
| ------------------------------------------------------------ | ------------ | -------- |
| Finalize full checklist, information form, consent form and questionnaire | Haochen Wang | Oct 28   |
| Construct and deploy the project website                     | Haochen Wang | Oct 28   |
| Design a low-fidelity prototype                              | Haochen Wang | Oct 31   |



### 5.2 Research 

#### 5.2.1 Research on Virtual Try-on Models

| **Research Focus**                         | Responsible             | Deadline |
| ------------------------------------------ | ----------------------- | -------- |
| **Qwen-image-edit**                        | Yuchen Fan              | Oct 31   |
| **Diffusion-based Virtual Try-on Models ** | Jilin Song              | Oct 31   |
| **Comparison and Deployment Feasibility**  | Yuchen Fan & Jilin Song | Oct 31   |



#### 5.2.2 Research on **Evaluation and Recommendation LLMs**

| **Research Focus** | Responsible | Deadline |
| ------------------ | ----------- | -------- |
| **Qwen3**          | Ruixi Yang  | Oct 31   |



#### 5.2.3 Research on **Outfit Recommendation Logic and Rules**

| **Research Focus**               | Responsible | Deadline |
| :------------------------------- | :---------- | :------- |
| **Outfit Recommendation Logic ** | Jiajun Chen | Oct 31   |



#### 5.2.4 Research on **Market Background and Competitive Analysis**

| **Research Focus**                               | Responsible & Deadline |
| :----------------------------------------------- | :--------------------- |
| **Competitive Analysis & Project Justification** | To be confirmed        |



#### 5.2.5 Research on **Platform**

| **Research Focus**     | Responsible & Deadline |
| :--------------------- | :--------------------- |
| **Platform Selection** | To be confirmed        |



#### 5.2.6 Research on **Data Storage Methods**

| **Research Focus**            | Responsible & Deadline |
| ----------------------------- | ---------------------- |
| **Database and Data Storage** | To be confirmed        |




---

## 7. Next Formal Meeting

**Date:** Friday, 2025-10-31
**Time:** 13:30 - 14:30
**Place:**  IEB-520