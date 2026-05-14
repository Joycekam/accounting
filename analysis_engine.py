import pandas as pd

class AnalysisEngine:

    def __init__(self, df, schema):
        self.df = df
        self.schema = schema

    def compute_kpis(self):

        results = {}

        amount = self.schema.get("amount")
        date = self.schema.get("date")
        account = self.schema.get("main_account")
        beneficiary = self.schema.get("beneficiary")

        # =====================================================
        # 1. KPI GLOBAUX
        # =====================================================

        if amount:

            results["total_amount"] = self.df[amount].sum()

            results["avg_amount"] = self.df[amount].mean()

            results["count"] = self.df.shape[0]

        # =====================================================
        # 2. ANALYSE PAR COMPTE
        # =====================================================

        if amount and account:

            group = (
                self.df.groupby(account)[amount]
                .sum()
                .sort_values(ascending=False)
            )

            results["top_accounts"] = group.head(10)

            results["account_contribution"] = (
                group / group.sum() * 100
            ).head(10)

        # =====================================================
        # 3. ANALYSE TEMPORELLE (VERSION ROBUSTE)
        # =====================================================

        if amount and date:

            df_temp = self.df.copy()

            # -----------------------------
            # Conversion multi-formats
            # -----------------------------
            date_formats = [
                "%Y%m%d",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d-%m-%Y"
            ]

            converted = None

            for fmt in date_formats:

                temp_dates = pd.to_datetime(
                    df_temp[date].astype(str),
                    format=fmt,
                    errors="coerce"
                )

                valid_ratio = temp_dates.notna().mean()

                if valid_ratio > 0.7:
                    converted = temp_dates
                    break

            # -----------------------------
            # Si conversion réussie
            # -----------------------------
            if converted is not None:

                df_temp[date] = converted

                df_temp = df_temp.dropna(subset=[date])

                if not df_temp.empty:

                    # MODIFICATION : On ajoute .dt.to_timestamp() pour rendre 
                    # l'objet compatible avec la sérialisation JSON de Plotly
                    df_temp["month"] = (
                        df_temp[date]
                        .dt.to_period("M")
                        .dt.to_timestamp()
                    )

                    monthly = (
                        df_temp.groupby("month")[amount]
                        .sum()
                    )

                    results["monthly_trend"] = monthly

        # =====================================================
        # 4. ANALYSE BENEFICIAIRES
        # =====================================================

        if amount and beneficiary:

            top_benef = (
                self.df.groupby(beneficiary)[amount]
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )

            results["top_beneficiaries"] = top_benef

        # =====================================================
        # 5. DETECTION ANOMALIES
        # =====================================================

        if amount:

            q1 = self.df[amount].quantile(0.25)

            q3 = self.df[amount].quantile(0.75)

            iqr = q3 - q1

            upper_bound = q3 + 1.5 * iqr

            anomalies = self.df[
                self.df[amount] > upper_bound
            ]

            results["anomalies"] = anomalies.head(10)

        return results