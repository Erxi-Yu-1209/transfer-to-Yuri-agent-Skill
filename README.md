# Yuri Card Workbench

Turn character cards, posts and novels into **yuri roleplay cards for SillyTavern**. Keep the characters and story you care about, decide what should change, and let your AI agent handle the files.

[中文说明](Chinese-Version/README.md)

## Get started

1. Save the project folder and open it with an AI agent that can read and edit files. The workbench runs through your agent; finished cards are used in SillyTavern.
2. Give the agent your character card, post or novel, then use one of the prompts below. Ask it to handle any initial setup.
3. Discuss the important choices in the conversation. When the card is ready, import the final JSON or PNG file into SillyTavern.

## Start with what you have

**An existing character card:**

```text
I'd like to use Yuri Card Workbench to turn this character card into a yuri card.
First help me understand what should be preserved, then handle the conversion and files.
Use my saved preferences and discuss important choices with me here.
```

**A post or saved webpage:**

```text
I'd like to turn this post into a yuri roleplay card.
Read the complete post, keep the original facts separate from the adaptation, and help me choose a playable starting point.
Handle the files and ask important questions in this conversation.
```

**A novel:**

```text
I'd like to turn this novel into a yuri roleplay card.
Estimate the reading cost and work through all supplied chapters, keeping the characters' voices and story stages consistent.
Save progress as you go and discuss important creative choices with me here.
```

**A card's appearance:**

```text
Help me review this converted card's appearance.
Check its opening page, status bar and images against the story, then help me decide what to keep or redesign.
Discuss image changes with me before making them.
```

## What happens next

The agent reads your material, proposes the adaptation and creates the card. Existing opening pages and status bars are preserved during conversion; afterward, you can keep their styling or request a redesign. Images are checked against the converted story, with possible changes discussed before proceeding.

Novels use **all supplied chapters by default**. Long works are read in parts with saved progress. You can request a particular chapter range; if a conversation ends early, ask the agent to continue from its saved progress.

You control your player character's current actions and replies. The adaptation can retain friendship, conflict and family relationships alongside romance.

## Your preferences

| Choice | Starting preference |
| --- | --- |
| Women in scope | Characters their creator defines as women, including virtual and nonhuman characters |
| Characters to adapt | Main cast; preserve background characters |
| Relationship changes | Allow changes supported by the adapted circumstances |

These preferences are reused. Tell the agent whenever you want to change them.

## Find your way around

| Folder | What it is for |
| --- | --- |
| Project root | English guide and the complete workbench |
| `Chinese-Version/` | Chinese guide and Chinese user interaction |
| `skills/` | The four task guides listed below |
| `config/` | Your saved preferences, maintained by the agent |
| `docs/` | Optional detailed guides and reference material |

| Task guide | Use it for |
| --- | --- |
| `yuri-card-adapter` | An existing character card |
| `post-to-yuri-card` | A post or saved webpage |
| `novel-excerpt-to-yuri-card` | A whole novel or a chapter range you choose |
| `card-presentation` | Keeping or revising a card's appearance |

You can describe your goal in ordinary language and let the agent choose the appropriate guide.

## Refine your card

Try the finished card in SillyTavern, then tell the agent what worked and what you want changed. Give feedback in the conversation; the agent maintains the files and prepares the next revision.

## License

This repository uses a split licensing boundary. Newly written extension code, instructions, tests and documentation are licensed under MIT. The vendored Foreverse exporter keeps its existing MIT license and attribution, TavernWeave components keep their PolyForm Noncommercial terms and notices, and existing Workbench v1.2.0 original files keep their unchanged licensing status. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the full boundary.

[Technical reference](docs/TECHNICAL_USAGE.md) · [Credits and third-party license notes](THIRD_PARTY_NOTICES.md)
