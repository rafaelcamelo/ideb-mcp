# IDEB MCP

Conecte o Claude ao banco de dados do **IDEB** (Índice de Desenvolvimento da Educação Básica) e consulte o desempenho educacional de qualquer município brasileiro diretamente na conversa.

Cobre os 10 ciclos de avaliação (2005 a 2023) para cerca de 5.570 municípios, nas redes Estadual, Municipal e Pública, com IDEB observado, metas projetadas, notas de Matemática e Português e indicador de fluxo escolar.

Dados públicos do INEP/MEC.

---

## O que você pode perguntar

<!-- INSERIR PRINT: conversa mostrando ranking de municípios de SP -->

<!-- INSERIR PRINT: conversa mostrando série histórica de um município -->

<!-- INSERIR PRINT: conversa comparando dois municípios -->

---

## Etapas disponíveis

| Etapa | Descrição |
|-------|-----------|
| Anos Iniciais | Ensino Fundamental — 1º ao 5º ano |
| Anos Finais | Ensino Fundamental — 6º ao 9º ano |
| Ensino Médio | Ensino Médio |

---

## Instalação passo a passo

### 1. Instale o Python

Acesse https://www.python.org/downloads e baixe a versão mais recente.

> **Windows:** durante a instalação, marque a opção **"Add Python to PATH"** antes de clicar em Install.

Para verificar se a instalação funcionou, abra o terminal e digite:
```
python --version
```

### 2. Instale o Git

Acesse https://git-scm.com/downloads e instale o Git para o seu sistema.

Para verificar:
```
git --version
```

### 3. Instale o Git LFS

O banco de dados do IDEB tem ~75MB e é armazenado via Git LFS (Large File Storage). Acesse https://git-lfs.com e instale.

Para verificar:
```
git lfs version
```

### 4. Clone o repositório

Abra o terminal e rode:

```bash
git lfs install
git clone https://github.com/rafaelcamelo/ideb-mcp.git
cd ideb-mcp
```

### 5. Instale o pacote

```bash
pip install -e .
```

---

## Configuração no Claude Desktop

> Não tem o Claude Desktop? Baixe em https://claude.ai/download

**1.** Abra o arquivo de configuração do Claude Desktop:

- **Windows:** pressione `Win + R`, digite `%APPDATA%\Claude` e abra o arquivo `claude_desktop_config.json`
- **macOS:** abra o Finder, pressione `Cmd + Shift + G`, cole `~/Library/Application Support/Claude` e abra o arquivo `claude_desktop_config.json`

Se o arquivo não existir, crie-o.

**2.** Adicione o servidor IDEB ao JSON. Se o arquivo estiver vazio, cole isto:

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

Se o arquivo já tiver conteúdo, adicione apenas o bloco `"ideb"` dentro de `"mcpServers"`:

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

> **Windows:** se o Claude não encontrar o Python, substitua `"python"` pelo caminho completo. Para descobrir o caminho, abra o terminal e rode `where.exe python`. O resultado será algo como `C:\Users\SEU_USUARIO\AppData\Local\Programs\Python\Python312\python.exe` — use esse valor no lugar de `"python"`.

**3.** Salve o arquivo e **reinicie o Claude Desktop completamente** (feche pelo ícone na bandeja do sistema, não só a janela).

**4.** Abra uma nova conversa e pergunte algo como:

> "Qual o IDEB de Campinas em 2023?"

---

## Outros clientes compatíveis

O protocolo MCP é suportado por outros clientes além do Claude Desktop. A configuração varia — consulte a documentação de cada um:

- **[Cursor](https://cursor.com)** — editor de código com IA
- **[Zed](https://zed.dev)** — editor de código com IA
- **[Continue](https://continue.dev)** — extensão para VS Code e JetBrains

> **ChatGPT e Gemini** não suportam o protocolo MCP nativamente.

---

## Exemplos de perguntas

**Consulta por município:**
- "Qual o IDEB de Ariquemes (RO) nos anos iniciais?"
- "Como foi a evolução do IDEB de Campinas de 2005 a 2023?"
- "Qual a nota de Matemática de São Paulo nos anos finais em 2023?"

**Rankings:**
- "Quais os 10 municípios com melhor IDEB no Ensino Médio em MG?"
- "Qual município de SC teve o pior IDEB nos anos iniciais em 2023?"

**Comparações:**
- "Compare o IDEB de Curitiba e Londrina nos anos finais"
- "Qual cresceu mais entre 2005 e 2023: Recife ou Fortaleza?"

**Visão geral:**
- "Qual a média do IDEB nos anos iniciais no Brasil em 2023?"
- "Qual estado tem a maior média de IDEB no Ensino Médio?"

---

## Procedência dos dados

Extraídos das planilhas públicas de divulgação de resultados do IDEB por município, disponibilizadas pelo INEP/MEC em https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/ideb/resultados.

---

## Licença

Código sob licença MIT. Dados do IDEB são públicos (INEP/MEC).
