# Bounded resource plan — 2026-11-10

Estimated before semantic work: implementation 35,000–60,000 tokens; focused sample reading, drafting and review 15,000–30,000 tokens total. Actual provider billing/token receipts are unavailable, so these are estimates rather than measured consumption.

| Input | Measured size before reading | Conservative one-pass token range | Chosen semantic scope |
| --- | --- | --- | --- |
| Forum post | 3,232 characters before LF normalization | 3,232–6,464 | Entire post; 3,206 normalized characters |
| General novel | 53,177 characters before LF normalization | 53,177–106,354 | First chapter only; 2,511 normalized characters |
| GL EPUB | About 95,044 extracted text characters across text members, including some non-narrative pages | 95,044–190,088 | First narrative member, paragraph-bounded scene of 2,939 characters |

A full novel's repeated semantic passes would exceed the implementation estimate; they were excluded. Structural EPUB enumeration, file hashing and local character counting do not send the full novel to the model. About 8,656 normalized source characters were used in the three actual trials. One isolated agent handled the post through the new standalone skill; the parent handled the two novel excerpts. General serialization was reused rather than re-benchmarked. One PNG/worldbook wrapper smoke check used a one-pixel original technical carrier.

The estimates are planning ranges, not a hard runtime token meter. No live provider/model roleplay calls or paid comparison harness were launched.
