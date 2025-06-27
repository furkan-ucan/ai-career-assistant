import sys
from pathlib import Path

import streamlit as st

# Allow imports from the src package
sys.path.append(str(Path(__file__).resolve().parent))

from src.config import get_config
from src.pipeline import run_end_to_end_pipeline

config = get_config()

available_personas = list(config.get("persona_search_configs", {}).keys())

st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🚀 AI Career Assistant")
st.markdown("Discover your next career opportunity with the power of AI.")

if "job_results" not in st.session_state:
    st.session_state.job_results = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False

sidebar = st.sidebar
sidebar.header("⚙️ Analysis Configuration")

st.session_state.similarity_threshold = sidebar.slider(
    "Similarity Threshold (%)",
    min_value=40,
    max_value=100,
    value=config["job_search_settings"].get("min_similarity_threshold", 60),
)

hours_option = sidebar.selectbox(
    "Date Range",
    options=[("Last 24 hours", 24), ("Last 3 days", 72), ("Last 7 days", 168)],
    format_func=lambda x: x[0],
)

st.session_state.hours_old = hours_option[1]

selected_personas = sidebar.multiselect(
    "Personas",
    options=available_personas,
    default=available_personas,
)

if sidebar.button("🤖 Find My Perfect Jobs", type="primary", use_container_width=True):
    st.session_state.is_running = True
    st.session_state.job_results = None

if st.session_state.is_running:
    with st.spinner("Analyzing your CV against the job market... This may take a few minutes. ⏳"):
        try:
            results = run_end_to_end_pipeline(
                selected_personas=selected_personas or None,
                similarity_threshold=st.session_state.similarity_threshold,
                hours_old=st.session_state.hours_old,
            )
            st.session_state.job_results = results
            st.session_state.is_running = False
            st.success(f"Analysis complete! Found {len(results) if results else 0} suitable opportunities.")
            st.balloons()
        except Exception as exc:  # pragma: no cover - visual feedback
            st.session_state.is_running = False
            st.error(f"An error occurred during analysis: {exc}")

results = st.session_state.job_results
if results:
    for job in results:
        st.subheader(job.get("title", "No Title"))
        col1, col2, col3 = st.columns(3)
        score = job.get("fit_score", job.get("similarity_score", 0))
        col1.metric("Fit Score", f"{score:.1f}")
        col2.metric("Source", job.get("source_site", "N/A"))
        col3.metric("Persona", job.get("persona_source", "N/A"))

        with st.expander("AI Insights"):
            reasoning = job.get("reasoning")
            if reasoning:
                st.write(reasoning)
            mk = job.get("matching_keywords")
            if mk:
                st.write("**Matching Skills:**", ", ".join(mk))
            miss = job.get("missing_keywords")
            if miss:
                st.write("**Missing Skills:**", ", ".join(miss))
        url = job.get("url") or job.get("job_url")
        if url:
            st.link_button("View Job", url)
        st.divider()
elif results is not None:
    st.info("No suitable jobs found.")
