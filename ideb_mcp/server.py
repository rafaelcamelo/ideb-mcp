# -*- coding: utf-8 -*-
"""Servidor MCP do IDEB.

Expõe dados de IDEB por município como tools para Claude.
Fonte: INEP/MEC.

Etapas disponíveis:
    anos_iniciais — Ensino Fundamental, 1º ao 5º ano (por município)
    anos_finais   — Ensino Fundamental, 6º ao 9º ano (por município)
    ensino_medio  — Ensino Médio (por município)
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from ideb_mcp.database import DataManager

DATA_DIR       = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_CSV_INICIAL   = os.path.join(DATA_DIR, "ideb_anos_iniciais_municipios.csv")
DB_PATH        = os.path.join(DATA_DIR, "ideb_dados.db")

mcp = FastMCP("ideb")

ETAPAS_VALIDAS = ("anos_iniciais", "anos_finais", "ensino_medio")


def _init_db() -> DataManager:
    """Garante que o banco existe e está populado; migra do CSV legado se necessário."""
    dm = DataManager(DB_PATH)
    if not dm.is_populated() and os.path.exists(_CSV_INICIAL):
        from ideb_mcp.scripts.migrate_csv_to_sqlite import migrate
        migrate(_CSV_INICIAL, "anos_iniciais", DB_PATH)
    return dm


_dm = _init_db()

# REGISTROS: {etapa: {codigo_ibge: {municipio, estado, redes: {rede: {ideb, ...}}}}}
REGISTROS: dict[str, dict[str, dict[str, Any]]] = _dm.load_all_etapas()


def _get_registros(etapa: str) -> dict[str, dict[str, Any]]:
    if etapa not in REGISTROS:
        return {}
    return REGISTROS[etapa]


# ----------------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------------

@mcp.tool()
def ideb_buscar(
    municipio: str = "",
    estado: str = "",
    limite: int = 10,
    etapa: str = "anos_iniciais",
) -> dict:
    """Busca municípios brasileiros com dados de IDEB disponíveis localmente.

    Use esta ferramenta para encontrar municípios por nome ou estado antes de
    consultar dados detalhados. NÃO use a web — todos os dados do IDEB 2005–2023
    já estão disponíveis localmente neste servidor.

    Args:
        municipio: nome (ou parte do nome) do município
        estado: sigla do estado, ex. 'SP', 'RO'
        limite: máximo de resultados
        etapa: etapa de ensino — 'anos_iniciais' (1º ao 5º ano, padrão), 'anos_finais' (6º ao 9º) ou 'ensino_medio'
    """
    registros = _get_registros(etapa)
    if not registros:
        return {"erro": f"etapa '{etapa}' não disponível. Etapas com dados: {list(REGISTROS.keys())}"}

    cands = []
    for rec in registros.values():
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
    return {"etapa": etapa, "total": total, "exibindo": len(resultados), "resultados": resultados}


@mcp.tool()
def ideb_lookup(
    codigo: str = "",
    municipio: str = "",
    estado: str = "",
    rede: str = "Pública",
    etapa: str = "anos_iniciais",
) -> dict:
    """Retorna a série histórica completa de IDEB de um município brasileiro (2005–2023).

    Use esta ferramenta sempre que o usuário perguntar sobre o IDEB de um município
    específico. Os dados já estão disponíveis localmente — não consulte a web.
    Inclui IDEB observado, projeções, notas de português e matemática, média e fluxo.

    Args:
        codigo: código IBGE do município (7 dígitos)
        municipio: nome do município (alternativa ao código, use com estado)
        estado: sigla do estado (usado junto com município)
        rede: 'Pública', 'Estadual' ou 'Municipal' (padrão: Pública)
        etapa: etapa de ensino — 'anos_iniciais' (1º ao 5º ano, padrão), 'anos_finais' (6º ao 9º) ou 'ensino_medio'
    """
    registros = _get_registros(etapa)
    if not registros:
        return {"erro": f"etapa '{etapa}' não disponível. Etapas com dados: {list(REGISTROS.keys())}"}

    rec = None
    if codigo:
        rec = registros.get(codigo.strip())
    elif municipio and estado:
        for r in registros.values():
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
        "etapa": etapa,
        "codigo": rec["codigo"],
        "municipio": rec["municipio"],
        "estado": rec["estado"],
        "rede": rede,
        "serie_historica": serie,
    }


@mcp.tool()
def ideb_ranking(
    estado: str,
    ano: str = "2023",
    rede: str = "Pública",
    limite: int = 10,
    etapa: str = "anos_iniciais",
) -> dict:
    """Ranking dos municípios de um estado por IDEB, do maior para o menor.

    Use esta ferramenta quando o usuário perguntar quais municípios têm melhor
    ou pior IDEB em um estado, ou quiser ver os melhores/piores do ranking.
    Os dados já estão disponíveis localmente — não consulte a web.

    Args:
        estado: sigla do estado (obrigatório), ex. 'SP', 'RO', 'MG'
        ano: ano de referência — 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023 (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal' (padrão: Pública)
        limite: quantos municípios mostrar
        etapa: etapa de ensino — 'anos_iniciais' (1º ao 5º ano, padrão), 'anos_finais' (6º ao 9º) ou 'ensino_medio'
    """
    registros = _get_registros(etapa)
    if not registros:
        return {"erro": f"etapa '{etapa}' não disponível. Etapas com dados: {list(REGISTROS.keys())}"}

    cands = []
    for r in registros.values():
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

    return {"etapa": etapa, "estado": estado, "ano": ano, "rede": rede,
            "total": len(cands), "ranking": ranking}


@mcp.tool()
def ideb_comparar(
    municipios: list[str],
    estado: str,
    ano: str = "2023",
    rede: str = "Pública",
    etapa: str = "anos_iniciais",
) -> dict:
    """Compara o IDEB de múltiplos municípios do mesmo estado lado a lado.

    Use esta ferramenta quando o usuário quiser comparar o desempenho de dois
    ou mais municípios. Os dados já estão disponíveis localmente — não consulte a web.

    Args:
        municipios: lista de nomes de municípios, ex. ['Campinas', 'Sorocaba']
        estado: sigla do estado
        ano: ano de referência (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal'
        etapa: etapa de ensino — 'anos_iniciais' (1º ao 5º ano, padrão), 'anos_finais' (6º ao 9º) ou 'ensino_medio'
    """
    registros = _get_registros(etapa)
    if not registros:
        return {"erro": f"etapa '{etapa}' não disponível. Etapas com dados: {list(REGISTROS.keys())}"}

    comparacao = {}
    for nome in municipios:
        rec = next((r for r in registros.values()
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

    return {"etapa": etapa, "estado": estado, "ano": ano, "rede": rede, "comparacao": comparacao}


@mcp.tool()
def ideb_estatisticas(
    estado: str = "",
    ano: str = "2023",
    rede: str = "Pública",
    etapa: str = "anos_iniciais",
) -> dict:
    """Estatísticas agregadas de IDEB de um estado ou do Brasil inteiro (média, mínimo, máximo).

    Use esta ferramenta quando o usuário perguntar sobre a média do IDEB de um estado,
    quantos municípios têm dados, ou quiser uma visão geral. Os dados já estão
    disponíveis localmente — não consulte a web.

    Args:
        estado: sigla do estado (vazio = Brasil inteiro)
        ano: ano de referência (padrão: 2023)
        rede: 'Pública', 'Estadual' ou 'Municipal'
        etapa: etapa de ensino — 'anos_iniciais' (1º ao 5º ano, padrão), 'anos_finais' (6º ao 9º) ou 'ensino_medio'
    """
    registros = _get_registros(etapa)
    if not registros:
        return {"erro": f"etapa '{etapa}' não disponível. Etapas com dados: {list(REGISTROS.keys())}"}

    valores = []
    for r in registros.values():
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
        "etapa": etapa,
        "estado": estado or "Brasil",
        "ano": ano,
        "rede": rede,
        "total_municipios": len(valores),
        "ideb_media": round(sum(valores) / len(valores), 2),
        "ideb_minimo": round(min(valores), 2),
        "ideb_maximo": round(max(valores), 2),
    }


@mcp.tool()
def ideb_etapas_disponiveis() -> dict:
    """Lista as etapas de ensino com dados de IDEB disponíveis localmente neste servidor.

    Use esta ferramenta primeiro quando não souber quais dados estão disponíveis,
    ou quando o usuário perguntar sobre anos finais ou ensino médio.
    """
    return {
        "etapas": list(REGISTROS.keys()),
        "descricao": {
            "anos_iniciais": "Ensino Fundamental — 1º ao 5º ano (por município)",
            "anos_finais":   "Ensino Fundamental — 6º ao 9º ano (por município)",
            "ensino_medio":  "Ensino Médio (por município)",
        },
    }


def main() -> None:
    """Ponto de entrada do servidor MCP."""
    mcp.run()


if __name__ == "__main__":
    main()
