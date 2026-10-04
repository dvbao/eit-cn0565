# Archived pilot draft: 24 electrodes (2026-10-01)

This is the historical C24/P12 proposal. The active first-collection pilot uses 16 electrodes; see ../facial-bioimpedance-pilot-01.md.

Version 0.1, 2026-10-01. Lab-review draft; not an approved human-use protocol.

## 0. Quyết định chính và cách đọc bằng chứng

**Mục tiêu:** kiểm tra một số facial tasks có tạo ra complex-impedance patterns
lặp lại với electrodes ngoài anterior target-muscle regions hay không, kể cả
sau tháo-gắn. Chưa reconstruct ảnh, chưa phân tách từng cơ, chưa nghiên cứu
bệnh nhân dysarthria. Đây là engineering pilot trước một feasibility study
nhiều người; không hứa publication hoặc clinical validity từ một người.

Ký hiệu dùng trong protocol:

- **[E] Evidence:** điều nguồn thực sự đã đo/mô tả. Luôn ghi phạm vi.
- **[P] Proposal:** lựa chọn thiết kế của pilot này, có rationale nhưng chưa
  được paper chứng minh tối ưu. Những số này phải được khóa trước acquisition.
- **[V] Verify:** phải đo, xác nhận hoặc phê duyệt trước khi thực hiện phần
  liên quan; không điền một giá trị đoán cho đủ bảng.

**Không có source đã đọc nào validate toàn bộ tổ hợp 24 gold cups + C24
remote layout + các tasks dưới đây.** Literature hỗ trợ từng nguyên tắc; pilot
phải tạo bằng chứng cho tổ hợp mới. C24 trong tài liệu trước cũng chỉ là [P].

Đi cùng file này: `protocols/facial-pilot-01-design.json`, chứa site IDs,
candidate measurement patterns, randomized trial orders và các trường chưa
được xác nhận. Đây là design manifest, không phải chương trình điều khiển board.

## 1. Trước khi đặt bất kỳ electrode có kích thích nào lên người

### 1.1 Human-use gate [V]

Lab phải xác nhận toàn hệ thống thực tế: CN0565/firmware, power/USB, leads,
electrodes/contact medium, từng intended current path, normal/fault current,
DC/leakage/isolation và các thiết bị ghép đồng thời. Chốt người chịu trách
nhiệm, institutional review/consent cần thiết và participant screening theo
protocol của lab. Tự thử không tạo miễn trừ. Không suy current an toàn từ
100 mV của Liu, current của Kim, hay một resistor đơn lẻ trên evaluation board.

**Chưa chốt human excitation amplitude/current trong tài liệu này.** Không
bypass DC blocking/current limit hoặc nối người vào earth/USB ground. Nếu có
đau, nóng/rát, co cơ ngoài ý muốn, chóng mặt hoặc khó chịu, dừng acquisition
và xử lý theo quy trình lab; không tăng kích thích để tìm tín hiệu.

Nguồn kỹ thuật: [S1] mô tả isolation và excitation nhưng không chứng nhận
toàn bộ setup người dùng. [S4] có ethics approval riêng và hệ đo khác.

### 1.2 Bench day: làm được ngay, không có người nối vào mạch

| Check | Cách làm / output cần lưu | Cơ sở |
|---|---|---|
| Đủ 24 đường | Kiểm tra từng lead bằng known load/continuity phù hợp khi board ở trạng thái an toàn; lập bảng site -> lead -> P1 -> chip/X -> software index | [E:S1], mapping thực tế [V] |
| Ground không bị nhầm | P1 3-14 = X0-X11; 17-28 = X12-X23. P1 1,2,15,16,29,30 = GND_ISO. X number không mặc định bằng Python index | [E:S1 schematic Rev B sheet 2] |
| Đúng four-terminal measurement | Known resistor/RC network có separate Force/Sense access; thử một thay đổi load biết trước | [E:S1,S7]; implementation [V] |
| Đúng số và đơn vị | Phân biệt raw DFT/voltage, calibrated complex impedance, current; verify sign và phase trên resistor/RC | [E:S1], [V] |
| Noise, drift, crosstalk, settling | Giữ tải tĩnh, log liên tục; so channel trước/sau switching, lặp order đảo trên bench; dùng network không đối xứng để phát hiện swap/misrouting | [E:S1,S7]; test chi tiết [P] |
| Dynamic response | Chuyển giữa các tải biết trước, log thời gian và step response; biết signal thật có được thấy hay không | [P], không giả step là facial change |
| Thời gian scan | Log start/end mỗi configuration và frame; báo median, 95th percentile và worst observed, không lấy ADC sample rate làm frame rate | [E:S1,S7]; metrics [P] |
| Gold-cup interface | Characterize cup + contact medium trên fixture/phantom phù hợp; record material/area, không coi saline test là skin validation | [E:S11], [P] |
| Null phantom | Electrode geometry cố định, không target change; đo drift rồi thử riêng chuyển động boundary/contact trên phantom | [E:S5], protocol cụ thể [P] |

**Không cần phantom anatomy hoàn chỉnh để bắt đầu bench.** Resistor/RC giúp
kiểm tra electronics; tank/gel giúp kiểm tra multiplexing, geometry và
electrode interface. Một tank hình tròn không chứng minh sensitivity ở mặt.

Frequency characterization đề xuất trên bench: **20, 50, 100 kHz [P]**.
Lý do: S1 có characterization ở 20 kHz; S4 dùng 50 kHz trên hệ khác; S3 báo
100 kHz. Đây không phải optimal frequencies cho mặt. Candidate single
frequency cho human pilot là **50 kHz [P,V]** nếu lab duyệt và bench đáp ứng;
nếu đổi, cập nhật protocol trước data. Không sweep frequency trong primary
5 s trials để tránh đánh đổi thêm tốc độ và làm khó diễn giải.

Collector hiện tại **chưa được certify ready**: local `adi/cn0565.py` có
`electrode_count_available=[8,16,32]` dù two chips tạo 24 X lines;
`all_voltages` ép `impedance_mode=False` và cache switch sequence. Thay đổi
protocol phải bảo đảm cache/mapping được cập nhật. `cn0565_sample_plot.py`
dùng reference toàn 1 cho demo; không dùng reference đó cho mặt. Không có
hardware modification/acquisition nào được thực hiện khi viết tài liệu này.

## 2. Electrode placement C24: quyết định có rationale, chưa có facial proof

**24 gold cups [user-confirmed].** Không gán mỗi cup cho một cơ. Mỗi cup nối
một electrode connection và có thể đổi Force/Sense giữa configurations.
Không thêm body-ground cup vào GND_ISO. [E:S1]

### 2.1 L/R nghĩa là bên trái/phải của participant, không phải ảnh camera

Các vị trí dưới đây là **anatomical zones [P]**, không phải các tọa độ đã
được đo trên bạn. Dùng cùng site IDs trên hai bên. Trong fitting có giám sát,
chọn tâm cup vừa vặn, không chạm/gel-bridge nhau; chụp và ghi tọa độ trước khi
thu primary data. Nếu không đặt vừa, sửa layout version, không ép đủ 24.

| Site mỗi bên | Vùng định vị ứng viên | Tổng hai bên | Hypothesis / confound |
|---|---|---:|---|
| L1,L2 / R1,R2 | Hai điểm upper/lower ở trán ngoài, ngoài vùng cơ môi-má mục tiêu; không trên mí/quanh mắt | 4 | Thêm coverage trên; frontalis/contact vẫn có thể đổi |
| L3 / R3 | Thái dương, vị trí tiếp xúc ổn định ngoài hair nếu có thể | 2 | Lateral view; temporalis/vascular signal |
| L4,L5 / R4,R5 | Da trước tai: điểm cao hơn và thấp hơn, không trong ear canal | 4 | Lateral attachment; jaw/skin motion |
| L6 / R6 | Da sau tai có thể gắn cup ổn định | 2 | Low-visibility candidate; curvature/hair/contact |
| L7-L10 / R7-R10 | Bờ dưới hàm: góc hàm; hai điểm trung gian; điểm phía trước dưới hàm gần cằm. Không chuyển lên trước má/môi | 8 | Lower-face coverage; jaw movement, local muscles |
| L11,L12 / R11,R12 | Hai điểm anterior/posterior dưới cằm trên mỗi bên, không cùng một điểm midline, không đẩy xuống cổ trước | 4 | Lower view; floor-of-mouth/tongue/swallow effects |
| **Tổng** | **12 sites mỗi bên** | **24** | **C24 là proposal, không có nguồn chứng minh optimum** |

Không có khoảng cách mm được invent: cup diameter, usable skin area và
contact medium chưa biết. “Điểm trung gian” được **đo và lưu khi fitting**,
không chỉ ghi mô tả bằng lời. Cho redonning, dùng anatomical landmarks, ảnh
front/left/right/under-chin và distance measurements. 2D photos hỗ trợ đặt
lại nhưng không thay thế 3D electrode coordinates cho reconstruction sau này.

**Placement record bắt buộc:** cup model/diameter và effective contact area
nếu biết; paste/gel; site ID; ảnh; landmark distances; P1/software mapping;
fixation; lead routing/strain relief; hair; tình trạng da và mọi deviation.
Không kéo dây căng vào cups khi cử động. Skin preparation/cleaning theo
manufacturer IFU và lab; không tự prescribe abrasion hoặc chất kết dính.

### 2.2 Cơ sở thực sự bảo vệ được

- [E:S4] Kim chọn anatomy-linked landmarks và dùng MRI/3D boundary để
  kiểm chứng; **target là airway**, không chứng minh C24 thấy cơ môi.
- [E:S10] Hyvönen tối ưu positions với geometry/prior/noise cụ thể trong
  2D numerical studies; không có universal facial optimum.
- [E:S5,S6,S11] contact, geometry, placement và vật liệu có thể ảnh hưởng
  measurement; vì thế ghi geometry và test redonning là cần thiết.
- [E:S9] near-ear có thể có local muscle activation khi facial task; vì
  vậy “remote placement” không đồng nghĩa nguồn tín hiệu từ remote muscle.

**C24 rationale [P]:** giữ constraint user, bilateral symmetry để khảo sát
laterality, thêm upper/lower coverage, ưu tiên jaw/under-chin. Đây là một
candidate pool để bắt đầu, không phải exhaustive search mọi vị trí trên mặt.

**24 cups và dây là exploratory laboratory apparatus**, chưa phải bằng chứng
thiết bị cuối cùng unobtrusive. Ghi donning time, visibility, số vị trí phải
đặt lại và participant feedback; không đồng nhất “không nằm trên cơ mục tiêu”
với “ít gây vướng”. Mục tiêu giảm electrodes cần một study tiếp theo.

## 3. Measurement protocol: tối đa contacts không đồng nghĩa tối đa patterns

Một pattern dùng bốn sites khác nhau: F+,F-,S+,S-. Thu
`Z_m = (V_S+ - V_S-) / I_F` complex cùng frequency. Force +/- là quy ước AC,
không phải cathode/anode DC cố định. Current field phân bố trong 3D, không
giới hạn trong đường thẳng giữa electrodes. [E:S1]

**Candidate P12 [P,V]:** 12 cấu hình dưới đây sử dụng đủ 24 contacts. Mục
đích là có ipsilateral, bilateral và upper/lower comparisons với scan ngắn.
Đây không phải tập patterns đã được optimize hoặc proven trên mặt.

| Pattern | F+ | F- | S+ | S- | Family |
|---|---|---|---|---|---|
| P01 | L4 | L10 | L7 | L9 | Left lower-face |
| P02 | R4 | R10 | R7 | R9 | Mirrored right |
| P03 | L6 | L12 | L8 | L11 | Left lateral/submental |
| P04 | R6 | R12 | R8 | R11 | Mirrored right |
| P05 | L1 | L7 | L3 | L5 | Left upper/lateral |
| P06 | R1 | R7 | R3 | R5 | Mirrored right |
| P07 | L2 | L10 | L4 | L8 | Left upper/lower |
| P08 | R2 | R10 | R4 | R8 | Mirrored right |
| P09 | L7 | R7 | L10 | R10 | Bilateral lower-face |
| P10 | L4 | R4 | L9 | R9 | Bilateral lateral/lower |
| P11 | L6 | R6 | L11 | R11 | Bilateral posterior/submental |
| P12 | L1 | R1 | L12 | R12 | Bilateral upper/lower |

P12 must pass **all**: physical mapping, load tests, adequate measurable
transfer voltage, correct settling/current readout, frame timing, and lab
approval of each human current path. Near-zero/noisy patterns are not useful
just because they cover a site. If rejected/replaced, version the manifest
before primary data; never hide a substitution after inspecting task accuracy.

P12 intentionally is a **small initial observation panel**, not maximum
information from 24 contacts. A negative result applies to this layout,
pattern set, frequency and tasks, not all facial BioZ. If time budget allows,
add a predeclared complementary panel in a separate exploratory run. Do not
concatenate different task repetitions into one purported simultaneous frame.
Offline electrode-subset results from P12 alone have limited optimization
scope; a later broader configuration pool will usually be needed.

Reciprocal Force/Sense-swapped pairs can help **bench/static QC**; compare
calibrated transfer impedances, not unnormalized voltages under different
drive currents. Do not count them as independent anatomy measurements or
expect identical readings across a changing human task.

### 3.1 Timing target [P,V]

- Aim for **complete frame <= 0.25 s**, equivalently at least 4 full frames/s.
- This is derived from wanting approximately 12 complete observations in the
  3 s plateau below, **not** a literature-proven optimal rate or a real-time
  speech/IPG specification. Window boundaries and gaps can reduce the count.
- Log actual start/end per configuration. Use only complete frames inside
  the analysis window; do not pretend sequential channels are simultaneous.
- If P12 is too slow, fix communication/settling implementation without
  compromising accuracy, or redesign the panel/protocol before human data.
  Do not quietly stretch holds or combine rest and task measurements.
- The cyclic adjacent 24 x 21 = 504 protocol is not a mandatory facial
  protocol. At a hypothetical 20 ms/config it would take 10.08 s/frame.
  This arithmetic is not a measured CN0565 benchmark.

## 4. Study design: one-person engineering pilot with remounting

### 4.1 Participants and sessions [P]

Start with **one consenting healthy adult** under the lab's approved process,
potentially the user. One person is for debugging and within-person feasibility,
not healthy population inference, participant-level ICC or dysarthria claims.

| Run | When / attachment | Question |
|---|---|---|
| A1 | Day A, first mounting | Are signals measurable and task-linked? |
| A2 | Day A, all cups removed and reapplied using placement record | Do patterns survive redonning? |
| B1 | A different day, fresh mounting | Is there cross-day repeatability? |

Record elapsed time and actual recovery/skin condition. These **two days,
three mountings [P]** are chosen to expose two practical failure modes with
limited burden, not established sufficient sample size. If tissue/skin has
not recovered or participant fatigued, do not force the next run.

A1/A2 can be development/diagnostic runs. Freeze preprocessing and classifier
choices before B1. If the setup changes after A1, A2/B1 are not clean repeats
of the original setup: assign a new version. B1 loses held-out status if its
labels/results are used to tune; record that rather than calling it validation.

### 4.2 Core conditions: five labels, five trials each per run [P]

| Label | Instruction at comfortable, repeatable effort | Why choose it / what source proves |
|---|---|---|
| REST | Stay in the practiced relaxed neutral pose through the task cue | Negative/cue control [P]; not just a baseline before every action |
| PURSE | Purse lips, no whistling, avoid deliberately clenching jaw | [E:S2 T14] orbicularis-oris-dominant among sampled muscles, not isolation |
| SMILE_L | Voluntary smile on participant's left side; video verifies | [E:S2 T23] lateralized task; does not prove a single muscle |
| SMILE_R | Mirror on participant's right side | [E:S2 T22]; tests laterality and possible attachment asymmetry |
| PUFF_BOTH | Comfortable bilateral cheek puff; no forceful straining | [E:S3] direct facial BioZ precedent; [E:S2 T15]. Secondary air/geometry-rich task, not muscle-specific positive control |

Rehearse each action with demonstration and correction before recording,
following the task-atlas approach [E:S2]. Do not rename a bilateral smile as
successful unilateral smile. Failed/mixed tasks get a label from video and
are reported. Stop puff/other holds if uncomfortable; no prolonged forced
breath holding. Leave vowels, maximal clench and the full 19-label set for
later, after acquisition and reproducibility are understood.

Five blocks per run; every block includes each of the five labels once,
in a pre-generated random order saved in the design manifest. This gives
five trials per label without a long fixed task-order confound. Randomization
is a design choice, not a guarantee that fatigue/carryover disappears.

### 4.3 Trial timing [P], conditional on Section 3.1

Each trial has **5 s pre-rest + 5 s task + 5 s post-rest = 15 s**.

- The pre-rest is actually measured with the same drive/sense settings.
- Keep raw onset and offset, even though the primary feature uses a plateau.
- Adjacent trials therefore have **10 s between active periods** (post-rest
  + next pre-rest), not the user's original 5 s inter-repetition rest. This
  is an explicit proposed revision to obtain local reference and recovery data.
- Suggested analysis baseline: last 3 s of pre-rest. Suggested task plateau:
  seconds 1-4 after independently annotated actual action onset, wholly inside
  the task period. A trial without a valid 3 s plateau is flagged, not filled
  with invented/interpolated data. REST uses the equivalent cue-aligned window.
- This 3 s trimming rule is [P]: it avoids transition mixing; it is not proof
  that every person reaches steady state after exactly 1 s.
- Extend rest when needed and log the extension. Do not force a task because
  the timer ended. If baseline cannot stabilize, pause/review rather than
  remove the trend invisibly in processing.

### 4.4 Nuisance/control block [P]

After core trials, collect three repetitions each of:

1. **Gentle head turn and return**, face otherwise neutral, within comfortable
   range agreed by the lab. Video records actual motion; this is a composite
   head/neck/contact/lead-motion challenge, **not pure electrode artifact**.
2. **Gentle jaw opening with lips closed**, within comfortable achievable range.
   Atlas T18 supports it as a reproducible task instruction [E:S2]; it includes
   muscle activation and geometry change, so it is **not a no-muscle control**.

Same nominal 5/5/5 s timing. Controls are analyzed separately, not silently
added to a five-class primary classifier. Similarity to target patterns flags
ambiguity; dissimilarity does not prove muscle-source isolation.

Pure lead/contact perturbations should first be tested on the static phantom,
not by pressing facial arteries or manually distorting a participant's face.
Spontaneous swallow, blink, breath changes and cup/lead adjustments are logged
as events. Do not remove every vascular component by an arbitrary filter.

### 4.5 Run duration, derived not borrowed

- Initial quiet rest recording: **60 s [P]**, after contact has stabilized.
- Core trials: 5 labels x 5 repetitions x 15 s = **375 s**.
- Four between-block breaks: 4 x **30 s [P]** = **120 s**.
- Break before control block: **30 s [P]**.
- Controls: 2 conditions x 3 repetitions x 15 s = **90 s**.
- Total nominal recording/run = **675 s = 11 min 15 s**.
- Three runs = **33 min 45 s** recorded, excluding fitting, safety checks,
  rehearsal, mounting/remounting, extra recovery and failed trials.

Durations are workload planning, not mandatory uninterrupted exposure or
proof of adequate physiological recovery. Save all trials. One replacement
trial per label/run at most [P] may be collected for a predefined technical
failure; do not repeat until a desired signal appears. Report original and
replacement separately, and do not replace a valid no-response trial.

## 5. Thu gì? Minimum dataset, not just a heatmap

| Data | Required? | Purpose / provenance |
|---|---|---|
| Calibrated complex Z, real+imaginary, per configuration | Primary target; verify mode/units first | Preserve both amplitude and phase [E:S6,S7] |
| Raw voltage/current or raw instrument output when exposed | Save what the validated interface exposes; do not invent missing channels | Audit drive stability, calibration and clipping [E:S1] |
| Measurement start/end, frame ID, pattern ID, F+/F-/S+/S- | Yes | Detect temporal mixing/mapping mistakes |
| Frequency, excitation setting, measured-current info, gain/RTIA, settling/DFT settings, firmware/library versions | Yes, available fields with explicit unavailable markers | Voltage excitation is not constant-current excitation [E:S1] |
| Cue, actual task onset/offset, trial/run/day IDs, deviations | Yes | Separate instructed action from actual execution |
| Synchronized face video + view of attachment/lead movement | Yes for this design | Check task/laterality/head/jaw motion; not direct muscle-activation ground truth |
| Site photos/coordinates, cup/gel/fixation/lead mapping | Yes | Reproducibility and redonning interpretation [E:S4-S6,S11] |
| Comfort/skin/contact/technical events and rejected-data reasons | Yes | Feasibility and quality, not only successful trials |
| Facial/auricular sEMG, PPG or motion sensor | Optional later, with compatibility review | Stronger mechanistic validation; not needed to label task recognition in this first pilot |

Video candidate **30 fps [P]** gives approximately 33 ms nominal frame
spacing, finer than a 250 ms impedance frame. Verify actual timestamps,
variable-frame-rate behavior, synchronization offset and drift. A visible
cue marker recorded with acquisition time can establish alignment; simply
pressing Record in two apps does not demonstrate synchronization.

CN0565 and an EMG device must not be interconnected on a participant by
guessing their grounds. [S4] observed interference with EEG/chin EMG; [S8]
used a specifically designed simultaneous setup. For the minimal pilot,
BioZ plus video is simpler. Without EMG/source validation, limit conclusions
to task-associated impedance, not electrical muscle activation or pure EMG.

Face video is identifying data: use approved consent/storage/access rules,
pseudonymous IDs in data tables and no unconsented image publication.

Suggested records (formats need not be CSV): `session_metadata`,
`electrode_map`, `measurement_patterns`, `raw_measurements`, `events`,
`trial_quality`, `video_sync`, `calibration_results`, and an immutable raw
data copy. Protocol manifest contains definitions, **not observed data**.

## 6. Analysis: câu hỏi có thể trả lời được

### 6.1 First plots and trial features [P]

For each pattern m and trial r, calculate the complex baseline from the
predefined pre-rest window: `b[m,r] = mean(Z[m,t] in pre-rest window)`.
Then `dZ[m,t] = Z[m,t] - b[m,r]`.

Keep raw and difference together. Primary trial feature: mean real and mean
imaginary dZ in the valid plateau, giving **24 numbers for P12**. Twelve
measurements is not twelve electrodes; 24 real-valued features is not 24
independent anatomical sources. Optionally display magnitude and circular
phase differences, but do not subtract wrapped phase naively. Relative
normalization needs a predeclared denominator/noise-floor check; raw dZ is
the initial primary representation to avoid division near zero.

Produce, in this order:

1. Raw real/imaginary traces with task/rest and dropout markers.
2. Per-pattern rest noise/drift, frame timing and quality summaries.
3. Aligned repetitions of dZ for each task, showing **all trials**, not only
   the best channel or repeat.
4. Pattern-by-time heatmap; axes are measurement patterns and time, **not
   anatomical face coordinates**.
5. Trial-pattern comparison for REST, target tasks and nuisance controls,
   then A1 versus A2 versus B1 with identical scales.

Rest subtraction does not isolate muscle: geometry/contact can change
[E:S5], airway/air volume can produce EIT contrast [E:S4], and vascular
mechanics can contribute facial IPG [E:S8]. Fixed bone still influences
sensitivity. A null pattern can mean insufficient sensitivity/noise/poor
task execution; it does not diagnose a nonfunctioning muscle.

### 6.2 Optional classifier, deliberately secondary

Start with one feature vector per complete trial. Use a simple training-only
scaled nearest-centroid classifier [P] before complex models. Inspect whether
A1 predicts A2; lock final settings using A1/A2 before testing B1 once. Report
confusion matrix, macro-F1, balanced accuracy and all trial counts. Five
balanced classes give **20% expected accuracy for uniform random guessing**,
not a significance threshold or a guaranteed null for biased data.

No random splitting of overlapping windows from the same trial. No feature,
channel, frequency or electrode selection on B1. Pre-task normalization
within a test trial can be allowed if declared as required deployment
calibration; do not then claim calibration-free recognition. [S12] shows
the risks of dependent-window evaluation in a different wearable modality.

With one participant, results are descriptive and within-person. Do not
report population confidence from thousands of frames as if they were people.
No participant-level ICC with n=1. Selection of fewer electrodes is later:
retain a pattern only if all four contacts are in the retained subset, select
on development data, then validate by physically re-recording reduced layout.

## 7. Progression criteria: không chọn sau khi nhìn kết quả

This pilot is not an efficacy trial. The principle of explicit feasibility
objectives/progression criteria is supported by [S13], with the limitation
that its checklist concerns randomized pilot trials, not this sensor study.

| Gate | Decision rule for this pilot | If it fails |
|---|---|---|
| Safety / authorization [V] | Lab confirms setup, exposure settings/current paths, participant process | Bench only; do not start human exposure |
| Instrument validity [V] | All 24 paths mapped; known-load response/sign/units verified; no unexplained saturation, dropouts or switching transients | Fix acquisition, not classifier |
| Timing [P] | Chosen panel supports <=0.25 s frame target; enough complete frames wholly within baseline and plateau | Revise panel/protocol and version it before primary human runs |
| Protocol feasibility [P] | At least 4 of the 5 originally scheduled trials usable per label/run; failures judged from execution/technical QC, not signal amplitude | Revise task/fixation; show missingness, no performance claim for failed labels |
| Signal feasibility [P] | At least one core motor task has a task-associated pattern distinguishable descriptively from REST variation, present in at least 4/5 technically valid scheduled trials in development; nominate and freeze its pattern/sign/summary before B1 | No task-information claim; reassess placement/pattern/frequency/contact within approved scope |
| Repeatability [P] | Frozen candidate has consistent direction/pattern in A2 and B1 and task response still exceeds observed REST variability in those runs | Report remount/day failure; do not conceal with within-session accuracy |
| Confound interpretation [P] | Compare candidate with head/jaw controls and video; if similar, explicitly restrict interpretation | Task recognition may remain possible, muscle-specific interpretation does not |

For the exploratory signal gate, define “exceeds observed REST variability”
as a descriptive plot/summary against the **range of valid REST-trial
features**, not a p-value. Nominate a signed pattern/projection using A1/A2
only and preserve the same scaling on B1. Five REST trials give an uncertain
range; crossing it is a reason to proceed to a larger study, **not statistical
proof**. If several candidates are explored, report how many. The 4/5 rule
is an 80% engineering consistency target [P], not a validated clinical cutoff.

**Green:** safe valid acquisition, a repeatable candidate signal, and feasible
protocol -> design a multi-person study with participant/session-level
evaluation. **Amber:** within-mount response but failure after redonning or
poor controls -> revise attachment/measurement design. **Red:** invalid
electronics/safety or no response under this configuration -> do not add
model complexity to hide the failure. Absence here does not refute all EIT.

## 8. Numbers and provenance ledger

| Number / choice | Status | Rationale, source and limit |
|---|---|---|
| 24 contacts | [E + user] | Hardware maximum [S1], prof's exploratory plan; not optimal facial count |
| Gold cups | User + [V] | Existing equipment; material alone does not establish active-BioZ suitability |
| 12 sites/side and C24 allocation | [P] | Symmetry/allowed-site coverage; no paper validates exact coordinates |
| P12, 12 measurements/frame | [P,V] | A short observation panel using all 24; not reconstruction completeness or optimal information |
| 20/50/100 kHz bench; 50 kHz candidate human | [P,V] | Precedents [S1,S3,S4]; freeze only after validation/review, not optimum claim |
| Human current/amplitude | [V], unset | Requires complete-system assessment; not copied from literature |
| >=4 full frames/s target | [P,V] | Approximately 12 samples in 3 s static plateau; not speech-onset/IPG specification |
| One adult, two days, three mountings | [P] | Debug, remount, cross-day checks; no population power |
| Five conditions x five repetitions | [P] | Small balanced pilot workload; task identities supported by [S2,S3], counts are not |
| 5/5/5 s and 3 s feature windows | [P] | User's starting hold length plus explicit local rest/recovery; validate execution/settling |
| 60 s initial rest; 30 s block breaks | [P] | Observe baseline and allow recovery; not proven sufficient for all subjects |
| Three repetitions/control | [P] | Qualitative nuisance challenge, not power for causal separation |
| 30 fps video | [P,V] | Nominal timing finer than impedance frame; actual sync must be measured |
| 4/5 usable/consistent target | [P] | Practical 80% progression criterion, not clinical/statistical threshold |
| 11 min 15 s/run | Derived | Arithmetic from the specified schedule, excludes fitting/extra recovery |

## 9. Sources: what each contributes, and what it does not

**S1. Analog Devices CN0565.**
https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/CN0565.html
Local `cn0565 rev. a.pdf`; schematic `02_066534 Rev B`, sheet 2/3, in
`cn0565-designsupport/`. Supports switch architecture, excitation/current
measurement, calibration/isolation and connector mapping. Does not validate
the human setup or C24 layout.

**S2. Schumann et al., 2021. Atlas of voluntary facial muscle activation.**
https://doi.org/10.1371/journal.pone.0254932
Table 1 and methods inspected; 30 men, 29 tasks, facial sEMG. Supports
instructions and dominant sampled muscle patterns, not isolation or this
BioZ timing/layout. Local `papers/tasks/journal.pone.0254932.pdf`.

**S3. Liu et al., 2025. Facial Gesture Recognition Using Bio-impedance Sensing.**
https://doi.org/10.1145/3745900.3746120
Full supplied three-page PDF. Four participants, three wet contacts at
below-mouth/cheeks, two channels, puff/suck recognition; reported 100 kHz and
20 Hz sampling. Not remote placement, 24-channel timing or cross-day proof.

**S4. Kim et al., 2019. Real-Time Identification of Upper Airway Occlusion
Using Electrical Impedance Tomography.**
https://doi.org/10.5664/jcsm.7714
https://pmc.ncbi.nlm.nih.gov/articles/PMC6457513/
Local full text inspected. Anatomy-linked 16-electrode layout, MRI and later
PSG comparisons; motion and EMG/EEG interference discussed. Airway target,
different hardware/contacts. Does not justify copying excitation or placement.

**S5. Boyle & Adler, 2011. Impact of Electrode Area, Contact Impedance and
Boundary Shape on EIT Images.**
https://aboyle.ca/pubs/boyle2011a-elec_mvmt.pdf
FEM/CEM difference-EIT evidence that contact/area/boundary changes can create
artifacts. Supports nuisance tests, not their exact amplitude on the face.

**S6. Schooling et al., 2020/2021. Modelling and analysis of electrical
impedance myography of the lateral tongue.**
https://doi.org/10.1088/1361-6579/abcb9b
Local full-text extraction inspected. Layered anisotropic model, clinical
spectra, placement/contact and reliability. Supports complex data and
reapplication checks; does not establish facial phase immunity to artifacts.

**S7. Kusche et al., 2024. A Wearable Dual-Channel Bioimpedance Spectrometer
for Real-Time Muscle Contraction Detection.**
https://doi.org/10.1109/JSEN.2024.3359284
Local full text inspected. Device/phantom characterization and forearm
complex multifrequency measurements. Supports bench-first and retaining
phase; not equivalent CN0565 speed or validated single-frequency facial sensing.

**S8. Levit et al., 2024. Soft electrodes for simultaneous bio-potential and
bio-impedance study of the face.**
https://doi.org/10.1088/2057-1976/ad28cb
Local full text inspected. Four healthy volunteers, dedicated IPG/sEMG
setup and vascular interpretation. Not proof that all task-linked change is
vascular or that the devices available here are mutually compatible.

**S9. Rüschenschmidt et al., 2022. Ear-muscle EMG study.**
https://doi.org/10.3390/diagnostics12010121
Local `papers/tasks/diagnostics-12-00121.pdf`. Supports local auricular
co-activation as a confound; not facial BioZ sensitivity evidence.

**S10. Hyvönen, Seppänen & Staboulis. Optimizing Electrode Positions in EIT.**
https://doi.org/10.1137/140966174
https://arxiv.org/abs/1404.7300
Model/prior-specific position optimization, 2D numerical experiments.
Supports geometry/ROI-dependent design; supplies no ready-made facial layout.

**S11. Kurniawan et al., 2022. Electrochemical performance study of Ag/AgCl
and Au flexible electrodes for unobtrusive monitoring of human biopotentials.**
https://doi.org/10.1002/nano.202100345
Primary abstract evidence for material/diameter/frequency dependence, not
the specific gold cups, skin contacts or high-frequency performance here.

**S12. Dehghani et al., 2019. A Quantitative Comparison of Overlapping and
Non-Overlapping Sliding Windows for Human Activity Recognition Using Inertial Sensors.**
https://pmc.ncbi.nlm.nih.gov/articles/PMC6891351/
https://doi.org/10.3390/s19225026
Methodological transfer: dependent-window splits can overestimate wearable
recognition performance; not a facial BioZ result.

**S13. Eldridge et al., 2016. CONSORT extension for randomized pilot and
feasibility trials.**
https://doi.org/10.1136/bmj.i5239
https://link.springer.com/article/10.1186/s40814-016-0105-8
Use only the methodological principle of feasibility objectives and declared
progression criteria. This non-randomized sensor pilot is not a CONSORT RCT.

## 10. Before-run sign-off sheet

- [ ] Protocol/layout/pattern version and frozen trial order recorded.
- [ ] Cup model/size/paste, nonoverlapping fit and site mapping recorded.
- [ ] Lab human-use/electrical review complete; authorized operator identified.
- [ ] Human frequency/amplitude/current limits filled from review, not from AI.
- [ ] Calibration, 24-path mapping, pattern quality and frame timing passed.
- [ ] Raw data schema and all clocks/synchronization verified.
- [ ] Participant consent/screening, privacy/storage and stopping procedure set.
- [ ] Tasks rehearsed; exclusions/failures/replacements defined before looking at responses.
- [ ] A1/A2/B1 roles and held-out restrictions agreed with the professor.

An unfilled safety/measurement field means the human protocol is not ready;
it does not block completing the bench work or reviewing this study design.
