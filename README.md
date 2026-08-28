<!-- mcp-name: io.github.guilhermebonald/igpsport-mcp -->
# igpsport-mcp

**Português** | [English](README.en.md) | [简体中文](README.zh-CN.md)

Servidor local [MCP](https://modelcontextprotocol.io) que conecta seus **dados de ciclismo da iGPSport e Strava** a clientes LLM como Claude Desktop, Claude Code e Cursor. Analise seus treinos em linguagem natural, compare segmentos do Strava de forma 100% offline via telemetria GPS e prescreva treinos estruturados diretamente para o seu ciclocomputador.

---

## Destaques & Diferenciais

- ⚡ **Métricas Derivadas no Servidor**: NP, IF, TSS, hrTSS, CTL (Condicionamento), ATL (Fadiga) e TSB (Forma) calculados localmente com exatidão matemática (< 2% de erro vs. Strava/TrainingPeaks).
- 🗺️ **Integração Strava Segments Offline**: Algoritmo de *map-matching* espacial (Haversine vetorial) sobre o arquivo `.fit` da iGPSport. Calcula tempos, velocidade, potência, FC e VAM em segmentos do Strava com comparação a PRs e KOMs **sem precisar subir o pedal no Strava**.
- 📋 **Prescrição de Treinos (Workout IR)**: Crie treinos intervalados em linguagem natural (ex: *2x20min SST*) e envie diretamente para o iGPSport App / ciclocomputador com opção de calendário iCal.
- 🔒 **100% Local & Seguro**: Opera via stdio com cache SQLite local (`activities.db`) e arquivos `.fit`. Zero envio de telemetria a servidores de terceiros.
- 🌐 **Suporte Multi-Idioma & Multi-Região**: Português (`pt`), Inglês (`en`) e Chinês (`zh`). Compatível com servidor Internacional (`app.igpsport.com`) e China (`app.igpsport.cn` com WASM).

---

## Demonstração

```
Você:   Analise a carga de treino dos últimos 90 dias e veja se bati algum PR nos segmentos do pedal de hoje.
Claude: 
  📊 Carga de Treino:
  - CTL (Condicionamento): 72 | ATL (Fadiga): 91 | TSB (Forma): -19 (Fadiga alta, recomendo 3 dias leves).
  
  🏆 Segmentos Identificados no Pedal 90672495 (49.46 km):
  1. Ponte Iúna até ICC (2.41 km): 7m02s (20.6 km/h, VAM 165 m/h) | Seu PR: 4m27s | KOM: 3m36s
  2. SUBIDINHA (713 m, 11.9%): 4m59s (8.6 km/h, VAM 1.004 m/h) | Seu PR/KOM: 3m23s
  3. Subida do Dante (538 m, 6.0%): 3m32s (9.1 km/h, VAM 571 m/h) | Seu PR: 1m29s | KOM: 1m25s
```

---

## Instalação Rápida

### 1. Instale o `uv` (gerenciador rápido de pacotes Python)

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Instale e execute o Assistente Interativo

```bash
uv tool install igpsport-mcp
igpsport-mcp --setup --lang pt
```

O assistente solicitará suas credenciais iGPSport (e opcionalmente Strava API) e salvará em:
- **macOS / Linux**: `~/.igpsport-mcp/config.json`
- **Windows**: `C:\Users\SeuUsuario\.igpsport-mcp\config.json`

### 3. Configure no seu Cliente LLM (Claude Desktop / Cursor)

Adicione ao seu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "igpsport": {
      "command": "uvx",
      "args": ["igpsport-mcp"],
      "env": {
        "IGPSPORT_USERNAME": "seu_email@exemplo.com",
        "IGPSPORT_PASSWORD": "sua_senha",
        "IGPSPORT_REGION": "intl",
        "STRAVA_CLIENT_ID": "177152",
        "STRAVA_CLIENT_SECRET": "seu_strava_secret",
        "STRAVA_REFRESH_TOKEN": "seu_strava_refresh_token"
      }
    }
  }
}
```

---

## CLI & Comandos

| Comando | Descrição |
|---|---|
| `igpsport-mcp --setup` | Assistente interativo completo de configuração |
| `igpsport-mcp --check` | Testa conexão e autenticação com iGPSport e Strava |
| `igpsport-mcp --mcp-config` | Gera e exibe o bloco JSON pronto para o Claude Desktop |
| `igpsport-mcp --lang pt\|en\|zh` | Define idioma da interface CLI (padrão: `pt`) |
| `igpsport-mcp --version` | Exibe a versão instalada |

---

## Ferramentas MCP Disponíveis (21 Tools)

### 🚴 Atividades & Desempenho (9 tools)
- `list_activities`: Lista atividades com paginação, datas, distâncias e status de sincronização.
- `get_activity_summary`: Resumo consolidado de métricas (distância, ganho altimétrico, NP, IF, TSS, hrTSS, zonas de potência e FC).
- `get_activity_streams`: Séries temporais em 1Hz (potência, FC, cadência, altitude, velocidade) com subamostragem sob demanda.
- `get_activity_laps`: Detalhamento de voltas/parciais com médias isoladas por volta.
- `get_athlete_profile`: Perfil do ciclista (peso, FC máx, FTP, LTHR e zonas calculadas).
- `get_athlete_stats`: Estatísticas agregadas de quilometragem, tempo e ganho altimétrico.
- `get_member_statistics`: Totais anuais e recordes pessoais (maior distância, maior subida, maior potência).
- `compare_activities`: Comparativo lado a lado de 2 a 5 atividades com diferenças percentuais.
- `estimate_thresholds`: Estimação de FTP e LTHR com base na curva MMP histórica (Mean-Max Power).

### 📈 Carga de Treino & Periodização (1 tool)
- `analyze_training_load`: Análise de longo prazo de Fitness (CTL, 42d), Fadiga (ATL, 7d) e Prontidão (TSB) para prevenção de overtraining e timing de pico de performance.

### 🗺️ Segmentos Strava & Map-Matching (4 tools)
- `sync_strava_segments`: Sincroniza segmentos favoritos (*starred*) do Strava com coordenadas geográficas e polylines para cache local.
- `match_activity_segments`: Executa map-matching GPS no FIT da iGPSport, detectando passagens por segmentos do Strava e calculando tempos, velocidade média, VAM e métricas fisiológicas.
- `get_strava_segment_leaderboard`: Consulta recordes, KOM/QOM e top 10 do ranking Strava.
- `compare_segment_efforts`: Compara histórico de passagens no mesmo segmento entre diferentes pedais.

### 🏔️ Segmentos Nativos iGPSport (3 tools - apenas servidor CN)
- `list_segments_collected`: Segmentos salvos no perfil iGPSport.
- `get_segment_detail`: Detalhes de elevação, gradiente e PR.
- `get_segment_rank`: Classificação oficial no ranking iGPSport.

### 📝 Treinos Estruturados / Workouts (4 tools - Leitura & Criação)
- `list_workouts`: Lista treinos estruturados salvos na nuvem iGPSport.
- `get_workout_detail`: Detalhes de blocos, zonas-alvo e intervalos.
- `create_workout`: Compila treino em linguagem natural/IR para formato nativo do ciclocomputador (com suporte a `dry_run` e exportação iCal).
- `delete_workout`: Exclui treino estruturado (requer confirmação explícita `confirm=True`).

---

## Configurações & Variáveis de Ambiente

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `IGPSPORT_USERNAME` | ✅ | - | E-mail da conta (servidor Internacional) ou telefone (servidor CN) |
| `IGPSPORT_PASSWORD` | ✅ | - | Senha da conta iGPSport |
| `IGPSPORT_REGION` | Opcional | `intl` | Região da conta: `intl` (`app.igpsport.com`) ou `cn` (`app.igpsport.cn`) |
| `STRAVA_CLIENT_ID` | Opcional | - | Client ID da API do Strava |
| `STRAVA_CLIENT_SECRET` | Opcional | - | Client Secret da API do Strava |
| `STRAVA_REFRESH_TOKEN` | Opcional | - | Refresh Token OAuth2 com escopo `activity:read_all` |
| `IGPSPORT_FTP` | Opcional | Auto | FTP em Watts (sobrescreve perfil da nuvem se fornecido) |
| `IGPSPORT_LTHR` | Opcional | Auto | Frequência Cardíaca no Limiar em bpm |
| `IGPSPORT_LANG` | Opcional | `pt` | Idioma padrão da CLI (`pt`, `en`, `zh`) |
| `IGPSPORT_CACHE_DIR` | Opcional | `~/.cache/igpsport-mcp` | Diretório para cache de `.fit` e banco SQLite |
| `IGPSPORT_LOG_LEVEL` | Opcional | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

---

## Créditos & Autoria

- **Manutenção & Recursos Avançados (Strava Segments, i18n PT, Map-Matching)**: [Guilherme Bonald](https://github.com/guilhermebonald)
- **Autor Original & Engenharia Reversa Inicial**: [dengxuhui](https://github.com/dengxuhui/igpsport-mcp)

Distribuído sob a licença MIT. Sinta-se livre para contribuir, reportar issues ou enviar Pull Requests!
