# **10th Formal Meeting Minutes**

**Date:** Wednesday, 18 March 2026
**Time:** 13:00 - 14:30
**Place:** PB-428

------

## **Abstract**

This meeting focused on demonstrating the current **frontend and backend integration** of the system and the **interim report** feedback.

During the system demonstration, the supervisor provided detailed feedback on the **Recommendation AI module** and **MyWardrobe module**, particularly regarding recommendation diversity, system interaction design, and data preparation for the final demo.

In addition, the supervisor emphasized that the **fianl report should include sufficient discussion and justification** for all figures and tables, and suggested moving detailed database content to the appendix.

Finally, the deadline for submitting the **final report draft** was confirmed.



## **1. Participants**

| Member       | Role  | Present / Apology |
| ------------ | ----- | ----------------- |
| Haochen Wang | Chair | Present           |
| Jilin Song   | /     | Present           |
| Ruixi Yang   | /     | Present           |
| Yuchen Fan   | /     | Present           |
| Jiajun Chen  | /     | Present           |



## **2. Agenda**

- Demonstrate frontend and backend integration
- Collect supervisor feedback on system modules
- Provide interim report
- Discuss final report requirements



## **3. Main Discussion Points**

### **3.1 System Demonstration**

- The team demonstrated the current **integrated system**, including front-end and back-end interaction.
- The system is now functionally connected, but still requires improvement in usability and completeness.

------

### **3.2 Recommendation AI Module**

**Current issue:**

- The system only outputs **one outfit per user query** (e.g., “What should I wear this morning?”).

**Supervisor’s suggestions:**

- Generate **multiple outfit options** for each query
  - Provide users with choices
  - Improve recommendation flexibility
  - Reduce mismatch between recommendation and user preference
- Improve **module interaction:**
  - Add a **quick access button** to allow users to directly jump from recommendation results to the **Virtual Try-On module**
- Implement **prompt mapping** (OPTIONAL):
  - Transform user input into optimized prompts
  - Improve generation quality and consistency

------

### **3.3 MyWardrobe Module**

**Current issue:**

- The number of clothing items in the wardrobe is currently too limited.

**Supervisor’s suggestion:**

- For the final demo, prepare:
  - **200–300 clothing items**
  - Ensure sufficient diversity and realism

------

### **3.4 Interim Report Feedback**

**Main issue:**

- The report mainly presents results but lacks sufficient explanation.

**Supervisor’s requirements:**

- Every **figure and table must include:**
  - Discussion
  - Justification
- The report should clearly demonstrate **design thinking**, including:
  - Why this design was chosen
  - What the design is
  - What impact it has
  - How it is implemented
- Section **5.3 (Database Design)** can be moved to the **Appendix** to reduce main text length

------

### **3.5 Final Report Preparation**

- The **draft of the final report** must be sent to the supervisor **before 26 March 2026**
- If major issues are identified:
  - An additional meeting will be held on **27 March 2026**



## **4. General Action Points**

| Software Task                               | Responsible             |
| ------------------------------------------- | ----------------------- |
| **RecommendationAI** Frontend & Integration | Haochen Wang            |
| **VirtualTryOn** Backend & ComfyUI workflow | Jilin Song & Yuchen Fan |

| Final Report       | Responsible |
| ------------------ | ----------- |
| Final Report Draft | Ruixi Yang  |
| User Manual        | Jiajun Chen |



## **5. Next Formal Meeting**

**Date:** 27 March 2026 (if required)
**Time:** TBC
**Place:** TBC