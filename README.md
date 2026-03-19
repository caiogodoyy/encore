# Encore!

> **⚠️ EM DESENVOLVIMENTO** — Este projeto está em fase ativa de desenvolvimento. Funcionalidades podem mudar ou apresentar instabilidades.

Transforme suas playlists do Spotify em playlists no YouTube automaticamente.

## Arquitetura

```
frontend/   → Next.js 15 + React 19 + Tailwind CSS 4
backend/    → FastAPI + httpx (OAuth 2.0 + sync engine)
Redis       → Sessões e tokens (via Docker)
```

### Fluxo

1. Usuário conecta **Spotify** e **YouTube** via OAuth 2.0
2. Backend armazena os tokens na sessão Redis
3. Usuário escolhe uma playlist do Spotify
4. Backend lê as faixas (via embed page scraping — contorna a limitação do Spotify Basic Quota Mode), busca equivalentes no YouTube (via innertube API — sem consumir quota) e cria a playlist
5. Frontend exibe progresso em tempo real via polling

### Decisões técnicas

| Desafio | Solução |
|---------|---------|
| Spotify Basic Quota Mode bloqueia endpoints de tracks | Scraping da página embed (`open.spotify.com/embed/playlist/{id}`) que retorna tracks no `__NEXT_DATA__` JSON |
| YouTube Data API Search cobra 100 unidades/chamada (quota de 10k/dia) | Busca via YouTube innertube API (0 quota), API oficial usada apenas para criar playlists e inserir vídeos |
| Tokens OAuth expiram durante sync longo | Auto-refresh de tokens mid-sync com retry automático |

## Pré-requisitos

- Python 3.12+
- Node.js 22+
- Docker (para Redis)
- Credenciais OAuth:
  - [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) → criar app com **Web API**, redirect URI: `http://127.0.0.1:3000/api/auth/spotify/callback`
  - [Google Cloud Console](https://console.cloud.google.com/apis/credentials) → OAuth Client ID, redirect URI: `http://127.0.0.1:3000/api/auth/youtube/callback`, habilitar **YouTube Data API v3**

> **Nota:** O Spotify aceita `http://127.0.0.1` para desenvolvimento local. Não use `localhost` nem `https`.

## Setup

### 1. Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
SPOTIFY_CLIENT_ID=seu_client_id
SPOTIFY_CLIENT_SECRET=seu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:3000/api/auth/spotify/callback

GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:3000/api/auth/youtube/callback

REDIS_URL=redis://127.0.0.1:6379/0
FRONTEND_URL=http://127.0.0.1:3000
SESSION_TTL_SECONDS=3600
```

### 2. Com Docker Compose (tudo de uma vez)

```bash
docker compose up --build
```

### 3. Desenvolvimento local

**Redis:**

```bash
docker run -d --name encore-redis -p 6379:6379 redis:7-alpine
```

**Backend:**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Acesse `http://127.0.0.1:3000`.

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/auth/spotify/login` | Inicia OAuth Spotify |
| GET | `/auth/spotify/callback` | Callback OAuth Spotify |
| GET | `/auth/youtube/login` | Inicia OAuth YouTube |
| GET | `/auth/youtube/callback` | Callback OAuth YouTube |
| GET | `/auth/status` | Status de conexão |
| GET | `/sync/playlists` | Playlists do usuário |
| POST | `/sync/start?playlist_id=X` | Inicia sincronização |
| GET | `/sync/status` | Progresso da sincronização |
| GET | `/health` | Health check |

## Limitações conhecidas

- A página embed do Spotify retorna no máximo **100 tracks** por playlist
- A YouTube Data API tem quota de **10.000 unidades/dia** (criar playlist + inserir vídeos ≈ 5.050 unidades para 100 tracks)
- O app Spotify precisa estar em **Basic Quota Mode** ou superior (acesso automático ao criar o app)

## Estrutura do projeto

```
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + CORS
│   │   ├── config.py        # Pydantic Settings (.env)
│   │   ├── routers/
│   │   │   ├── auth.py      # OAuth login/callback
│   │   │   └── sync.py      # Playlist listing + sync trigger
│   │   └── services/
│   │       ├── session.py    # Redis session CRUD
│   │       ├── spotify.py    # Spotify OAuth + embed scraping
│   │       ├── youtube.py    # YouTube OAuth + innertube search
│   │       └── sync.py       # Background sync orchestrator
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx      # Página principal (3 steps)
│   │   │   ├── layout.tsx    # Root layout
│   │   │   └── globals.css   # Tailwind + tema escuro
│   │   ├── components/
│   │   │   ├── ConnectButton.tsx
│   │   │   ├── PlaylistCard.tsx
│   │   │   └── SyncProgress.tsx
│   │   └── lib/
│   │       └── api.ts        # Fetch helpers
│   ├── next.config.mjs       # Proxy /api → backend
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env
└── .gitignore
```
| GET | `/health` | Health check |

## Licença

Apache 2.0
