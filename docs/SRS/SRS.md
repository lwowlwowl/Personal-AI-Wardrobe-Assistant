# AI Wardrobe Assistant SRS

## 1. Introduction

### 1.1 Purpose

This document aims to clarify the functional requirements, performance requirements and system constraints of the "AI Intelligent Dressing Assistant" system, providing a unified basis for subsequent system design, development, testing and maintenance.

### 1.2 Background

With the development of artificial intelligence and image recognition technology, users' demands for personalized dressing and smart wardrobe management are increasing day by day. This system is designed to utilize AI algorithms and weather data to provide users with intelligent dressing advice and virtual try-on experiences, helping them manage their wardrobes efficiently and enhancing the convenience and fashion experience of their lives.

### 1.3 Definitions and abbreviations

| Abbreviation | Meaning                       |
| :----------- | :---------------------------- |
| AI           | Artificial Intelligence       |
| FR           | Functional Requirement        |
| SRS          | Software Requirement Specification |
| UI           | User Interface                |

---

## 2. Overall Description

### 2.1 System Objective

The AI wardrobe assistant aims to provide users with personalized fashion recommendations, virtual try-on experiences, and wardrobe management functions. By integrating weather, occasions, and user preferences, it enables efficient and intelligent fashion decisions.

### 2.2 User Characteristics

-   **Regular User**: Have the basic ability to use smart device.
-   **Fashion Enthusiasts**: Have high demands for personalized fashion matching.

### 2.3 Operating Environment

To be finished ……

---

## 3. Functional Requirements

-   **FR-01 User registration and login**
    The system should support user registration, login and logout. After logging in for the first time, enter the wardrobe database creation guidance process.

-   **FR-02 Wardrobe data creation (Form)**
    The system should allow users to add clothing items (category, brand, color, material, size, season, scene label, purchase year, photo, etc.) through forms.

-   **FR-03 Wardrobe data Creation (Image)**
    The system should support users in uploading clothes photos in batches, automatically identify category/color/pattern/season attributes and generate candidate tags. Users can correct them and then store them in the database.

-   **FR-04 User Preferences**
    The system should generate lightweight preference portraits based on the user's wardrobe characteristics and interaction behaviors (frequently worn colors, styles, scenarios), and display editable preference panels.

-   **FR-05 Occasion and constraint input**
    The system should allow users to specify recommended conditions: occasions (such as interviews, work, dates, travels, banquets), dress etiquette requirements, color preferences, comfort/warmth priority, and whether rain protection is needed, etc.

-   **FR-06 Weather data acquisition**
    The system should automatically obtain weather conditions (temperature range, precipitation probability, wind force, humidity) based on the user's location and date as recommended constraints. Users can manually rewrite the weather conditions for simulation.

-   **FR-07 Outfit recommendation generation**
    The system should generate no less than 3 sets of dressing schemes (tops/bottoms/coats/shoes/accessories) from the "wardrobe database" under the occasions and weather conditions set by the user, meeting the following requirements:
    - Match etiquette/occasion;
    - Match with weather constraints (temperature levels, whether rainproof or windproof);
    - Be as consistent as possible with the user preference profile;
    - Pair it with history to avoid high repetition.

-   **FR-08 Recommended explanations and alternatives**
    The system should provide a brief explanation for each set of recommendations (why they were chosen/what conditions/style keywords they are suitable for), and offer alternative items (at least one piece/set) for fine-tuning.

-   **FR-09 Feedback loop and learning**
    The system should support users' feedback on the recommendation of "collect/like/dislike/no longer recommend this item/this style", and incorporate the feedback into preference and rule learning to influence the subsequent recommendation ranking.

-   **FR-10 Virtual try-on (user photo)**
    The system should allow users to upload full-body photos of themselves (including basic pose constraint prompts), complete human body segmentation and pose estimation, and visually preview the candidate outfits on their photos.

-   **FR-11 Virtual try-on (clothing photos)**
    The system should allow users to upload photos of individual pieces of clothing, corresponding them to wardrobe entries or as "temporary clothing", to complete the division/straightening/pasting of the clothing for preview during fitting.

-   **FR-12 Export and share the try-on results**
    The system should support the export (PNG/JPEG) or generation of shareable links for single or multiple sets of try-on preview images (including validity period and access permission Settings).

-   **FR-13 Wardrobe Maintenance**
    The system should support the query, filtering (category/season/color/occasion), batch editing, delisting/deletion and viewing of historical change records of wardrobe items.

---

## 4. Non-functional Requirements

### 4.1 Performance Requirements

-   **NF1**: The system should respond to user recommendation requests within 3 seconds.
-   **NF2**: The system should support concurrent users without significant performance degradation.
-   **NF3**: The virtual try-on rendering for a single 720p image should be completed within 10 seconds.

### 4.2 Usability Requirements

-   **NF4**: The UI should follow a clean and consistent visual style.
-   **NF5**: Key functions (upload, recommendation, sharing) should require no more than three clicks or steps.
-   **NF6**: New users should be able to complete registration and wardrobe setup within 2 minutes.
-   **NF7**: The system should provide English and Chinese language switching.

### 4.3 Security and Privacy Requirements

-   **NF8**: User-uploaded personal photos should be used exclusively for the virtual try-on function and not for any other purpose.
-   **NF9**: The system should allow users to delete their accounts and personal data at any time.

### 4.4 Reliability Requirements

-   **NF10**: The system shall maintain an annual availability of no less than 99%.
-   **NF11**: User data shall not be lost in the event of an abnormal program termination.

### 4.5 Compatibility Requirements

-   **NF12**: The front end should be compatible with major browsers (latest versions of Chrome, Edge, Safari, and Firefox).
-   **NF13**: The system should support mobile access on Android ≥ 10 and iOS ≥ 14.

---

## 5. Use Case Specifications

| Use Case ID | Use Case Name                 | Key Participants | Goals                                                       | Description                                                              |
| :---------- | :---------------------------- | :--------------- | :---------------------------------------------------------- | :----------------------------------------------------------------------- |
| **UC-01**   | Manage Account                | User             | Register or log in to the system                            | Users create accounts, log in or log out of the system.                  |
| **UC-02**   | Manage Digital Wardrobe       | User             | Establish and maintain a digital wardrobe                   | Add, edit, delete and browse clothing information.                       |
| **UC-03**   | Get Outfit Recommendation     | User             | Get Outfit Recommendation                                   | The system generates personalized recommendations based on conditions. |
| **UC-04**   | Provide Recommendation Feedback | User             | Improve the system                                          | When users give feedback on their likes or dislikes, the system will make optimizations. |
| **UC-05**   | Perform Virtual Try-on        | User             | Experience the effect of outfit recommendations             | Upload personal photo and view the fitting picture.                      |
| **UC-06**   | Share Try-on Result           | User             | Share photos of user’s outfit and look                      | Share the virtual try-on result on social media platforms.               |
| **UC-07**   | View/Edit User Profile        | User             | Users can view or adjust the style preferences summarized by the system. | Users can view the personal style analyzed by AI and make manual interventions. |

