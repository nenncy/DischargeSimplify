# DischargeSimplify

**DischargeSimplify** is a web-based application that transforms complex medical discharge instructions into simple, patient-friendly summaries. Using NLP techniques and large language models (LLMs), it ensures patients better understand their care plans post-discharge — reducing confusion, enhancing safety, and lowering avoidable readmissions.

---

## 🚀 Features

- **Simplify Medical Texts**: Converts complex discharge instructions into plain language.
- **Multilingual Support**: Translates outputs into multiple languages for wider accessibility.
- **Validation Engine**: Confirms that simplified outputs match the intent of the original.
- **Chat Assistant**: Patients can ask follow-up questions about their instructions.
- **Streamlit Interface**: Clean, responsive UI with support for uploads and chat.

---

## 🛠️ Installation

### Requirements

- Python 3.8+
- pip
- Backend API (FastAPI recommended)

### Setup

```bash
# Clone the repo
git clone https://github.com/nenncy/DischargeSimplify.git
cd DischargeSimplify

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variable
echo "BACKEND_URL=http://127.0.0.1:8000" > .env

# Run the app
streamlit run app.py
