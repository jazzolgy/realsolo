# RealSolo Audio Asset Policy

## Goal

Only ship audio assets that are legally suitable for commercial redistribution
inside RealSolo. "Royalty-free for recordings" is not sufficient. The license
must allow redistribution of the underlying sample material as part of the app
or a downloadable RealSolo sound pack.

## Approval classes

### APPROVED
Preferred for default bundled content.

Requirements:
- commercial use allowed
- redistribution of the sample material allowed
- adaptation / format conversion allowed
- no NonCommercial restriction
- no NoDerivatives restriction
- no ambiguous "music use only" limitation
- provenance and license source archived

Default preference: CC0 / public-domain-equivalent material.

### CONDITIONAL
May be technically and legally usable, but product packaging needs compliance
work before shipping.

Typical examples:
- CC BY 3.0 / 4.0
- attribution required
- changes must be indicated
- license link / notices required
- "no additional restrictions" must remain respected

CC-BY assets must not become default bundled assets until the release packaging,
attribution screen, downloadable license notices, EULA interaction, and any
store/platform DRM implications have been reviewed.

### REJECT
Do not bundle into RealSolo.

Examples:
- NC / non-commercial licenses
- ND where RealSolo needs conversion or modification
- licenses that only allow musical output but prohibit redistribution of samples
- ambiguous community uploads without a verifiable license chain
- proprietary libraries whose license forbids embedding/repackaging samples

## Current baseline set

| Role | Asset | License | Status | Reason |
|---|---|---|---|---|
| Upright bass | Karoryfer Meatbass | CC0-1.0 | APPROVED | Commercial use, modification, and redistribution are compatible with RealSolo packaging. |
| Drums | Virtuosity Drums | CC0 | APPROVED | Contemporary jazz kit and CC0. Strong default candidate. |
| Piano | Salamander Grand Piano V3 | CC-BY-3.0 | CONDITIONAL | High quality, but attribution/release packaging obligations must be handled. |
| Saxophone | MTG Solo Sax | CC-BY-4.0 | CONDITIONAL | Commercial sharing/adaptation allowed with attribution and modification notice requirements. |

## Explicit exclusions

Spitfire LABS and Pianobook content are not part of the RealSolo baseline set.
Do not bundle third-party proprietary/community sample libraries unless their
specific license explicitly permits redistribution of the underlying samples.

## Asset intake checklist

Before adding a bank:

1. Record canonical source URL.
2. Record exact asset/version.
3. Save the license identifier and license text/reference.
4. Verify commercial use.
5. Verify redistribution of underlying samples.
6. Verify modification/format conversion.
7. Verify attribution requirements.
8. Check ShareAlike / NC / ND / DRM restrictions.
9. Record provenance of original recordings, not only the mapper/repackager.
10. Assign APPROVED, CONDITIONAL, or REJECT.
11. Keep the sound files outside source control unless explicitly approved.
12. Only APPROVED assets may be selected as automatic default product bundles.

## Renderer rule

The music engine must remain independent of the selected library. Player output
continues to use instrument role, articulation, velocity, timing, and duration.
Asset-specific key switches / programs belong in the renderer mapping layer.
