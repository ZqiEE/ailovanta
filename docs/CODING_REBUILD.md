# Ailovanta Coding Rebuild

Ailovanta is being repurposed from a generic distributed-AI network into an autonomous coding model factory.

## Core product thesis

The product exists to close the gaps between the strongest coding assistants by combining three complementary capability peaks into one owned coding model:

- Frontend teacher stream: visual UI, browser rendering, interaction, responsive quality and product taste.
- Backend teacher stream: repository-level implementation, APIs, databases, services, architecture and long-horizon engineering.
- Repair teacher stream: bug reproduction, root-cause localization, patching, tests and regression control.

The three streams are training-time specialists. The deployment target is one unified Ailovanta-owned checkpoint.

## Financing MVP requirement

The financing MVP MUST contain a real trained student checkpoint. A dashboard-only training simulator, router-only product, or generic open model wrapper is not sufficient.

The first student may be small (for example a 7B/14B open-weight coding base), but it must demonstrate real weight adaptation from all three teacher streams and measurable improvement over the untouched base model.

Minimum proof:

1. Collect a small, high-density frontend teacher trajectory set.
2. Collect a small, high-density backend engineering trajectory set.
3. Collect a small, high-density repair/debug trajectory set.
4. Train three specialist adapters/checkpoints from the same base.
5. Unify the three specialists into one student checkpoint.
6. Evaluate base vs specialists vs unified student on held-out frontend, backend and repair tasks.
7. Reject the unified model if any domain falls below its minimum floor.
8. Serve the unified student in the public coding product.

The investor demo must therefore show both a working product and evidence that Ailovanta owns a model artifact whose weights changed through the three-stream training process.

## Reused infrastructure

Keep the existing scheduler, node registry, result verification, reputation, artifact handling, checkpoint promotion, runtime routing, autonomous-loop scaffolding and H-SwarmTrain distributed-compute direction.

## New training loop

1. Benchmark all three domains.
2. Select the weakest domain.
3. Generate or select tasks for that domain.
4. Dispatch rollout and sandbox work to distributed nodes.
5. Verify results with browser/build/test/runtime signals.
6. Train a specialist candidate.
7. Keep the candidate only if it wins.
8. Periodically unify all three specialists.
9. Promote a unified checkpoint only when every domain clears its score floor.

## Distributed roles

CPU nodes run repositories, builds and tests. Consumer GPU nodes produce rollouts and visual evaluations. GPU islands perform larger specialist jobs. A smaller authoritative cluster handles major weight updates, unification and final promotion.

## Product direction

The public product becomes a free-first coding assistant powered by the unified Ailovanta student model. Optional compute contributors can exchange useful idle compute for product credits or higher service levels. More users should create more verified feedback and potentially more compute supply, strengthening the owned model over time.
