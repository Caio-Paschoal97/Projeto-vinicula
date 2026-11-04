# Projeto-vinicula — AgroClima Cloud

Plataforma de monitoramento climático e gestão de plantações para o Vale do São Francisco.

## Estrutura

| Módulo | Stack | Porta padrão |
| --- | --- | --- |
| `frontend/` | SPA em JavaScript puro + Vite | 5173 (dev) / 8081 (Docker) |
| `backend-java/` | Spring Boot 3.4 · JWT · RBAC · JPA/Hibernate · Flyway · MySQL | 8080 |
| `backend-python/` | FastAPI · Pandas (análises e dashboards) | 8000 |

Os ZIPs originais foram mantidos como referência; o código-fonte extraído é a versão ativa.

## Execução local

1. **MySQL**: crie o banco `agroclima` e configure `backend-java/.env` (veja `.env.example`).
   Defina `INITIAL_ADMIN_PASSWORD` para criar a conta administrativa inicial no primeiro boot.
2. **API Java**: `cd backend-java && ./run-local.sh` (Flyway aplica o schema e o catálogo RBAC).
3. **API Python**: `cd backend-python && pip install -r requirements.txt && uvicorn app.main:app --port 8000`.
4. **Frontend**: `cd frontend && npm install && npm run dev` — o Vite proxya `/api/java` e `/api/python`.

## Segurança e personalização (novidades)

- **RBAC de ponta a ponta**: a API Java é a autoridade (JWT + permissões por rota, `403` para acessos
  não autorizados). O login/perfil devolve `permissionKeys`; a sidebar, as ações e as URLs (`#/pagina`)
  só exibem o que o perfil pode acessar. A API Python consome as mesmas permissões.
- **Sem cadastro público**: contas são criadas exclusivamente pelo administrador em
  *Permissões e RBAC* (`POST /api/users`, permissão `users.manage`). O endpoint `/api/auth/register`
  e o botão "Criar conta" foram removidos.
- **Design System funcional**: cores (por tema), fontes, escala tipográfica, bordas, cantos e sombras
  são tokens persistidos em `/api/settings` (seção `design`) e aplicados em tempo real em todas as
  páginas, para todos os usuários, em temas claro e escuro. Salvar, descartar e restaurar padrão.
- **Telefone brasileiro validado** nas duas camadas: máscara `(81) 99999-9999` / `(81) 3333-4444`,
  DDD real, celular/fixo, sem sequências repetidas; armazenamento somente dígitos com DDI `55`.

## Testes

```bash
cd frontend && npm test          # node --test (RBAC, design, telefone, login, integração)
cd backend-python && python -m pytest -q   # inclui testes de permissão das rotas
cd backend-java && mvn test      # requer JDK 21 + Maven (Docker para MySqlPersistenceTest)
```
