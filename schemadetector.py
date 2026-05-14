import pandas as pd

class SchemaDetector:
    def __init__(self, df):
        self.df = df.copy()
        self.schema = {}

    def detect(self):

        # 🔹 Détection de la date
        for col in self.df.columns:
            if self.is_date_column(col):
                self.schema["date"] = col
                break

        # 🔹 Détection du montant
        for col in self.df.columns:
            if self.is_amount_column(col):
                self.schema["amount"] = col
                break

        # 🔹 Détection des comptes (MODIFIÉ ICI)
        for col in self.df.columns:
            if self.is_debit_account(col):
                self.schema["debit_account"] = col
            elif self.is_credit_account(col):
                self.schema["credit_account"] = col

        # 🔹 Conversion de la date
        if "date" in self.schema:
            col = self.schema["date"]
            try:
                self.df[col] = pd.to_datetime(self.df[col], format="%Y%m%d", errors="coerce")
            except:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce")

        return self.schema, self.df


    # -------------------------
    # 🔍 DETECTION
    # -------------------------

    def is_date_column(self, col):
        name = col.lower()
        series = self.df[col].dropna().astype(str)

        # 🔹 priorité au nom
        if "date" in name:
            return True

        sample = series.head(10)

        # 🔹 format YYYYMMDD (ex: 20110228)
        if sample.str.len().eq(8).all():
            try:
                parsed = pd.to_datetime(sample, format="%Y%m%d", errors="coerce")
                if parsed.notna().mean() > 0.8:
                    return True
            except:
                pass

        # 🔹 format classique
        parsed = pd.to_datetime(sample, errors="coerce")
        if parsed.notna().mean() > 0.7:
            return True

        return False


    def is_amount_column(self, col):
        name = col.lower()

        if any(x in name for x in ["amount", "montant", "total", "value"]):
            return True

        return pd.api.types.is_numeric_dtype(self.df[col])

    #  Détection du Débit
    def is_debit_account(self, col):
        name = col.lower()
        # On ajoute "debit", "deb" pour que ce soit robuste sur d'autres fichiers
        return any(x in name for x in ["imputd", "debit", "deb"])

    #  Détection du Crédit 
    def is_credit_account(self, col):
        name = col.lower()
        # On ajoute "credit", "cre" pour que ce soit robuste sur d'autres fichiers
        return any(x in name for x in ["imputc", "credit", "cre"])