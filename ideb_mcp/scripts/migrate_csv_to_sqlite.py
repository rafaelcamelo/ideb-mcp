# -*- coding: utf-8 -*-
"""Migra dados de um CSV do INEP para o banco de dados SQLite.

Uso:
    python -m ideb_mcp.scripts.migrate_csv_to_sqlite <csv> <etapa> [db]

Etapas suportadas:
    anos_iniciais   — CSV de municípios, anos iniciais do EF (1º ao 5º)
    anos_finais     — CSV de municípios, anos finais do EF (6º ao 9º)
    ensino_medio    — CSV de municípios, Ensino Médio
    escolas         — CSV de escolas individuais
"""
from __future__ import annotations

import csv
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
DB_PATH  = os.path.join(DATA_DIR, "ideb_dados.db")

ANOS = ["2005", "2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021", "2023"]
ANOS_PROJECAO = ["2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021"]

# Configuração de colunas por etapa (ajuste se o CSV do INEP usar nomes diferentes)
ETAPA_CONFIG: dict[str, dict] = {
    "anos_iniciais": {
        "col_ideb":       lambda ano: f"VL_OBSERVADO_{ano}",
        "col_projecao":   lambda ano: f"VL_PROJECAO_{ano}",
        "col_matematica": lambda ano: f"VL_NOTA_MATEMATICA_{ano}",
        "col_portugues":  lambda ano: f"VL_NOTA_PORTUGUES_{ano}",
        "col_media":      lambda ano: f"VL_NOTA_MEDIA_{ano}",
        "col_fluxo":      lambda ano: f"VL_INDICADOR_REND_{ano}",
        "anos": ANOS,
        "anos_projecao": ANOS_PROJECAO,
        "tipo": "municipio",
    },
    "anos_finais": {
        "col_ideb":       lambda ano: f"VL_OBSERVADO_{ano}",
        "col_projecao":   lambda ano: f"VL_PROJECAO_{ano}",
        "col_matematica": lambda ano: f"VL_NOTA_MATEMATICA_{ano}",
        "col_portugues":  lambda ano: f"VL_NOTA_PORTUGUES_{ano}",
        "col_media":      lambda ano: f"VL_NOTA_MEDIA_{ano}",
        "col_fluxo":      lambda ano: f"VL_INDICADOR_REND_{ano}",
        "anos": ANOS,
        "anos_projecao": ANOS_PROJECAO,
        "tipo": "municipio",
    },
    "ensino_medio": {
        "col_ideb":       lambda ano: f"VL_OBSERVADO_{ano}",
        "col_projecao":   lambda ano: f"VL_PROJECAO_{ano}",
        "col_matematica": lambda ano: f"VL_NOTA_MATEMATICA_{ano}",
        "col_portugues":  lambda ano: f"VL_NOTA_PORTUGUES_{ano}",
        "col_media":      lambda ano: f"VL_NOTA_MEDIA_{ano}",
        "col_fluxo":      lambda ano: f"VL_INDICADOR_REND_{ano}",
        "anos": ANOS,
        "anos_projecao": ANOS_PROJECAO,
        "tipo": "municipio",
    },
    "escolas": {
        "col_ideb":       lambda ano: f"VL_OBSERVADO_{ano}",
        "col_projecao":   lambda ano: f"VL_PROJECAO_{ano}",
        "col_matematica": lambda ano: f"VL_NOTA_MATEMATICA_{ano}",
        "col_portugues":  lambda ano: f"VL_NOTA_PORTUGUES_{ano}",
        "col_media":      lambda ano: f"VL_NOTA_MEDIA_{ano}",
        "col_fluxo":      lambda ano: f"VL_INDICADOR_REND_{ano}",
        "anos": ANOS,
        "anos_projecao": ANOS_PROJECAO,
        "tipo": "escola",
        # Colunas de identificação da escola no CSV
        "col_codigo_escola": "CO_ESCOLA",
        "col_nome_escola":   "NO_ESCOLA",
        "col_etapa_escola":  "DS_ETAPA",  # anos_iniciais ou anos_finais
    },
}


def _to_float(val: str) -> float | None:
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", "."))
    except ValueError:
        return None


def migrate(csv_path: str, etapa: str, db_path: str = DB_PATH) -> None:
    """Migra um CSV do INEP para o banco SQLite na etapa informada."""
    if etapa not in ETAPA_CONFIG:
        raise ValueError(
            f"Etapa '{etapa}' desconhecida. Válidas: {list(ETAPA_CONFIG.keys())}"
        )

    from ideb_mcp.database import DataManager

    cfg = ETAPA_CONFIG[etapa]
    print(f"Migrando {csv_path} → {db_path} (etapa: {etapa})")
    dm = DataManager(db_path)

    if cfg["tipo"] == "municipio":
        _migrate_municipios(dm, csv_path, etapa, cfg)
    else:
        _migrate_escolas(dm, csv_path, etapa, cfg)

    dm.close()


def _migrate_municipios(dm, csv_path: str, etapa: str, cfg: dict) -> None:
    from ideb_mcp.database import DataManager

    rede_ids: dict[str, int] = {}
    municipio_ids: dict[str, int] = {}

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

            for ano in cfg["anos"]:
                dm.insert_serie(
                    id_municipio=id_municipio,
                    id_rede=id_rede,
                    ano=int(ano),
                    etapa=etapa,
                    ideb_observado=_to_float(row.get(cfg["col_ideb"](ano), "")),
                    ideb_projecao=_to_float(row.get(cfg["col_projecao"](ano), ""))
                        if ano in cfg["anos_projecao"] else None,
                    nota_matematica=_to_float(row.get(cfg["col_matematica"](ano), "")),
                    nota_portugues=_to_float(row.get(cfg["col_portugues"](ano), "")),
                    nota_media=_to_float(row.get(cfg["col_media"](ano), "")),
                    indicador_fluxo=_to_float(row.get(cfg["col_fluxo"](ano), "")),
                )

            if (i + 1) % 1000 == 0:
                dm.commit()
                print(f"  {i + 1} linhas processadas...")

    dm.commit()
    n_mun   = dm.conn.execute("SELECT COUNT(*) FROM municipios").fetchone()[0]
    n_series = dm.conn.execute(
        "SELECT COUNT(*) FROM series_historicas WHERE etapa = ?", (etapa,)
    ).fetchone()[0]
    print(f"Concluído: {n_mun} municípios no banco, {n_series} séries para '{etapa}'.")


def _migrate_escolas(dm, csv_path: str, etapa: str, cfg: dict) -> None:
    escola_ids: dict[str, int] = {}
    municipio_ids: dict[str, int] = {}

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for i, row in enumerate(reader):
            cod_escola = row.get(cfg["col_codigo_escola"], "").strip()
            nome_escola = row.get(cfg["col_nome_escola"], "").strip()
            cod_mun = row.get("CO_MUNICIPIO", "").strip()
            nome_mun = row.get("NO_MUNICIPIO", "").strip()
            estado = row.get("SG_UF", "").strip()
            rede = row.get("REDE", "").strip()
            etapa_escola = row.get(cfg.get("col_etapa_escola", ""), "").strip() or etapa

            if not cod_escola:
                continue

            if cod_mun and cod_mun not in municipio_ids:
                municipio_ids[cod_mun] = dm.upsert_municipio(cod_mun, nome_mun, estado)

            id_municipio = municipio_ids.get(cod_mun)

            if cod_escola not in escola_ids:
                escola_ids[cod_escola] = dm.upsert_escola(
                    cod_escola, nome_escola, id_municipio, rede
                )

            id_escola = escola_ids[cod_escola]

            for ano in cfg["anos"]:
                dm.insert_serie_escola(
                    id_escola=id_escola,
                    ano=int(ano),
                    etapa=etapa_escola,
                    ideb_observado=_to_float(row.get(cfg["col_ideb"](ano), "")),
                    ideb_projecao=_to_float(row.get(cfg["col_projecao"](ano), ""))
                        if ano in cfg["anos_projecao"] else None,
                    nota_matematica=_to_float(row.get(cfg["col_matematica"](ano), "")),
                    nota_portugues=_to_float(row.get(cfg["col_portugues"](ano), "")),
                    nota_media=_to_float(row.get(cfg["col_media"](ano), "")),
                    indicador_fluxo=_to_float(row.get(cfg["col_fluxo"](ano), "")),
                )

            if (i + 1) % 1000 == 0:
                dm.commit()
                print(f"  {i + 1} linhas processadas...")

    dm.commit()
    n_escolas = dm.conn.execute("SELECT COUNT(*) FROM escolas").fetchone()[0]
    n_series  = dm.conn.execute(
        "SELECT COUNT(*) FROM series_escolas WHERE etapa = ?", (etapa,)
    ).fetchone()[0]
    print(f"Concluído: {n_escolas} escolas no banco, {n_series} séries para '{etapa}'.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    csv_arg   = sys.argv[1]
    etapa_arg = sys.argv[2]
    db_arg    = sys.argv[3] if len(sys.argv) > 3 else DB_PATH
    migrate(csv_arg, etapa_arg, db_arg)
