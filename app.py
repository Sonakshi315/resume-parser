
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from parser import parse_resume, match_job_description

st.set_page_config(
    page_title="Resume Parser",
    page_icon="📄",
    layout="wide"
)

st.title("📄 Resume Parser")
st.write(
    "Upload resumes to extract candidate information "
    "and compare skills with a job description."
)

st.warning(
    "Prototype: extracted information may be incomplete. "
    "Always verify results manually."
)

if "candidates" not in st.session_state:
    st.session_state.candidates = []

tab1, tab2, tab3 = st.tabs(
    ["Upload & Parse", "Job Matching", "Dashboard"]
)

with tab1:
    st.subheader("Upload resumes")

    uploaded_files = st.file_uploader(
        "Choose PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

    if st.button("Parse Resumes", type="primary"):
        if not uploaded_files:
            st.warning("Upload at least one resume.")
        else:
            for uploaded_file in uploaded_files:
                temp_path = None

                try:
                    suffix = Path(uploaded_file.name).suffix

                    with tempfile.NamedTemporaryFile(
                        suffix=suffix, delete=False
                    ) as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_path = temp_file.name

                    result = parse_resume(temp_path)
                    result["filename"] = uploaded_file.name

                    st.session_state.candidates.append(result)
                    st.success(
                        f"Parsed: {uploaded_file.name}"
                    )

                except Exception as error:
                    st.error(
                        f"{uploaded_file.name}: {error}"
                    )

                finally:
                    if temp_path and Path(temp_path).exists():
                        Path(temp_path).unlink()

    for candidate in st.session_state.candidates:
        with st.expander(candidate["filename"]):
            st.write("**Name:**", candidate["name"])
            st.write("**Email:**", candidate["email"])
            st.write("**Phone:**", candidate["phone"])
            st.write("**Skills:**", ", ".join(candidate["skills"]))

            st.write("**Possible education entries**")
            st.write(candidate["education"])

            st.write("**Possible experience entries**")
            st.write(candidate["experience"])

            with st.expander("View extracted text"):
                st.text(candidate["raw_text"][:20000])

with tab2:
    st.subheader("Job description matching")

    job_description = st.text_area(
        "Paste a job description",
        height=200,
        placeholder="Example: Python, SQL, Pandas and Machine Learning"
    )

    if st.button("Compare Skills"):
        if not st.session_state.candidates:
            st.warning("Parse a resume first.")
        elif not job_description.strip():
            st.warning("Enter a job description.")
        else:
            for candidate in st.session_state.candidates:
                result = match_job_description(
                    candidate["skills"],
                    job_description
                )

                st.markdown(f"### {candidate['filename']}")
                st.metric(
                    "Job skill keyword overlap",
                    f"{result['match_percentage']}%"
                )

                st.write(
                    "**Matched skills:**",
                    ", ".join(result["matched_skills"]) or "None"
                )
                st.write(
                    "**Other job skills:**",
                    ", ".join(result["missing_skills"]) or "None"
                )

            st.caption(
                "This percentage measures keyword overlap, "
                "not the probability of being hired."
            )

with tab3:
    st.subheader("Candidate dashboard")

    candidates = st.session_state.candidates

    if not candidates:
        st.info("Parse resumes to see the dashboard.")
    else:
        rows = []

        for candidate in candidates:
            rows.append({
                "Filename": candidate["filename"],
                "Name": candidate["name"],
                "Email": candidate["email"],
                "Phone": candidate["phone"],
                "Skills": ", ".join(candidate["skills"])
            })

        df = pd.DataFrame(rows)

        col1, col2 = st.columns(2)
        col1.metric("Resumes parsed", len(candidates))
        col2.metric(
            "Emails detected",
            sum(c["email"] != "Not found" for c in candidates)
        )

        st.dataframe(df, use_container_width=True)

        st.download_button(
            "Download results as CSV",
            data=df.to_csv(index=False).encode("utf-8-sig"),
            file_name="parsed_candidates.csv",
            mime="text/csv"
        )

        if st.button("Clear candidates"):
            st.session_state.candidates = []
            st.rerun()
