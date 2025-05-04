import os
import pycountry
import openai
import streamlit as st
from dotenv import load_dotenv, find_dotenv

# ─── Load .env & set API key ────────────────────────────────────────────────────
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
print("🔑 Using OPENAI_API_KEY=", os.getenv("OPENAI_API_KEY"))


# ─── Language mappings ──────────────────────────────────────────────────────────
LANGUAGE_MAPPING = {lang.name: lang.alpha_2 for lang in pycountry.languages if hasattr(lang, 'alpha_2')}
languages = sorted(LANGUAGE_MAPPING.keys(), key=lambda x: x.lower())

# ─── LLM‐backed translator ──────────────────────────────────────────────────────
def _call_openai(prompt: str, model: str = "gpt-4o", temperature: float = 0.0, top_p: float = 1.0) -> openai.ChatCompletion:
    return openai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        top_p=top_p
    )

# ─── Core translation functions ────────────────────────────────────────────────
def t(s: str) -> str:
    if st.session_state.ui_language_code == "en":
        return s
    lang_name = st.session_state.selected_language
    cache_key = (s, lang_name)
    if cache_key in st.session_state.translations:
        return st.session_state.translations[cache_key]
    try:
        prompt = (
            "You are a perfectly literal translator.  "
            f"Translate the following text exactly into {lang_name}, "
            "without adding, removing, or changing any words or meaning.  "
            "Respond with only the translated text.\n\n"
            f"{s}"
        )
        resp = _call_openai(prompt)
        translated = resp.choices[0].message.content.strip()
        if translated.startswith('"""') and translated.endswith('"""'):
            translated = translated[3:-3].strip()
        st.session_state.translations[cache_key] = translated
        return translated
    except Exception as e:
        st.error(f"Translation error: {e}")
        return s
    
# ─── Assistant Translator ──────────────────────────────────────────────────────────
def at(s: str, tarlang: str | None = None) -> str:
    src = None
    dest = tarlang or st.session_state.selected_language
    if tarlang is None:
        if st.session_state.ui_language_code == "en":
            return s
        src = "English"
    else:
        if tarlang == "English":
            src = st.session_state.selected_language
        else:
            src = "English"
    cache_key = (s, src, dest)
    if cache_key in st.session_state.translations:
        return st.session_state.translations[cache_key]
    try:
        prompt = (
            "You are a perfectly literal translator.\n"
            f"Translate the following text exactly from {src} into {dest}, "
            "without adding, removing, or changing any words or meaning. "
            "Respond with only the translated text.\n\n"
            f"{s}"
        )
        resp = _call_openai(prompt)
        translated = resp.choices[0].message.content.strip().strip('"""')
        st.session_state.translations[cache_key] = translated
        return translated
    except Exception as e:
        st.error(f"Translation error: {e}")
        return s

# ─── Core Language Functions ────────────────────────────────────────────────────────────
def update_language():
    new_lang = st.session_state.selected_language
    try:
        st.session_state.ui_language_code = LANGUAGE_MAPPING[new_lang]
    except KeyError:
        st.error(f"⚠️ {t('Unsupported language')}: {new_lang}")
        st.session_state.ui_language_code = "en"
    finally:
        st.session_state.translations.clear()

# ─── Selection functions ────────────────────────────────────────────────────────
def language_selector():
    current_idx = languages.index(st.session_state.selected_language)
    st.selectbox(
        t("Select a language"),
        languages,
        index=current_idx,
        key="selected_language",
        on_change=update_language,
        label_visibility="collapsed"
    )