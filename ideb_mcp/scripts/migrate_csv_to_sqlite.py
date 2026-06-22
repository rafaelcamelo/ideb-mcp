# -*- coding: utf-8 -*-
"""Migra os dados do CSV original para o banco de dados SQLite."""
from __future__ import annotations

import csv
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "ideb_anos_iniciais_municipios.csv")
DB_PATH  = os.path.join(DATA_DIR, "ideb_dados.db")

ANOS = ["2005", "2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021", "2023"]
ANOS_PROJECAO = ["2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021"]


def _to_float(val: str) -> float | None:
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", "."))
    except ValueError:
        return None


def migrate(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    from ideb_mcp.database import DataManager

    print(f"Migrando {csv_path} → {db_path}")
    dm = DataManager(db_path)

    rede_ids: dict[str, int] = {}
    municipio_ids: dict[str, int] = {}
    rows_inserted = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader):
            codigo = row.get("CO_MUNICIPIO", "").strip()
            rede   = row.get("REDE", "").strip()
            nome   = row.get("NO_MUNICIPIO", "").strip()
            estado = row.get("SG_UF", "").strip()

            if not codigo or not rede:
                continue

            if codigo not in municipio_ids:
                municipio_ids[codigo] = dm.upsert_municipio(codigo, nome, estado)

            if rede not in rede_ids:
                rede_ids[rede] = dm.get_or_create_rede(rede)

            id_municipio = municipio_ids[codigo]
            id_rede      = rede_ids[rede]

            for ano in ANOS:
                dm.insert_serie(
                    id_municipio=id_municipio,
                    id_rede=id_rede,
                    ano=int(ano),
                    ideb_observado=_to_float(row.get(f"VL_OBSERVADO_{ano}", "")),
                    ideb_projecao=_to_float(row.get(f"VL_PROJECAO_{ano}", "")) if ano in ANOS_PROJECAO else None,
                    nota_matematica=_to_float(row.get(f"VL_NOTA_MATEMATICA_{ano}", "")),
                    nota_portugues=_to_float(row.get(f"VL_NOTA_PORTUGUES_{ano}", "")),
                    nota_media=_to_float(row.get(f"VL_NOTA_MEDIA_{ano}", "")),
                    indicador_fluxo=_to_float(row.get(f"VL_INDICADOR_REND_{ano}", "")),
                )
                rows_inserted += 1

            if (i + 1) % 1000 == 0:
                dm.commit()
                print(f"  {i + 1} linhas do CSV processadas...")

    dm.commit()

    n_municipios = dm.conn.execute("SELECT COUNT(*) FROM municipios").fetchone()[0]
    n_series     = dm.conn.execute("SELECT COUNT(*) FROM series_historicas").fetchone()[0]
    dm.close()

    print(f"Migração concluída: {n_municipios} municípios, {n_series} registros de séries.")


if __name__ == "__main__":
    migrate()
