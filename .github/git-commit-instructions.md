# Commit Guidelines (fin-infra)

Keep messages concise and traceable. Use conventional prefix tags when helpful.

Format:
- type(scope): summary
- Body: what/why, links to PRs/issues/ADRs if relevant.

Examples:
- feat(providers): add AlphaVantage + CoinGecko adapters
- fix(settings): load ALPHAVANTAGE_API_KEY from settings
- ci: add acceptance + PyPI publish workflows
- docs: quickstart for equities/crypto

Notes:
- Reference tests you added/updated.
- If skipping work (existing functionality), note path in body.