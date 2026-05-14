import pandas as pd
import os

def load_accounting_file(file_path: str) -> pd.DataFrame:
    """
    Tente de charger un fichier CSV ou Excel de manière robuste.
    Gère les erreurs d'encodage et de séparateur.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Le fichier {file_path} est introuvable.")

    file_extension = file_path.split('.')[-1].lower()

    if file_extension == 'csv':
        # Liste des encodages et séparateurs courants en France/Europe
        encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
        separators = [';', ',', '\t']
        
        for enc in encodings:
            for sep in separators:
                try:
                    # on_bad_lines='skip' permet d'ignorer les lignes corrompues au lieu de planter
                    df = pd.read_csv(file_path, sep=sep, encoding=enc, on_bad_lines='skip')
                    
                    # Si on a qu'une seule colonne, c'est que le séparateur n'est pas le bon
                    if len(df.columns) > 1:
                        print(f"✅ Fichier chargé avec succès (Encodage: {enc}, Séparateur: '{sep}')")
                        return df
                except Exception:
                    continue # On essaie la combinaison suivante
                    
        raise ValueError("Impossible de lire le CSV. Vérifiez le format du fichier.")

    elif file_extension in ['xls', 'xlsx']:
        try:
            df = pd.read_excel(file_path)
            print("✅ Fichier Excel chargé avec succès.")
            return df
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier Excel : {e}")
            
    else:
        raise ValueError("Format non supporté. Veuillez fournir un fichier .csv, .xls ou .xlsx")

# --- Pour tester le script ---
if __name__ == "__main__":
    # Tu pourras tester en mettant un vrai fichier dans ton dossier data/
    df = load_accounting_file("data/bdcompta.csv")
    print(df.head())
    pass