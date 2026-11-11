# Yuri Card Workbench 1.2.0

Adapt character cards, posts and novels into **yuri roleplay cards**, using your saved preferences. The agent does the reading, drafting and record keeping; you make important choices in the conversation.

[中文说明](Chinese-Version/README.md) · [Technical commands](docs/TECHNICAL_USAGE.md) · [Attribution](THIRD_PARTY_NOTICES.md)

## Start with your agent

Already have a JSON or PNG character card:

```text
Use yuri-card-adapter to turn this card into a yuri card.
First understand the original characters and story, then adapt it using my saved preferences.
Preserve the existing front-end styling and settings during conversion. If new openings are needed, use the authored rebuild workflow. Afterward, ask whether I want to keep the styling or redesign it, and review whether all images fit the converted story.
Handle the files and records for me; bring important choices into this conversation.
```

Have a post or a saved webpage:

```text
Use post-to-yuri-card to adapt this post into a yuri roleplay card.
Keep original facts separate from fictional adaptation choices, preserve unknown source identity, and leave my player character's current actions to me.
Read the complete supplied post and maintain the records for me. Ask important questions here.
```

Have a novel or EPUB:

```text
Use novel-excerpt-to-yuri-card to adapt this novel into a yuri roleplay card.
Estimate reading cost, then process all supplied chapters through resumable reading units. Do not substitute a sample or shorten the chapter scope without my explicit request.
Preserve provenance, character voice and story stages. Maintain progress and choices for me in this conversation.
```

Want to preserve or revise an existing card's appearance:

```text
Use card-presentation to review this converted card's opening screen, status bar and regex renderers.
Keep the existing presentation working while we decide whether to retain it or redesign it.
Compare the main PNG, embedded UI images and linked images with the converted story, then discuss any changes with me before adding image tools.
```

The novel skill keeps its existing folder name for compatibility; **whole-work conversion is the default**. You can explicitly request a particular chapter or excerpt. An estimate or context limit changes the reading batch size, not the agreed coverage. If a session ends early, the agent records incomplete progress and resumes later.

## What the workbench handles

- Existing JSON/PNG cards, supplied posts, TXT/Markdown and readable EPUB text.
- Source-linked yuri adaptation, including already-GL works, ensembles and nonhuman characters.
- New openings and larger rewrites through an explicit authored rebuild, alongside the original converter for local edits.
- Preservation of inherited HTML/CSS, status protocols, regex renderers, extension settings and worldbook activation metadata.
- A post-conversion styling choice and visual review of the main image, embedded UI images and linked assets. Image editing/generation is not integrated in this release.
- Shared provenance, reusable extraction records, resumable full-source reading and conversational feedback.

Source facts and adaptation choices stay separate. Unknown original-poster gender remains unknown in the source record. A selected first-person protagonist normally uses `{{user}}`; the model plays the counterpart. Friendship, conflict, family bonds and independent goals remain valid; romance is optional.

Supplied masculine sexual anatomy inconsistent with the requested yuri output is quietly adapted into non-graphic woman-consistent or anatomy-neutral wording. The agent does not quote details or offer to retain them. Nonsexual background identities and source evidence remain intact; age boundaries still apply.

## Saved defaults

| Choice | Default |
| --- | --- |
| Women in scope | Author-defined women, including virtual and nonhuman characters |
| Cast | Main cast; preserve background identities |
| Relationships | Permit changes supported by specific altered circumstances |

Ready preferences are reused. Tell the agent when you want a different choice; no per-card questionnaire or Markdown feedback form is required. The Chinese edition keeps core instructions and code in English, with Chinese user interaction and default-option labels.

## Try and give feedback

Ask the agent to produce the card you actually want to use. Import the final JSON/PNG into SillyTavern, then describe what worked or felt wrong here. The agent maintains the evidence and next revision. Offline file checks, visual previews, actual host use and your judgment are recorded separately.

The three earlier miniature development samples were withdrawn and are not recommended test cards. Current real-use feedback and its limits are summarized in [the feedback review](docs/REAL_USE_FEEDBACK.md). Your private cards and test folders are outside the public distribution.

## Setup and delivery

Use an agent with local file access and Python 3.10+. Ask it to install `requirements.txt` when necessary. Scripts do not call a model API or require an API key; reading and authoring use the agent's host capabilities.

Each skill folder contains its required runtime and notices, or identifies its companion for a different task. The maintained shared implementation is in `shared/`. Command reference, batch use and release maintenance belong in [technical usage](docs/TECHNICAL_USAGE.md); the agent handles those steps.

Delivery uses a Google Drive folder with the directory structure retained. `.gitignore` and an explicit public allowlist keep private source material, casework, local profiles and credentials out of public releases. No source novels or original EPUB artwork are bundled. Foreverse export code remains unmodified under its MIT license; TavernWeave supplies attributed workflow references. The project's own overall license remains for its rights holder to decide.
