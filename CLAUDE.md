# Tracefinity

Before changing code or documentation, read [CONTRIBUTING.md](CONTRIBUTING.md).
For feature requests, substantial product changes, or issue/PR scope decisions,
also read [CONSTITUTION.md](CONSTITUTION.md) and use the `scope-triage` skill.
Read [DESIGN.md](DESIGN.md) before making architectural changes.

Before writing public issues, PRs, comments, commit messages or release notes,
follow [the public writing rules](CONTRIBUTING.md#public-writing).

Tracefinity turns photos or scans of physical objects into fitted,
Gridfinity-compatible storage. The backend is Python/FastAPI with OpenCV and
manifold3d; the frontend is Next.js/React/TypeScript with react-three-fiber.

Project setup and commands live in [README.md](README.md). Consult the relevant
document under [docs/](docs/) before changing a subsystem. In particular,
[docs/gotchas.md](docs/gotchas.md) records coordinate-system, image-lifecycle,
geometry, and deployment traps that are easy to reintroduce.

Follow the verification requirements in `CONTRIBUTING.md` and preserve unrelated
worktree changes.

## Context & Quota Efficiency (Mac)

Offload only when the token savings outweigh the latency. Conserve Claude and Google AI Pro windows without slowing normal work.

- **Fast path (no `ollama_prep`, no cloud offload):** target files under ~250 lines, targeted edits where line ranges are known, or anything solvable in 1–2 `grep`/`read` calls. Never call `ollama_prep` when `rg` or line-bounded reads can extract the exact lines deterministically in <50ms.
- **Tier 0, local pre-digest (`ollama_prep "<prompt>" <file>`, $0 quota):** Mac only (`127.0.0.1:11434`). Available on `$PATH` as `ollama_prep`. Use for noisy data before entering context: (1) unstructured logs over 300 lines; (2) screenshots/UI images (`.png`/`.jpg`/`.webp`) for labels or layout; (3) unfamiliar boilerplate/config over 400 lines when only structural summary is needed. Output is an untrusted hint: read exact source lines before editing.
- **On-demand local models:** Ollama is configured with `OLLAMA_NUM_PARALLEL=2` and `OLLAMA_MAX_LOADED_MODELS=2`. `qwen3-vl:4b` (default / vision / deep log search) and `qwen2.5:3b` (fast text summaries via `--model qwen2.5:3b`) spin up on demand and run concurrently without evicting each other.
- **Context hygiene:** prefer targeted reads with offset/limit over reading multi-thousand-line files in full.
