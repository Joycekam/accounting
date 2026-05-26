import pandas as pd

class SchemaDetector:
    """
    Analyseur sémantique et structurel chargé de cartographier automatiquement
    les variables clés d'un fichier comptable (dates, montants, imputations).
    """
    
    def __init__(self, df):
        self.df = df.copy()
        self.schema = {}

    def detect(self):
        """
        Exécute les règles heuristiques de détection sur l'ensemble des en-têtes.
        
        Retourne:
            tuple: Le dictionnaire de correspondance (schéma) et le DataFrame initial.
        """
        for col in self.df.columns:
            if self.is_date_column(col):
                self.schema["date"] = col
                break

        for col in self.df.columns:
            if self.is_amount_column(col):
                self.schema["amount"] = col
                break

        for col in self.df.columns:
            if self.is_debit_account(col):
                self.schema["debit_account"] = col
            elif self.is_credit_account(col):
                self.schema["credit_account"] = col

        return self.schema, self.df

    def is_date_column(self, col):
        """Évalue si une colonne encapsule des données temporelles."""
        name = col.lower()
        if any(x in name for x in ["date", "dat", "periode"]):
            return True

        series = self.df[col].dropna().astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        sample = series.head(10)

        if sample.str.len().max() < 6:
            return False

        # Validation structurelle du format compact YYYYMMDD
        if sample.str.len().eq(8).all() and sample.str.isnumeric().all():
            try:
                parsed = pd.to_datetime(sample, format="%Y%m%d", errors="coerce")
                if parsed.notna().mean() > 0.8:
                    return True
            except:
                pass

        # Validation des formats standards délimités
        if sample.str.contains(r'[-/]').any():
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.7:
                return True

        return False

    def is_amount_column(self, col):
        """Évalue si une colonne porte les flux financiers."""
        name = col.lower()
        if any(x in name for x in ["amount", "montant", "total", "value"]):
            return True
        return pd.api.types.is_numeric_dtype(self.df[col])

    def is_debit_account(self, col):
        """Identifie les colonnes d'imputation de destination (Débit)."""
        name = col.lower()
        return any(x in name for x in ["imputd", "debit", "deb"])

    def is_credit_account(self, col):
        """Identifie les colonnes d'imputation de provenance (Crédit)."""
        name = col.lower()
        return any(x in name for x in ["imputc", "credit", "cre"])