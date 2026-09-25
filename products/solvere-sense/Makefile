.PHONY: verify doctor test lint evidence

FORGE := /home/user/solvere-web/plugins/forge/bin/forge

# Run every automatable verification rung (CONTRACTS.md §9) and record evidence.
verify:
	$(FORGE) verify --all

# Toolchain, MCP-lock and file-integrity health checks (fail closed).
doctor:
	$(FORGE) doctor

# Pytest for every script with logic (plugins/forge/tests/, and this project's own tests/).
test:
	uv run --with pytest pytest tests -q

# Agent frontmatter, skill hygiene, CLAUDE.md length, evidence wording.
lint:
	$(FORGE) lint agents
	$(FORGE) lint skills
	$(FORGE) lint claudemd
	$(FORGE) lint wording
	$(FORGE) lint manifest

# Print the current evidence/manifest.json summary.
evidence:
	$(FORGE) evidence summary
