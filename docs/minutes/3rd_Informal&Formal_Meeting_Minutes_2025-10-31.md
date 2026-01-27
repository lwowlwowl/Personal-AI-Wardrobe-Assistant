# 3rd Informal & Formal Meeting Minutes

**Date:** Thursday, 2025-10-30 & Friday, 2025-10-31
**Time:** 20:00 - 20:40 & 13:30 – 14:30 
**Place:** Online (Tencent Meeting) & IEB-520



## Abstract 

The third informal and formal meetings focused on **integrating research outcomes** and **demonstrating the low-fidelity system prototype**.
Each team members presented progress on **virtual try-on models**, **LLM-based evaluation and recommendation**, and **outfit recommendation logic**.
Through comparative analysis, the team found that **Qwen-image-edit** outperformed **OOTDiffusion** in stability and reliability, and was therefore selected as the **primary model for virtual try-on**.



## 1. Participants

|    Member    |   Role    | Present / Apology |
| :----------: | :-------: | :---------------: |
| Haochen Wang |   Chair   |      Present      |
|  Jilin Song  |     /     |Present|
|  Ruixi Yang  |     /     |      Present      |
|  Yuchen Fan  |     /     |      Present      |
| Jiajun Chen  | Secretary |      Present      |



## 2. Agenda

- Present research progress for each direction (Virtual Try-on, LLM Evaluation, Recommendation Logic).
- Confirm the essential components of the prototype.
- Introduce the essential components of the Midterm Report.



## 3. Main Discussion Points

- **Research on Virtual Try-on Models**

  - **Qwen-image-edit:**

    - Current local deployment and API testing revealed network instability and limited memory
    - Local interface for demo purposes: upload an image + text description → generate new image

  - **Diffusion-based Model:**

    - Overall generation time acceptable (~3 seconds per image)	

    - Performs well when the clothing background is clean, but the OOTDiffusion mask is relatively large and ideally requires a solid-color background for optimal results.

  - Therefore, the team decided to adopt **Qwen-image-edit** as the primary virtual try-on model for system integration.

- **Research on Evaluation and Recommendation LLMs (Qwen3)**
  - Local deployment failed due to **insufficient VRAM (4B model)**.
  - Primary intended functions to improve user experience:
    - **Outfit recommendation generation**
    - **Virtual try-on evaluation feedback**

- **Research on Outfit Recommendation Logic and Rules:**

  - Proposed defining input information labels and building a simple internal model to find similar clothing from the database.

  - Mentioned Polyvore as a potential data source for similarity-based recommendations.



## 4. Possible Encounter and Utilize

- For the Diffusion-based Model, with **multiple users**, total inference time could increase significantly — **discussion raised whether multi-user queuing or preloading is needed.**



## 5. Action Points

### 5.1 UML Diagram

| Task                                        | Responsible  | Deadline |
| ------------------------------------------- | ------------ | -------- |
| Design and develop a mid-fidelity prototype | Haochen Wang | Nov 05   |



### 5.2 Research 

#### 5.2.1 Research on Virtual Try-on Models

| **Research Focus**  | Responsible             | Deadline |
| ------------------- | ----------------------- | -------- |
| **Qwen-image-edit** | Yuchen Fan & Jilin Song | Nov 05   |



#### 5.2.2 Research on **Evaluation and Recommendation LLMs**

| **Research Focus** | Responsible | Deadline |
| ------------------ | ----------- | -------- |
| **Qwen3**          | Ruixi Yang  | Nov 05   |



#### 5.2.3 Research on **Outfit Recommendation Logic and Rules**

| **Research Focus**               | Responsible | Deadline |
| :------------------------------- | :---------- | :------- |
| **Outfit Recommendation Logic ** | Jiajun Chen | Nov 05   |



#### 5.2.4 Research on **Market Background and Competitive Analysis**

| **Research Focus**                               | Responsible  | Deadline |
| :----------------------------------------------- | :----------- | -------- |
| **Competitive Analysis & Project Justification** | Haochen Wang | Nov 05   |



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

**Date:** Wednesday, 2025-11-05
**Time:** 14:30 - 15:30
**Place:**  IEB-114