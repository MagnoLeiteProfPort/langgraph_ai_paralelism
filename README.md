# Outfit Gender Classification Workflow

A modern, clean, and production‑ready multi‑agent LangGraph workflow that generates an outfit
(head, torso, legs) **in parallel**, classifies each clothing item as **male**, **female**, or **none**, and validates whether the outfit is gender‑consistent.

If the outfit is:

- **All male** → approved
- **All female** → approved
- **Mixed/none** → regenerated until approved or until `MAX_ATTEMPTS` is reached

The workflow is fully configurable through the `.env` file and automatically exports a graph diagram:
`workflow_graph.png`.

---

## 🚀 Features

### ✅ Parallel Generation

Three independent nodes generate:

- Head clothing
- Torso clothing
- Leg clothing

All run concurrently for speed and modularity.

### ✅ Robust Validation

The validator:

- Classifies each item as **male / female / none**
- Determines overall outfit gender
- Enforces consistency rules
- Loops intelligently up to `MAX_ATTEMPTS`

### ✅ Configurable via `.env`

Environment variables:

```
MAX_ATTEMPTS=5
ANTHROPIC_API_KEY=YOUR_KEY
```

### 🧠 Powered by Anthropic Claude (via LangChain)

Uses:

- `ChatAnthropic`
- `langgraph` StateGraph workflow engine

---

## 🗂 Project Structure

```
project/
│
├── main.py                  # Full workflow implementation
├── workflow_graph.png       # Auto‑generated workflow diagram
├── .env                     # Runtime configuration (not committed)
├── .env.example             # Template for config
└── README.md                # This documentation
```

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-repo/outfit-gender-workflow
cd outfit-gender-workflow
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Mac/Linux
# or
.\.venv\Scripts\ctivate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example:

```bash
cp .env.example .env
```

Fill in your `ANTHROPIC_API_KEY`.

---

## ▶️ Running the Workflow

To execute the entire outfit‑generation pipeline:

```bash
python main.py
```

During execution, you will see:

- Step‑by‑step logs of the three generated items
- Gender classification per item
- Retry loop logic
- Final accepted outfit

A graph diagram will be generated automatically:

👉 **`workflow_graph.png`**

---

## 🧩 Workflow Diagram

Below is the generated diagram representing the full LangGraph logic:

![Workflow Diagram](workflow_graph.png)

---

## ⚙️ Configuration

### `.env`

```
ANTHROPIC_API_KEY=YOUR_KEY_HERE
MAX_ATTEMPTS=5
```

### `.env.example`

```
ANTHROPIC_API_KEY=
MAX_ATTEMPTS=5
```

---

## 🎯 Validation Logic

| Condition          | Result                        |
| ------------------ | ----------------------------- |
| All items → male   | ✔ Approved                    |
| All items → female | ✔ Approved                    |
| Anything else      | ❌ Retry (until max attempts) |

The logic guarantees deterministic validation even when clothing items are gender‑ambiguous.

---

## 🧪 Extend / Customize

You can easily:

- Add more clothing categories (shoes, accessories…)
- Customize gender rules
- Add persistent memory between runs
- Implement more detailed fashion classification models

---

## 📄 License

This project is provided for demonstration and educational purposes.

---

## 👤 Author

Developed by **Magno Leite**  
Software Engineering & AI Workflows

---

Enjoy exploring the workflow!  
Feel free to contribute improvements 🚀
