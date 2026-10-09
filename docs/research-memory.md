# Research memory — EIT / CN0565

Updated: 2026-10-02.

This is a persistent project note. It records user-confirmed context separately
from interpretations and questions that still need answers. Read it before
advising on the research objective or planning experiments. Do not treat an
unconfirmed interpretation as the user's research goal.

## Confirmed from the user's messages

- The user has CN0565 hardware. The latest user decision is **16 electrodes
  per session, in two separate sessions/layouts** (direct near-muscle and
  remote unobtrusive) for first data collection (2026-10-02), superseding
  the 2026-10-01 plan to begin with the hardware's maximum 24. The hardware
  maximum remains 24.
- The user wants to understand simulation, conductivity, mesh nodes/elements,
  boundary-voltage changes, and BP, JAC, and GREIT from beginner level through
  mathematical theory and implementation.
- `scripts/eit_sim_playground.py` is the current simulation sandbox.
- The user wants a conceptual reproduction of CN0565 Figure 14 and controlled
  tests that explain differences among reconstruction algorithms.
- The user is considering a medium/phantom experiment, including a Petri dish,
  before considering measurements on a person. This is a question under
  discussion, not a confirmed experimental protocol.
- Explanations should introduce new concepts simply, retain English technical
  terminology, and support English presentation to a professor with bilingual
  English–Vietnamese explanations.
- The user explicitly requested clarification of the research problem and
  persistent recording of their answers on 2026-09-29.

## Research objective — user confirmed on 2026-09-29

- Primary application: post-stroke dysarthria. The user is interested in
  impaired facial muscle activation affecting speech production, with possible
  relevance to weakness after other etiologies. This is the target problem;
  do not assume that every dysarthria presentation is caused by muscle weakness.
- Sense facial muscle/task-related changes using EIT/bioimpedance during a
  defined task list, initially including smiling, and investigate differences
  from a resting reference.
- The user's proposed reference contains existing anatomy: bone/skull, facial
  nerves, blood vessels, and other tissues. This is a modeling intention, not
  evidence that those tissues remain electrically or geometrically constant
  during a task or that baseline subtraction isolates muscle activation.
- Long-term desired outputs include task recognition, spatial information,
  identifying muscles that function poorly, and quantitative impairment or
  activation measures. A percentage scale and its reference are not defined
  yet. These are research ambitions, not demonstrated capabilities of EIT.
- Central design constraint: unobtrusive electrode placement, preferably near
  the chin/jaw and/or ears. Avoid placing electrodes directly over visible
  target muscles such as orbicularis oris or zygomaticus.
- Accepted sites, explicitly confirmed in the follow-up: under the chin,
  along the jawline, in front of/behind both ears, temples, and forehead.
  Avoid the anterior target-muscle regions. The forehead was explicitly
  accepted; do not interpret the constraint as excluding every anterior-facing
  skin surface, or assume the accepted sites contain no muscles.
- Temporary facial EMG AND synchronized camera recordings are acceptable as
  validation references, even though the final device must be unobtrusive.
- The user intends to test initial feasibility on themself. This does not
  establish that a human experiment has occurred or that an electrical-safety
  review, institutional determination/approval, or clinical collaboration exists.
  Do not treat self-experimentation as a safety or ethics exemption.
- The user anticipates that remote placement may require signal separation
  or decomposition, electrode optimization, and suitable reconstruction.
  Feasibility has not yet been established.
- Motivation: conventional facial EMG electrodes over muscles feel too
  obtrusive for the intended final device. The user also mentioned EEG as an
  approach encountered in related work; do not equate EEG with direct muscle
  activation measurement.
- Immediate desired milestone: obtain facial measurements during tasks and
  determine what usable information is present. No human measurement has been
  verified in this conversation.
- Requested literature investigation: facial EIT feasibility, unobtrusive
  electrode arrangements including closed/partial rings, and prior current
  injection/bioimpedance measurement involving facial muscles.
- The user initially asked whether facial EIT had been published; this was a
  literature question, not a confirmed novelty claim. See the findings below.

## Working research question — assistant synthesis, not a validated result

First paper: Can electrodes outside the anterior facial target-muscle regions
recognize a small, predefined set of facial tasks reliably across sessions and
electrode reapplication? This is a proposed operational question, not a result.

Longer term: Can those measurements support muscle-specific information and
eventually assessment of post-stroke dysarthria? That requires separate validation.

## Follow-up decisions — user confirmed on 2026-09-29

- The FIRST paper prioritizes **task recognition with unobtrusive placement**,
  not identifying individual muscles or estimating impairment percentages.
- The user added `EIT related works/` and requested a deeper review of facial
  bioimpedance prior work, tissue/equivalent-circuit models, and defensible
  electrode placement. A few useful tasks are acceptable; publication suitability
  and novelty are questions to investigate, not confirmed facts.
- The user answered **yes** to being able to recruit healthy participants for
  multiple sessions/electrode reapplication and having lab support for
  safety/ethics review. This supersedes uncertainty about resource availability,
  but does NOT establish protocol approval, device clearance, a named reviewer,
  a clinical collaborator, or a specific recruitment/sample-size commitment.
- To the question about a temporary cheek/below-mouth bioimpedance baseline,
  the exact answer was: "ideally là 2, nhưng có thể làm study design cho 1 cũng
  được." The numbered preference is ambiguous in isolation. Working
  interpretation communicated to the user: prefer the unobtrusive design,
  potentially accept a temporary anterior baseline if needed. Confirm the exact
  baseline option before treating it as a finalized study decision.
- Temporary facial EMG and synchronized video remain accepted references.
  Their simultaneous operation with active impedance hardware needs an
  interference/safety assessment; availability is not proof of compatibility.

## Latest user-confirmed research framing — 2026-09-30

- Separate the first **few-electrode, unobtrusive bioimpedance task-recognition**
  study from the ultimate **multi-electrode 3D EIT reconstruction** aspiration.
  The first paper need not reconstruct an image. The user hopes that the later
  study may help identify weak facial muscles, but this is not yet a feasible
  or proven output; 3D coarse-ROI imaging and individual-muscle weakness are
  separate validation gates. See Section 11 of
  `docs/facial-bioimpedance-models-placement-novelty.md`.
- The user explicitly proposes reference measurements at rest with all native
  anatomy present, then the same current-injection/voltage-sensing protocol
  during a task, using `Delta v = v_task - v_reference`. The hypothesis is that
  task changes cause a detectable boundary-voltage pattern. They have not
  claimed a human result; rest subtraction does not isolate muscle effects.
- The user supplied two PDFs in `reference/papers/tasks/`: a 2021 atlas of 29 voluntary
  facial tasks using high-channel sEMG and a 2022 ear-muscle EMG study. These
  inform task selection and placement confounds; neither proves bioimpedance
  task recognition at the intended ear/jaw sites.
- Proposed candidate tasks: pursed lips; unilateral smiles; lower-lip
  protrusion; opening lips wide while jaw closed; upper-lip raise; bilateral
  smile; lip press; mouth-corners downward; five unspecified vowels; open jaw
  with closed lips; open jaw wide; jaw clench; cheek puff and suck. This is
  **19 task labels** if left/right smiles count separately. The claimed
  single-muscle associations are provisional; the atlas shows co-activation,
  does not measure buccinator, and has six German rather than five universal
  vowels.
- Proposed timing is **five repetitions per task, each with five seconds active
  and five seconds rest, plus ten seconds between tasks**. This is a study
  idea, not a validated protocol. Clarify the last-rest convention, language/
  phonemes, effort, and whether all 19 tasks are exploratory or primary.
- The user wants provenance for every numerical parameter and a critical
  editor-style audit: each claim should have direct prior evidence or a
  concrete experiment capable of testing it. They requested an English
  presentation using `Powerpoint_template.pptx` with full paper links.

## Acquisition clarification — user confirmed on 2026-10-01

- The professor recommends starting with the maximum available electrodes to
  inspect task-related data, then reducing the electrode count if appropriate.
  For this CN0565 board the hardware maximum is **24 electrode connections**.
  This supersedes the assistant's earlier interpretation of a fixed
  16-electrode acquisition. It does not change the first-paper priority of
  unobtrusive task recognition, nor establish 24 simultaneous ADC channels.
- The user has **gold cup electrodes**. Manufacturer/model, cup diameter,
  contact gel/paste, connector type and lead length have not been confirmed.
  Do not silently replace them with Ag/AgCl, label them dry, assume a 10 mm
  cup, or assume qualification for active facial impedance measurement.
- The user needs an actionable explanation of CN0565 wiring, Force/Sense
  roles, bias/ground/reference, and facial placement without assuming a
  circular ring or one electrode per target muscle.
- In reply to a connector-photo question, the user directed the assistant to
  `reference/cn0565-designsupport/` and confirmed 30 P1 pins: 24 electrode connections
  and six grounds. The assistant checked the supplied Rev B schematic:
  electrode pins 3–14 and 17–28; GND_ISO pins 1, 2, 15, 16, 29, 30.
  Do not ask for the same schematic again. Physical cable orientation and
  software-to-connector mapping have not yet been bench-verified.
- No specific facial 24-site layout, electrical excitation settings or human
  measurement protocol has been approved/confirmed. Any candidate layout in
  the review is an assistant proposal, not a user decision or published optimum.

## First-collection revision — user confirmed on 2026-10-02

- Use **16 electrodes** for first data collection. Do not continue treating
  C24/P12 as the active design, or obtain a 16-site protocol by deleting
  eight contacts without checking every measurement pattern.
- The user explicitly wants all missing questions asked before committing
  to an interpretable study: placement rationale, wiring/ground/bias,
  rest-versus-task comparison, influential parameters and task design.
- The user clarified that **both** placements are wanted in **two separate
  sessions**: 16 gold cups over selected facial-muscle regions as a near-muscle
  comparator, and 16 cups in an unobtrusive remote layout. The final wearable
  goal still avoids anterior cheek/lip sites. Do not merge 32 sites into one
  frame or claim the remote sites directly overlie oral/cheek muscles.
- Gold-cup model/diameter/contact medium, active acquisition script and bench
  results, actual human-use review status, repeat-session logistics and exact
  vowel/task execution remain unanswered. General lab support and acceptance
  of video/EMG references were already confirmed; do not ask those as if new.
- The active pilot now proposes C16-R remote sites with eight four-terminal
  patterns (M08) and a separate D16-M near-muscle site manifest. D16-M patterns
  are not yet designed or verified. Exact site choices are assistant proposals,
  not user decisions or validated placement. The 24-electrode
  C24/P12 files are archived under docs/archive/ and docs/protocols/archive/.
  Approved excitation values have not yet been finalized.

## Pending clarifications

### Immediate priority clarified by user, 2026-10-03

- Professor's current instruction: collect resting reference, perform task,
  and inspect differences. Prioritize raw-data capture and repeatability
  plots; do not make completed facial image validation a prerequisite for
  investigating task-associated signals. Ultimate spatial/EIT goals remain.
- User states no lab is available for the present self-test and makes the
  decisions themselves. Earlier general lab-support answer must not be
  treated as verified current electrical-safety support.
- Rest–task–rest repetitions, rest-only controls, and frame selection/video
  checks in `cn0565-rest-task-first-look.md` are assistant proposals, not
  user-confirmed acquisition settings. Actual URI/frequency/amplitude and
  safety of assembled human-current setup remain unknown.

### Longer-term clarifications

1. Which small task set and practical first-paper use case should be primary?
2. What electrode-count, visibility, attachment and calibration burden is acceptable?
3. Exact cup model/footprint and whether the D16-M sites physically fit without
   overlap or obstructing tasks; anatomical confirmation and viable pattern set.
4. What exact recruitment/session resources and review status exist? Is an SLP
   collaborator available for later clinical task selection? Do not ask again
   whether general lab/recruitment support exists; that was answered yes.
5. A percentage-impairment definition remains a later-stage question, not a
   prerequisite for the first task-recognition paper.

Record later answers as they arrive and preserve uncertainty explicitly.
Keep literature findings and assistant proposals distinct from user decisions.

## Literature follow-up — assistant findings, not user-confirmed decisions

The pilot document and both manifests under docs/protocols/ contain a
**proposed** paired 16-site-layout engineering pilot. User confirmed the
comparison concept, not the specific sites or patterns. Candidate C16-R
placement/M08 measurement panel, D16-M muscle-site selection, remount/day
checks, five task labels and timing are assistant proposals. Manifests do not
control hardware. Human excitation/current, D16-M pattern set, electrode model/diameter/contact
medium and human-use review remain unverified; questions were sent. Never
interpret an unset approval field or literature precedent as authorization.

See `docs/facial-eit-feasibility-review.md` for the dated evidence review,
source access limitations, candidate layouts, and proposed validation gates.
See `docs/facial-bioimpedance-models-placement-novelty.md` for the deeper follow-up,
including full-text Liu 2025 analysis, Painometry 2020, facial EIM, lower-face
airway EIT, equivalent circuits, placement justification, and study design.
Liu 2025 is no longer an inaccessible lead: the user supplied its full PDF.
Facial EIT/bioimpedance has prior art. Do not claim "nobody has used EIT on
the face" or infer that task recognition proves muscle-specific impairment
measurement. The user's exact remote-layout/post-stroke application remains
unvalidated in the sources examined.
