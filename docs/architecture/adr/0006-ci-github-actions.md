# ADR-0006: CI — GitHub Actions

- Status: accepted (2026-10-07)

## Context
Спека требует quality gates (§34), но CI-систему не называет (gap). Репозиторий
публикуется на GitHub; для open-source это бесплатный раннер «из коробки».

## Decision
`.github/workflows/ci.yml`: два job — backend (setup-python 3.12, ruff, mypy,
pytest против service-postgres:16) и frontend (node 20, eslint, tsc, vitest,
build). Запуск на push в `rc-*`/`main` и на PR.

## Consequences
- (+) гейт приёмки RC (§54.2) автоматизирован;
- (–) привязка к GitHub-раннерам; при смене платформы миграция workflow'ов —
  линейная (пересборка синтаксиса).
