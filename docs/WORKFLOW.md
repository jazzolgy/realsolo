# Parallel Chat / Branch Workflow

## Branch ownership

- `main`: integrated stable baseline
- `research/legend-intelligence`: Music Intelligence Core + legend research
- `player/piano`: AI pianist
- `realtime/ensemble-app`: live ensemble application

## Rule

A workstream should not silently rewrite shared core assumptions.

If a branch needs a shared-core change, create or update `CORE_CHANGE_REQUEST.md` in that branch and describe:
- requested core change
- musical reason
- affected modules
- regression risk
- tests required

Shared-core changes are reviewed before integration.

## Merge discipline

1. branch work
2. tests
3. PR to main
4. inspect conflicts / cross-stream effects
5. merge only stable changes

The user should not have to manually shuttle code between chats.
