import pandas as pd

from schemadetector import SchemaDetector
from analysis_engine import AnalysisEngine


def main():

    # -------------------------
    # 1. Chargement des données
    # -------------------------
    print("Chargement des données...")
    df = pd.read_csv(
        "data/bdcompta.csv",
        sep=";",
        low_memory=False
    )

    # -------------------------
    # 2. Détection du schéma
    # -------------------------
    detector = SchemaDetector(df)
    schema, df_clean = detector.detect()

    # -------------------------
    # 3. Affichage du schéma détecté
    # -------------------------
    print("\nSchéma détecté :")
    for key, value in schema.items():
        print(f"{key} : {value}")

    # -------------------------
    # 4. Analyse (KPI Engine)
    # -------------------------
    engine = AnalysisEngine(df_clean, schema)
    results = engine.compute_kpis()

    # -------------------------
    # 5. Affichage des KPI
    # -------------------------
    print("\n--- KPI ---")

    for key, value in results.items():
        print(f"\n{key} :")
        print(value)


if __name__ == "__main__":
    main()