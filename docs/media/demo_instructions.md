# Demo Recording Instructions

1. Start services: `make dev`
1. Record terminal session: `asciinema rec demos/switchboard.cast --command "make demo-e2e"`
1. Convert to GIF (requires `agg`): `agg demos/switchboard.cast demos/switchboard.gif`
1. Embed GIF in README or presentations.

Tip: narrate the approvals UI step separately using a short screen recording.
