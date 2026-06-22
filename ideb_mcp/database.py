# -*- coding: utf-8 -*-
"""Camada de acesso ao banco de dados SQLite do IDEB."""
from __future__ import annotations

import sqlite3
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS municipios (
    id_municipio INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_ibge  TEXT UNIQUE NOT NULL,
    nome         TEXT NOT NULL,
    estado       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mun_estado ON municipios(estado);
CREATE INDEX IF NOT EXISTS idx_mun_nome   ON municipios(nome);

CREATE TABLE IF NOT EXISTS redes (
    id_rede INTEGER PRIMARY KEY AUTOINCREMENT,
    nome    TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS series_historicas (
    id_serie         INTEGER PRIMARY KEY AUTOINCREMENT,
    id_municipio     INTEGER NOT NULL,
    id_rede          INTEGER NOT NULL,
    ano              INTEGER NOT NULL,
    ideb_observado   REAL,
    ideb_projecao    REAL,
    nota_matematica  REAL,
    nota_portugues   REAL,
    nota_media       REAL,
    indicador_fluxo  REAL,
    FOREIGN KEY(id_municipio) REFERENCES municipios(id_municipio),
    FOREIGN KEY(id_rede)      REFERENCES redes(id_rede),
    UNIQUE(id_municipio, id_rede, ano)
);
CREATE INDEX IF NOT EXISTS idx_ser_mun  ON series_historicas(id_municipio);
CREATE INDEX IF NOT EXISTS idx_ser_rede ON series_historicas(id_rede);
CREATE INDEX IF NOT EXISTS idx_ser_ano  ON series_historicas(ano);
CREATE INDEX IF NOT EXISTS idx_ser_mun_rede_ano ON series_historicas(id_municipio, id_rede, ano);
"""


class DataManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.ensure_tables()

    def ensure_tables(self) -> None:
        for stmt in SCHEMA.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self.conn.execute(stmt)
        self.conn.commit()

    def is_populated(self) -> bool:
        row = self.conn.execute("SELECT COUNT(*) FROM municipios").fetchone()
        return row[0] > 0

    # ------------------------------------------------------------------ write

    def upsert_municipio(self, codigo_ibge: str, nome: str, estado: str) -> int:
        self.conn.execute(
            "INSERT OR IGNORE INTO municipios(codigo_ibge, nome, estado) VALUES (?, ?, ?)",
            (codigo_ibge, nome, estado),
        )
        return self.conn.execute(
            "SELECT id_municipio FROM municipios WHERE codigo_ibge = ?", (codigo_ibge,)
        ).fetchone()[0]

    def get_or_create_rede(self, nome: str) -> int:
        self.conn.execute("INSERT OR IGNORE INTO redes(nome) VALUES (?)", (nome,))
        return self.conn.execute(
            "SELECT id_rede FROM redes WHERE nome = ?", (nome,)
        ).fetchone()[0]

    def insert_serie(
        self,
        id_municipio: int,
        id_rede: int,
        ano: int,
        ideb_observado: float | None,
        ideb_projecao: float | None,
        nota_matematica: float | None,
        nota_portugues: float | None,
        nota_media: float | None,
        indicador_fluxo: float | None,
    ) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO series_historicas
               (id_municipio, id_rede, ano, ideb_observado, ideb_projecao,
                nota_matematica, nota_portugues, nota_media, indicador_fluxo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_municipio, id_rede, ano, ideb_observado, ideb_projecao,
             nota_matematica, nota_portugues, nota_media, indicador_fluxo),
        )

    def commit(self) -> None:
        self.conn.commit()

    # ------------------------------------------------------------------ read

    def get_all_municipios(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT id_municipio, codigo_ibge, nome, estado FROM municipios"
        ).fetchall()

    def get_all_redes(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT id_rede, nome FROM redes").fetchall()

    def get_series_for_municipio(self, id_municipio: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT r.nome AS rede, s.ano, s.ideb_observado, s.ideb_projecao,
                      s.nota_matematica, s.nota_portugues, s.nota_media, s.indicador_fluxo
               FROM series_historicas s
               JOIN redes r ON r.id_rede = s.id_rede
               WHERE s.id_municipio = ?
               ORDER BY r.nome, s.ano""",
            (id_municipio,),
        ).fetchall()

    def load_all(self) -> dict[str, dict[str, Any]]:
        """Reconstrói o dicionário REGISTROS a partir do banco de dados."""
        municipios = {
            row["id_municipio"]: {
                "codigo": row["codigo_ibge"],
                "municipio": row["nome"],
                "estado": row["estado"],
                "redes": {},
            }
            for row in self.get_all_municipios()
        }

        for row in self.conn.execute(
            """SELECT m.id_municipio, m.codigo_ibge, r.nome AS rede, s.ano,
                      s.ideb_observado, s.ideb_projecao,
                      s.nota_matematica, s.nota_portugues, s.nota_media, s.indicador_fluxo
               FROM series_historicas s
               JOIN municipios m ON m.id_municipio = s.id_municipio
               JOIN redes r ON r.id_rede = s.id_rede"""
        ):
            rec = municipios[row["id_municipio"]]
            rede = row["rede"]
            ano = str(row["ano"])

            if rede not in rec["redes"]:
                rec["redes"][rede] = {
                    "ideb": {}, "projecao": {}, "matematica": {},
                    "portugues": {}, "media": {}, "fluxo": {},
                }

            serie = rec["redes"][rede]
            if row["ideb_observado"] is not None:
                serie["ideb"][ano] = row["ideb_observado"]
            if row["ideb_projecao"] is not None:
                serie["projecao"][ano] = row["ideb_projecao"]
            if row["nota_matematica"] is not None:
                serie["matematica"][ano] = row["nota_matematica"]
            if row["nota_portugues"] is not None:
                serie["portugues"][ano] = row["nota_portugues"]
            if row["nota_media"] is not None:
                serie["media"][ano] = row["nota_media"]
            if row["indicador_fluxo"] is not None:
                serie["fluxo"][ano] = row["indicador_fluxo"]

        return {rec["codigo"]: rec for rec in municipios.values()}

    def close(self) -> None:
        self.conn.close()
