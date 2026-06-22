# IDEB MCP

Servidor [MCP](https://modelcontextprotocol.io) que expõe os dados do **IDEB** (Índice de Desenvolvimento da Educação Básica) por município brasileiro para consulta via Claude.

Cobre os 10 ciclos de avaliação (2005 a 2023) para cerca de 5.570 municípios, nas redes Estadual, Municipal e Pública (combinada), com IDEB observado, metas projetadas, notas de Matemática e Português e indicador de fluxo escolar.

Dados públicos do INEP/MEC.

---

## Etapas disponíveis

| Etapa | Descrição | Municípios |
|-------|-----------|-----------|
| `anos_iniciais` | Ensino Fundamental — 1º ao 5º ano | ~5.567 |
| `anos_finais` | Ensino Fundamental — 6º ao 9º ano | ~5.569 |
| `ensino_medio` | Ensino Médio | ~5.570 |

---

## Sumário

- [Instalação](#instalação)
- [Configuração no Claude Desktop](#configuração-no-claude-desktop)
- [Configuração no Claude Code](#configuração-no-claude-code)
- [Tools](#tools)
- [Exemplos de uso](#exemplos-de-uso)
- [Procedência dos dados](#procedência-dos-dados)
- [Estrutura do projeto](#estrutura-do-projeto)

---

## Instalação

Requer Python 3.10+ e [Git LFS](https://git-lfs.com) (para baixar o banco de dados).

```bash
git lfs install
git clone https://github.com/rafaelcamelo/ideb-mcp.git
cd ideb-mcp
pip install -e .
```

---

## Configuração no Claude Desktop

Edite o arquivo de configuração do Claude Desktop:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Adicione a chave `mcpServers`:

```json
{
  "mcpServers": {
    "ideb": {
      "command": "python",
      "args": ["-m", "ideb_mcp"]
    }
  }
}
```

> **Windows:** se o comando `python` sozinho não funcionar, use o caminho completo do executável (descubra com `where.exe python`), por exemplo:
> ```json
> "command": "C:\\Users\\SEU_USUARIO\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
> ```

Reinicie o Claude Desktop completamente após salvar.

---

## Configuração no Claude Code

```bash
claude mcp add ideb --scope user -- python -m ideb_mcp
```

---

## Tools

### `ideb_etapas_disponiveis()`
Lista as etapas de ensino com dados disponíveis no servidor.

### `ideb_buscar(municipio, estado, limite, etapa)`
Busca municípios por nome e/ou estado.

### `ideb_lookup(codigo, municipio, estado, rede, etapa)`
Retorna a série histórica completa (2005–2023) de um município: IDEB observado, metas projetadas, notas de Matemática e Português e indicador de fluxo. Localizável por código IBGE ou por nome + estado.

### `ideb_ranking(estado, ano, rede, limite, etapa)`
Ranking de municípios por IDEB em um estado, em um ano específico.

### `ideb_comparar(municipios, estado, ano, rede, etapa)`
Compara o IDEB de múltiplos municípios do mesmo estado.

### `ideb_estatisticas(estado, ano, rede, etapa)`
Resumo estatístico (média, mínimo, máximo) por estado e ano.

---

## Exemplos de uso

> "Qual o IDEB de Campinas nos anos finais em 2023?"

> "Quais os 10 melhores municípios de SP no ensino médio?"

> "Compare o IDEB de Ariquemes e Porto Velho em Rondônia"

> "Qual a média do IDEB dos anos iniciais no Brasil em 2023?"

---

## Procedência dos dados

Extraídos das planilhas públicas de divulgação de resultados do IDEB por município, disponibilizadas pelo INEP/MEC em https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/ideb/resultados.

O banco de dados SQLite pré-gerado (~75MB) está versionado via [Git LFS](https://git-lfs.com).

---

## Estrutura do projeto

```
ideb-mcp/
├── pyproject.toml
├── README.md
├── LICENSE.md
├── .gitattributes          # configura Git LFS para *.db
├── ideb_mcp/
│   ├── __init__.py
│   ├── server.py           # tools MCP
│   ├── database.py         # acesso ao SQLite
│   ├── scripts/
│   │   └── migrate_csv_to_sqlite.py   # migração de novos CSVs do INEP
│   └── data/
│       └── ideb_dados.db   # banco SQLite (~75MB, via Git LFS)
└── teste.py
```

---

## Licença

Código sob licença MIT. Dados do IDEB são públicos (INEP/MEC).
