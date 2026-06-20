# -*- coding: utf-8 -*-
"""Servidor MCP do IDEB.

Expõe dados de IDEB por município (anos iniciais) como tools para Claude.
Fonte: INEP/MEC.
"""
from __future__ import annotations

import csv
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
MUNICIPIOS_CSV = os.path.join(DATA_DIR, "ideb_anos_iniciais_municipios.csv")

mcp = FastMCP("ideb")

# ----------------------------------------------------------------------------
# Dicionário de colunas: cada métrica tem uma coluna por ano no CSV original
# (ex.: VL_OBSERVADO_2023, VL_OBSERVADO_2021...). Essas funções geram o nome
# da coluna certa para cada ano, em vez de escrever cada nome na mão.
# ----------------------------------------------------------------------------
ANOS = ["2005", "2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021", "2023"]
ANOS_PROJECAO = ["2007", "2009", "2011", "2013", "2015", "2017", "2019", "2021"]

def _col_ideb(ano: str) -> str:
    return f"VL_OBSERVADO_{ano}"

def _col_projecao(ano: str) -> str:
    return f"VL_PROJECAO_{ano}"

def _col_matematica(ano: str) -> str:
    return f"VL_NOTA_MATEMATICA_{ano}"

def _col_portugues(ano: str) -> str:
    return f"VL_NOTA_PORTUGUES_{ano}"

def _col_media(ano: str) -> str:
    return f"VL_NOTA_MEDIA_{ano}"

def _col_fluxo(ano: str) -> str:
    return f"VL_INDICADOR_REND_{ano}"


def _to_float(val: str) -> float | None:
    """Converte string com vírgula decimal para float. Vazio -> None."""
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace(",", "."))
    except ValueError:
        return None


def _load() -> dict[str, dict[str, Any]]:
    """Carrega o CSV. Cada município pode ter até 3 linhas (uma por rede:
    Estadual, Municipal, Pública). Agrupamos tudo sob o código do município."""
    registros: dict[str, dict[str, Any]] = {}

    with open(MUNICIPIOS_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            codigo = row.get("CO_MUNICIPIO", "").strip()
            rede = row.get("REDE", "").strip()
            if not codigo or not rede:
                continue

            if codigo not in registros:
                registros[codigo] = {
                    "codigo": codigo,
                    "municipio": row.get("NO_MUNICIPIO", "").strip(),
                    "estado": row.get("SG_UF", "").strip(),
                    "redes": {},
                }

            serie = {"ideb": {}, "projecao": {}, "matematica": {},
                     "portugues": {}, "media": {}, "fluxo": {}}

            for ano in ANOS:
                v = _to_float(row.get(_col_ideb(ano), ""))
                if v is not None:
                    serie["ideb"][ano] = v
                v = _to_float(row.get(_col_matematica(ano), ""))
                if v is not None:
                    serie["matematica"][ano] = v
                v = _to_float(row.get(_col_portugues(ano), ""))
                if v is not None:
                    serie["portugues"][ano] = v
                v = _to_float(row.get(_col_media(ano), ""))
                if v is not None:
                    serie["media"][ano] = v
                v = _to_float(row.get(_col_fluxo(ano), ""))
                if v is not None:
                    serie["fluxo"][ano] = v

            for ano in ANOS_PROJECAO:
                v = _to_float(row.get(_col_projecao(ano), ""))
                if v is not None:
                    serie["projecao"][ano] = v

            registros[codigo]["redes"][rede] = serie

    return registros


REGISTROS = _load()

# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------

@mcp.tool()
def ideb_buscar(municipio: str = "", estado: str = "", limite: int = 10) -> dict:
    """Busca municípios por nome e/ou estado.

    Args:
        municipio: nome (ou parte do nome) do município
        estado: sigla do estado, ex. 'SP', 'RO'
        limite: máximo de resultados
    """
    cands = []
    for rec in REGISTROS.values():
        if municipio and municipio.lower() not in rec["municipio"].lower():
            continue
        if estado and rec["estado"].upper() != estado.upper():
            continue
        cands.append(rec)

    cands.sort(key=lambda r: r["municipio"])
    total = len(cands)
    resultados = [
        {"codigo": r["codigo"], "municipio": r["municipio"], "estado": r["estado"],
         "redes_disponiveis": list(r["redes"].keys())}
        for r in cands[:limite]
    ]
    return {"total": total, "exibindo": len(resultados), "resultados": resultados}


@mcp.tool()
def ideb_lookup(codigo: str = "", municipio: str = "", estado: str = "",
                rede: str = "Pública") -> dict:
    """Retorna a série histórica completa de IDEB de um município (todos os
    anos disponíveis: 2005 a 2023).

    Pode localizar por código IBGE OU por nome + estado.

    Args:
        codigo: código IBGE do município (7 dígitos)
        municipio: nome do município (alternativa ao código, use com estado)
        estado: sigla do estado (usado junto com município)
        rede: 'Pública', 'Estadual' ou 'Municipal' (padrão: Pública)
    """
    rec = None
    if codigo:
        rec = REGISTROS.get(codigo.strip())
    elif municipio and estado:
        for r in REGISTROS.values():
            if (r["municipio"].lower() == municipio.lower()
                    and r["estado"].upper() == estado.upper()):
                rec = r
                break

    if not rec:
        return {"erro": "município não encontrado. Use ideb_buscar para localizar."}

    serie = rec["redes"].get(rede)
    if not serie:
        return {"erro": f"rede '{rede}' não disponível para este município",
                "redes_disponiveis": list(rec["redes"].keys())}

    return {
        "codigo": rec["codigo"],
        "municipio": rec["municipio"],
        "estado": rec["estado"],
        "rede": rede,
        "serie_historica": serie,
    }


@mcp.tool()
def ideb_ranking(estado: str, ano: str = "2023", rede: str = "Pública",
                 limite: int = 10) -> dict:
    """Ranking de municípios por IDEB em um estado, em um ano específico.

    Args:
        estado: sigla do estado (obrigatório)
        ano: ano de referência. Anos disponíveis: 2005, 2007, 2009, 2011,
            2013, 2015, 2017, 2019, 2021, 2023 (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal' (padrão: Pública)
        limite: quantos municípios mostrar
    """
    cands = []
    for r in REGISTROS.values():
        if r["estado"].upper() != estado.upper():
            continue
        serie = r["redes"].get(rede)
        if not serie:
            continue
        ideb = serie["ideb"].get(ano)
        if ideb is not None:
            cands.append((r["municipio"], ideb))

    cands.sort(key=lambda x: x[1], reverse=True)
    ranking = [{"posicao": i + 1, "municipio": nome, "ideb": ideb}
               for i, (nome, ideb) in enumerate(cands[:limite])]

    return {"estado": estado, "ano": ano, "rede": rede,
            "total": len(cands), "ranking": ranking}


@mcp.tool()
def ideb_comparar(municipios: list[str], estado: str, ano: str = "2023",
                  rede: str = "Pública") -> dict:
    """Compara o IDEB de múltiplos municípios (mesmo estado) em um ano.

    Args:
        municipios: lista de nomes de municípios
        estado: sigla do estado
        ano: ano de referência (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal'
    """
    comparacao = {}
    for nome in municipios:
        rec = next((r for r in REGISTROS.values()
                    if r["municipio"].lower() == nome.lower()
                    and r["estado"].upper() == estado.upper()), None)
        if not rec:
            comparacao[nome] = {"erro": "não encontrado"}
            continue
        serie = rec["redes"].get(rede)
        if not serie:
            comparacao[nome] = {"erro": f"rede '{rede}' não disponível"}
            continue
        comparacao[nome] = {"ideb": serie["ideb"].get(ano)}

    return {"estado": estado, "ano": ano, "rede": rede, "comparacao": comparacao}


@mcp.tool()
def ideb_estatisticas(estado: str = "", ano: str = "2023", rede: str = "Pública") -> dict:
    """Resumo estatístico do IDEB (média, mínimo, máximo) por estado em um ano.

    Args:
        estado: sigla do estado (vazio = Brasil inteiro)
        ano: ano de referência (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal'
    """
    valores = []
    for r in REGISTROS.values():
        if estado and r["estado"].upper() != estado.upper():
            continue
        serie = r["redes"].get(rede)
        if not serie:
            continue
        v = serie["ideb"].get(ano)
        if v is not None:
            valores.append(v)

    if not valores:
        return {"erro": "nenhum dado encontrado para esses filtros"}

    return {
        "estado": estado or "Brasil",
        "ano": ano,
        "rede": rede,
        "total_municipios": len(valores),
        "ideb_media": round(sum(valores) / len(valores), 2),
        "ideb_minimo": round(min(valores), 2),
        "ideb_maximo": round(max(valores), 2),
    }


def main() -> None:
    """Ponto de entrada do servidor MCP."""
    mcp.run()


if __name__ == "__main__":
    main()