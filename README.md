
# DischargeSimplify

**DischargeSimplify** is a full-stack application that leverages AI to simplify medical discharge summaries into patient-friendly language. It ensures better understanding, enhances follow-up compliance, and bridges the gap between complex clinical language and patient literacy.

## 🌟 Key Features

- 🔍 **Simplification Engine**: Converts dense medical summaries into sixth-grade reading level using GPT-based models.
- 🌐 **Multilingual Support**: Translates discharge summaries into over 50 languages.
- 💬 **Chat Assistant**: Interactive Q&A chatbot built with OpenAI Assistants API, providing context-aware support to patients.
- ⚠️ **Risk Mitigation**: Reduces hallucinations and enhances trust through prompt engineering and readability thresholds.
- 🧾 **Structured Outputs**: Displays simplified content with clear sections—summary, medications, follow-ups, precautions, etc.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI (Python)
- **AI Integration**: OpenAI GPT (Assistants API)
- **Translation**: GPT-based multi-language translation
- **Deployment**: Cross-platform (local or cloud ready)

## 📂 Project Structure

```
DischargeSimplify/
├── backend/
│   ├── app.py
│   ├── simplify.py
│   ├── assistant.py
│   ├── prompt_templates/
│   └── utils/
├── frontend/
│   └── streamlit_app.py
├── assets/
├── .env.example
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/nenncy/DischargeSimplify.git
cd DischargeSimplify
```

### 2. Set Up Environment

- Rename `.env.example` to `.env` and add your OpenAI API key.

```bash
cp .env.example .env
```

- Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Run the Application

Start the backend (FastAPI):

```bash
uvicorn backend.app:app --reload
```

Start the frontend (Streamlit):

```bash
streamlit run frontend/streamlit_app.py
```

The app will be available at: `http://localhost:8501`

## 💡 Innovation Highlights

- Introduced multilingual discharge support using LLM-based translation.
- Integrated Assistants API for dynamic, real-time medical Q&A.
- Designed prompts and outputs to optimize for readability and patient trust.

## 🤝 Contributing

1. Fork the repo
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

---

Made with ❤️ for healthcare innovation.
