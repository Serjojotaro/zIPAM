# ADR-0005: Celery и Redis не входят в RC-01

- Status: accepted (2026-10-07)

## Context
Спека допускает Redis/Celery «где нужны» (§3, §27) и запрещает брать их
без причины (§76). В RC-01 нет long-running операций: import/экспорт,
синхронизации и discovery отложены (roadmap rc-02+).

## Decision
RC-01 — только PostgreSQL. Никаких Celery/Redis/фоновых очередей.

## Consequences
- (+) меньше движущихся частей в deploy (`docker compose up` из 3 сервисов);
- критерий включения Celery фиксируем заранее: появление операции,
  превышающей HTTP-таймаут (bulk import >10k строк, sync с внешней системой).
