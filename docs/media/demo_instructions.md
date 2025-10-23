# Media Automation Guide

The media kit can be regenerated end-to-end for demos, docs, and social previews.

## Quick Start

```bash
make install
make dev-media
make media-hero
make media-approvals-gif
make media-screenshots
make policy-heatmap
make poster
make dev-media-down
```

Generated assets land in `docs/media/generated/` and `docs/media/screenshots/`.

## One-Shot Pipeline

```bash
make media-artifacts
```

This target orchestrates service startup, captures Playwright walkthroughs, generates screenshots, renders the policy heatmap, and exports the architecture poster.

### Troubleshooting

- Ensure `ffmpeg` and `npx` are installed on your system.
- To debug Playwright flows visually, add `--no-headless` to the script commands (e.g., `python scripts/media/walkthrough.py --no-headless --video ...`).
- `make dev-media` starts Docker services in the background; run `make dev-media-down` to stop them when finished.
