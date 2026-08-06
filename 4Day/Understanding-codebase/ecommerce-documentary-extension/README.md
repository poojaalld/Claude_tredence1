# E-Commerce Documentary Extension Lab

This folder reuses the same catalog from the main documentary lab but adds experience-level challenges that only appear after you prompt Claude for fresh style guides and promotional tiles. Think of this as the “prompt-activated” extension pack: Claude reads the base repo, then you invite it to invent editorial style, badges, and hero tiles that fit the catalog world.

## Repository layout
- `backend/` holds the helpers or metadata you might need to pair tiles with inventory, badge rules, or tone descriptors before the frontend renders them.
- `frontend/` contains the React pieces that will eventually display the promotional tiles, badges, and any editorial copy inspired by the style guide prompts.
- `docs/` now stores the extension-specific templates (`Documentary-template.md`) and prompt logs (`prompt-strategies.md`) so you can converge on a narrative before or after Claude drafts the new assets.

## Activities
1. Start by scanning the backend and frontend folders just like in the base lab, but keep the extension narrative in mind: you are looking for the pieces claude will later remix for style guides and tiles.
2. Use the new `docs/Documentary-template.md` to script a documentary-style story that explains the extension’s style guide intent, how promotional tiles are composed, and where prompts plug in to refresh the experience.
3. Prompt Claude to generate style guide assets (palettes, typography, spacing, tone) and ask it to map those assets onto promotional tile ideas.
4. Capture all of your prompts, revisions, and observations in `docs/prompt-strategies.md`; note what stayed accurate, what needed clarifying, and which strategy (function-level vs. folder-level) worked best for each feature.

## Prompt ideas
- “Summarize the color, typography, and tone rules that should accompany the next wave of promotional tiles.”
- “Design a hero promotional tile for the ‘Storyteller Capsule’ collection, include badge copy, CTA, and the catalog segment it calls out.”
- “Review the style guide and tell me how the frontend should animate the badge transitions so marketing feels cohesive.”
- “Compare the catalog JSON to the badge rules and explain how to keep the promotional tiles aligned with inventory availability.”

## Unlocking the experience
- Treat claude as both your reader and collaborator: ask it to describe the current repo state, then ask it to extend the repo with new artifacts (guides, tiles, copy).
- If Claude misses the tone or badge details, feed back specific snippets from `frontend` or `backend` and rerun the prompt; the prompt log should capture that back-and-forth.

## Next steps
After spanning this extension, head back to the base lab (`../ecommerce-documentary`) to cross-check your narratives, then revisit this folder when you want to add more editorial overlays, wishlist features, or further marketing tiles with Claude.
