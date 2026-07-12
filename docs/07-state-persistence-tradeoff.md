# ADR 07: Sessions are in-memory (and the upgrade path if that stops being enough)

**Status:** Accepted, with a documented upgrade path
**Date:** Step 7 of the v2.0 rebuild

## Context
`backend/state.py:SessionStore` keeps every `ProjectState` in a plain
Python dict in the backend process's memory, evicting entries after a
TTL (`SESSION_TTL_SECONDS`, default 6 hours of inactivity). This is the
simplest possible thing that works for a single-user or small-team
deployment running one backend process.

It has two real limitations:
1. **Restart-fragile** — redeploying or crashing the backend loses every
   in-progress session (uploaded data, generated reports, everything).
2. **Single-process only** — it cannot be horizontally scaled behind a
   load balancer with multiple `uvicorn` workers, because each worker
   would have its own independent dict and a session created on worker A
   would 404 on worker B.

## Decision
Accept these limitations for v1. The dataset a person uploads is
typically re-uploadable in seconds, sessions are short-lived (a single
analysis sitting), and the deployment target is a single backend
instance. Building a persistence layer before there's a real multi-user,
multi-process requirement would be premature complexity.

## Upgrade path (when this needs to change)
If the deployment grows to need multiple backend workers or
restart-durability:
- Replace `SessionStore`'s internal dict with Redis (`session_id` →
  serialized `ProjectState`). The `dataclass` shape of `ProjectState`
  maps cleanly to a Redis hash or a single JSON blob; the large object
  (`df`, `cleaned_df`, `X`) would need to be pickled or moved to a
  short-lived object store (e.g. S3/local disk) with only a pointer kept
  in Redis.
- Alternatively, back it with a real database (Postgres) if
  session history needs to be queryable/auditable later, not just
  ephemeral.
- The public interface (`store.create()`, `store.get(session_id)`) is
  already the seam to swap the implementation behind — no route or agent
  code would need to change.

## Consequences
- Zero infrastructure to run for v1 beyond the two application
  containers.
- A backend restart during a live analysis session loses that session's
  progress — communicated to users as "sessions last a few hours; if you
  hit an error, re-upload."
