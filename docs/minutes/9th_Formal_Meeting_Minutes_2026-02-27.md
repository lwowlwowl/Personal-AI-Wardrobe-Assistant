# 9th Formal Meeting Minutes

**Date:** Friday, 27 February 2026
**Time:** 12:30 – 13:30
**Place:** IEB-102



## Abstract 

This meeting mainly focused on demonstrating the current progress of our **web system** and reporting the work completed during the winter holiday, as well as the unfinished parts.

During the demonstration, the supervisor provided feedback on several modules, including the **Recommendation AI**, **MyWardrobe**, and **MyCalendar** sections. Suggestions were given on improving response speed, adjusting data logic, and enriching the page content. The supervisor also mentioned that the overall UI design still looks too simple and needs further improvement.

Finally, we confirmed that before the next meeting, all modules should be completed and at least fully runnable for an integrated demonstration.



## 1. Participants

|    Member    |   Role    | Present / Apology |
| :----------: | :-------: | :---------------: |
| Haochen Wang |   Chair   |      Present      |
|  Jilin Song  |     /     |Absent (schedule conflict)|
|  Ruixi Yang  |     /     |      Present      |
|  Yuchen Fan  |     /     |      Absent (schedule conflict)      |
| Jiajun Chen  | / |      Present      |



## 2. Agenda

- Demonstrate the current web system
- Report winter holiday progress
- Discuss unfinished modules
- Collect supervisor feedback
- Confirm next stage requirements



## 3. Main Discussion Points

### 3.1 Recommendation AI Module

**Issue:** Response time and efficiency.

**Supervisor’s suggestion:**

- Prepare some high-frequency questions locally in advance, such as:
  - “What should I wear to school on a sunny day?”
  - “What should I wear on a rainy day?”
- Reuse these prepared results when possible to
  - Reduce response time
  - Improve user experience
  - Reduce real-time generation pressure

------

### 3.2 MyWardrobe Module

#### (a) Tagging logic

**Current situation:**

- Two tagging methods:
  - AI-generated tags
  - Manually entered tags

**Suggested adjustment:**

- Use AI-generated tags as default.
- Allow users to manually modify them if necessary.

#### (b) Frequently Worn Outfits

- A “Frequently Worn Outfits” section can be displayed locally in the Wardrobe module.

- The data can be generated based on users’ outfit selections.

  This can make the wardrobe page more informative and visually richer.

------

### 3.3 Virtual Try-On Module

- Not demonstrated in this meeting.
- Needs to be completed before the next meeting.

------

### 3.4 MyCalendar Module

**Current logic:**

- Users manually record what they wear each day.

**Supervisor’s suggestion:**

- Instead of only recording clothing items, the system should record user decisions. For example,

  - The Recommendation AI provides three outfit options.

  - The user selects the second one.

  - The Calendar records this decision.

**Further discussion:**

1. The “wearing frequency” data should not only come from manual uploads.

2. It should mainly come from users’ selections in the Recommendation AI module. After each selection, 

   - The Calendar records the decision automatically.

   - Wearing statistics are updated.

   - The data can support wardrobe analysis and frequently worn outfit display.

**Final decision:**

- Keep the current basic function (to avoid large refactoring).
- Adjust the logic to make data flow more consistent and reasonable.

------

### 3.5 Wardrobe Analysis Module

- Not demonstrated in this meeting.
- Needs to be fully implemented before the next meeting.

------

### 3.6 UI / Design

- The current interface looks too plain.

---

### 3.7 Demonstration preparation

- For the final demo, we should prepare more clothing images locally.
- The final presentation can run on a local machine.
- There is no need to rent or deploy to a public server.



## 4. General Action Points

- **Complete all unfinished modules**

- **Ensure all modules are fully runnable**

- Improve:

  - Recommendation response strategy

  - Calendar data logic

  - Tagging logic

  - Wearing frequency data source
  - Improve overall UI design.

  

## 5. Next Formal Meeting

**Date:** Wednesday, 2026-03-11
**Time:** 13:00-14:00
**Place:**  TBC