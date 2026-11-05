# Projeto-vinicula — AgroClima Cloud

Plataforma de monitoramento climático e gestão de plantações para o Vale do São Francisco.

## Estrutura

| Módulo | Stack | Porta padrão |
| --- | --- | --- |
| `frontend/` | SPA em JavaScript puro + Vite | 5173 (dev) / 8081 (Docker) |
| `backend-java/` | Spring Boot 3.4 · JWT · RBAC · JPA/Hibernate · Flyway · MySQL | 8080 |
| `backend-python/` | FastAPI · Pandas (análises e dashboards) | 8000 |

Os ZIPs `AgroClima_*` e as pastas `frontend/`, `backend-java/`, `backend-python/` contêm **o mesmo código-fonte atualizado** (com RBAC, Design System e Modelos Preditivos). Pode rodar qualquer um dos dois — o código original foi substituído. Se extrair os ZIPs, rode de dentro da pasta `AgroClima_*-main/` gerada; se usar as pastas do repositório, rode `frontend/`, `backend-java/`, `backend-python/` diretamente.

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

## Modelos preditivos (novidades)

A página **Modelos Preditivos** (permissão `analytics.view`) reúne três camadas, todas calculadas a
partir do histórico real da estação (ThingSpeak via API Java). Nenhuma delas é previsão meteorológica:
são **projeções estatísticas do histórico da estação**, sem chuva, solo ou radiação medida.

- **Estatística**: Holt-Winters (tendência + sazonalidade semanal, amortecida) com intervalo de
  confiança de 95% e *backtesting* (MAE, RMSE, R²) por origem móvel. Substitui a regressão linear
  simples quando há histórico suficiente; cai para a tendência linear com poucos dias.
- **Machine learning**: `scikit-learn` (Random Forest / Gradient Boosting) com 20 features de lag e
  calendário, treinado no histórico diário via API Java. O modelo ativo é persistido
  (`joblib` + metadados JSON) e usado nas projeções. Treino real protegido por `models.manage`
  (ADMIN/ANALYST), com mínimo de dias completos configurável (`MODEL_MIN_TRAIN_DAYS`, padrão 60).
  A página mostra as métricas de validação e a comparação entre algoritmos candidatos.
- **Agronômica**: por plantação real, acumulado de graus-dia (GDD) desde o plantio, janela de colheita
  projetada, risco de míldio/oídio e necessidade de irrigação (ET0 de Hargreaves, ETc = ET0·Kc, DPV).
  Exige `plantations.manage` ou `plantations.read.all`.

O treino e a remoção do modelo geram **trilha de auditoria** (`POST /api/audit-events` no Java).
A permissão `models.manage` é criada pela migração Flyway `V2__add_models_manage_permission.sql`.

## Testes

```bash
cd frontend && npm test          # node --test (RBAC, design, telefone, login, integração)
cd backend-python && python -m pytest -q   # inclui testes de permissão das rotas
cd backend-java && mvn test      # requer JDK 21 + Maven (Docker para MySqlPersistenceTest)
```
