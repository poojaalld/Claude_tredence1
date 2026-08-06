# Prompt Strategies Log

## Function-level vs folder-level
- Function-level prompts keep the narrative precise (for example, “Describe how `frontend/src/components/PromoTile.jsx` composes badges and CTA copy”). That detail helps you guide Codex through the promotional tile variations.
- Folder-level prompts cover the broader extension (styles + tiles) so you can surface relationships between the style metadata, document docs, and the UI components at once.
- Track how confident each strategy feels depending on whether you point Codex at a single tile helper or the entire `frontend/src/tiles` and `docs` folders.

## Style guide prompts
- Log every prompt that asks Codex to write, audit, or transform a style guide (palette, typography, spacing, tone). Note which context you provided (a `style-guides.md` stub, a set of colors, or a screenshot description) and whether the response stayed accurate.
- Include any follow-up prompts you use to refine the guide, such as “Adjust the hero palette to be more premium” or “Show how the typography scales on mobile tiles.”

## Promotional tile prompts
- Record prompts that summon promotional tile concepts, pairing them with catalog segments (seasonal drops, exclusive bundles, editorial picks).
- Note whether you prompted for creative direction (“Craft a tile celebrating trainer drops with a limited badge”) versus metadata (“Summarize the badge rules so the frontend helper can render consistent CTAs”).

## Prompt log
- Chronicle each prompt iteration, the inputs sent (files, folder paths, example tiles), and how long the response remained aligned with the repo before you needed to re-prompt or clarify.
- After every wave of prompts, explain which strategy helped you capture the README sections for the extension and what you would try next when expanding the experience again.
