import pandas as pd

class AnalysisEngine:
    """
    Moteur d'analyse financière chargé de calculer les indicateurs clés (KPI),
    les répartitions de flux par compte et la détection des opérations atypiques.
    """

    def __init__(self, df, schema):
        """
        Initialise le moteur avec le jeu de données nettoyé et son schéma de colonnes.
        """
        self.df = df
        self.schema = schema

    def compute_kpis(self):
        """
        Exécute la chaîne globale de calculs financiers.
        
        Retourne:
            dict: Regroupement des KPI globaux, des top comptes et des anomalies.
        """
        results = {}

        amount = self.schema.get("amount")
        date = self.schema.get("date")
        debit_account = self.schema.get("debit_account")
        credit_account = self.schema.get("credit_account")
        beneficiary = self.schema.get("beneficiary")

        # =====================================================
        # INDICATEURS GLOBAUX
        # =====================================================
        if amount:
            results["total_amount"] = self.df[amount].sum()
            results["avg_amount"] = self.df[amount].mean()
            results["count"] = self.df.shape[0]

        # =====================================================
        # ANALYSE ALGORITHMIQUE DES FLUX (TOP 10 & CONTRIBUTIONS)
        # =====================================================
        if amount and debit_account:
            group_debit = (
                self.df.groupby(debit_account)[amount]
                .sum()
                .sort_values(ascending=False)
            )
            results["top_debit_accounts"] = group_debit.head(10)
            results["debit_contribution"] = (group_debit / group_debit.sum() * 100).head(10)

        if amount and credit_account:
            group_credit = (
                self.df.groupby(credit_account)[amount]
                .sum()
                .sort_values(ascending=False)
            )
            results["top_credit_accounts"] = group_credit.head(10)
            results["credit_contribution"] = (group_credit / group_credit.sum() * 100).head(10)

        # =====================================================
        # ANALYSE DE LA TENDANCE TEMPORELLE
        # =====================================================
        if amount and date:
            df_temp = self.df.copy()

            if not pd.api.types.is_datetime64_any_dtype(df_temp[date]):
                s = df_temp[date].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                df_temp[date] = pd.to_datetime(s, format="%Y%m%d", errors="coerce")

            df_temp = df_temp.dropna(subset=[date])

            if not df_temp.empty:
                df_temp["month"] = (
                    df_temp[date]
                    .dt.to_period("M")
                    .dt.to_timestamp()
                )
                results["monthly_trend"] = df_temp.groupby("month")[amount].sum()

        # =====================================================
        # ANALYSE DES TIERS / BÉNÉFICIAIRES
        # =====================================================
        if amount and beneficiary:
            results["top_beneficiaries"] = (
                self.df.groupby(beneficiary)[amount]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )

        # =====================================================
        # CALCUL DU SEUIL D'ANOMALIE (MÉTHODE HYBRIDE STAT/MÉTIER)
        # =====================================================
        if amount:
            q1 = self.df[amount].quantile(0.25)
            q3 = self.df[amount].quantile(0.75)
            iqr = q3 - q1
            
            # Seuil statistique strict pour les valeurs extrêmes (Modèle IQR x 3)
            plafond_stat = q3 + 3 * iqr
            
            # Paramétrage initial de la matérialité à 0.5% du volume global annuel
            plafond_metier = self.df[amount].sum() * 0.005  
            
            # Arbitrage par le principe de prudence : sélection du filtre le plus restrictif
            upper_bound = max(plafond_stat, plafond_metier)
            
            anomalies = self.df[self.df[amount] > upper_bound]
            results["anomalies"] = anomalies.sort_values(by=amount, ascending=False)

        return results