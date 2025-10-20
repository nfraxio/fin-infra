# Planning Methodology (PLANS_METHOD) — fin-infra

This methodology mirrors svc-infra’s disciplined workflow. Use it to (re)generate `PLANS.md` for new fin-infra milestones.

- Follow stage gates strictly: Research → Design → Implement → Tests → Verify → Docs → Acceptance.
- Prefer reuse over rebuild; mark skips `[~]` with file paths.
- Record evidence (PRs, commits, test names) under each item.

See svc-infra’s PLANS_METHOD.md for rationale; apply the same structure to fin-infra domains (providers, cashflows, API surface, SDKs).
