# Personal AI Wardrobe Assistant Installation Guide

Welcome to Personal AI Wardrobe Assistant! This guide walks you through project download, environment setup, and running the system. Please follow the steps below.

## Recommended Configuration

For the best performance, the following hardware is recommended:

### GPU
NVIDIA GeForce RTX 4090 or above

#### Memory
32 GB or above

## Download the Project

```bash
git clone https://github.com/lwowlwowl/Personal-AI-Wardrobe-Assistant.git
cd Personal-AI-Wardrobe-Assistant
```

Or download the ZIP package directly: click the green **Code** button on the repository page and choose **Download ZIP**.

## Software Preparation

### Node.js

- Download: https://nodejs.org/en/download
- Version requirement: Node.js **18 or above** (npm is installed together with Node.js)
- Verify:

```bash
node -v
npm -v
```

### PostgreSQL

- Download: https://www.postgresql.org/download/
- Installation tutorial: https://www.postgresql.org/docs/current/tutorial-install.html
- Notes:
  - Remember the database username and password you set during installation.
  - Create an empty database in PostgreSQL in advance, and configure the correct connection info in `.env`.
  - On the **first successful backend startup**, this project automatically creates required tables in PostgreSQL, so **no separate SQL table-creation script is needed**.
  - After installation, make sure the PostgreSQL service is running.

### ComfyUI

- Download: https://www.comfy.org/download
- Installation tutorial: https://github.com/comfyanonymous/ComfyUI#readme
- Workflow setup:
  1. Open ComfyUI.
  2. Drag the project workflow file `qwen_edit_v1.json` into the ComfyUI interface.

  ```bash
  # Workflow file location
  src\backend\app\resources
  ```

  ![Workflow drag example](./images/workflow_drag.png)
  ![Workflow diagram](./images/workflow.png)
  

  3. Download models: click the **Templates** button at the lower part of the left panel. In **All Templates**, search for "Qwen Image"; or click **Qwen-Image** in **Model Filter** below the search box. Select **Qwen Image Edit 2509** and download all required models.

  4. Place the models in the correct folder:

  ```bash
  # Model folder location
  ComfyUI\models
  ```

  ![Model structure](./images/model_structure.png)
  

## Running the Project

### Virtual Environment Setup

Create and activate a virtual environment in the project root:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

### Frontend

1. Enter the frontend directory:

```bash
cd src/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Build and start:

```bash
npm run build:h5
npm run dev:h5
```

4. Visit http://localhost:5173 in your browser. If you see the login page, startup is successful.

### Backend

1. Open a new terminal window (keep the frontend running).
2. Enter the backend directory:

```bash
cd src/backend
```

3. Configure environment variables: create a `.env` file under `src/backend`, and fill in values based on `env_example.txt` (replace database username and password with your PostgreSQL settings). For course use, you may also use our provided `.env` directly and only modify database-related settings.

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start the backend service:

```bash
python -m uvicorn main:app --reload --port 8000
```

6. Visit http://localhost:8000/docs. If the API documentation page appears, startup is successful.

## Verify Installation

| Service | URL | Status |
|------|------|------|
| Frontend | http://localhost:5173 | Login page appears |
| Backend | http://localhost:8000/docs | API docs page appears |

At this point, the project has been successfully downloaded, installed, and started.
