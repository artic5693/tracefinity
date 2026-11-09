# Tracefinity project context (handoff, 2026-11-03)

Use this as background for continuing my project. Where this file and the code disagree, trust the code. Items marked "unverified" have not been confirmed.

## Goal

Make custom Gridfinity bins from photos of my tools (pliers, wrenches) and 3D print them on a Bambu Lab H2S. I am using the open-source Tracefinity app, and I have a Gemini Pro plan.

## What Tracefinity is

- **Function:** turns a photo of tools on paper into fitted Gridfinity bins, exported as STL/3MF.
- **Workflow:** place tools on paper, photograph from above, adjust paper corners for scale, trace outlines, save to the tool library, group into a project, create and arrange a bin, export.
- **Backend:** Python/FastAPI, OpenCV, manifold3d.
- **Frontend:** Next.js/React/TypeScript, react-three-fiber.
- **Upstream:** https://github.com/tracefinity/tracefinity

## My setup

- **Source install on my Mac:** `~/Dev/tracefinity`, not Docker.
- **Ports:** frontend 4001, backend 8000.
- **Start command:** defined as the `tracefinity` entry in `~/Dev/homelab/.claude/launch.json`:

```bash
cd ~/Dev/tracefinity
export TRACERS=inspyrenet,birefnet-lite,isnet NEXT_PUBLIC_API_URL= BACKEND_URL=http://127.0.0.1:8000
(cd backend && exec venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000) &
(cd frontend && exec npx --yes pnpm@10.29.2 exec next dev -H 127.0.0.1 -p 4001) &
wait
```

- **Keep `NEXT_PUBLIC_API_URL` empty.** The browser then goes through port 4001. When it fetched the STL directly from port 8000, the 3D preview got a 401, apparently because the loader did not send the login cookie across ports.
- **Login:** native login with an admin account. Restarts may require logging in again.
- **Data:** `backend/storage/default/` (`tools.json`, `bins.json`, `outputs/`).
- **Git:** `main` is 1 commit ahead of `origin/main`. The local commit is `bb3c106`, "Align Dockerfile GEMINI_IMAGE_MODEL default with config.py". It has not been pushed, and the worktree is otherwise clean.

## Tracing decisions & Local Model Workflow

- **Local models only for now.** I chose to skip the Gemini API because its image models are pay-per-use, even with a Gemini Pro plan.
- **Default tracer:** InSPyReNet (`mps` on Apple Silicon). BiRefNet Lite and IS-Net are also enabled (`TRACERS=inspyrenet,birefnet-lite,isnet`).
- **API key:** a Tracefinity-only key exists but is deliberately not loaded. Do not ask me for it or suggest pasting it into chat.
- **Local model cascade:**
  1. **InSPyReNet (Default):** First pass for most tools; fast on Apple Silicon MPS and handles matte/dual-material grips well.
  2. **BiRefNet Lite:** Use via **Re-trace** when InSPyReNet clips polished chrome jaws or merges shadows.
  3. **IS-Net:** Lightweight fallback (~0.8s) if heavier models over-segment internal features.
- **Fallback for bad traces (Manual Mask via Gemini Web App):**
  - Confirmed and wired in `frontend/src/app/trace/[id]/page.tsx` so **Manual mask upload** is selectable in the Tracer dropdown and via **Upload a mask manually** even when only local tracers are configured.
  - Flow: Click **Upload a mask manually** -> **Download Image** -> **Copy Prompt** -> paste both into [gemini.google.com](https://gemini.google.com) -> download the black-on-white mask -> **Upload Mask**.
  - `POST /api/sessions/{id}/trace-mask` automatically enables template-matching alignment (`align=True`) when the uploaded mask dimensions differ from the perspective-corrected image.
- **Optional local auto-naming:** Set `TOOL_LABEL_PROVIDER=ollama` (`TOOL_LABEL_MODEL=qwen3-vl:4b`, `TOOL_LABEL_OLLAMA_URL=http://localhost:11434`) to auto-name traced polygons locally; degrades gracefully to `tool N` if Ollama is offline.
- **Capture & Fit-Test SOP:**
  - Shoot directly overhead from **60 cm+** on a dark background so thick tools ($t \approx 19\text{ mm}$) stay within ~3% perspective projection ($\frac{H}{H - t}$).
  - Measure length and max thickness with calipers; use **Fill in** in the Tool Editor to remove fragile interior slots/islands and add a **Finger hole** ($15\text{ mm}$ radius).
  - Max cutout depth is $7\text{u} - 6.75\text{ mm}$ ($14.25\text{ mm}$ at $3\text{u}$, $21.25\text{ mm}$ at $4\text{u}$).
  - In Bambu Studio, use the **Cut** tool (`C`) to slice the top $5\text{–}6\text{ mm}$ of the bin and flip it flat onto the plate for a fast fit test before printing the full bin.

## Current tool and bin

**Tool**
- The tool is saved as `knipex alligator`, but the photo shows **Knipex Cobra 87 01 250**, so it should be renamed.
- The traced length is 250.4 mm, which fits the nominal 250 mm suggested by the model number. A caliper check is still pending.
- Thickness is unverified: one retailer lists about 19 mm, and it needs measuring.
- The interior slot near the jaws was removed from the trace, so it is now open pocket floor. The raised area between the handles is part of the outer outline and remains.

**Bin: `Tool Drawer bin 1`** (the only bin, holding this one tool)

| Setting | Value |
|---|---|
| Grid | 7 x 2 (about 293.5 x 83.5 mm) |
| Height | 3u |
| Cutout depth | 14 mm, so the pliers stand proud |
| Clearance | 1.0 mm |
| Cutout chamfer | 1.0 mm |
| Wall thickness | 1.6 mm |
| Stacking lip | On |
| Magnets | Corners only (4), 6 x 2.4 mm |
| Half-grid base, partial bins, insert | Off |
| Bed size | 320 mm |

**Printer:** Bambu's specs list a 340 x 320 x 340 mm build volume. The same page also shows a 310 x 260 mm figure whose meaning I did not confirm. The bin fits within both, so let the slicer confirm.

**Exports**, in `~/Projects/3D-Printing/`:
- `Tool_Drawer_bin_1_7u2u3u_14mm-tracefinity.stl` is the current version. Its 17:31 timestamp is after the island edit, so it likely includes that edit, but this has not been checked by inspecting the mesh.
- `Tool_Drawer_bin_1_7u2u4u_14mm-tracefinity.stl` is the older 4u version.

## Tool Cabinet Drawer Grid Capacities (Harbor Freight Series 3 42" Roll Cab)

Based on standard Gridfinity unit sizing (42 mm × 42 mm base pitch, heights in 7 mm units / "u") and interior drawer dimensions for the 42" × 22" Series 3 Roll Cab (Item 70368 / 58723):

- **Top Full-Width Drawers (2 drawers — 22 wide × 11 deep = 242 spaces each, 484 spaces total)**:
  - Usable Dimensions: ~37-1/8" W × ~19-3/8" to 19-5/8" D (~943 × 492–498 mm; ~18 mm side margin, ~30–36 mm front-to-back margin).
  - **Drawer 1 (Very Top — Hardware & Fasteners)**: Usable height ~3-3/4" to 4.75" H (~95–120 mm), max height **12u–16u** (~84–112 mm). Intended for divided hardware bins, screw/bolt organizers, heat-set inserts, and small parts bins (with scoops and label tabs up to 6u–12u).
  - **Drawer 2 (2nd Top — Hand Tools)**: Usable height ~2-1/4" to 2-1/2" H (~57–63 mm), max height **7u–8u** (~49–56 mm). The prime home for flat hand tools and custom Tracefinity tool shadow bins (pliers, wrenches, diagonal cutters, strippers, knives) at 3u–5u height.

- **Left Bank Drawers (4 drawers — 10 wide × 11 deep = 110 spaces each, 440 spaces total)**:
  - Usable Width & Depth: ~17-1/8" to 17-1/4" W × ~19-3/8" to 19-5/8" D (~435–438 × 492–498 mm; ~15–18 mm side margin, ~30–36 mm front-to-back margin).
  - **Drawers 1–3 (Shallow)**: Usable height ~2-1/4" to 2-1/2" (~57–63 mm), max height **7u–8u**.
  - **Drawer 4 (Bottom Deep)**: Usable height ~5-1/4" to 6" (~133–152 mm), max height **18u–20u**.

- **Right Bank Drawers (4 drawers — 10 wide × 11 deep = 110 spaces each, 440 spaces total)**:
  - Usable Width & Depth: ~17-1/8" to 17-1/4" W × ~19-3/8" to 19-5/8" D (~435–438 × 492–498 mm; ~15–18 mm side margin, ~30–36 mm front-to-back margin).
  - **Drawers 1–3 (Medium)**: Usable height ~3-3/4" to 4" (~95–102 mm), max height **12u–13u**.
  - **Drawer 4 (Bottom Deep)**: Usable height ~6-1/4" to 6-1/2" (~159–165 mm), max height **22u–23u**.

- **Entire Roll Cab Total (10 drawers)**:
  - Nominal Total: **1,364 standard Gridfinity spaces** (242 × 2 top + 440 left + 440 right).

## Next steps

1. Open the 3u STL in Bambu Studio. Confirm that the slot is gone, there are 4 corner magnet holes, and it is a single piece that fits the plate.
2. Measure the pliers with calipers (length and thickest point) and revisit the 14 mm depth. The depth slider has less room at 3u.
3. Check my magnets against the 6 x 2.4 mm holes.
4. Print a fit test: use the Cut tool to keep the top 5-6 mm, then flip it so the flat cut side is on the plate.
5. Adjust based on the fit test:
   - Sticks or won't seat: raise clearance by 0.2-0.3 mm.
   - Rattles a lot: lower clearance by 0.2-0.3 mm.
   - Outline is off in one spot: fix that part of the trace.
   - Fits well: print the full bin, keeping supports out of the magnet holes.
6. Rename the tool to Knipex Cobra, then repeat the workflow for more tools.

## Working rules

- **Read before changing the repo:** `CONTRIBUTING.md`; `DESIGN.md` for architecture; `CONSTITUTION.md` for feature or scope decisions; the relevant file in `docs/`.
- **Known traps:** `docs/gotchas.md` covers Y-axis inversion, cutout pipeline order, auto-size with the stacking lip, EXIF orientation, paper corner detection, and Gemini mask quirks.
- **Public writing:** issues, PRs, comments, commit messages, and release notes stay strictly technical, with no personal context.
- **Checks:** `make lint`, `venv/bin/python -m pytest`, `pnpm test`. See `CONTRIBUTING.md` for the exact requirements.
- **Editing saved data:** prefer the app UI. Direct edits to `tools.json` or `bins.json` require a backup and a stopped server. An open browser tab can overwrite changes with old values, so reload it before editing.
- **Existing backups:** `bins.json.bak-20261103`, `tools.json.bak-island`, `bins.json.bak-island`.

## Not captured

- I asked to compare Tracefinity performance on my Tower server versus this Mac. I ended up installing on the Mac, but this handoff does not include the comparison results.
- Full-print results: no fit test or full bin has been recorded as printed.
