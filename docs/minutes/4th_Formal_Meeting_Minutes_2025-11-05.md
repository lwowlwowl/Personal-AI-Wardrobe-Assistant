# 4nd Formal Meeting Minutes

**Date:** Wednesday, 2025-11-5
**Time:** 14:30 – 15:00 
**Place:** IEB 114



## Abstract 

The fourth project meeting centered on solidifying research directions and defining technical tasks for the next phase. Progress across the four model research paths was reviewed, with additional discussion on model inference efficiency, platform selection rationale, and the logical framework for aesthetic-based outfit recommendations.

Further planning included expanded research into Qwen3 deployment (local, API, AutoDL), data storage security, and user experience design. The team agreed to deliver comprehensive UML diagrams, finalize background and requirements documentation, and complete backend implementation ahead of the midterm report.

The meeting concluded with confirmed deadlines, assigned research responsibilities, and reinforced emphasis on user-centered design and system scalability.

Initial discussions were held regarding the utilization of large language models (LLMs) and findings from the model evaluation.
A simple prototype was reviewed, along with potential future enhancements.
Next steps will involve exploring the underlying logic of LLMs to clarify their capabilities and limitations,
as well as studying relevant papers and foundational concepts within the dataset.



## 1. Participants

|    Member    |   Role    | Present / Apology |
| :----------: | :-------: | :---------------: |
| Haochen Wang |   /   |      Present      |
|  Jilin Song  |  Chair |Present|
|  Ruixi Yang  |     /     |      Present      |
|  Yuchen Fan  |  Secretary   |      Present      |
| Jiajun Chen  | /|      Present      |



## 2. Agenda

- Finalize the model selection for the project.
- Briefly summarize the three model research directions discussed previously.
- Expand on existing research:
Initial discussion on the usage approaches for large language models (LLMs)
Initial dicussion on model deployment schemes (local, API, or AutoDL)
Review of the simple prototype and discussion on future enhancements
- Conduct further research on:
User profile creation and preference categorization
Brand and price-based preference analysis for recommendations
Two recommendation approaches:
  -Visual-based recommendation (color and style)
  -Comfort-based recommendation (temperature, humidity, material thickness) combined with aesthetic matching
Dataset research on clothing aesthetics
Literature review on outfit matching methods for LLM input
Full outfit image input methodology
Outfit evaluation and scoring after virtual try-on
Investigation of LLM capabilities and limitations
Study of relevant papers and foundational theories in the dataset
Use case definition (functional and non-functional requirements)
User story development
Platform selection justification (e.g., WeChat Mini Program)
Project background and requirement specifications
Data storage and privacy protection design
- Confirm project timeline and key milestones



## 3. Main Discussion Points

- In-depth Research Required

- Comparison between different models in terms of inference speed and output quality
- Evaluation of Large Language Models for deployment strategy and their specific functionalities within the project (e.g., recommendation tasks)
- Platform evaluation: software/hardware justification, backend support libraries, and specific technology stack selection
- Project background analysis: examination of existing systems, user evaluations, performance metrics, and rationale for developing our proposed system
- Research on aesthetic recommendation logic:
- First loading of Qwen-image-edit model takes longer - currently running locally via web interface using jilin host, code needs distinction between loading and non-loading states
5090 desktop setup with 7-8 seconds inference time is acceptable
- Consider internal network setup for demo day, network infrastructure in PMB hall
- LLM API costs (7-8/hour for debugging and final demonstration, focus on VRAM optimization) small size models
- Electronic description via LLM: cannot analyze user personality from images, but can analyze user preferences
- Optimization knowledge required for outfit matching logic - need to understand API underlying principles and prompt mapping
- Core functionality understanding of recommendation systems
- LLM consistency requirements
- Outfit matching at image level vs cognitive level (not yet found) - using rules for LLM comprehension, matching rules, natural language descriptions (aesthetics domain papers, color schemes, contrasting styles)
- Encoding rules through LLM: using "aesthetic logic" as role encoding for coordinated colors, contrasting styles, specific themes (e.g., Chinese style)
- Current implementation methods: learning from images and/or aesthetic rules (e.g., black-white-gray combinations), multiple rule learning
- Interface feasibility assessment
- Paper study required for underlying logic
- Clear understanding of what LLMs can and cannot do, and why

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

- Possible Challenges & Solutions
- Insufficient GPU Resources
- Deploy large-scale models on AutoDL specifically during the testing phase
- Maintain a quantized local version of Qwen3 as a low-cost backup solution
- High API Costs and Token Management
- Implement strict token usage monitoring and budgeting controls
- Utilize the local quantized Qwen3 version for routine development and testing
- Unclear or Evolving User Requirements
- Integrate user feedback mechanisms and satisfaction questionnaires during testing
- Conduct iterative prototype demonstrations to validate feature alignment with user expectations



## 5. Action Points

### 5.1 Requirement Documentation

| Task                               | Responsible | Deadline |
| ---------------------------------- | ----------- | -------- |
| Initial Requirement Document       | Ruixi Yang  | Nov 09   |
| Complete Requirement Specification | All members | Nov 11   |



### 5.2 Research aim
- Dataset and Model Investigation
- Conduct in-depth research on dataset models, focusing on understanding their underlying principles and operational mechanisms
- Explore methods for evaluating model features and performance metrics
- Investigate how to optimize LLM-generated prompts for better compatibility and synergy with these dataset models
- Proactively search for and review newly published research; ensure team-wide comprehension of relevant findings
- Identify and analyze aesthetic rules and principles
- Examine how consistent styles can be effectively interpreted and applied in recommendations

#### 5.2.1 UML Diagram


| Task                                                      | Responsible  | Deadline |
| --------------------------------------------------------- | ------------ | -------- |
| **User Case Diagram**                                     | Ruixi Yang   | Nov 08   |
| **Activity Diagram**                                      | Yuchen Fan   | Nov 11   |
| **Persona & User Story**                                  | Jilin Song   | Nov 11   |
| **Sequence Diagram (Login, Register, Recommendation)**    | Jiajun Chen  | Nov 11   |
| **Sequence Diagram (Virtual Try-on, Wardrobe, Analysis)** | Haochen Wang | Nov 11   |
| **Mid-fidelity Prototype**                                | Haochen Wang | Nov 11   |




#### 5.2.2 Research


| **Research Focus**                             | Responsible             | Deadline |
| ---------------------------------------------- | ----------------------- | -------- |
| **Virtual Try-on Model (Qwen-image-edit)**     | Jilin Song & Yuchen Fan | Nov 11   |
| **Evaluation and Recommendation LLM (Qwen3)**  | Ruixi Yang              | Nov 11   |
| **Outfit Recommendation Logic **               | Jiajun Chen             | Nov 11   |
| **Market Background and Competitive Analysis** | Haochen Wang            | Nov 11   |
| **Platform Selection**                         | To be confirmed         | /        |
| **Data Storage Methods**                       | To be confirmed         | /        |




---

## 6. Next Formal Meeting

**Date:** Wednesday, 2025-11-12
**Time:**  14:30 – 15:00 
**Place:**  IEB-520