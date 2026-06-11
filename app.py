import streamlit as st
import pandas as pd
import plotly.express as px

from schemadetector import SchemaDetector
from analysis_engine import AnalysisEngine

# =========================================================
# INITIALISATION ET FEUILLES DE STYLE DE L'INTERFACE
# =========================================================
st.set_page_config(
    page_title="Smart Accounting Analyzer",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.main { background-color: #f5f7fa; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #1f2937; }
.metric-container { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0px 2px 8px rgba(0,0,0,0.08); }
.stDataFrame { background-color: white; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Smart Accounting Analyzer")

st.markdown("""
Analyse automatique de données comptables et budgétaires.
L’outil :
- détecte automatiquement les colonnes importantes
- calcule des KPI comptables
- génère des analyses visuelles
- identifie des anomalies potentielles
""")

# =========================================================
# SUBSISTÈME DE PERSISTANCE EN MÉMOIRE (SÉCURISÉ POUR LE CLOUD)
# =========================================================
# Le bouton de réinitialisation vide uniquement la mémoire vive (Session State)
if st.sidebar.button("Nouvelle Analyse / Réinitialiser", use_container_width=True):
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("Configuration")
separator = st.sidebar.selectbox("Séparateur CSV", [";", ",", "|"], index=0)

uploaded_file = st.file_uploader("Importer un fichier comptable CSV", type=["csv"])

# LECTURE ET SAUVEGARDE EN MÉMOIRE VIVE (Aucune écriture sur le disque)
if uploaded_file is not None:
    # On vérifie si c'est un nouveau fichier pour éviter de recharger inutilement
    if "current_file_name" not in st.session_state or st.session_state["current_file_name"] != uploaded_file.name:
        try:
            # Lecture du fichier directement depuis le buffer mémoire
            df = pd.read_csv(uploaded_file, sep=separator, low_memory=False, decimal=',')
            st.session_state["df"] = df
            st.session_state["current_file_name"] = uploaded_file.name
            st.success("Fichier chargé et sécurisé en mémoire vive. (Les données disparaîtront à la fermeture de l'onglet).")
        except Exception as e:
            st.error(f"Erreur lors du chargement : {e}")

# =========================================================
# SEQUENCE EXECUTIONNELLE PRINCIPALE (ENGINE PIPELINE)
# =========================================================
if "df" in st.session_state:
    
    df = st.session_state["df"].copy() # On travaille sur une copie de la mémoire

    with st.expander("Aperçu des données", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)
        st.write(f"Dimensions du dataset : {df.shape}")

    # Détection automatique de l'architecture des données
    detector = SchemaDetector(df)
    schema, df_clean = detector.detect()

    st.subheader("Schéma détecté")
    schema_df = pd.DataFrame({"Type détecté": schema.keys(), "Colonne associée": schema.values()})
    st.dataframe(schema_df, use_container_width=True)

    # Console d'ajustement et d'homologation des variables
    st.subheader("Validation des colonnes")
    columns = [""] + list(df.columns)
    col1, col2 = st.columns(2)

    with col1:
        schema["date"] = st.selectbox("Date", columns, index=columns.index(schema.get("date", "")) if schema.get("date", "") in columns else 0)
        schema["amount"] = st.selectbox("Montant", columns, index=columns.index(schema.get("amount", "")) if schema.get("amount", "") in columns else 0)

    with col2:
        schema["debit_account"] = st.selectbox("Compte Débit (Destination / IMPUTD)", columns, index=columns.index(schema.get("debit_account", "")) if schema.get("debit_account", "") in columns else 0)
        schema["credit_account"] = st.selectbox("Compte Crédit (Source / IMPUTC)", columns, index=columns.index(schema.get("credit_account", "")) if schema.get("credit_account", "") in columns else 0)

    # Filtrage analytique par exercice comptable
    date_col = schema.get("date")
    if date_col and date_col in df_clean.columns:
        if not pd.api.types.is_datetime64_any_dtype(df_clean[date_col]):
            s = df_clean[date_col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            date_formats = ["%Y%m%d", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
            converted_dates = None
            
            for fmt in date_formats:
                parsed = pd.to_datetime(s, format=fmt, errors="coerce")
                if parsed.notna().mean() > 0.7:  
                    converted_dates = parsed
                    break
            
            if converted_dates is None:
                converted_dates = pd.to_datetime(s, errors="coerce")
                
            df_clean[date_col] = converted_dates

        temp_dates = df_clean[date_col]
        if temp_dates.notna().any():
            years = sorted(temp_dates.dt.year.dropna().unique().astype(int))
            st.sidebar.markdown("---")
            st.sidebar.subheader("Filtre temporel")
            selected_year = st.sidebar.selectbox("Sélectionner l'exercice comptable", ["Toutes les années"] + list(years))
            
            if selected_year != "Toutes les années":
                df_clean = df_clean[temp_dates.dt.year == selected_year]

    # Lancement des calculs financiers
    engine = AnalysisEngine(df_clean, schema)
    results = engine.compute_kpis()

    # =========================================================
    # SECTION RESTITUTION : BLOCS METRICS (KPI GLOBAUX)
    # =========================================================
    st.subheader("KPI Comptables")
    metric1, metric2, metric3 = st.columns(3)
    
    with metric1: 
        st.metric("Montant Total", f"{results.get('total_amount', 0):,.0f}".replace(",", " ") + " FCFA")
    with metric2: 
        st.metric("Nombre d'opérations", f"{results.get('count', 0):,.0f}".replace(",", " "))
    with metric3: 
        st.metric("Montant Moyen", f"{results.get('avg_amount', 0):,.0f}".replace(",", " ") + " FCFA")

    # =========================================================
    # SECTION RESTITUTION : DATAVIZ DES FLUX COMPTABLES
    # =========================================================
    st.subheader("Analyse des Comptes")
    tab_debit, tab_credit = st.tabs(["Flux Débit (Où va l'argent)", "Flux Crédit (D'où vient l'argent)"])

    with tab_debit:
        if "top_debit_accounts" in results:
            top_debit = results["top_debit_accounts"].reset_index()
            top_debit.columns = ["Compte Débit", "Montant"]
            top_debit["Compte Débit"] = top_debit["Compte Débit"].astype(str)
            top_debit["Montant_Millions"] = top_debit["Montant"] / 1000000

            fig_bar_deb = px.bar(
                top_debit, x="Compte Débit", y="Montant_Millions", 
                custom_data=["Montant"], title="Top 10 des comptes débités"
            )
            fig_bar_deb.update_xaxes(type='category', title="Numéro de Compte")
            fig_bar_deb.update_yaxes(tickformat=",.0f", title="Montant (en Millions FCFA)") 
            fig_bar_deb.update_layout(separators=" ,")
            fig_bar_deb.update_traces(hovertemplate="<b>Compte: %{x}</b><br>Montant exact: %{customdata[0]:,.0f} FCFA")
            st.plotly_chart(fig_bar_deb, use_container_width=True)

            if "debit_contribution" in results:
                contrib_deb = results["debit_contribution"].reset_index()
                contrib_deb.columns = ["Compte Débit", "Pourcentage"]
                contrib_deb["Compte Débit"] = contrib_deb["Compte Débit"].astype(str)
                contrib_deb["Tous les comptes"] = "Total Débits"
                
                fig_tree_deb = px.treemap(
                    contrib_deb, path=["Tous les comptes", "Compte Débit"], values="Pourcentage", 
                    color="Pourcentage", color_continuous_scale=px.colors.sequential.Teal, title="Répartition globale des débits (%)"
                )
                fig_tree_deb.update_layout(coloraxis_showscale=False)
                fig_tree_deb.update_traces(textinfo="label+value", texttemplate="%{label}<br>%{value:.2f}%", hovertemplate="%{label}<br>%{value:.2f}%")
                st.plotly_chart(fig_tree_deb, use_container_width=True)
            
            st.dataframe(top_debit[["Compte Débit", "Montant"]], use_container_width=True)

    with tab_credit:
        if "top_credit_accounts" in results:
            top_credit = results["top_credit_accounts"].reset_index()
            top_credit.columns = ["Compte Crédit", "Montant"]
            top_credit["Compte Crédit"] = top_credit["Compte Crédit"].astype(str)
            top_credit["Montant_Millions"] = top_credit["Montant"] / 1000000

            fig_bar_cre = px.bar(
                top_credit, x="Compte Crédit", y="Montant_Millions", 
                custom_data=["Montant"], title="Top 10 des comptes crédités", color_discrete_sequence=["#00CC96"]
            )
            fig_bar_cre.update_xaxes(type='category', title="Numéro de Compte")
            fig_bar_cre.update_yaxes(tickformat=",.0f", title="Montant (en Millions FCFA)")
            fig_bar_cre.update_layout(separators=" ,")
            fig_bar_cre.update_traces(hovertemplate="<b>Compte: %{x}</b><br>Montant exact: %{customdata[0]:,.0f} FCFA")
            st.plotly_chart(fig_bar_cre, use_container_width=True)

            if "credit_contribution" in results:
                contrib_cre = results["credit_contribution"].reset_index()
                contrib_cre.columns = ["Compte Crédit", "Pourcentage"]
                contrib_cre["Compte Crédit"] = contrib_cre["Compte Crédit"].astype(str)
                contrib_cre["Tous les comptes"] = "Total Crédits"
                
                fig_tree_cre = px.treemap(
                    contrib_cre, path=["Tous les comptes", "Compte Crédit"], values="Pourcentage", 
                    color="Pourcentage", color_continuous_scale=px.colors.sequential.Blues, title="Répartition globale des crédits (%)"
                )
                fig_tree_cre.update_layout(coloraxis_showscale=False)
                fig_tree_cre.update_traces(textinfo="label+value", texttemplate="%{label}<br>%{value:.2f}%", hovertemplate="%{label}<br>%{value:.2f}%")
                st.plotly_chart(fig_tree_cre, use_container_width=True)
            
            st.dataframe(top_credit[["Compte Crédit", "Montant"]], use_container_width=True)

    # Tendance chronologique mensuelle
    if "monthly_trend" in results:
        trend = results["monthly_trend"]
        if len(trend) > 0:
            st.subheader("Evolution Mensuelle")
            trend_df = trend.reset_index()
            trend_df.columns = ["Mois", "Montant"]
            trend_df["Montant_Millions"] = trend_df["Montant"] / 1000000
            
            fig_trend = px.line(trend_df, x="Mois", y="Montant_Millions", custom_data=["Montant"], markers=True, title="Evolution des montants")
            fig_trend.update_yaxes(tickformat=",.0f", title="Montant (en Millions FCFA)")
            fig_trend.update_layout(separators=" ,")
            fig_trend.update_traces(hovertemplate="<b>Mois: %{x|%B %Y}</b><br>Montant exact: %{customdata[0]:,.0f} FCFA")
            st.plotly_chart(fig_trend, use_container_width=True)

    # =========================================================
    # BLOC DETECTION CRITIQUE : MODULE AUDIT DYNAMIQUE
    # =========================================================
    if "anomalies" in results:
        st.subheader("Anomalies détectées (Basées sur des montants exceptionnels)")
        
        col_text, col_slider = st.columns([2, 1])
        with col_text:
            st.write("Niveau de filtrage (0.1 = Voir toutes les anomalies, 2.0 = Ne voir que les montants gigantesques) :")
        with col_slider:
            taux_selectionne = st.slider(
                "Filtre d'anomalies", min_value=0.1, max_value=2.0, value=0.5, step=0.1, label_visibility="collapsed"
            )
        
        amount_col = schema.get("amount")
        if amount_col:
            total_global = df_clean[amount_col].sum()
            nouveau_seuil_metier = total_global * (taux_selectionne / 100)
            
            q1 = df_clean[amount_col].quantile(0.25)
            q3 = df_clean[amount_col].quantile(0.75)
            iqr = q3 - q1
            plafond_stat = q3 + 3 * iqr
            
            limite_finale = max(plafond_stat, nouveau_seuil_metier)
            anomalies_dynamiques = df_clean[df_clean[amount_col] > limite_finale].sort_values(by=amount_col, ascending=False)
            
            if len(anomalies_dynamiques) > 0:
                st.warning(f"{len(anomalies_dynamiques)} opérations anormales correspondent à votre critère de filtrage.")
                
                cols_to_show = []
                for key in ["date", "debit_account", "credit_account", "beneficiary", "amount"]:
                    col_name = schema.get(key)
                    if col_name and col_name in anomalies_dynamiques.columns:
                        cols_to_show.append(col_name)
                        
                with st.expander("Voir les détails des opérations"):
                    st.dataframe(anomalies_dynamiques[cols_to_show], use_container_width=True)
            else:
                st.success("Aucune opération anormale détectée avec ce niveau de filtrage.")

    # =========================================================
    # DISPOSITIF DE RECONSTRUCTION ET EXPORTATION CSV
    # =========================================================
    st.subheader("Export")
    csv_export = df_clean.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Télécharger les données nettoyées", data=csv_export, file_name="cleaned_data.csv", mime="text/csv"
    )

else:
    st.info("Veuillez importer un fichier CSV pour commencer.")