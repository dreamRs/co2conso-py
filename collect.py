import requests
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path
from datetime import datetime, timezone

BASE_URL = "https://odre.opendatasoft.com"
DATASET = "part-enr-intensite-ges-conso-tr"
BASE_DIR = Path(__file__).parent
PARQUET_PATH = BASE_DIR / "inputs" / "donnees.parquet"

def download_dataset(where=None):
    url = f"{BASE_URL}/api/explore/v2.1/catalog/datasets/{DATASET}/exports/csv"
    params = {"limit": -1}
    if where:
        params["where"] = where
    headers = {"User-Agent": "Python dashboard (odre.opendatasoft.com)"}
    res = requests.get(url, params=params, headers=headers)
    res.raise_for_status()
    from io import StringIO
    df = pd.read_csv(StringIO(res.text), sep=";")
    return df

def charger_donnees():
    (BASE_DIR / "inputs").mkdir(exist_ok=True)

    if PARQUET_PATH.exists():
        cache = pd.read_parquet(PARQUET_PATH)
        cache["date_heure_utc"] = pd.to_datetime(cache["date_heure_utc"], utc=True)
        cache = (cache
            .dropna(subset=["intensite_emissions_conso"])
            .drop_duplicates(subset=["date_heure_utc"])
            .sort_values("date_heure_utc"))

        date_max = cache["date_heure_utc"].max()
        now = datetime.now(timezone.utc)
        diff_hours = (now - date_max).total_seconds() / 3600

        if diff_hours > 0:
            where = f"date_heure_utc >= '{date_max.strftime('%Y-%m-%dT%H:%M:%S')}'"
            nouvelles = download_dataset(where=where)
            nouvelles["date_heure_utc"] = pd.to_datetime(nouvelles["date_heure_utc"], utc=True)

            donnees = (pd.concat([cache, nouvelles])
                .sort_values("date_heure_utc")
                .dropna(subset=["intensite_emissions_conso"])
                .drop_duplicates(subset=["date_heure_utc"]))

            donnees.to_parquet(PARQUET_PATH, index=False)
            return donnees
        else:
            return cache
    else:
        donnees = download_dataset()
        donnees["date_heure_utc"] = pd.to_datetime(donnees["date_heure_utc"], utc=True)
        donnees = (donnees
            .dropna(subset=["intensite_emissions_conso"])
            .drop_duplicates(subset=["date_heure_utc"]))
        donnees.to_parquet(PARQUET_PATH, index=False)
        return donnees

if __name__ == "__main__":
    df = charger_donnees()
    print(f"✓ {len(df)} lignes chargées")