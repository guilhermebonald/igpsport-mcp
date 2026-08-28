<!-- mcp-name: io.github.dengxuhui/igpsport-mcp -->
# igpsport-mcp

[English](https://github.com/guilhermebonald/igpsport-mcp/blob/main/README.en.md) | **Português** | [简体中文](https://github.com/guilhermebonald/igpsport-mcp/blob/main/README.zh-CN.md)

Servidor local [MCP](https://modelcontextprotocol.io) que conecta seus **dados de ciclismo da iGPSport** a clientes LLM como Claude. Analise seus treinos em linguagem natural: *"Como está minha carga de treino esta semana?"* *"Compare meus dois pedais longos da semana passada e desta semana."* *"Quantos quilômetros pedalei este ano e quais são meus recordes pessoais?"* — e até mesmo **peça para o Claude prescrever treinos**: *"Crie uma sessão 2×20 SST com base no meu FTP e envie para o meu ciclocomputador."*

**Diferencial**: As métricas de treino derivadas — NP / IF / TSS / CTL / ATL / TSB — são **calculadas localmente na camada MCP** antes do envio. O LLM recebe valores prontos para interpretação, não streams de dados brutos.

```
Você:   Qual é a tendência da minha carga de treino nos últimos 90 dias? Devo descansar?
Claude (via analyze_training_load):
       CTL atual (Condicionamento) 72, ATL (Fadiga) 91, TSB (Forma) -19 — você está com acúmulo significativo de fadiga.
       O TSS esteve acima do CTL nas últimas duas semanas. Considere um bloco de recuperação de 3 a 5 dias para trazer o TSB de volta acima de -5…
```

## Demonstração

![igpsport-mcp demo](assets/demo.gif)

> ⚠️ **Projeto não oficial**. Esta ferramenta funciona **simulando requisições do cliente web da iGPSport**. A iGPSport pode alterar a API a qualquer momento. Use por sua conta e risco. Executa 100% local via stdio — **seus dados nunca passam por servidores de terceiros**.

## Início Rápido (Recomendado)

Esta ferramenta é um servidor MCP e requer um **cliente compatível com MCP** (ex: [Claude Desktop](https://claude.ai/download), Claude Code, Cursor).

**1. Instale o uv** (gerenciador de runtime autônomo — **não precisa de Python pré-instalado**):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**2. Instale e execute o assistente de configuração**:

```bash
uv tool install igpsport-mcp
igpsport-mcp --setup --lang pt
```

O assistente salva as credenciais no arquivo de configuração local e exibe o bloco pronto para copiar e colar:

- **macOS / Linux**: `~/.igpsport-mcp/config.json`
- **Windows**: `C:\Users\SeuNome\.igpsport-mcp\config.json`

**3. Cole a configuração gerada no seu cliente MCP e reinicie-o.**

> Para testar o login antes: `igpsport-mcp --check --lang pt`
> Para exibir o JSON de configuração novamente: `igpsport-mcp --mcp-config --lang pt`

## Uso via Linha de Comando (CLI)

| Comando | Descrição |
|---|---|
| `igpsport-mcp --setup` | Assistente interativo para login e configuração |
| `igpsport-mcp --mcp-config` | Exibe o bloco de configuração JSON para clientes MCP |
| `igpsport-mcp --check` | Valida credenciais com teste real de login |
| `igpsport-mcp --lang pt\|en\|zh` | Define idioma de saída (ou via env `IGPSPORT_LANG`, padrão `pt`) |
| `igpsport-mcp --version` | Exibe a versão instalada |
| `igpsport-mcp --help` | Mostra ajuda e opções |

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `IGPSPORT_USERNAME` | ✅ | Usuário (telefone no servidor CN / e-mail no servidor Internacional) |
| `IGPSPORT_PASSWORD` | ✅ | Senha da conta |
| `IGPSPORT_REGION` | Opcional | Região: `intl` (padrão / global em `app.igpsport.com`) ou `cn` (China em `app.igpsport.cn`) |
| `IGPSPORT_FTP` | Opcional | FTP em watts (se não informado, obtém automaticamente do perfil iGPSport) |
| `IGPSPORT_LTHR` | Opcional | Frequência cardíaca no limiar (bpm) para cálculo de hrTSS e zonas de FC |
| `IGPSPORT_LANG` | Opcional | Idioma das mensagens (`pt`, `en`, `zh`) |
| `IGPSPORT_CACHE_DIR` | Opcional | Diretório de cache local dos arquivos FIT e SQLite |
| `IGPSPORT_LOG_LEVEL` | Opcional | Nível de log (padrão: `INFO`) |

## Ferramentas MCP Disponíveis (17 tools)

- **Atividades & Resumos**: `list_activities`, `get_activity_summary`, `get_activity_laps`, `get_activity_streams`, `compare_activities`, `get_yearly_stats`, `get_personal_records`.
- **Análise Avançada**: `analyze_training_load` (CTL/ATL/TSB), `estimate_thresholds` (MMP, FTP, LTHR).
- **Segmentos**: `list_starred_segments`, `get_segment_leaderboard`, `get_segment_efforts`.
- **Perfil**: `get_athlete_profile`.
- **Treinos Estruturados**: `list_workouts`, `get_workout_detail`, `create_workout` (compilação IR para ciclocomputador), `delete_workout`.
