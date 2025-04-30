# 🏥 DischargeSimplify

When patients are discharged from hospitals — especially from Emergency Rooms — they often receive complex, jargon-filled instructions. Many struggle to understand critical details like medication schedules, follow-up appointments, and lifestyle recommendations, which leads to missed treatments, complications, and avoidable readmissions.

💡 **Fact:** Hospital readmissions cost over **$1,000 per patient on average**.

This project uses **Large Language Models (LLMs)** to translate clinical discharge summaries into clear, actionable instructions at a **6th-grade reading level**, and in the **patient’s preferred language**.

---

## 🏗️ Features

- **Simplification of Medical Language**  
  Converts complex discharge instructions into patient-friendly summaries.

- **Multi-language Support**  
  Translates summaries into the patient’s native language if needed.

- **Critical Information Highlighting**  
  Emphasizes details like medication timings, dosages, and follow-up schedules.

- **Structured Output**  
  Outputs clean, structured JSON for easy EHR (Electronic Health Record) integration.

- **Validation Layer**  
  Post-processes LLM outputs to ensure they meet safety and accuracy standards.

- **💬 Assistant Chat**  
  An AI-powered assistant answers user questions using only the simplified summary context.

---

## ⚙️ Tech Stack

| Layer                    | Technology                               |
|--------------------------|-------------------------------------------|
| Backend Framework        | FastAPI                                   |
| AI Model Interface       | Huggingface Transformers, SentenceTransformers |
| Database (optional/future) | SQL                                     |
| Retrieval/Indexing Layer | FAISS for semantic search                 |
| Frontend (optional/future) | Streamlit                              |
| Language Models Used     | Local models or OpenAI APIs (configurable) |

---

## 🚀 Setup Instructions

> 📲 **Python 3.10** or higher recommended.

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/discharge-simplify.git
cd discharge-simplify
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
Create a `.env` file:
```bash
OPENAI_API_KEY=your-api-key
```

### 5. Run the FastAPI server
```bash
uvicorn backend.app:app --reload
```
Visit `http://127.0.0.1:8000/docs` for API documentation.

---

## 🧹 API Endpoints

| Method | Endpoint                     | Purpose                               |
|:-------|:------------------------------|:------------------------------------- |
| POST   | `/simplify`       | Simplify discharge instructions       |
| POST   | `/validate`       | Validate the simplified output        |
| POST   | `/assistant/chat`           | Assistant chat from the simplified output |

(Interactive Swagger documentation auto-generated at `/docs`.)

---

## 📊 Example Workflow

1. Input complex discharge notes.
2. LLM generates a simplified 6th-grade summary.
3. Validation Layer:
   - Chunk text.
   - Build FAISS semantic index.
   - Verify all required fields are present (e.g., medication, follow-up).
   - Filter inappropriate/unsafe outputs.
4. Output structured JSON:
```json
{
  "patient_summary": "...",
  "medications": [...],
  "follow_up": [...],
  "important_notes": "..."
}
```

---

## 🛡️ Risk Mitigation

- **Validation Layer** to catch AI hallucinations.
- **Clinical Oversight** suggested for real-world deployment.
- **Continuous fine-tuning** based on real discharge samples (with de-identified data).

---

## 🌱 Future Work

- Deploy production version with authentication and logging.
- Implement FHIR-compliant outputs for EHR integrations.
- Add Streamlit/React frontend for easier clinician interaction.
- Fine-tune LLMs on domain-specific datasets.
- Support for emergency-specific discharge scenarios.

---

## 🤝 Contributing

Pull requests are welcome!  
For major changes, please open an issue first to discuss what you would like to change.

---

## 📜 License

[MIT License](LICENSE)

---
