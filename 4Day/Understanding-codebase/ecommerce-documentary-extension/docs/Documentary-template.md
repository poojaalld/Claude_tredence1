# Extension Documentary Template

## Opening Scene
- Highlight how this extension reuses the original apparel and shoe catalog but layers experience-level features that only become visible once Codex produces new style guides and promotional tiles. Point out that the catalog data stays unchanged—Codex simply remixes it with new editorial overlays and promotional treatments.
- Describe the persona dueling between the documentation curator (who asks the prompts) and the creative lead (whose decks the newfound style guides support); showcase how the curator probes Codex for clarity while the creative lead tests whether the resulting guides and tiles can anchor the next marketing sprint.

## Style Guide Chronicle
- Outline where the extension stores its style guide intents (palette, typography, layout rules) and how prompts seed those assets before any UI work begins.
- Note how the backend might hold abstract style metadata (colors, gradients, copy tone) and how the frontend applies it to the catalog UI in the absence of production-ready tokens.

## Promotional Tile Narrative
- Describe how the promotional tiles are meant to showcase limited-time collections, storyboard callouts, or curated bundles pulled from the catalog.
- Explain the data flow from the prompt (ask Codex to draft a tile concept), through the backend helper that pairs the concept with products, to the frontend tile component that renders the creative brief at the top of the grid.
- Mention how each tile can mention CTA text, badges, and target segments (e.g., “Sustainable Picks,” “Trainer Drops,” “Daily Deals”).

## UI Storyboard
- Call out where these tiles hook into the existing ProductGrid, filter rail, and CTA panel so learners can narrate how the extension coexists with the base UI.
- Include notes on how the documentation panel or editorial space should consume the new style guides and tiles for future prompt sessions.

## Prompt Hooks
- Record the prompts you use to unlock each new experience: style guide prompts (“Summarize a fresh palette and typography direction for the promo tiles”) and promotional tile prompts (“Create a hero tile that highlights a capsule collection plus the supporting call-to-action copy”).
- Track whether you feed Codex function-level files (specific tile component) or larger folders (whole promo utilities) and how the response changes.

## Extension Hooks
- Mention how the extension builds on the same catalog JSON and services folders so Codex can compare the vanilla repo with the experience-level story.
- Leave space for future prompts that might add wishlist features, editorial overlays, or additional marketing tiles.
