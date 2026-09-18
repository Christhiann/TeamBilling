# TeamBilling

TeamBilling é uma aplicação SaaS de cobrança para equipes e múltiplas organizações. O projeto demonstra um fluxo completo de autenticação, criação de workspace, permissões, planos, assinaturas e checkout.

## O que foi construído

- Cadastro e login com JWT.
- Workspaces multi-organização com associação de usuários.
- Permissões separadas entre proprietários e membros.
- Dashboard web para visão geral, equipe e faturamento.
- Planos ativos e checkout integrado ao serviço Stripe.
- Webhook idempotente para atualizar assinaturas.
- API documentada com Swagger/OpenAPI.
- Ambiente local reproduzível com Docker Compose.

## Arquitetura

O frontend foi desenvolvido com Next.js 14, React e TypeScript. Ele consome a API REST usando tokens JWT e mantém o estado do workspace no navegador.

O backend usa Django 5.1 e Django REST Framework. Os domínios estão separados em aplicações de contas, organizações, billing e segurança. O PostgreSQL é executado em um container próprio, e as migrations são aplicadas automaticamente ao iniciar o backend.

Em desenvolvimento, o Stripe funciona em modo mock usando `sk_test_placeholder`, permitindo testar o fluxo de checkout sem credenciais externas. Para integração real, substitua as variáveis Stripe no `docker-compose.yml` por chaves de teste válidas.

## Requisitos

- Docker Desktop com o engine Linux ativo.
- Git.

Node.js e Python não são necessários para a execução via Docker.

## Executar com Docker

Na raiz do projeto:

```powershell
docker compose up --build
```

Depois, acesse:

| Serviço | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/api/docs/ |
| Schema OpenAPI | http://localhost:8000/api/schema/ |

Para executar em segundo plano:

```powershell
docker compose up --build -d
```

Para acompanhar os logs ou parar os serviços:

```powershell
docker compose logs -f
docker compose down
```

## Dados iniciais

Com os containers ativos, carregue os planos padrão:

```powershell
docker compose exec backend python manage.py seed_plans
```

Para criar um usuário administrador:

```powershell
docker compose exec backend python manage.py createsuperuser
```

## Desenvolvimento sem Docker

### Backend

É necessário ter PostgreSQL rodando e as variáveis de conexão configuradas. No PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:POSTGRES_DB = "teambilling"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "postgres"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
python manage.py migrate
python manage.py runserver
```

### Frontend

Em outro terminal:

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

## Testes e validações

```powershell
docker compose exec backend python manage.py test
cd frontend
npm run build
```

## Estrutura principal

```text
backend/    API Django, regras de negócio, modelos e migrations
frontend/   Dashboard Next.js, autenticação e telas do produto
docker-compose.yml  PostgreSQL, backend e frontend locais
```
