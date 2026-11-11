# 1.1.1 — player binding and large-input follow-up

Applied the 2026-11-11 conversation feedback. Post and GL perspective roles now use {{user}} consistently; the model controls the counterpart. Source identities and the confirmed GL surname remain in evidence. The general sample is unchanged. Full-source text registration now has resumable reading units, with unread coverage prevented from being silently approved. The human will perform the small SillyTavern import trial and report in conversation.

# 1.1.0 — source-media yuri adaptation

This community-focused iteration brings source-media skills and file adapters forward without making a formal roleplay benchmark a prerequisite. Version follows the user-selected v1.1 delivery label, building on v0.5.0.

Added two standalone skills: post-to-yuri-card and novel-excerpt-to-yuri-card. They share frozen text/evidence records, explicit source-versus-adapted gender, source-linked card drafts and reviewed exact-span adaptation decisions. Default output is a yuri card under the saved three choices; a source-faithful card is retained for comparison. Unknown poster gender is not retroactively rewritten; already-GL scenes can stay unchanged; female-centered kinship and friendship do not require romance.

General card serialization, lorebook construction and PNG writing reuse the unmodified MIT Foreverse tool with its notice. TavernWeave informed source-library design; its implementation is not copied. New integration adds bounded TXT/Markdown/EPUB excerpts, PNG payload reading and explicit structured-worldbook copying. It is a file adapter, not a live host/API integration. Attribution and immutable code identity are in THIRD_PARTY_NOTICES.md.

The focused three-source trials, automatic checks and scope limitations are in docs/SAMPLE_RESULTS.md and docs/RELEASE_CHECKS.json. No full-novel coverage, new live SillyTavern roleplay or matched model benchmark is claimed. Earlier reported card-016 import evidence remains historical; no older private batch is resumed.

Delivery is a Google Drive folder with public source and a separate ignored private-casework area. The Chinese runtime keeps English reasoning and Chinese setup choices. No new skill is silently installed into the user's personal skill directory.

Verification: 93 English-project and 87 Chinese-runtime automatic checks passed, including 12 focused yuri-policy checks. Standalone shared bundles and Chinese/English reasoning-core parity passed; reused span routines match the existing engine. The upstream exporter and license match their recorded Git blobs. General exporter benchmarking was not repeated.
