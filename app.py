
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="GovernIQ | AI Governance Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# LOAD POLICY DATASET
# --------------------------------------------------

DATA_FILE = Path(__file__).parent / "data" / "policies.csv"

if not DATA_FILE.exists():
    st.error(f"Dataset not found: {DATA_FILE}")
    st.stop()

df = pd.read_csv(DATA_FILE)

required_columns = {
    "Country",
    "Year",
    "Policy",
    "Type",
    "Topic",
    "Status",
    "Summary",
    "Source",
    "PublicationDate",
    "EffectiveDate",
    "LegalStatus",
    "SourceType",
    "LastVerified",
    "EvidenceNote",
}

missing = required_columns - set(df.columns)

if missing:
    st.error(
        "Missing required columns: "
        + ", ".join(sorted(missing))
    )
    st.info(
        "Check that data/policies.csv contains all 14 required columns."
    )
    st.stop()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df = df.dropna(subset=["Country", "Policy", "Year"]).copy()
df["Year"] = df["Year"].astype(int)
df = df.fillna("Not specified")

if df.empty:
    st.error("The policy dataset contains no valid records.")
    st.stop()

COUNTRIES = sorted(df["Country"].unique())

# --------------------------------------------------
# DESIGN
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
    }

    [data-testid="stMetric"] {
        background: rgba(128,128,128,0.08);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.18);
    }

    div[data-testid="stTabs"] button {
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌐 GovernIQ")

st.markdown(
    "Your window into global AI governance, safety, regulation "
    "and accountability."
)

st.caption(
    "Independent research prototype · Source-linked policy records · "
    "Not legal advice or an official government database"
)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("Explore the data")
st.sidebar.caption(
    "Choose filters to update the entire dashboard."
)

selected_countries = st.sidebar.multiselect(
    "Countries and jurisdictions",
    COUNTRIES,
    default=COUNTRIES,
)

selected_topics = st.sidebar.multiselect(
    "Research topics",
    sorted(df["Topic"].unique()),
    default=sorted(df["Topic"].unique()),
)

selected_types = st.sidebar.multiselect(
    "Instrument type",
    sorted(df["Type"].unique()),
    default=sorted(df["Type"].unique()),
)

year_min = int(df["Year"].min())
year_max = int(df["Year"].max())

year_range = st.sidebar.slider(
    "Publication year",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
)

search = st.sidebar.text_input(
    "Search policy records",
    placeholder="e.g. safety, legislation...",
)

if st.sidebar.button(
    "Reset all filters",
    use_container_width=True,
):
    st.rerun()

# --------------------------------------------------
# FILTER ENGINE
# --------------------------------------------------

filtered = df[
    df["Country"].isin(selected_countries)
    & df["Topic"].isin(selected_topics)
    & df["Type"].isin(selected_types)
    & df["Year"].between(year_range[0], year_range[1])
].copy()

if search.strip():
    search_mask = (
        filtered["Policy"].astype(str).str.contains(
            search, case=False, na=False
        )
        | filtered["Summary"].astype(str).str.contains(
            search, case=False, na=False
        )
        | filtered["Country"].astype(str).str.contains(
            search, case=False, na=False
        )
        | filtered["Topic"].astype(str).str.contains(
            search, case=False, na=False
        )
    )

    filtered = filtered[search_mask]

# --------------------------------------------------
# OVERVIEW METRICS
# --------------------------------------------------

st.subheader("Overview")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Matching records", len(filtered))
m2.metric("Jurisdictions", filtered["Country"].nunique())
m3.metric("Instrument types", filtered["Type"].nunique())
m4.metric("Research topics", filtered["Topic"].nunique())

if filtered.empty:
    st.warning(
        "No records match these filters. Change your selection."
    )
    st.stop()

st.divider()

# --------------------------------------------------
# DASHBOARD TABS
# --------------------------------------------------

tab_overview, tab_explorer, tab_methodology = st.tabs(
    ["📊 Analytics", "🔎 Policy explorer", "📚 Methodology"]
)

# --------------------------------------------------
# ANALYTICS TAB
# --------------------------------------------------

with tab_overview:
    st.subheader("Policy landscape")

    left, right = st.columns(2)

    with left:
        st.markdown("**Records by jurisdiction**")

        counts = (
            filtered.groupby("Country")
            .size()
            .reset_index(name="Records")
            .sort_values("Records", ascending=False)
        )

        fig = px.bar(
            counts,
            x="Country",
            y="Records",
            color="Country",
            text="Records",
            template="plotly_dark",
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="Jurisdiction",
            yaxis_title="Number of records",
            margin=dict(t=20, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.markdown("**Composition by instrument type**")

        type_counts = (
            filtered.groupby("Type")
            .size()
            .reset_index(name="Records")
        )

        fig = px.pie(
            type_counts,
            names="Type",
            values="Records",
            hole=0.48,
            template="plotly_dark",
        )

        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    left2, right2 = st.columns(2)

    with left2:
        st.markdown("**Research topics by jurisdiction**")

        topic_counts = (
            filtered.groupby(["Country", "Topic"])
            .size()
            .reset_index(name="Records")
        )

        fig = px.bar(
            topic_counts,
            x="Country",
            y="Records",
            color="Topic",
            barmode="stack",
            template="plotly_dark",
        )

        fig.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with right2:
        st.markdown("**Records by publication year**")

        yearly = (
            filtered.groupby("Year")
            .size()
            .reset_index(name="Records")
        )

        fig = px.line(
            yearly,
            x="Year",
            y="Records",
            markers=True,
            template="plotly_dark",
        )

        fig.update_layout(
            xaxis_title="Publication year",
            yaxis_title="Number of records",
            margin=dict(t=20, b=20),
        )

        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Charts describe the selected dataset only. They do not measure "
        "the effectiveness, strictness or safety of a jurisdiction's policies."
    )

# --------------------------------------------------
# POLICY EXPLORER TAB
# --------------------------------------------------

with tab_explorer:
    st.subheader("Policy explorer")

    st.write(
        f"Showing **{len(filtered)}** records matching your current filters."
    )

    display_columns = [
        "Country",
        "Year",
        "Policy",
        "Type",
        "Topic",
        "Status",
        "Summary",
        "PublicationDate",
        "EffectiveDate",
        "LegalStatus",
        "SourceType",
        "LastVerified",
        "EvidenceNote",
        "Source",
    ]

    display = (
        filtered[display_columns]
        .sort_values(["Country", "Year"])
    )

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        height=440,
    )

    st.subheader("Inspect a policy")

    policy_names = filtered["Policy"].tolist()

    chosen_policy = st.selectbox(
        "Select a record",
        policy_names,
    )

    record = filtered[
        filtered["Policy"] == chosen_policy
    ].iloc[0]

    st.markdown(f"### {record['Policy']}")
    st.write(f"**Jurisdiction:** {record['Country']}")
    st.write(f"**Year:** {record['Year']}")
    st.write(f"**Instrument type:** {record['Type']}")
    st.write(f"**Topic:** {record['Topic']}")
    st.write(f"**Recorded status:** {record['Status']}")
    st.write(f"**Summary:** {record['Summary']}")

    # New governance metadata section
    st.subheader("Governance metadata")

    metadata_labels = {
        "PublicationDate": "Publication date",
        "EffectiveDate": "Effective date",
        "LegalStatus": "Legal status",
        "SourceType": "Source type",
        "LastVerified": "Last verified",
        "EvidenceNote": "Evidence note",
    }

    for column, label in metadata_labels.items():
        st.write(f"**{label}:** {record[column]}")

    source_url = str(record["Source"]).strip()

    if source_url.startswith(("https://", "http://")):
        st.link_button(
            "Open source website",
            source_url,
        )
    else:
        st.caption(
            "No valid source URL is available for this record."
        )

    # CSV export
    csv_data = filtered.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download filtered records (CSV)",
        data=csv_data,
        file_name="ai_governance_observatory.csv",
        mime="text/csv",
    )

    # JSON export
    json_data = filtered.to_json(
        orient="records",
        indent=2,
    )

    st.download_button(
        "⬇ Download filtered records (JSON)",
        data=json_data,
        file_name="ai_governance_observatory.json",
        mime="application/json",
    )

# --------------------------------------------------
# METHODOLOGY TAB
# --------------------------------------------------

with tab_methodology:
    st.subheader("Research methodology")

    st.markdown(
        """
        **Scope**

        This prototype collects selected policy instruments, government
        initiatives, frameworks and guidelines concerning AI governance.

        **Source verification**

        Each record includes a source link. A source homepage is not always
        the specific document supporting a record. Replace general links
        with direct document URLs where possible and record when each source
        was checked.

        **Metadata fields**

        - **PublicationDate:** Date the policy or document was published.
        - **EffectiveDate:** Date the policy became effective, where applicable.
        - **LegalStatus:** Whether the instrument is binding legislation,
          voluntary guidance, a framework, or another type.
        - **SourceType:** Type of source used to document the record.
        - **LastVerified:** Date the record was last checked.
        - **EvidenceNote:** Caveats, verification needs, and context.

        **Data quality**

        A valid source URL does not guarantee factual accuracy. Verify
        publication dates, legal status and effective dates against official
        sources. Treat metadata as provisional until checked against the
        underlying documents.

        **Comparability**

        A law, voluntary framework, government institution and strategy are
        different types of instruments. They should not be treated as equivalent.

        **Interpretation**

        Counts and charts represent records in this dataset, not every policy
        that exists in a jurisdiction. They cannot establish which country
        has the best or safest AI governance.

        **Limitations**

        The dataset is illustrative, not exhaustive. Publication year is not
        necessarily the effective date. Current legal status and amendments
        must be independently verified before drawing legal conclusions.
        """
    )

    st.warning(
        "This project is a research prototype, not legal advice or an "
        "official government database."
    )

    st.markdown("**Records by jurisdiction**")

    jurisdiction_summary = (
        filtered.groupby("Country")
        .agg(
            Record_count=("Policy", "count"),
            Earliest_year=("Year", "min"),
            Latest_year=("Year", "max"),
        )
        .reset_index()
    )

    st.dataframe(
        jurisdiction_summary,
        use_container_width=True,
        hide_index=True,
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown(
    "**GovernIQ** · AI Governance Intelligence Platform · "
    "Built with Python, Streamlit, pandas and Plotly"
)
