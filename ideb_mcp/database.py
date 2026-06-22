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
    etapa            TEXT NOT NULL DEFAULT 'anos_iniciais',
    ideb_observado   REAL,
    ideb_projecao    REAL,
    nota_matematica  REAL,
    nota_portugues   REAL,
    nota_media       REAL,
    indicador_fluxo  REAL,
    FOREIGN KEY(id_municipio) REFERENCES municipios(id_municipio),
    FOREIGN KEY(id_rede)      REFERENCES redes(id_rede),
    UNIQUE(id_municipio, id_rede, ano, etapa)
);
CREATE INDEX IF NOT EXISTS idx_ser_mun       ON series_historicas(id_municipio);
CREATE INDEX IF NOT EXISTS idx_ser_rede      ON series_historicas(id_rede);
CREATE INDEX IF NOT EXISTS idx_ser_ano       ON series_historicas(ano);
CREATE INDEX IF NOT EXISTS idx_ser_etapa     ON series_historicas(etapa);
CREATE INDEX IF NOT EXISTS idx_ser_mun_rede_ano ON series_historicas(id_municipio, id_rede, ano, etapa);

CREATE TABLE IF NOT EXISTS escolas (
    id_escola     INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_escola TEXT UNIQUE NOT NULL,
    nome          TEXT NOT NULL,
    id_municipio  INTEGER,
    rede          TEXT,
    FOREIGN KEY(id_municipio) REFERENCES municipios(id_municipio)
);
CREATE INDEX IF NOT EXISTS idx_esc_mun ON escolas(id_municipio);

CREATE TABLE IF NOT EXISTS series_escolas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_escola       INTEGER NOT NULL,
    ano             INTEGER NOT NULL,
    etapa           TEXT NOT NULL,
    ideb_observado  REAL,
    ideb_projecao   REAL,
    nota_matematica REAL,
    nota_portugues  REAL,
    nota_media      REAL,
    indicador_fluxo REAL,
    FOREIGN KEY(id_escola) REFERENCES escolas(id_escola),
    UNIQUE(id_escola, ano, etapa)
);
CREATE INDEX IF NOT EXISTS idx_sesc_escola ON series_escolas(id_escola);
CREATE INDEX IF NOT EXISTS idx_sesc_etapa  ON series_escolas(etapa);
"""

MIGRATIONS = [
    # Adiciona coluna etapa se o banco foi criado antes dessa feature
    "ALTER TABLE series_historicas ADD COLUMN etapa TEXT NOT NULL DEFAULT 'anos_iniciais'",
]


class DataManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.ensure_tables()
        self._run_migrations()

    def ensure_tables(self) -> None:
        for stmt in SCHEMA.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                self.conn.execute(stmt)
        self.conn.commit()

    def _run_migrations(self) -> None:
        """Aplica migrações de schema que podem não existir em bancos antigos."""
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(series_historicas)")}
        if "etapa" not in cols:
            self.conn.execute(MIGRATIONS[0])
            self.conn.commit()

    def is_populated(self) -> bool:
        row = self.conn.execute("SELECT COUNT(*) FROM municipios").fetchone()
        return row[0] > 0

    def get_etapas(self) -> list[str]:
        """Retorna as etapas com dados no banco."""
        rows = self.conn.execute(
            "SELECT DISTINCT etapa FROM series_historicas ORDER BY etapa"
        ).fetchall()
        return [r[0] for r in rows]

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
        etapa: str,
        ideb_observado: float | None,
        ideb_projecao: float | None,
        nota_matematica: float | None,
        nota_portugues: float | None,
        nota_media: float | None,
        indicador_fluxo: float | None,
    ) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO series_historicas
               (id_municipio, id_rede, ano, etapa, ideb_observado, ideb_projecao,
                nota_matematica, nota_portugues, nota_media, indicador_fluxo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_municipio, id_rede, ano, etapa, ideb_observado, ideb_projecao,
             nota_matematica, nota_portugues, nota_media, indicador_fluxo),
        )

    def upsert_escola(
        self, codigo_escola: str, nome: str, id_municipio: int | None, rede: str | None
    ) -> int:
        self.conn.execute(
            """INSERT OR IGNORE INTO escolas(codigo_escola, nome, id_municipio, rede)
               VALUES (?, ?, ?, ?)""",
            (codigo_escola, nome, id_municipio, rede),
        )
        return self.conn.execute(
            "SELECT id_escola FROM escolas WHERE codigo_escola = ?", (codigo_escola,)
        ).fetchone()[0]

    def insert_serie_escola(
        self,
        id_escola: int,
        ano: int,
        etapa: str,
        ideb_observado: float | None,
        ideb_projecao: float | None,
        nota_matematica: float | None,
        nota_portugues: float | None,
        nota_media: float | None,
        indicador_fluxo: float | None,
    ) -> None:
        self.conn.execute(
            """INSERT OR REPLACE INTO series_escolas
               (id_escola, ano, etapa, ideb_observado, ideb_projecao,
                nota_matematica, nota_portugues, nota_media, indicador_fluxo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_escola, ano, etapa, ideb_observado, ideb_projecao,
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

    def load_all(self, etapa: str = "anos_iniciais") -> dict[str, dict[str, Any]]:
        """Reconstrói o dicionário REGISTROS para uma etapa específica."""
        municipios: dict[int, dict[str, Any]] = {}

        for row in self.conn.execute(
            """SELECT DISTINCT m.id_municipio, m.codigo_ibge, m.nome, m.estado
               FROM series_historicas s
               JOIN municipios m ON m.id_municipio = s.id_municipio
               WHERE s.etapa = ?""",
            (etapa,),
        ):
            municipios[row["id_municipio"]] = {
                "codigo": row["codigo_ibge"],
                "municipio": row["nome"],
                "estado": row["estado"],
                "redes": {},
            }

        for row in self.conn.execute(
            """SELECT m.id_municipio, r.nome AS rede, s.ano,
                      s.ideb_observado, s.ideb_projecao,
                      s.nota_matematica, s.nota_portugues, s.nota_media, s.indicador_fluxo
               FROM series_historicas s
               JOIN municipios m ON m.id_municipio = s.id_municipio
               JOIN redes r ON r.id_rede = s.id_rede
               WHERE s.etapa = ?""",
            (etapa,),
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

    def load_all_etapas(self) -> dict[str, dict[str, Any]]:
        """Carrega todas as etapas disponíveis. Retorna {etapa: {codigo: {...}}}."""
        return {etapa: self.load_all(etapa) for etapa in self.get_etapas()}

    def close(self) -> None:
        self.conn.close()
