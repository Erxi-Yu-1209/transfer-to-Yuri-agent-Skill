# Focused yuri trials — 1.1.0

These are agent-executed source/adaptation trials, not real-host roleplay or a general conversion benchmark. Reading was bounded before semantic work; see RESOURCE_PLAN.md. About 8,656 frozen source characters were used, without full-novel analysis.

| Sample | Read scope | Yuri-specific result | Preserved |
| --- | --- | --- | --- |
| Forum post | Complete supplied post; 3,206 normalized characters | Original poster remains gender-unknown in extraction; the fictional counterpart is designated a woman through one decision and one field patch | Existing successful confession, girlfriend's initiative, source-attributed recollections, unknown narrator age, player identity |
| GL novel | First narrative EPUB member, paragraph-bounded to 2,939 characters | Both main characters already qualify as women; zero identity decisions and zero field patches | Scene-stage uncertainty, distinct voices, casual companionship, unresolved relationship outcome and narrator-name uncertainty |
| General novel | First chapter only; 2,511 characters | Selected protagonist becomes a girl through one decision and two field patches | Stated age, fourth-child position, two elder brothers, sister and younger sister, background men, family affection, practical ambitions and open institutional questions |

The general-novel trial uses the saved broad definition: female-centered kinship and family life do not require inventing romance. It does not establish a full-work adaptation or later gender-dependent institutional rules. The GL scene does not import later franchise knowledge. The forum source contains only the poster's account; reported partner feelings are not independent testimony.

Final trial artifacts are under private-casework/<post|gl|general>/final/yuri-card.v2.json. Reusable source records, frozen excerpts, card drafts and current plans accompany them. Creative greetings and player interfaces are declared separately from extracted events. Process/audit language is kept out of the final roleplay narrative where practical, with provenance in creator notes and adaptation sidecars.

A fresh-context agent executed the post using the standalone skill. The parent reviewed its source-gender distinction and requested a small revision to move audit wording out of narrative fields. The two novel trials were executed and spot-reviewed by the parent. All three final outputs were built with the maintained 1.1 core and exact hash bindings. User literary acceptance remains available through conversation; no form is required.

General export code was reused from the pinned Foreverse Git blob without an exhaustive new test program. A small wrapper smoke confirmed PNG metadata round-trip, unchanged image payload and structured-worldbook round-trip using an original one-pixel technical carrier. A batch smoke confirmed failure isolation and safe reuse of a current completed output. Neither smoke imported into a running SillyTavern instance. Focused automated yuri tests cover identity designation, protected cast, already-women preservation, causality and stale evidence.

## 1.1.1 conversational corrections

The post perspective is now {{user}} and the model plays the girlfriend, consistently in greeting/worldbook. The original narrator's gender remains unknown in source evidence. The GL perspective is also {{user}}, with 安達 as {{char}}. A new slightly longer frozen scene confirms surname 島村 after the old cutoff; no given name is supplied. The general card is unchanged. Each corrected case has a scoped profile.player.json and a newly bound plan. These exports still have no new actual host import/roleplay observation; the user will perform the next manual trial.
