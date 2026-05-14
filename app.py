import streamlit as st
import pandas as pd
import plotly.express as px

from schemadetector import SchemaDetector
from analysis_engine import AnalysisEngine


# =========================================================
# CONFIGURATION PAGE
# =========================================================

st.set_page_config(
    page_title="Smart Accounting Analyzer",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# STYLE CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

h1, h2, h3 {
    color: #1f2937;
}

.metric-container {
    background-color: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}

.stDataFrame {
    background-color: white;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.title(" Smart Accounting Analyzer")

st.markdown("""
Analyse automatique de données comptables et budgétaires.

L’outil :
- détecte automatiquement les colonnes importantes
- calcule des KPI comptables
- génère des analyses visuelles
- identifie des anomalies potentielles
""")


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ Configuration")

separator = st.sidebar.selectbox(
    "Séparateur CSV",
    [";", ",", "|"],
    index=0
)


# =========================================================
# UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    " Importer un fichier comptable CSV",
    type=["csv"]
)


# =========================================================
# MAIN
# =========================================================

if uploaded_file:

    # =====================================================
    # LOAD DATA
    # =====================================================

    # Utilisation du cache pour optimiser les performances lors des interactions
    @st.cache_data
    def load_data(file, sep):
        # Ajout de decimal=',' pour bien lire les centimes au format français
        return pd.read_csv(
            file,
            sep=sep,
            low_memory=False,
            decimal=','
        )

    try:
        df = load_data(uploaded_file, separator)
        st.success("Fichier chargé avec succès ")

    except Exception as e:
        st.error(f"Erreur lors du chargement : {e}")
        st.stop()


    # =====================================================
    # DATA OVERVIEW
    # =====================================================

    with st.expander("🔍 Aperçu des données", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)

        st.write("Dimensions du dataset :")
        st.write(df.shape)


    # =====================================================
    # SCHEMA DETECTION
    # =====================================================

    detector = SchemaDetector(df)
    schema, df_clean = detector.detect()

    st.subheader(" Schéma détecté")

    schema_df = pd.DataFrame({
        "Type détecté": schema.keys(),
        "Colonne associée": schema.values()
    })

    st.dataframe(schema_df, use_container_width=True)


    # =====================================================
    # USER VALIDATION
    # =====================================================

    st.subheader(" Validation des colonnes")

    columns = [""] + list(df.columns)

    col1, col2 = st.columns(2)

    with col1:

        schema["date"] = st.selectbox(
            "Date",
            columns,
            index=columns.index(schema.get("date", ""))
            if schema.get("date", "") in columns else 0
        )

        schema["amount"] = st.selectbox(
            "Montant",
            columns,
            index=columns.index(schema.get("amount", ""))
            if schema.get("amount", "") in columns else 0
        )

    with col2:

        schema["main_account"] = st.selectbox(
            "Compte principal",
            columns,
            index=columns.index(schema.get("main_account", ""))
            if schema.get("main_account", "") in columns else 0
        )

        schema["secondary_account"] = st.selectbox(
            "Compte secondaire",
            columns,
            index=columns.index(schema.get("secondary_account", ""))
            if schema.get("secondary_account", "") in columns else 0
        )


    # =====================================================
    # ANALYSIS ENGINE
    # =====================================================

    engine = AnalysisEngine(df_clean, schema)
    results = engine.compute_kpis()


    # =====================================================
    # KPI SECTION
    # =====================================================

    st.subheader(" KPI Comptables")

    metric1, metric2, metric3 = st.columns(3)

    with metric1:
        st.metric(
            "Montant Total",
            # Formatage avec espaces pour les milliers
            f"{results.get('total_amount', 0):,.0f}".replace(",", " ")
        )

    with metric2:
        st.metric(
            "Nombre d'opérations",
            # Formatage avec espaces
            f"{results.get('count', 0):,.0f}".replace(",", " ")
        )

    with metric3:
        st.metric(
            "Montant Moyen",
            # Formatage avec espaces
            f"{results.get('avg_amount', 0):,.0f}".replace(",", " ")
        )


    # =====================================================
    # TOP ACCOUNTS
    # =====================================================

    if "top_accounts" in results:

        st.subheader(" Top Comptes")

        top_accounts = results["top_accounts"].reset_index()

        top_accounts.columns = ["Compte", "Montant"]

        fig_accounts = px.bar(
            top_accounts,
            x="Compte",
            y="Montant",
            title="Top 10 des comptes"
        )

        st.plotly_chart(fig_accounts, use_container_width=True)

        st.dataframe(top_accounts, use_container_width=True)


    # =====================================================
    # CONTRIBUTION %
    # =====================================================

    if "account_contribution" in results:

        st.subheader(" Contribution des comptes (%)")

        contrib = results["account_contribution"].reset_index()

        contrib.columns = ["Compte", "Pourcentage"]

        fig_pie = px.pie(
            contrib,
            names="Compte",
            values="Pourcentage",
            title="Répartition des comptes"
        )

        st.plotly_chart(fig_pie, use_container_width=True)


    # =====================================================
    # MONTHLY TREND
    # =====================================================

    if "monthly_trend" in results:

        trend = results["monthly_trend"]

        if len(trend) > 0:

            st.subheader(" Evolution Mensuelle")

            trend_df = trend.reset_index()

            trend_df.columns = ["Mois", "Montant"]

            fig_trend = px.line(
                trend_df,
                x="Mois",
                y="Montant",
                markers=True,
                title="Evolution des montants"
            )

            st.plotly_chart(fig_trend, use_container_width=True)


    # =====================================================
    # ANOMALIES
    # =====================================================

    if "anomalies" in results:

        st.subheader("🚨 Anomalies détectées")

        anomalies = results["anomalies"]

        if len(anomalies) > 0:
            st.warning(f"{len(anomalies)} anomalies potentielles détectées")

            st.dataframe(
                anomalies.head(20),
                use_container_width=True
            )

        else:
            st.success("Aucune anomalie détectée")


    # =====================================================
    # EXPORT
    # =====================================================

    st.subheader("⬇️ Export")

    csv_export = df_clean.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Télécharger les données nettoyées",
        data=csv_export,
        file_name="cleaned_data.csv",
        mime="text/csv"
    )

else:

    st.info("Veuillez importer un fichier CSV pour commencer.")