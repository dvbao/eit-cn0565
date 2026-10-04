# Facial bioimpedance: prior work, tissue models, electrode placement, và novelty

Ngày rà soát: 2026-10-02. Dành cho dự án CN0565 của Bao Dang.

Đây là targeted literature review, không phải systematic review/PRISMA hay
chứng nhận "first-ever". Không chạy thí nghiệm người, không thay đổi simulator
hoặc hardware. Các thiết kế dưới đây là đề xuất nghiên cứu, chưa phải kết quả.

**Cập nhật 2026-10-02:** user dùng **16 electrodes mỗi phiên** cho
**hai phiên riêng**: D16-M gần/trên vùng cơ làm comparator và C16-R remote
unobtrusive. [Pilot 01](facial-bioimpedance-pilot-01.md) có ma trận
task–muscle theo Table 1 của Schumann 2021, layout D16-M ứng viên và C16-R
với panel 8 phép đo M08. D16-M **chưa có measurement patterns**;
cả hai chưa qua bench/human-use review.
[Bản C24/P12](archive/facial-bioimpedance-pilot-01-24-v0.1.md) chỉ là lịch sử.
Đang làm rõ placement, hardware validation và study details trước khi chốt.
Không dùng các proposal trong review như kết quả đã chứng minh.

## 1. Kết luận cho đúng bài toán hiện tại

Người dùng đã chốt: **paper đầu tiên là task recognition với unobtrusive
placement**. Đánh giá từng cơ và post-stroke dysarthria là hướng dài hạn.

1. Không đúng nếu nói chỉ có một công trình về facial bioimpedance. Ngoài Liu
   2025 còn facial EIM, Painometry, preliminary facial EIT và nghiên cứu liên quan
   ở mặt dưới/cổ. Tuy nhiên chúng không giải quyết cùng một bài toán.
2. Không tìm thấy trong các nguồn đã kiểm tra một nghiên cứu xác nhận đầy đủ
   tổ hợp: tasks tự tạo bằng mặt, tránh anterior target-muscle regions, và
   recognition ổn định qua nhiều buổi/tháo-gắn lại với đúng layout của bạn.
   Đây là **candidate gap**, không phải bằng chứng không có paper nào khác.
3. Vài tasks có thể là scope hợp lý. Giá trị không nằm ở "ít tasks cũng được"
   mà ở constraint có ý nghĩa, so sánh công bằng và bằng chứng generalization.
4. Không cần EIT image reconstruction để làm paper task recognition. Nếu chỉ
   đo nhiều kênh impedance rồi classify, gọi là **multichannel bioimpedance
   sensing**; không dùng heatmap để ngầm claim muscle imaging.

**Phân tầng mục tiêu (editorial verdict):** Paper A về task recognition với ít
electrodes là một hypothesis có precedent trực tiếp và mức khả thi *trung bình,
có điều kiện*. Paper B về 3D **coarse region-of-interest (ROI) difference EIT**
có precedent gần mặt/cổ nhưng layout tránh phần trước mặt là bài toán coverage
khó; mức khả thi *chưa rõ/cao rủi ro*. Bước xa hơn — gọi tên từng cơ yếu hay gán
"yếu X%" từ 3D image — là claim **khác Paper B**, rủi ro rất cao, cần
muscle-specific và clinical ground truth. Tăng electrode count không tự biến
Paper A thành hai claim sau. Chi tiết proof gates ở Sections 11–16.

Working English question:

> Can electrodes outside anterior facial target-muscle regions recognize a
> small set of facial tasks reliably across sessions and electrode reapplication?

"Outside target regions" không có nghĩa là electrodes nằm ở nơi không có cơ.
Tai/hàm/trán có tissue và cơ riêng; tín hiệu có thể chứa các vùng đó.

## 2. Evidence map: cái gì thực sự đã được làm?

Các source cards dùng English để dễ đưa vào related work. Phân biệt rõ modality,
target và mức evidence; không cộng tất cả thành "facial muscle EIT".

### 2.1 Liu et al., 2025: prior gần nhất về facial task recognition

**Facial Gesture Recognition Using Bio-impedance Sensing**, AHs 2025, 491-493.
[DOI](https://doi.org/10.1145/3745900.3746120).
Full three-page PDF supplied in `EIT related works/`; all pages inspected.

- Three **wet electrodes**: the paper explicitly calls the below-mouth contact
  the stimulus electrode and the two cheek contacts measurement electrodes;
  two BioZ channels. It does not provide a detailed wiring schematic proving
  the exact return, sense, bias or multiplexing topology. Do not label the
  cheek contacts current-free sense-only electrodes or assume Ag/AgCl material.
- Four participants; left puff, right puff, omni puff and suck. The conclusion
  also mentions a null class. One introductory "three" is inconsistent with
  the four named gestures; do not silently adopt it.
- AD5941/ESP32; reported excitation 100 kHz and 100 mV peak-to-peak; sampling
  20 Hz. These describe that apparatus, NOT a human-use recipe for CN0565.
- Random Forest, 100 trees; 20-sample overlapping windows, approximately 1 s;
  peak replacement by the mean; an 80/20 training/test split.
- Table 1 reports mean accuracy 0.93 and mean macro F1 0.92 across four subjects.
- No tomography, separate-muscle validation, stroke cohort, or explicit
  leave-one-subject/session-out demonstration. The overlapping-window split
  lacks grouping detail, creating possible leakage; leakage is not established.
- Authors attribute puff/suck changes partly to oral air. Their interpretation
  is not an experiment isolating muscle conductivity from geometry/contact.

**Hệ quả cho mình:** benchmark gần nhất là task-related impedance recognition,
không phải muscle activation %. Không lấy 93% này so trực tiếp với cross-session
accuracy của mình: population, tasks, splits và metrics phải tương thích.
Paper chưa chứng minh trong chính study này rằng BioZ luôn ít motion artifacts
hơn EMG, dù có lập luận như vậy trong introduction.

### 2.2 Painometry, Truong et al., MobiSys 2020

**Painometry: Wearable and Objective Quantification System for Acute
Postoperative Pain.** [Author PDF](https://people.cs.umass.edu/~phuc/papers/Painometry_2020.pdf),
[DOI](https://doi.org/10.1145/3386901.3389022).

Full methods and Figure 4 inspected. Sweep Impedance Profiling uses two contacts
per corrugator supercilii region, four for bilateral sensing, near the eyebrows/
glabella. Its simplified circuit includes skin-contact and overlying-tissue
contributions. The 23-person evaluation is multimodal pain estimation, combining
SIP with EEG, PPG and GSR; aggregate accuracy is not facial-gesture or SIP-only
accuracy. This is direct facial impedance prior art, but not remote jaw/ear
recognition. Its local equivalent circuit is not a validated whole-face model.

### 2.3 Statland et al., 2016: facial EIM trong FSHD

**Electrical Impedance Myography in Facioscapulohumeral Muscular Dystrophy.**
[Original article](https://pmc.ncbi.nlm.nih.gov/articles/PMC4972708/),
[DOI](https://doi.org/10.1002/mus.25065).
Full local PDF: `EIT related works/EIM in Facioscapulohumeral.pdf`.

Handheld EIM measured bilateral orbicularis oris, using a smaller probe suitable
for the face. Thirty-five patients participated; eighteen returned for retesting.
Facial reliability was asymmetric: right-side ICC <0.5 versus left 0.84-0.91,
with operator order/learning, hair and smaller sensors discussed as limitations.
Figure 1D shows direct facial placement. This supports facial EIM precedent,
not unobtrusive gesture recognition or a stroke-related impairment percentage.

### 2.4 Visentin, 2017: direct facial EIT proof of concept

**An Electrical Tomographic Approach to Detect Deformation over Soft and
Flexible Materials**, PhD thesis, Chapter 6.3, printed pp. 55-57.
[University repository PDF](https://tsukuba.repo.nii.ac.jp/record/43368/files/DA08090.pdf).

Eight electrodes on one side of one volunteer's face, including anterior sites,
were used with exaggerated vowels and smiling. A and smile yielded the clearest
patterns. Deformation/electrode displacement was part of the sensing mechanism.
Dissertation proof of concept, not a validated classifier or individual-muscle map.
Placement figure and relevant section inspected in the earlier review.

### 2.5 Levit, Funk & Hanein, 2024: facial BioZ có vascular information

**Soft electrodes for simultaneous bio-potential and bio-impedance study of the
face.** [PubMed](https://pubmed.ncbi.nlm.nih.gov/38350124/), DOI 10.1088/2057-1976/ad28cb.

Soft arrays combine facial biopotential recordings and temporal-region
impedance plethysmography. Relevant to validation and vascular contributions,
not evidence that remote impedance isolates one facial muscle. Abstract and
available author text checked; no new numerical performance claim made here.

### 2.6 Kim et al., 2019: EIT ở mặt dưới, placement theo anatomy

**Real-Time Identification of Upper Airway Occlusion Using Electrical Impedance
Tomography.** [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC6457513/),
DOI 10.5664/jcsm.7714.

Sixteen electrodes followed lower-face/neck landmarks selected using MRI to
intersect the retroglossal airway. Feasibility involved simultaneous MRI/EIT;
later reconstruction used scanned boundary geometry and a cheek reference.
Target: airway air-volume change, not facial-muscle tasks. This is a useful
placement-justification precedent, not this project's unobtrusive layout.
Simultaneous EEG/chin EMG suffered interference, relevant to planning combined
recordings. Indexed original methods and figure captions checked.

### 2.7 Các nguồn liên quan nhưng không nên gộp sai

| Source | Evidence actually relevant | Not established |
|---|---|---|
| [McIlduff et al., 2016, Face and Neck EIM normative values](https://doi.org/10.1212/WNL.86.16_supplement.P6.266) | Meeting abstract metadata verified | Full methods, normative numbers and task recognition not verified |
| [iFace, 2024](https://arxiv.org/html/2403.18433v1) | Shoulder BioZ detects hand-face contact, changing conductive paths | Facial-muscle contractions without hand contact |
| [FaceSense, 2021](https://people.cs.umass.edu/~phuc/papers/facesense_2021.pdf) | Ear-worn face-touch system including contact-impedance sensing | Remote muscle conductivity tomography |
| [Piccin et al., 2023, neck EIT](https://www.frontiersin.org/journals/sleep/articles/10.3389/frsle.2023.1238508/full) | 32 electrodes in two circumferential bands, CT-derived 3D model; airway target | Ear-only or partial-ring facial-task validation |
| [Briko et al., 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12694238/) | Superficial head microcirculation BioZ | Facial gesture classification or isolated muscle activation |
| [From Neck to Head, 2025](https://arxiv.org/abs/2507.12884) | BioZ head-pose estimation, adjacent application | Lip/cheek task recognition; abstract-level screening here |
| [US5772605A, 1998](https://patents.google.com/patent/US5772605A/en) | Patent describes facial movement/symmetry via injected-field impedance | Peer-reviewed performance or clinical validation; no legal opinion implied |

Exclusions to keep the review honest: electrode impedance measured only to
validate an EMG sensor is not a BioZ task-recognition experiment; capacitive/
electric-field sensing is not automatically galvanic EIT; body-composition BIA
correlated with masseter thickness is not localized facial EIM. Secondary papers
occasionally use loose modality labels, so inspect the cited primary method.

`iMove` and `iEat` in the supplied folder also should not both be described as
"arm-muscle models": activity-related geometry and additional conductive paths
through contact can matter. A useful classifier need not isolate one muscle.

## 3. Model: cơ mặt có intracellular/extracellular không?

Có. Các facial skeletal muscles vẫn có tế bào cơ, **intracellular fluid** ở
trong, **extracellular fluid** ở ngoài và **cell membrane/sarcolemma** ngăn cách.
Không cần một loại vật lý mới chỉ vì cơ nằm ở mặt. Cần phân biệt model của
**vật liệu tissue** với model của **cả vùng anatomy và electrodes**.

### 3.1 Equivalent circuit: mô tả tissue phản ứng theo frequency

Hình 1 của Kusche et al. 2024 trong folder là điểm bắt đầu tốt:
[DOI](https://doi.org/10.1109/JSEN.2024.3359284).
Full local PDF, printed p. 11318, Figures 1-3 inspected.

Một model tối giản (đổi ký hiệu để dễ hiểu) gồm hai nhánh song song:

- Nhánh ngoài tế bào: resistance \(R_e\).
- Nhánh đi qua màng và vào trong: capacitance \(C_m\) nối tiếp resistance \(R_i\).

\[
Z(\omega)=\left[\frac{1}{R_e}+
\frac{1}{R_i+1/(j\omega C_m)}\right]^{-1},\qquad \omega=2\pi f.
\]

\(R_e,R_i\) có đơn vị ohm; \(C_m\) là farad; \(f\) là Hz; \(j^2=-1\).
Đây là **effective circuit** đại diện hành vi điện, không phải vẽ một dây điện
thật chạy qua từng tế bào. Màng có cả leakage và cấu trúc phức tạp; model này bỏ
qua các chi tiết đó để giải thích một dispersion đơn giản.

Ở frequency thấp, nhánh capacitor cản mạnh: \(Z\to R_e\).
Ở frequency cao trong giới hạn lý tưởng của circuit, nhánh trong cũng tham gia:
\(Z\to R_e\parallel R_i\), KHÔNG phải chỉ còn intracellular fluid.
Không có một frequency cố định chia "ngoài" và "trong" cho mọi tissue/người.

Một mô tả phổ rộng hơn là Cole-type model:

\[
Z(f)=R_\infty+\frac{R_0-R_\infty}{1+(j2\pi f\tau)^\beta},
\quad 0<\beta\le1.
\]

- \(R_0,R_\infty\): hai giới hạn của model.
- \(\tau\): characteristic time, quyết định vị trí chuyển tiếp theo frequency.
- \(\beta\): độ rộng/phân tán của chuyển tiếp. Một số papers dùng \(1-\alpha\)
  thay cho \(\beta\); phải đọc convention trước khi copy giá trị.

Với simple circuit ở trên, \(R_0=R_e\) và \(R_\infty=R_e\parallel R_i\).
Với cả mặt nhiều lớp, fitted Cole parameters không tự động là intracellular/
extracellular resistance của riêng zygomaticus. Một frequency cho một complex
measurement chỉ có hai số thực: không đủ tự xác định ba hay nhiều unknowns
nếu không thêm constraints. Multifrequency thêm thông tin, không bảo đảm uniqueness.

### 3.2 Có model gần mặt/bulbar region đã được làm không?

**Schooling et al., Modelling and analysis of electrical impedance myography of
the lateral tongue**, Physiol. Meas. 41 (2020), 125008; online January 2021.
[Author PDF](https://eprints.whiterose.ac.uk/169988/1/Schooling_2020_Physiol._Meas._41_125008.pdf),
[DOI](https://doi.org/10.1088/1361-6579/abcb9b).

Methods/Figures 1 and 5 inspected. A layered, anisotropic tongue FEM was fitted
using multifrequency data from 41 ALS patients and 30 controls, then related to
a Cole-based lumped circuit. This connects anatomical geometry with intra-/
extracellular and capacitive interpretations. It is not a model of facial
expression or post-stroke contraction. Do not transplant its fitted parameters
into cheek muscles without validation; approximately 9,000 spectra are not
9,000 participants.

**Trả lời chính xác:** đã có local facial equivalent-circuit approaches và
anatomical/bulbar models. Chưa xác nhận được một off-the-shelf, validated model
đủ skin-fat-facial muscles-vessels-air cavities-contact, dự đoán các tasks bằng
đúng ear/jaw layout này. "Chưa có model trọn gói đã xác nhận" khác với "không
có model nào".

### 3.3 Anatomical forward model: trả lời placement đo vùng nào

Trong một model 3D, chia anatomy thành các tissue regions rồi gán complex
admittivity \(\gamma(\mathbf x,\omega)=\sigma+j\omega\varepsilon\).
\(\sigma\): conductivity, S/m; \(\varepsilon\): permittivity, F/m; \(u\): potential.
Với muscle anisotropy, \(\gamma\) có thể là tensor, nghĩa là dẫn khác nhau theo
hướng fiber. Forward solver giải dạng quasi-static:

\[
\nabla\cdot[\gamma(\mathbf x,\omega)\nabla u]=0.
\]

Electrodes cần boundary conditions và contact model. **Complete Electrode Model
(CEM)** mô tả contact hữu hạn và electrode-skin impedance, thay vì chỉ một point.
Nguồn cho electrode-model/design framework:
[Hyvönen, Seppänen & Staboulis, 2014](https://arxiv.org/abs/1404.7300).

Đề xuất độ phức tạp tăng dần, không phải tất cả bắt buộc ngay từ đầu:

| Thành phần | Đại diện cho gì? | Vì sao có thể ảnh hưởng phép đo? |
|---|---|---|
| Skin + electrode contact | Da và giao diện dán electrode | Contact area, pressure, hydration thay đổi |
| Fat/soft tissue | Tissue quanh cơ | Thay đổi đường phân bố dòng và sensitivity |
| Muscle ROIs | Các vùng mục tiêu ở mức coarse | Conductivity có hướng, hình học và co-activation |
| Mandible/skull | Xương và geometry cứng | Điều hướng phân bố dòng; vẫn ảnh hưởng reference field |
| Oral cavity/air/fluid | Khoang miệng thay đổi theo task | Puff hoặc há miệng có thể đổi impedance mà không phải chỉ đổi σ cơ |
| Vascular contributions | Blood volume/perfusion | Không mặc nhiên cố định khi cơ hoạt động |

Không cần mesh riêng từng facial nerve để làm classifier đầu tiên. Thêm structure
chỉ khi có hypothesis rõ, thông số có nguồn và sensitivity đủ lớn để cần phân biệt.
Anatomical segmentation có thể dựa trên MRI, nhưng một MRI geometry không tự
cung cấp frequency-dependent conductivity. Ví dụ MRI cơ môi đã được nghiên cứu:
[3D lip-muscle MRI study](https://pubmed.ncbi.nlm.nih.gov/20033581/).

### 3.4 Rest subtraction không loại hết skin, bone, blood

Tư duy đúng là \(y=F(\text{tissues, geometry, electrodes, contacts},f)\).
\(y_1-y_0\) bỏ đi phần measurement không đổi; anatomy cố định vẫn quyết định
độ nhạy đối với thứ thay đổi. Khi task xảy ra, cả geometry/contact/air volume
có thể đổi. Vì vậy không thể gọi \(\Delta Z\) là "pure muscle activation".

Với mục tiêu hiện tại, task-linked deformation có thể là **useful signal**.
Nó chỉ trở thành lý do bác bỏ claim khi mình quảng bá là isolated intrinsic
muscle conductivity, hoặc khi accidental movement làm classifier thất bại.

## 4. Electrode placement: closed-ring có bắt buộc không?

**Electrical circuit phải có current return path; electrodes không bắt buộc
tạo một vòng tròn hình học.** Closed-ring giúp lấy thông tin từ nhiều phía,
nhưng local/open-surface và partial-boundary measurements vẫn có ý nghĩa.
Thiếu coverage có thể giảm sensitivity ở xa và làm các nguồn khó phân biệt.

### 4.1 Các nguồn để defend phương pháp, không phải copy layout

| Nguồn | Dùng để biện minh điều gì? | Không được suy ra |
|---|---|---|
| Kim 2019, Section 2.6 | Anatomy và target quyết định landmarks | Lower-face airway coverage đủ để thấy mọi facial muscle |
| Visentin 2017, Section 2.4 | Direct facial EIT đã có proof of concept | Layout trước mặt đáp ứng constraint của bạn |
| [Rutkove, Pacheck & Sanchez 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5498265/) | FEM sensitivity depends on electrode geometry and layered tissues | Các tỷ lệ tissue contribution của limb đúng cho face |
| [Hyvönen et al. 2014](https://arxiv.org/abs/1404.7300) | Optimize placement using uncertainty/information under a forward model | Một nghiệm 2D là optimum trên đầu người thật |
| [Zhang, Wang & Song 2026](https://www.mdpi.com/2227-7390/14/5/840) | Partial-ring simulation/water-tank evidence | Half-ring face recognition đã validated; experimental reference là TV reconstruction, không ground truth conductivity |
| [Murphy et al., US/EIT](https://pmc.ncbi.nlm.nih.gov/articles/PMC6668036/) | Local surface arrays with anatomical information can support muscle imaging | Unobtrusive remote facial imaging đã giải quyết |
| [Hauptmann et al. 2017](https://arxiv.org/abs/1605.01309) | Mathematical partial-boundary reconstruction | Stable recovery từ vài contacts quanh tai trong mọi anatomy |

Nguồn sensitivity Rutkove là layered limb FEM; nguồn Hyvönen là model-based
optimal experimental design. Đây là nền tảng để xây phép kiểm tra cho mình,
không phải citations thay thế phép kiểm tra.

### 4.2 Ba candidate layouts trong constraint của bạn

Đây là **layout families để mô phỏng/so sánh**, chưa chốt số, khoảng cách,
drive pattern hay vị trí safe để thực hiện trên người.

| Layout | Vùng được dùng | Hypothesis phải kiểm tra |
|---|---|---|
| L1: ear + jawline/submental | Hai bên quanh tai, viền hàm, dưới cằm | Compromise giữa coverage và không che cơ môi/má mục tiêu |
| L2: L1 + temple/forehead | Thêm các sites bạn chấp nhận | Có thêm thông tin không trùng lặp, hay chủ yếu thêm nuisance? |
| L3: ear-only | Chỉ quanh hai tai | Wearability tốt hơn nhưng lower-face signal có thể yếu/khó tách |

Không có cơ sở hiện tại để gọi L1 là optimal hoặc L3 là chắc chắn khả thi.
Nếu fixed electrode budget, L2 phải **redistribute** cùng số electrodes;
thêm electrodes là một ablation riêng, không phải placement-only comparison.
Trán được bạn chấp nhận nhưng vẫn nhìn thấy; "unobtrusive" cần định nghĩa chính
xác thay vì mặc nhiên bằng "invisible".

### 4.3 Một cách defend placement có thể thực hiện được

1. Định nghĩa constraint: forbidden regions, electrode count/size và mounting.
2. Định nghĩa target: phân biệt task patterns, không mặc định phải reconstruct
   từng voxel. Anatomical ROI chỉ hỗ trợ giải thích sensitivity.
3. So sánh candidates bằng cùng forward model, noise assumptions và budget.
4. Perturb riêng muscle-region properties, tissue geometry, contacts và electrode
   position. Không thay tất cả cùng lúc rồi gọi là muscle effect.
5. Chọn layout có task-related information đủ lớn và ổn định trước nuisance.
6. Validate trên held-out people/sessions; không dùng test set để chọn layout.

Ví dụ định nghĩa sensitivity bằng finite difference:

\[
s_{m,k}=\frac{y_m(\theta+\delta e_k)-y_m(\theta)}{\delta}.
\]

\(m\): measurement channel; \(k\): một model parameter/ROI; \(\delta\): perturbation
nhỏ; \(e_k\): chỉ thay parameter k. Toàn bộ \(s_{:,k}\) là "dấu vân tay"
measurement của perturbation đó. Hai vùng tạo hai vector gần giống nhau thì khó
phân biệt, dù amplitude lớn. Với task recognition, kiểm tra dấu vân tay của
cả task pattern thay vì đòi sensitivity mỗi cơ độc lập.

Đề xuất score cho simulated task means, có noise weighting:
\(d^2_{ab}=(\mu_a-\mu_b)^T\Sigma^{-1}(\mu_a-\mu_b)\).
\(\mu\): mean features của task; \(\Sigma\): noise/nuisance covariance có
regularization khi cần. Đây là design metric đề xuất, không guarantee accuracy.
Tối ưu để cặp tasks khó nhất vẫn tách được, không chỉ tối đa raw voltage.

## 5. Các numbers phải có provenance thế nào?

| Parameter | Ý nghĩa thực | Cách chọn/kiểm chứng hợp lý |
|---|---|---|
| Electrode count | Contact burden và measurement diversity | Layout/count ablation; không mặc định 16 là optimal |
| Size, spacing, 3D positions | Contact area, fields, mounting repeatability | Landmarks/scan và documented placement tolerance |
| Frequency | Tissue dispersion, contact và hardware response | Bench-verified bandwidth + controlled sweep; không chọn chỉ vì paper dùng |
| Excitation | Signal level và electrical safety | Lab review of complete system; không suy safe từ một con số trong paper |
| Tissue σ/ε | Material properties, không phải whole-channel Z | Cùng tissue, frequency, direction và điều kiện; sweep uncertainty |
| Ri/Re/Cm or Cole parameters | Effective spectrum parameters | Fit multifrequency data với identifiability/residual checks |
| Contact impedance | Electrode-skin interface | Measurement/estimated range; separate from muscle parameter |
| Task amplitude | Mức biến dạng/effort và task reproducibility | Video/EMG-supported instructions, không gán thành % σ tùy ý |
| h0/mesh resolution | Numerical discretization | Mesh-convergence check of predicted measurements/sensitivity |
| Noise/drift | Hardware/contact/session uncertainty | Estimate from repeated reference/bench/pilot; report assumptions |

Một nguồn cho conductivity không tự chứng minh chính xác geometry hay contact
model. Model có nhiều parameters nhưng không có dữ liệu để constrain có thể
ít defensible hơn model đơn giản với uncertainty rõ.

`eit_sim_playground.py` hiện là unit-disk conductivity sandbox. `perm=10` đang
được dùng như conductivity contrast trong script, không phải "cơ activation
10 lần", không phải một đo đạc tissue và không tự mang đơn vị S/m. Simulation
hiện tại không có membrane capacitance, spectral tissue model hay facial anatomy.
Giữ nó để học EIT và test algorithms; không dùng làm physiological proof.

## 6. Study design cho paper đầu tiên: đề xuất, chưa phải protocol

### 6.1 Hypotheses và tasks

H1: permitted layouts chứa thông tin để phân biệt một task set định trước.
H2: performance còn hữu ích ở buổi khác/sau redonning, không chỉ random windows.
H3: layout selection cho trade-off đo được giữa accuracy và wearability/burden.

Candidate tasks để chọn cùng prof: smile, lip protrusion, lip press; tùy mục tiêu
thêm cheek puff làm bridge với Liu. Luôn có **rest/null**. Các task này không
tương đương kích hoạt một cơ duy nhất. Đây chưa phải validated dysarthria battery.
Chọn ít tasks vì use case và repeatability, không chọn sau khi nhìn test results.

### 6.2 Hai đường baseline đều có thể làm

**A. Permitted-layout-only study.** So L1/L2/L3 với cùng budget; có count/channel
ablations, simple classifier và robust evaluation. Có thể defend feasibility
trong constraint, nhưng không claim vượt cheek BioZ khi chưa đo cheek baseline.

**B. Thêm temporary anterior BioZ baseline.** Trong cùng participants/tasks,
so layout cheek/below-mouth với permitted layout nếu được chấp nhận. Nếu 3-electrode
two-terminal setup so với 16-electrode tetrapolar setup, đây là **system comparison**,
không cô lập placement effect. Cần matched protocol/budget subcomparison nếu
muốn claim placement tốt hơn. Không cần ép numerical replication khi paper gốc
thiếu split/stride details; document các quyết định của mình.

User's numbered answer on this baseline remains conditional/ambiguous; confirm
before finalizing B. Không mặc định consent cho một protocol trên người.

### 6.3 Dữ liệu và evaluation tránh kết luận quá mạnh

- Healthy participants trước; engineering pilot xác định noise/repeatability,
  rồi quyết định sample size theo precision/effect-size và nguồn lực. Chưa có
  cơ sở gọi một con số nhỏ bất kỳ là study đã đủ statistical power.
- Nhiều sessions, gồm tháo-gắn lại; ghi landmark, contact quality và thời gian.
- Randomize/counterbalance task và layout order để tránh fatigue/time confounding.
- Split theo participant/session/trial **trước windowing**; không để samples
  thuộc overlapping windows xuất hiện ở cả train và test. Nếu dùng time split,
  đặt gap phù hợp với window/filter để tránh boundary leakage.
- Fit normalization, feature selection và hyperparameters chỉ từ training data;
  chọn layout bằng development data hoặc nested validation, không test subjects.
- Report riêng within-session, cross-session same-person và unseen-person.
  Nếu cần user calibration, báo rõ calibration duration; không gọi là calibration-free.
- Macro F1, confusion matrix, rest false activations, latency, redonning drop và
  comfort/donning burden. Report uncertainty across participants, không coi hàng
  nghìn correlated windows là hàng nghìn independent subjects.
- Ground truth task: synchronized video/annotations. EMG là auxiliary reference
  cho timing/co-activation, không ground truth % lực/cơ. Kiểm tra interference
  của active BioZ trước khi assume concurrent EMG recordings đáng tin.

### 6.4 Controls cho cơ chế và robustness

| Test/control | Câu hỏi trả lời |
|---|---|
| Head rotation/no intended facial task | Có đang classify head pose? |
| Jaw motion/chewing/speaking ngoài task set | False positives trong use case thực? |
| Rest before/after remount | Contact/session offset lớn tới đâu? |
| Video task execution vs label cue | Model nhận chuyển động thật hay thời điểm prompt? |
| Single channel vs multichannel | Thêm channels có tạo thông tin độc lập? |
| Magnitude vs phase vs both, nếu available | Feature nào thực sự có ích trên held-out data? |
| Fixed vs allowed calibrated baseline | Bao nhiêu performance phụ thuộc calibration? |

Không phải mọi control đều cần làm cùng ngày đầu. Chọn theo claimed use case.
Nếu task-linked deformation tạo tín hiệu ổn định, đây vẫn có thể là thành công
cho task recognition. Đừng đổi tên nó thành muscle-specific imaging.

## 7. Novelty nên và không nên viết

Không nên: "first facial bioimpedance", "first EIT on face", "EMG always needs
electrodes on every target muscle", "deep muscle activation measured", hoặc
"diagnoses dysarthria" khi chỉ có healthy-task data.

Proposed English positioning, deliberately without a priority claim:

> We investigate facial task recognition using bioimpedance electrodes restricted
> to sites outside anterior target-muscle regions. We evaluate the trade-off
> between electrode layout, recognition performance, and robustness to session
> changes and electrode reapplication.

Nếu thực sự implement anatomy-informed selection rồi test held-out, thêm được
contribution về model-informed placement. Không gọi là optimization nếu chỉ
thử vài layouts mà không nêu objective/constraints/search procedure.

**Potential contribution package:** constrained sensing design + carefully
measured placement/robustness trade-off + reproducible multi-session evaluation.
Không bắt buộc phát minh classifier mới. Một Random Forest tốt được kiểm chứng
đúng có thể phù hợp hơn deep model trên một người và correlated windows.
Không ai có thể bảo đảm publish chỉ từ số tasks hoặc đề tài còn ít papers.

## 8. Safety boundary và những gì đã được xác nhận

Người dùng có lab support và recruitment capability, nhưng chưa xác nhận
approved human protocol hay electrical safety of the complete CN0565 setup.
Bench/phantom validate signal chain, không chứng nhận an toàn cho người.
Review phải tính power/USB/isolation, fault paths, electrode contacts, excitation
và concurrent equipment. Các nguồn nghiên cứu ở trên không phải hướng dẫn
tự nối hardware lên mặt. Tham khảo gate chi tiết ở review trước.

## 9. Các quyết định còn cần chốt, không hỏi lại mục tiêu đã rõ

1. Task set/use case cho first paper: lower-face voluntary gestures hay thêm
   speech-adjacent tasks? Chọn với prof, và SLP nếu muốn relevance lâm sàng.
2. Unobtrusive được định nghĩa bằng forbidden regions, visibility, count,
   donning time hay tất cả? Forehead allowed không có nghĩa invisible.
3. Có temporary anterior BioZ comparator không? Câu trả lời "ideally 2...1"
   chưa đủ rõ để khóa study condition; cả A và B đều đã có đường thiết kế.
4. Bao nhiêu người/buổi, hardware phase/frequency access, và calibration burden
   thực sự khả dụng? Chưa cần tất cả answers để hiểu related work.

## 10. Search scope và reading order

Nguồn: supplied PDFs; publisher/author repositories; PubMed/PMC; arXiv; primary
patent document for prior-art awareness. Search families included facial/face/
cheek/perioral/orbicularis/masseter BioZ, EIM, impedance spectroscopy, facial
gesture, ear/remote sensing, lower-face/neck EIT, partial boundary, electrode
optimization, and tongue Cole/FEM models. Citation trails were checked for
modality mismatches. Không claim đã search toàn bộ Scopus/WoS hoặc mọi ngôn ngữ.
Metadata-only and adjacent evidence được đánh dấu ở source cards.

Reading order cho dự án:

1. Liu 2025: closest task-recognition baseline và limits của evaluation.
2. Painometry Figure 4: direct facial impedance và local contact/tissue model.
3. Kusche Figures 1-3: circuit, spectrum, contraction-related geometry.
4. Kim 2019 placement methods: defend vị trí bằng target anatomy.
5. Rutkove 2017 + Hyvönen 2014: sensitivity và model-based design.
6. Schooling Figures 1/5: anatomy + spectrum + circuit khi cần model sâu hơn.
7. Visentin/partial-boundary papers nếu tiếp tục image reconstruction.

Các nguồn online có thể bị publisher/PMC access challenge; không biến search
snippet thành verified result khi nội dung cần thiết chưa đọc được. Báo cáo này
không xác nhận exact ear/jaw layout đã feasible: đó là câu hỏi cần experiments.

## 11. Hai (thực ra ba) claims không được nhập làm một

| Milestone | Câu hỏi có thể publish nếu trả lời tốt | Dữ liệu/đầu ra | Mức khả thi hiện tại và điều kiện tối thiểu |
|---|---|---|---|
| A. Constrained facial task recognition | Vài electrodes ở sites cho phép có phân biệt được một set task định trước qua buổi/tháo-gắn không? | Feature vector nhiều kênh (Z) hoặc (V/I) → task label; **không phải image** | **Trung bình, có điều kiện**. Liu 2025 chứng minh mặt có task-dependent BioZ nhưng layout ở má, n=4; iMove/iEat chứng minh nhận biết từ đường dẫn impedance không cần imaging. Layout của ta phải tự chứng minh signal vượt nuisance, generalization, và use case. Không thể bảo đảm có paper chỉ vì 2–4 classes. |
| B. 3D *coarse-ROI* time-difference EIT | Với coverage cho phép, có localize được thay đổi tại vài vùng lớn như lower-face trái/phải và tách chúng khỏi jaw/oral cavity/contact không? | Δvoltage → 3D change map kèm uncertainty/spatial-resolution metrics | **Cao rủi ro/chưa chứng minh cho layout này.** Kim 2019 và Piccin 2023 cho precedent upper-airway gần mặt/cổ, không phải facial muscles. Cần nhiều current/sense patterns độc lập, coverage 3D (thường các vị trí ở hơn một cao độ), geometry/contact model, phantom có ground truth và human cross-modal validation. |
| C. Muscle-specific deficit / clinical % | Cơ cụ thể nào yếu ở bệnh nhân và mức suy giảm là bao nhiêu? | ROI/clinical biomarker được hiệu chuẩn, không phải màu heatmap | **Rất cao rủi ro.** Facial muscles nông, đan xen/co-activate; EIT inverse problem mờ và ill-posed. Cần chứng minh từng cơ nhận dạng được trong model/phantom, đối chiếu EMG/video và chuẩn lâm sàng; định nghĩa denominator cho %. Post-stroke dysarthria không đồng nghĩa chỉ yếu cơ mặt. |

Vì vậy có thể có **Paper A**, rồi **Paper B** nếu gate 3D thành công. Claim C có thể là một paper lâm sàng riêng, hoặc chỉ là future work. Không thể hứa “hai paper” trước dữ liệu. Đặc biệt nhiều electrodes hơn tạo thêm measurements *có thể* hữu ích nhưng nếu các phép đo gần trùng nhau, contact/geometry chưa biết, hoặc dòng không đi qua ROI mong muốn, tính định vị không tăng tương ứng. CN0565 unit-disk 16-electrode 2D simulation hiện **không phải** anatomical facial 3D feasibility test.

**Proof gate A:** (a) bench + static phantom xác nhận raw complex/voltage data và drift; (b) cùng người, task vs rest đủ vượt biến thiên không-task; (c) thử các confounds (head/jaw/contact/respiration); (d) held-out session/redonning/participant với metrics uncertainty; (e) task set và split định trước; (f) so với simple baselines, optionally matched anterior placement. Nếu (b) thất bại, không nên lấp bằng classifier lớn.

**Proof gate B:** (a) 3D FEM với geometry và complete-electrode/contact assumptions; (b) tính Jacobian (J_{mk}=\partial V_m/\partial\sigma_k), singular values/column similarity và vùng low sensitivity; (c) target + nuisance perturbations riêng; (d) phantom 3D có inclusions biết vị trí và motion/air/contact controls; (e) blinded localization errors, resolution và false localization; (f) human validation đối chiếu anatomy/motion/EMG. Bước (b) trả lời layout có *thông tin* về ROI hay không; một hình reconstruction trông đẹp chưa đủ.

**Proof gate C:** independent evidence về muscle-specificity *và* relevance lâm sàng. Cần tiêu chí “weakness” do speech-language pathologist/clinician thống nhất (không chỉ task label), lặp qua ngày và người, lateralized/known-deficit validation, và prospective comparison với clinical scores/speech outcomes. [ASHA](https://www.asha.org/Practice-Portal/Clinical-Topics/Dysarthria-in-Adults/) mô tả dysarthria qua strength **cùng** speed, range, steadiness, tone, accuracy ở nhiều hệ speech; [Solomon et al. 2017](https://doi.org/10.1044/2017_AJSLP-16-0144) cảnh báo không suy impairment speech chỉ từ nonspeech strength. “% yếu” chưa có mẫu số: % so với chính người đó lúc khỏe, bên đối diện, nhóm control hay thang lâm sàng? Các lựa chọn này **không tương đương**.

## 12. Điều đang giả lập/đo: rest là anatomy thật, không phải background đồng nhất

Gọi (\theta_t) là trạng thái tại thời điểm (t): conductivity/permittivity của từng tissue, hình học (khoang miệng, hàm, da), máu/dịch, electrode positions và contact impedances. Ở cùng một drive pattern/current (I), dụng cụ cho vector measurements

\[
\mathbf v_{\rm rest}=F(\theta_{\rm rest},I,f)+\eta_{\rm rest},\qquad
\mathbf v_{\rm task}=F(\theta_{\rm task},I,f)+\eta_{\rm task},\qquad
\Delta\mathbf v=\mathbf v_{\rm task}-\mathbf v_{\rm rest}.
\]

*Rest* không phải không có current, không phải mặt “trống”: vẫn có da, mỡ, cơ, xương, máu, không khí, dịch và electrode contact. Điều kiện so sánh cần **cùng current amplitude, frequency, electrode pair/order, voltage sign convention, gain, reference và geometry registration**. Nếu drive thay đổi giữa hai trạng thái, phép trừ trộn trạng thái người với trạng thái máy. EIT đo **voltage differences ở electrodes**, không trực tiếp đo một “voltage drop của riêng cơ”. Một ΔV = 0 có thể do thay đổi yếu, sensitivity thấp hoặc các ảnh hưởng triệt tiêu; không chứng minh cơ không hoạt động.

Tuyến tính hóa gần reference:

\[
\Delta\mathbf v \approx J_\sigma\Delta\boldsymbol\sigma
 +J_g\Delta\mathbf g+J_c\Delta\mathbf c+J_b\Delta\mathbf b+\Delta\boldsymbol\eta.
\]

Trong đó (\Delta\mathbf g) là geometry/jaw/air changes, (\Delta\mathbf c) là contact/electrode displacement, (\Delta\mathbf b) là vascular/fluid changes. Đây là **conceptual decomposition** để thiết kế controls, không khẳng định mọi thành phần tách được từ data. Levit 2024 quan sát baseline impedance thay đổi gắn với artery/nearby muscle hoạt động; chính paper này làm giả định “blood vessels đều bất biến rồi phép trừ chỉ còn cơ” không đúng. Với task classifier, tổng tín hiệu có thể hữu ích; với muscle image, phải tách hoặc giới hạn confounds.

| Thành phần cần biết (beginner glossary) | Nó có thể làm gì với dòng/điện áp? | Paper/data precedent và vai trò trong project |
|---|---|---|
| **Skin / stratum corneum + electrode interface** (da/giao diện) | Thay contact impedance theo gel, hydration, áp lực, cử động; nguồn drift và current-density không đều | [Complete Electrode Model](https://doi.org/10.1137/0152060); [Kusche 2024](https://doi.org/10.1109/JSEN.2024.3359284) phân tích giao diện. Cần log/estimate contact, redonning control. |
| **Subcutaneous fat / fascia / SMAS** (mỡ/màng liên kết dưới da) | Tạo lớp giữa electrode và cơ, thay độ sâu và hình học sensitivity; SMAS là cấu trúc cơ–cân ở mặt, không phải signal class độc lập | [Rutkove et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC5498265/) hỗ trợ layered sensitivity ở limb, **không cung cấp số face**. 3D segmentation/uncertainty test trước khi claim deeper ROI. |
| **Facial skeletal muscles / fibers** | Intra-/extracellular ionic paths, membrane capacitance và hướng sợi gây frequency dependence/anisotropy; contraction còn đổi hình học | [Kusche](https://doi.org/10.1109/JSEN.2024.3359284) forearm circuit; [Schooling](https://doi.org/10.1088/1361-6579/abcb9b) tongue layered model. Có thể dùng làm *prior/model structure*, không copy tissue values thành face ground truth. |
| **Blood vessels / blood volume / pulse** | Dịch dẫn điện di động và co/giãn mạch có thể đổi BioZ cùng task; pulse là thành phần theo nhịp tim | [Levit 2024](https://doi.org/10.1088/2057-1976/ad28cb) face IPG; đo heart/pulse channel hoặc frequency/time controls để biết contribution. Họ infer vessel narrowing từ impedance model, không đo trực tiếp bán kính trong mọi trial. |
| **Mandible, maxilla, skull, teeth** (xương/răng) | Vật liệu và shape dẫn dòng khác soft tissue, tạo boundary/contrast; jaw movement đổi vị trí xương/răng | [Kim 2019](https://doi.org/10.5664/jcsm.7714) dùng anatomy/MRI để chọn placement. Cần geometry đúng, không giả xương biến mất khi rest subtraction. |
| **Oral/nasal air, saliva, other fluid** | Air cavity và fluid path thay mạnh theo puff, suck, open jaw, speech; dễ tạo task label dù không đo cơ mục tiêu | [Liu 2025](https://doi.org/10.1145/3745900.3746120) phân loại puff/suck; airway EIT [Kim 2019](https://doi.org/10.5664/jcsm.7714). Test “mouth air/shape” vs muscle hypothesis bằng video và matched controls. |
| **Facial nerve** | Chi phối cơ; không có lý do hiện tại cho rằng remote surface measurement định vị trực tiếp một nerve nhỏ | Thêm chi tiết nerve vào model chỉ nếu anatomy, sensitivity và validation hỗ trợ; không đặt claim “sensing nerve” ở Paper A. |
| **Anatomical co-activation / local ear muscles** | Một task thường gọi nhiều cơ; ear sites có thể thấy chính ear muscle, không phải tín hiệu “truyền xa” từ zygomatic | [Schumann 2021](https://doi.org/10.1371/journal.pone.0254932), [Rüschenschmidt 2022](https://doi.org/10.3390/diagnostics12010121). Dùng temporary facial/auricular EMG + video để kiểm tra confound nếu claim remote placement. |

**Provenance rule:** [IT'IS dielectric database](https://itis.swiss/virtual-population/tissue-properties/database/low-frequency-conductivity) và [Gabriel et al. review](https://pubmed.ncbi.nlm.nih.gov/19636081/) là **priors/ranges** theo frequency và tissue, không “chứng minh” một số (\sigma) đúng cho mọi người/cơ mặt. Lập bảng cho từng parameter: source, tissue, frequency, measurement conditions, uncertainty range, version, effect on (V), calibration measurement và planned sensitivity sweep. Nếu không có nguồn/đo riêng, ghi **unknown; sweep**, không bịa single value. (\sigma_{rel}=1) và `perm=10` của playground chỉ là normalization và toy contrast, không phải nước/máu/cơ người.

## 13. Audit nghiêm khắc các tasks từ `papers/tasks/`

Nguồn chính: [Schumann et al. 2021, Table 1](https://doi.org/10.1371/journal.pone.0254932), local `papers/tasks/journal.pone.0254932.pdf`: 30 nam khỏe mạnh, 29 tasks, 10 mimic muscle groups hai bên bằng high-channel sEMG; masseter/temporalis là control. “Highest” nghĩa là **cao nhất trong các cơ đã đo, dưới task đó**, không phải một cơ duy nhất. Atlas dùng color scale *riêng cho từng task* nên màu đỏ không so absolute activation giữa hai tasks. [Rüschenschmidt et al. 2022](https://doi.org/10.3390/diagnostics12010121), local `papers/tasks/diagnostics-12-00121.pdf`: ear-muscle EMG ở 12 healthy và 7 postparalytic synkinesis, không phải BioZ/EIT và không phải post-stroke dysarthria.

| Proposed task (sửa English label) | Atlas evidence / correction | Editorial use |
|---|---|---|
| **Purse lips** (T14) | Orbicularis oris highest **trong sampled muscles**, không chứng minh isolation | Tốt làm *anchor task pattern*, không gọi “single-muscle activation”. |
| **Unilateral smile, left/right** (T22/23) | Zygomaticus group highest; laterality được elicited, cần video kiểm tra bên | Good asymmetric contrast; không suy weak muscle từ classifier label. |
| **Protrude lower lip** (T11) | Mentális, depressor anguli oris, depressor labii, orbicularis oris | Mixed activation, **không** phải riêng depressor labii/mentalis. |
| **Open lips wide, jaw closed** (T20) | Inferior orbicularis oris, depressor labii, mentalis; atlas không liệt kê depressor anguli among highest ở T20 | Task hữu ích nhưng jaw-closed instruction/video cần nhất quán. |
| **Pull upper lip upward** (T12) | Levator labii superioris alaeque nasi + levator labii superioris + orbicularis oris | Ghi muscle labels đúng, nhưng multi-muscle. |
| **Bilateral voluntary smile** (T9) | Zygomatic, orbicularis oris, mentalis, depressor labii, depressor anguli | Không phải cùng task với unilateral smile; dễ đo nhưng mixed. |
| **Press lips together** (T7) | Orbicularis oris, depressor anguli, mentalis, depressor labii, zygomatic | Mixed; contact geometry cũng có thể đổi. |
| **Pull mouth corners downward** (T8) | Inferior orbicularis, depressor anguli, depressor labii, mentalis | Mixed; phù hợp task pattern. |
| **Pronounce vowels** (T1–6) | Atlas khảo sát **6 German vowels** A/Ä/E/I/O/U, không phải “5 vowels” universal. Lip/oral/jaw/voicing đều thay; mapping phụ thuộc ngôn ngữ | Xác định tiếng Việt hay tiếng Anh, âm IPA, *sustained phonation* hay dynamic speech. Vowels nên là exploratory functional block, không thay thế đo speech intelligibility. |
| **Open jaw with closed lips** (T18) | Mentalis, orbicularis, depressor labii, depressor anguli | Task hợp atlas nhưng jaw displacement là nuisance/chính signal cần ghi video. |
| **Open jaw wide** | Không phải task trong Table 1 của atlas này | Thêm nếu có rationale/use case riêng; đo jaw opening bằng video, không gán label cơ theo atlas. |
| **Jaw clench** | Không phải Table 1 task; masseter/temporalis là chewing muscle controls. EMG clench được nghiên cứu riêng, ví dụ [Visser et al. 1992](https://doi.org/10.1177/00220345920710020501) | Tốt làm **jaw confound/control**, nhưng không dùng clench maximal 5 s × 5 mặc định; xác định effort/comfort với clinician. |
| **Blow out cheeks / suck cheeks inward** (T15/T16) | Atlas highest = orbicularis oris, mentalis, depressor labii; **không đo buccinator**. [Perkins et al. 1977](https://doi.org/10.1177/00220345770560071301) dùng fine-wire ở 14 người và ghi co-activation trong oral tasks | Dùng như bridge tới Liu và oral-air control; không label “buccinator-specific”. |

**Ưu tiên cho Paper A:** Đừng mở đầu 19 classes. Pre-register một core set nhỏ và có rationale: `rest`, `purse lips`, `left smile`, `right smile`, có thể `lip press` hoặc `cheek puff` như *secondary* nếu use case rõ. Đây là **đề xuất**, không phải số classes/tasks “được paper chứng minh là tối ưu”. Block bổ sung (vowels, jaw, cheek) là tests về generalization và confounds hoặc data cho follow-up; nếu chọn classes sau khi xem test accuracy là selection bias. “Single-muscle anchors” nên đổi thành **dominant-pattern tasks**, và dùng temporary sEMG để quan sát thực tế từng người. Sự hiện diện của EMG electrode trên mặt trong validation không vi phạm constraint của thiết bị cuối.

## 14. Audit protocol 5 repetitions × 5 s hold × 5 s rest

Danh sách người dùng hiện có **19 task labels** nếu unilateral smile trái/phải là hai labels: 6 anchor, 3 mixed, 5 vowels + 3 jaw + 2 cheek = 19. Dưới định nghĩa *mỗi repetition gồm 5 s active và 5 s rest*, 95 trials, 475 s active, 475 s within-task rest, cộng 18 × 10 = 180 s between-task rest: **1,130 s = 18 min 50 s**, *chưa tính hướng dẫn, rehearsal, remount, failed trials và baseline*. Nếu bỏ 5 s rest cuối mỗi task thì 1,035 s = 17 min 15 s. Phải ghi rõ convention; nếu vowels thay đổi số task thì tổng đổi. Đây là phép tính từ **protocol đề xuất**, không phải thông số đã được paper chứng minh tối ưu.

| Design decision | Đánh giá và phép kiểm chứng cần làm |
|---|---|
| **5 repetitions** | Hợp lý cho engineering pilot/timing, **không** phải 5 độc lập đủ power, đặc biệt khi windows overlap. Pilot ước lượng variance intra-person/inter-session; chọn n subjects/sessions từ mục tiêu CI/effect size. |
| **5 s hold** | Phù hợp static face poses nếu duy trì đều; với *pronounce vowel* là sustained phonation (khác speech), jaw clench có thể fatigue/discomfort. Ghi effort và kiểm tra plateau onset–middle–offset; pilot rút/ngắt nếu khó duy trì. |
| **5 s rest / 10 s task gap** | Chưa có chứng cứ recovery đủ cho mọi task; kiểm tra pre-trial baseline quay về within tolerance, heart/pulse/contact drift và carryover. Cho phép adaptive rest theo predefined criterion thay vì coi số cố định là chân lý. |
| **Reference state** | Không dùng duy nhất reference đầu buổi cho mọi trial. Lưu raw rest trước (và sau) trial, định nghĩa window tham chiếu, kiểm tra drift; không vô tình chuẩn hóa bằng toàn session/test data. |
| **Order & cueing** | Randomize/counterbalance tasks hoặc block order theo load; ghi timestamps task cue vs actual video onset. Blind scoring. Lặp cùng cố định order có thể khiến classifier học elapsed time/fatigue. |
| **Unilateral tasks** | Video/FACS coding bên, bilateral EMG ở subset và mirror effects. Sự bất đối xứng electrode fit cũng tạo side signature. |
| **Recording channels** | BioZ raw magnitude+phase/voltage/current, geometry/contact, video, optional facial/auricular EMG; đồng bộ thời gian và kiểm tra active-drive interference trước khi ghép. |
| **Units of analysis** | Trial là đơn vị lặp trong người; participant/session là cluster. Split participant/session/trial trước windowing, report per-person distribution/CI. |
| **Clinical bridge** | Non-speech tasks có thể xác nhận sensing nhưng không chứng minh giải quyết dysarthria. Nên có speech-linked task và outcome bởi SLP ở pha sau; [ASHA](https://www.asha.org/Practice-Portal/Clinical-Topics/Dysarthria-in-Adults/) phân biệt speech subsystems và intelligibility. |

Protocol đầu tiên nên là **pilot có stop/continue criteria định trước**: signal quality, task–rest separability, remount drift, comfort, và an toàn hệ thống. Không copy timing của atlas: paper atlas đưa task mapping, không chứng minh 5/5/10 s là optimum cho BioZ. Thử trên bản thân là exploratory troubleshooting, không thay thế lab electrical review và institutional human-subject determination.

## 15. Electrode placement phải match claim, không chỉ “ring vs half-ring”

Với **Paper A**, tối ưu cho *task discrimination under allowed-site constraint*: giữ electrode budget, device, sampling, feature pipeline như nhau khi so L1/L2/L3. Đo per-site contact, distance/visibility/donning time. Một channel BioZ thuận tiện vẫn có thể classify vì geometry/air/contact, nên cần task-specific nuisance controls. Liu 2025 dùng 3 electrodes trước mặt và 2 channels; *3* không là bằng chứng “ít nhất cần 3” hoặc jaw/ear placement cũng hiệu quả.

Với **Paper B**, mục tiêu là *localized 3D information*. Test FEM nhiều planes/heights và coverage quanh ROI, không giả định closed ring bắt buộc về mặt lý thuyết. Một partial surface có thể reconstruct nhưng vùng xa/ít góc nhìn thường mờ; [Zhang et al. 2026 partial ring](https://www.mdpi.com/2227-7390/14/5/840) là simulation/water-tank precedent, **không phải facial proof**. [Kim 2019](https://doi.org/10.5664/jcsm.7714) chọn lower-face anatomical landmarks cho airway; [Piccin 2023](https://doi.org/10.3389/frsle.2023.1238508) dùng 32 electrodes/two circumferential neck bands và CT-derived 3D model, nhưng target cũng airway. Lấy từ họ **logic** anatomy → target → field coverage → validation, không copy count/layout. 3D imaging có thể buộc một số electrodes gần anterior face; nếu constraint hoàn toàn loại phần này, một honest negative FEM/phantom result cũng là decision gate.

Near-ear electrodes cần coi là *possible local signal site*: [Rüschenschmidt 2022](https://doi.org/10.3390/diagnostics12010121) ghi ear-muscle EMG với smiling và nhiều facial tasks. Nếu data ear-only classify smile, chưa biết nó đo deep cheek hay local ear co-activation. Test bằng local ear EMG và matched jaw/cheek video (ở subset) để tách hypothesis. “Non-obtrusive” cần operational definition: không che anterior target muscles, diện tích/visibility, donning time, comfort, redonning error — không chỉ dùng tính từ.

## 16. Evidence ledger: câu nào đã chứng minh, câu nào còn là prediction?

| Claim định đưa vào paper | Evidence đã có | Còn thiếu / test quyết định | Verdict hiện tại |
|---|---|---|---|
| Facial task changes can alter BioZ | [Liu 2025](https://doi.org/10.1145/3745900.3746120), [Levit 2024](https://doi.org/10.1088/2057-1976/ad28cb) | Exact permitted layout, tasks và validation | **Supported generally; project-specific unknown** |
| Jaw/ear sensors recognize selected tasks across people/sessions | Limb analog [iMove](https://doi.org/10.1109/PerCom59722.2024.10494489) không đủ; Liu layout khác | Matched experiments; held-out sessions/person | **Hypothesis** |
| Each prescribed task isolates one muscle | [Atlas](https://doi.org/10.1371/journal.pone.0254932) cho thấy đa số mixed | EMG/clinical task validation nếu cần muscle claim | **False as stated** |
| Rest subtraction leaves only muscle conductivity | [Levit](https://doi.org/10.1088/2057-1976/ad28cb), [Liu](https://doi.org/10.1145/3745900.3746120), [Kusche](https://doi.org/10.1109/JSEN.2024.3359284) nêu vascular/air/contact paths | Motion/contact/air controls and model | **False as stated** |
| 3D map locates facial muscle change with remote sites | Airway precedent [Kim](https://doi.org/10.5664/jcsm.7714), [Piccin](https://doi.org/10.3389/frsle.2023.1238508) | 3D identifiability + ground-truth phantom + cross-modal validation | **Unproven** |
| 3D map quantifies post-stroke weak muscle in % | No provided paper does this | Defined denominator, muscle-specific ground truth, clinical outcomes, repeatability | **Future hypothesis, not current claim** |

Do not use “first-ever” without a systematic novelty search across databases and citations. A defensible contribution is not absence of predecessors, but a **specific tested constraint**, robust evaluation and carefully limited claim.

**Literature update, 2026-09:** [Büchner et al. 2026](https://doi.org/10.1016/j.heliyon.2026.e45408) report synchronous high-resolution facial sEMG and 3D video in 36 healthy adults, with 3D *visualization* of EMG activation on a face model. It matters for anatomy/task validation, but it is **not 3D EIT** and should not be described as evidence that remote electrodes can tomographically recover deep facial muscle conductivity. This item was checked from publisher abstract/metadata, not its full methods PDF, so no stronger numerical claim is made.

## 17. Kế hoạch hiện tại: bắt đầu với 24 electrodes, không phải 24 cơ

**User clarification, 2026-10-01:** prof muốn dùng tối đa electrodes, quan sát
task-related data rồi mới giảm số lượng. Người dùng có **gold cup electrodes**;
chưa biết model, diameter, paste/gel hoặc đầu dây. Mục tiêu pilot là hỏi
“các cấu hình đo có tín hiệu lặp lại theo task không?”, chưa phải dựng ảnh cơ.

### 17.1 CN0565 nối như thế nào?

Nguồn: [CN0565 circuit note](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/CN0565.html),
local `cn0565 rev. a.pdf`, và schematic **02_066534 Rev B, sheet 2/3** trong
`cn0565-designsupport/CN0565-DesignSupport/EVAL-CN0565-ARDZ Files/`.

- Hai ADG2128 là **bidirectional 8 x 12 crosspoint switches**, không phải hai
  bộ 12 ADC. Tổng cộng có 24 đường electrode X. AD5940 đo qua các đường được
  switch lựa chọn; nhiều cấu hình được đo **tuần tự**.
- Mỗi cup có một dây đến một electrode connection. Không chia vĩnh viễn
  24 cups thành 12 kích thích + 12 sense, hoặc 6 nhóm độc lập bốn cups.
- Một phép đo tetrapolar chọn bốn contacts khác nhau: `F+`, `F-`, `S+`, `S-`.
  `F+`/`F-` là hai đầu drive/return của AC excitation; `S+`/`S-` đo hiệu điện
  thế. Ký hiệu +/- quy định chiều và dấu, không phải cực DC cố định.
- Ví dụ **logic, không phải chỉ định placement lên người**: phép A dùng
  E1/E8 làm Force và E4/E6 làm Sense; phép B có thể dùng E4/E6 làm Force và
  E1/E8 làm Sense. E4 không phải một loại “sense electrode” đặc biệt.
- `V_m = V(S+) - V(S-)`; nếu dùng transfer impedance thì
  `Z_m = [V(S+) - V(S-)] / I(F+,F-)`, với điện áp/dòng complex cùng tần số.
  Đây không phải riêng impedance của một cơ nằm giữa S+ và S-.

**Pinout theo schematic, chưa phải ảnh nhìn từ phía cắm cáp thực tế:**

| P1 pin numbers | Nets trên schematic | Ý nghĩa |
|---|---|---|
| 3–14, theo thứ tự số pin | X0–X11 | 12 electrode connections |
| 17–28, theo thứ tự số pin | X12–X23 | 12 electrode connections |
| 1, 2, 15, 16, 29, 30 | GND_ISO | Ground của miền mạch cách ly, **không phải sáu electrodes bổ sung** |

Ví dụ pin 3 = X0; pin 4 = X1; pin 14 = X11; pin 17 = X12; pin 28 = X23.
X0 trên schematic **không tự động** là index 0 trong mọi phiên bản Python/
firmware. Phải xác nhận pin 1, board revision, chiều mating connector và bảng
`skin site -> lead label -> P1 pin -> chip/X -> software index` trên bench.
Không nối thêm electrode cơ thể vào USB ground/earth hoặc P1 GND_ISO chỉ vì
nghĩ BioZ cần “ground electrode”. Không bypass đường DC-blocking/current limit.

### 17.2 Ground, bias, reference và bipolar là các chuyện khác nhau

| Từ | Ý nghĩa trong thí nghiệm này |
|---|---|
| **Current return** | F- hoàn tất đường dòng điện qua mẫu và mạch. Không đồng nghĩa earth ground. |
| **Voltage reference** | S- là phía được trừ khỏi S+ trong phép đo differential này. Có thể đổi theo cấu hình. |
| **Circuit ground / bias** | Mốc và điểm làm việc bên trong electronics. Circuit note mô tả TIA biased 1.1 V và AC blocking capacitors; đây **không phải** yêu cầu đặt 1.1 V DC lên mặt. |
| **Reference state / baseline** | Dữ liệu đo lúc nghỉ với cùng cấu hình; là một vector lưu trong máy tính, không phải một electrode riêng. |

Với BioZ, tên rõ nhất là **two-electrode/bipolar** nếu cùng hai contacts làm cả
drive và sense, hoặc **four-electrode/tetrapolar** nếu dùng bốn contacts khác
nhau. “Monopolar” không có nghĩa chỉ cần một dây và dòng không cần return;
trong các modality khác nhau từ này có thể chỉ cách dùng một reference xa.
Cho CN0565, hãy mô tả cụ thể Force/Sense thay vì chỉ ghi bipolar/monopolar.
Tetrapolar giảm đóng góp trực tiếp của sụt áp tại contact vào voltage sense,
nhưng không làm contact impedance, electrode movement hoặc current spreading
biến mất khỏi thí nghiệm.

Paper Liu xác nhận wet electrodes và ba vai trò theo Section 2.1 ở trên,
nhưng không công bố đủ sơ đồ để xác định chính xác return/bias. Không thấy
electrode ground thứ tư trong mô tả không có nghĩa electronics không có ground
hoặc bias. Ngược lại, Kim 2019 dùng một cheek reference bổ sung trên **hệ KHU**;
không suy từ đó rằng CN0565 cũng cần một electrode thứ 25.

### 17.3 Giới hạn phần mềm và tốc độ cần test trước

Read-only inspection ngày 2026-10-01 của local pyadi-iio:

- `adi/cn0565.py` thêm hai chips và `adi/adg2128.py` tạo 12 X lines/chip,
  nhưng `electrode_count_available` lại trả `[8, 16, 32]`. Đây là inconsistency
  phần mềm so với board 24 contacts, **không phải** bằng chứng board có 32
  electrodes hoặc firmware đang dùng đã được kiểm thử với 24.
- Generator adjacent/adjacent không cho sense dùng force contacts tạo
  `N(N-3)` measurements: 16 -> 208; 24 -> **504**. Đã kiểm tra phép đếm
  offline; chưa chạy hardware. Các reciprocal configurations có quan hệ với
  nhau, không phải 504 nguồn thông tin giải phẫu độc lập.
- Con số 504 chỉ dành cho protocol đó. Với layout mặt không phải circle,
  “next electrode index” chưa chắc là physical neighbor. Không áp cyclic
  ring indexing vào layout rời rạc mà không định nghĩa ý nghĩa từng pattern.
- Đo thời gian **toàn bộ scan** và timestamp từng measurement. Minh họa toán
  học, **không phải benchmark CN0565**: 20 ms/config x 504 = 10.08 s/frame,
  đã dài hơn proposed 5 s hold. Tăng số electrodes không bắt buộc đo mọi
  tổ hợp trong mỗi frame; có thể chọn một tập patterns phủ đủ 24 contacts.
- `all_voltages` đặt `impedance_mode=False`. Phải xác minh output mode,
  calibration và units, không đổi tên số raw thành ohms. Circuit CN0565 dùng
  **voltage excitation + current measurement**, không phải lý tưởng fixed-I
  như nhiều toy FEM. Cùng DAC amplitude không bảo đảm cùng current khi load
  đổi. Chọn calibrated transfer-impedance acquisition, hoặc đo/kiểm soát drive
  current và dùng forward model phù hợp khi diễn giải Delta V.
- `examples/cn0565/cn0565_sample_plot.py` có
  `v0 = np.full_like(current_data, 1)` cho demo. **Không dùng đây làm rest
  baseline của mặt**; phải đo baseline thật. Unit-circle mesh cũng không
  phải face geometry.

Chưa sửa collector, flash firmware, thay cấu hình thiết bị hoặc thực hiện
human acquisition trong lần rà soát này. Bench/resistor/phantom checks là bước
tiếp theo; việc nối lên người cần lab xác nhận toàn hệ thống, excitation,
isolation và quy trình nghiên cứu. Evaluation board hay một paper dùng dòng
nhất định không tự là chứng nhận an toàn cho cấu hình đang lắp.

## 18. Không cần closed ring để đo; placement phải có câu hỏi kiểm chứng

**Closed electrical circuit** và **closed spatial electrode ring** khác nhau.
Dòng cần đường đi qua mẫu từ một drive terminal trở về terminal kia; nó không
cần 24 cups tạo hình vòng tròn. Ring giúp bao phủ vùng cần imaging từ nhiều
hướng. Partial-boundary EIT có precedent, nhưng chất lượng và tính định vị phụ
thuộc coverage/model/noise. Không đặt được full ring không khiến phép đo
BioZ vô nghĩa; cũng không chứng minh remote 3D muscle imaging khả thi.

- [Kim 2019](https://doi.org/10.5664/jcsm.7714): chọn landmarks dựa MRI để
  electrode plane qua retroglossal airway, rồi đối chiếu MRI và đo boundary
  shape. Bài học: **target anatomy -> placement -> independent validation**.
  Target của họ là airway, không phải zygomaticus/orbicularis; không copy
  đường dưới môi–mastoid thành layout facial-muscle đã validated.
- [Zhang 2026](https://doi.org/10.3390/math14050840): simulation và water-tank
  experiments với half/three-quarter boundary. Bằng chứng nguyên lý cho
  partial coverage, không phải thử nghiệm mặt người.
- [Hyvönen et al.](https://doi.org/10.1137/140966174): với geometry, contact,
  conductivity prior và noise model cho trước, thay positions để giảm
  uncertainty của conductivity estimate. Demonstrations là **2D numerical**.
  Nó giúp thiết kế việc tối ưu sau này, không đưa sẵn tọa độ mặt để dán cups.

**Lịch sử: Candidate C24 (không áp dụng first collection 16 electrodes) — đề xuất coverage-first, chưa được paper validate:** dùng
12 vị trí mỗi bên, ưu tiên đối xứng và các vùng user đã cho phép. Các số sau
là **engineering allocation**, không phải số lượng tối ưu theo literature.

| Vùng có thể khảo sát | Mỗi bên | Tổng | Mục đích / điều cần kiểm tra |
|---|---:|---:|---|
| Trán ngoài, tránh vùng mắt | 2 | 4 | Thêm coverage phía trên; có thể chứa forehead-task/contact effects |
| Thái dương | 1 | 2 | Lateral view; temporalis/vascular contributions cần lưu ý |
| Da trước tai | 2 | 4 | Lateral attachment region; contact và jaw motion cần kiểm tra |
| Da sau tai | 1 | 2 | Candidate ít che mặt; khác curvature/hair/contact, chưa biết sensitivity ROI |
| Dọc bờ dưới hàm, từ góc hàm về phía cằm | 4 | 8 | Coverage gần vùng miệng hơn; không đồng nghĩa đo riêng cơ môi, có jaw effects |
| Dưới cằm, không phải mặt trước môi/cằm | 2 | 4 | Lower-face coverage; floor-of-mouth/tongue/swallow contributions |
| **Tổng** | **12** | **24** | Chỉ chốt vị trí khi cup size/fit, attachment, safety và recording quality đã được kiểm tra |

Đây không phải hướng dẫn cắm dòng vào 24 vị trí trên người ngay. Không xác định
millimeter coordinates khi chưa biết cup size/head geometry. Nếu không đủ chỗ
cho cups/paste không overlap, phải sửa allocation; không ép đủ số bằng cách
đặt chồng/chạm contacts. EIT electrodes là các **cửa truy cập điện vào volume**,
không phải 24 cảm biến của 24 cơ. Current field lan trong 3D; không chỉ chạy
thành một đường thẳng giữa hai contacts. Vị trí ngoài cơ mục tiêu vẫn có cơ
và mô tại chỗ; nhận biết smile ở tai chưa chứng minh đo được zygomaticus từ xa.

**Gold cup implications:** chưa có căn cứ loại bỏ hoặc mặc định phù hợp. Cần
ghi model/cup area, gel/paste, fixation và lead routing; kiểm tra drift/noise,
contact stability và movement effects ở tần số đo đã được lab xác nhận.
Không dùng threshold contact của EEG tần số thấp làm tiêu chí BioZ tùy ý.
[Kurniawan et al. 2022](https://doi.org/10.1002/nano.202100345) cho thấy
electrode impedance phụ thuộc material/diameter/frequency trong các điều kiện
của họ; đây là rationale cho characterization, không phải validation của
gold cups của user ở tần số CN0565 dự kiến. Dùng gold cup không làm setup trở
thành EEG; modality phụ thuộc cách kích thích và đo.

**Giảm electrodes đúng cách:** chọn một subset contacts, rồi chỉ giữ patterns
mà cả bốn Force/Sense contacts đều nằm trong subset đó. Giữ vài “channels”
nhưng vẫn cần tất cả 24 cups thì chưa giảm electrode count. Làm selection
trong training/validation, khóa subset trước held-out test; sau offline
ablation cần thu lại với thiết bị reduced thật. Không suy vị trí ngoài pool
C24 không tốt chỉ vì chưa được đo.

## 19. Mô hình cơ mặt: cần hiểu đến đâu ở giai đoạn đầu?

Đừng hình dung mỗi lớp là một resistor mắc nối tiếp duy nhất. Mặt là **volume
3D với nhiều đường dẫn song song**: interface da/electrode; skin/fat/connective
tissue; muscles có hướng sợi; blood/fluid; xương/răng; khoang khí và saliva.
Trong tế bào cơ vẫn có intracellular fluid, bên ngoài có extracellular fluid,
và cell membrane có tính điện dung. Đây là nguyên lý mô cơ, không phải cơ mặt
không có model vì khác cơ tay. Điều khó là hình học, tỷ lệ mô, hướng sợi và
co-activation của mặt khác, nên không copy các numerical values của forearm.

Trong pilot task recognition, cần biết **cái gì có thể làm số đo đổi** và ghi
controls tương ứng, chưa cần segment mọi nerve/vessel. Khi chuyển sang 3D EIT,
cần geometry/positions/contact và các tissue priors đủ để dự đoán sensitivity;
thêm độ chi tiết theo sensitivity analysis, không theo độ đẹp của anatomy mesh.

[Schooling, lateral tongue](https://doi.org/10.1088/1361-6579/abcb9b) có câu
hỏi dễ hiểu: “probe đặt lệch/ra mép/xoay thì có nhầm geometry thành tissue
change không?” Họ dùng layered anisotropic FEM, electrical models và dữ liệu
71 người (41 ALS, 30 healthy). Trong các điều kiện nghiên cứu của họ, phase
ít bị ảnh hưởng hơn magnitude ở một số thay đổi vị trí; mất contact làm kết
quả sai rõ. **Áp dụng cho mình:** lưu cả real/imaginary hoặc magnitude/phase,
và có redonning/placement-tolerance tests. **Không áp dụng:** tuyên bố phase
luôn chống motion trên mặt, copy tongue geometry, hoặc suy mỗi muscle có
một bộ R/C nhận diện được từ remote measurements.

## 20. Trừ reference vẫn hữu ích, nhưng kết luận phải đúng tầng

Với mỗi cấu hình `m`, đo rest thật ngay trước trial:

`b_m = mean(Z_m trong cửa sổ rest)`;
`Delta Z_m(t) = Z_m(t) - b_m`.

Lưu raw data và baseline, không chỉ difference; giữ thống nhất config/order,
frequency, sign và calibration. Nếu chia baseline để lấy relative change,
không dùng channels có baseline gần noise floor/zero; không trừ phase wrapped
như số thực thông thường. Khung 5 s rest của user là proposal: baseline window
phải được chọn trước và kiểm tra ổn định, không dùng test data để chọn đẹp nhất.

Ví dụ **số tự đặt để minh họa**, ba real-valued measurements: rest
`[100,120,80] ohm`, task `[103,119,84] ohm`, difference `[+3,-1,+4] ohm`.
Ta hỏi pattern này có xuất hiện lặp lại ở task A, khác task B và khác rest
drift không. Không hỏi “+3 ohm nghĩa là cơ yếu 3%”. Dấu transfer measurement
phụ thuộc drive/sense configuration; không có quy tắc toàn mặt “dương = cơ
co/yếu” hoặc “âm = cơ khỏe”.

**Bằng chứng vì sao không phải pure muscle:**

1. [Boyle & Adler, 2011](https://aboyle.ca/pubs/boyle2011a-elec_mvmt.pdf),
   *Impact of Electrode Area, Contact Impedance and Boundary Shape on EIT
   Images*: FEM/CEM simulations trong **difference EIT** cho thấy một số
   thay đổi contact/area/boundary tạo artifacts dù reconstruction quy chúng
   về conductivity. Không phải mọi contact change đều có cùng effect.
2. [Levit 2024](https://doi.org/10.1088/2057-1976/ad28cb): facial IPG/EMG có
   task-linked impedance changes liên quan vascular mechanics; narrowing là
   model-based interpretation, không phải direct radius measurement mọi trial.
3. [Kim 2019](https://doi.org/10.5664/jcsm.7714): upper-airway EIT đối chiếu
   MRI cho thấy một thay đổi khoang khí có thể tạo difference image; không cần
   giả thuyết riêng intrinsic muscle conductivity đổi. Họ cũng bàn motion và
   simultaneous EEG/EMG interference.

Do đó: baseline subtraction không xóa xương khỏi physics; xương vẫn định
hướng sensitivity với cái thay đổi. Nó loại phần **measurement không đổi**,
không tách được nguyên nhân của mọi phần thay đổi. Tuy nhiên hoàn toàn có
thể kết luận **task-associated impedance patterns** nếu vượt noise/drift và
lặp lại. Có held-out-session recognition thì kết luận về recognition được.
Muốn muscle-specific activation/weakness phải có bằng chứng độc lập mạnh hơn.

**Việc làm trước, theo thứ tự:** (1) map và test đủ 24 connections trên bench;
(2) đo scan duration, calibration/noise trên tải biết trước; (3) chốt feasible
cup layout và human-use review với lab; (4) pilot một core task set nhỏ kèm
rest/video và nuisance controls; (5) xem raw/time-series/channel-by-time heatmap
trước classifier hoặc ảnh mặt; (6) test redonning/held-out sessions rồi giảm
electrode subset. Heatmap measurement x time không phải anatomical EIT image.
