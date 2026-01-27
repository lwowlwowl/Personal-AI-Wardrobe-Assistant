# 7th Formal Meeting Minutes

**Date:** Tuesday, 2025-01-20
**Time:** 13:30 – 14:00 
**Place:** Online (Tencent Meeting)  



## Abstract 

This meeting focused on checking the GRP schedule, explaining how different parts of the system depend on each other, and discussing teamwork and performance **important notes**.

The meeting explained that the frontend, backend, and models can be developed separately, and that the whole project should not be blocked by one part. Different parts of the project should keep **close communication**, and if a problem cannot be solved, the team should work together to solve it.

We also discussed LLM integration, deployment options, real-time performance, and user experience, and suggested using a **mix of pre-generated results and real-time generation** to reduce performance pressure.



## 1. Participants

|    Member    |   Role    | Present / Apology |
| :----------: | :-------: | :---------------: |
| Haochen Wang |   Chair   |      Present      |
|  Jilin Song  |     /     |Absent (schedule conflict)|
|  Ruixi Yang  |     /     |      Present      |
|  Yuchen Fan  |     /     |      Present      |
| Jiajun Chen  | / |      Present      |



## 2. Agenda

- Confirm the overall project progress during the winter holiday.

- Restate some important notes:

  - Model-related issues
  - Team collaboration issues

  

------

## 3. Main Discussion Points

- **Overall project progress (Web development)**
  - Main modules include:
    - Home / Login / Registration
    - Virtual Try-On
    - Wardrobe Management
    - LLM Recommendation
    - Wardrobe Analysis
  - Frontend, backend, models, and integration are developed **in parallel**, not in a strict order.
  - API documentation is the **key agreement** between frontend, backend, and models.

------

- **LLM, model, and recommendation algorithm discussion**
  - Integration and deployment still need to be clearly defined:
    - How to connect the LLM / whether LLM alone is enough or a recommendation algorithm is also needed
    - Local deployment or cloud deployment
    - Whether local computing power is sufficient
  - Trade-offs need to be considered:
    - Latency
    - Cost
    - Stability

------

- **Real-time vs background generation**
  - LLM generation may take a long time, so not all features should use real-time generation.
  - Decide which parts can be generated in advance to improve speed and user experience.

------

- **Team communication**

  - If a problem cannot be solved by one member within **two or three days**, solve it together instead of waiting.
  - Different parts of the project should communicate more **frequently**.

  

## 4. General Action Points

![image-20260120154416237](C:\Users\Haochen Wang\AppData\Roaming\Typora\typora-user-images\image-20260120154416237.png)




---

## 5. Next Formal Meeting

**Date:** Friday, 2026-01-30
**Time:** 10:00-11:00 / 13:00-14:00
**Place:**  online