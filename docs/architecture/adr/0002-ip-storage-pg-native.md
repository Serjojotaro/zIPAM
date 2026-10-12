# ADR-0002: Хранение IP-иерархии — PostgreSQL-native (inet/cidr + GiST)

- Status: accepted (2026-10-07); реализация — M2 RC-01
- Решает: CLAUDE.md §12 (иерархия/overlap), §13 (конкурентная аллокация)

## Context
Спека требует parents/children/available/overlap (§12) и гарантию от двойной
аллокации (§13). Переносимая схема (ltree/materialized path) слабее гарантирует
обе вещи. PostgreSQL уже зафиксирован как единственная БД (§3), поэтому
переносимость ценности не имеет.

## Decision
Поле prefix типа `cidr`, адреса — `inet`. Иерархия и containment — операторами
PostgreSQL (`>>`, `<<`, `<<=`) с GiST-индексами (расширение `btree_gist`).
Overlap — exclusion constraint на уровне БД внутри VRF. Уникальность адреса —
UNIQUE (VRF, address). Аллокация — SELECT ... FOR UPDATE внутри транзакции;
concurrency-тесты обязательны (§13).

## Consequences
- (+) корректность обеспечивается БД, а не прикладным кодом;
- (+) быстрее реализация available/free-вычислений;
- (–) жёсткая привязка к PostgreSQL (принята осознанно);
- парсинг/валидация форм — стандартный `ipaddress` (§11), хранение — типами БД.
