# IDEB MCP

Servidor [MCP](https://modelcontextprotocol.io) que expõe os dados do **IDEB** (Índice de Desenvolvimento da Educação Básica) por município brasileiro — anos iniciais do Ensino Fundamental — para consulta via Claude.

Cobre os 10 ciclos de avaliação (2005 a 2023) para cerca de 5.570 municípios, nas redes Estadual, Municipal e Pública (combinada), com IDEB observado, metas projetadas, notas de Matemática e Português e indicador de fluxo escolar.

Dados públicos do INEP/MEC.

---

## Sumário

- [Instalação](#instalação)
- [Configuração no Claude Desktop](#configuração-no-claude-desktop)
- [Configuração no Claude Code](#configuração-no-claude-code)
- [Tools](#tools)
- [Procedência dos dados](#procedência-dos-dados)
- [Limitações](#limitações)
- [Estrutura do projeto](#estrutura-do-projeto)

---

## Instalação

Requer Python 3.10+.

```bash
git clone https://github.com/SEU_USUARIO/ideb-mcp.git
cd ideb-mcp
pip install -e .
```

---

## Configuração no Claude Desktop

Edite o arquivo de configuração do Claude Desktop:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Adicione:

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

### `ideb_buscar(municipio, estado, limite)`
Busca municípios por nome e/ou estado.

### `ideb_lookup(codigo, municipio, estado, rede)`
Retorna a série histórica completa (2005–2023) de um município: IDEB observado, metas, notas e indicador de fluxo. Localizável por código IBGE ou por nome + estado.

### `ideb_ranking(estado, ano, rede, limite)`
Ranking de municípios por IDEB em um estado, em um ano específico.

### `ideb_comparar(municipios, estado, ano, rede)`
Compara o IDEB de múltiplos municípios.

### `ideb_estatisticas(estado, ano, rede)`
Resumo estatístico (média, mínimo, máximo) por estado/ano.

---

## Procedência dos dados

Extraídos da planilha pública de divulgação de resultados do IDEB por município (anos iniciais), disponibilizada pelo INEP/MEC em https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/ideb/resultados.

---

## Limitações

- Cobre apenas os **anos iniciais** do Ensino Fundamental (não inclui anos finais nem Ensino Médio).
- Nem todos os municípios têm dado em todos os anos/redes (rede inexistente ou amostra insuficiente naquele ciclo).

---

## Estrutura do projeto:
ideb-mcp/

├── pyproject.toml

├── README.md

├── LICENSE.md

├── ideb_mcp/

│   ├── init.py

│   ├── main.py

│   ├── server.py

│   └── data/

│       └── ideb_anos_iniciais_municipios.csv

└── teste.py

---

## Licença

Código sob licença MIT. Dados do IDEB são públicos (INEP/MEC).