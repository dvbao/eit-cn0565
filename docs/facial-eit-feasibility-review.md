# Facial EIT feasibility — nghiên cứu, giới hạn, và hướng kiểm chứng

Ngày rà soát: 2026-09-29. Đối tượng: dự án CN0565 của Bao Dang.

Follow-up: [facial bioimpedance, models, placement và novelty](facial-bioimpedance-models-placement-novelty.md).
Bản follow-up bổ sung full text Liu 2025, Painometry và lower-face/neck EIT;
ưu tiên nó khi xác định related work và scope paper đầu tiên.

Đây là targeted literature review và đề xuất nghiên cứu, không phải systematic
review/PRISMA, xác nhận tính mới toàn diện, hay protocol được phép thử trên người.
Các kết luận feasibility bên dưới là tổng hợp có điều kiện, không phải kết quả
thực nghiệm của dự án. Không có thí nghiệm hardware/human nào được thực hiện
trong lần rà soát này.

## 1. Bài toán đã được người dùng xác nhận

Ứng dụng dài hạn: đánh giá hoạt động cơ mặt liên quan đến post-stroke dysarthria.
Thiết bị cuối cùng không đặt electrodes trực tiếp trên vùng cơ mục tiêu ở mặt
trước như orbicularis oris hoặc zygomaticus. Các vị trí được chấp nhận: dưới cằm,
viền hàm, trước/sau tai, thái dương, trán. Có thể dùng facial EMG và camera tạm
thời để validation. Người dùng đã chọn **task recognition với unobtrusive
placement** cho paper đầu tiên, và xác nhận có khả năng tuyển người khỏe mạnh
đo nhiều buổi cùng lab hỗ trợ safety/ethics review. Chưa xác nhận protocol được
phê duyệt; ý định self-pilot không phải một exemption.

**Research question đề xuất:**

> Can electrodes outside the anterior facial target-muscle regions capture
> repeatable, task-related bioimpedance changes, and how much muscle-specific
> information remains after accounting for motion and electrode-contact effects?

Nghĩa là: trước hết chứng minh có thông tin lặp lại được; sau đó mới kiểm tra
thông tin ấy có thực sự phân biệt các vùng cơ hay chỉ nhận biết chuyển động.

Dysarthria không chỉ là yếu cơ mặt: timing, coordination và các speech subsystems
khác cũng có thể bị ảnh hưởng. Vì vậy, nhận diện smile chưa phải đánh giá
dysarthria. Nguồn định hướng lâm sàng:
[ASHA — Dysarthria in Adults](https://www.asha.org/practice-portal/clinical-topics/dysarthria-in-adults/).

## 2. Kết luận feasibility theo từng mức

| Mức | Câu hỏi thực tế | Đánh giá từ tài liệu đã kiểm tra |
|---|---|---|
| Signal detection | Rest và một task có khác nhau không? | Có cơ sở để nghiên cứu; cần chứng minh với đúng layout của mình. |
| Task recognition | Phân biệt smile, lip protrusion, jaw opening? | Khả thi về hướng tiếp cận; robustness sau tháo/gắn lại là câu hỏi chính. |
| Regional information | Phân biệt thay đổi vùng trái/phải hoặc môi/má? | Chưa được bảo đảm; phụ thuộc sensitivity và mức tương đồng giữa các tín hiệu vùng. |
| Individual-muscle assessment | Riêng zygomaticus hay orbicularis hoạt động thế nào? | Khó hơn nhiều; phải xử lý co-activation, contact/motion và kiểm chứng specificity. |
| Clinical percentage | Cơ yếu bao nhiêu phần trăm ở bệnh nhân? | Chưa có định nghĩa/calibration/validation cho thiết kế này. Không suy ra từ màu heatmap. |

Đây là **judgment tổng hợp**, không phải xác suất thành công được papers công bố.
Các nguồn hỗ trợ và giới hạn được tách riêng dưới đây.

## 3. Evidence map — các nguồn quan trọng

Để giữ dễ tra cứu khi thuyết trình, phần tóm tắt paper dùng English; các phần
diễn giải và đề xuất phía sau dùng Vietnamese với English terminology.

### A. Direct facial EIT: Visentin, 2017

**An Electrical Tomographic Approach to Detect Deformation over Soft and
Flexible Materials**, PhD thesis, University of Tsukuba, Chapter 6.3,
printed pp. 55–57, Figures 6.3–6.4.

One volunteer performed exaggerated vowels and a smile. Adhesive electrodes
were placed on one side of the face, including anterior cheek/perioral sites.
Only A and smile produced clearly distinguishable reconstructed patterns.
The experiment deliberately exploited deformation/electrode displacement;
it does not establish isolated muscle conductivity imaging. Placement does
not satisfy this project's unobtrusiveness constraint. The reported excitation
wording is internally ambiguous and must not be copied as a safety recipe.

Access: full thesis section read; electrode-placement figure visually inspected.
Evidence type: dissertation proof of concept, not a clinical validation study.
[Full thesis](https://tsukuba.repo.nii.ac.jp/record/43368/files/DA08090.pdf).

### B. Direct facial-muscle impedance: FSHD EIM, 2016

**Electrical Impedance Myography in Facioscapulohumeral Muscular Dystrophy.**

The study used an electrically driven handheld probe, including measurements
over bilateral orbicularis oris. This directly establishes prior facial-muscle
impedance measurement. It is EIM, not remote-electrode tomography. Disease
composition measurements in FSHD do not establish task activation measurement
or post-stroke impairment estimation.

Access: full user-supplied PDF now available; methods, facial-placement figure
and reliability results checked. No facial gesture accuracy is inferred.
[Original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC4972708/).

### C. Facial EMG + impedance: Levit, Funk & Hanein, 2024

**Soft electrodes for simultaneous bio-potential and bio-impedance study of
the face**, Biomedical Physics & Engineering Express 10, 025036.

Separate soft arrays recorded muscle biopotentials and four-contact impedance
associated with the superficial temporal artery. Muscle activity coincided
with vascular-related impedance changes. ICA was applied to biopotentials,
not demonstrated as a method for separating EIT images into individual muscles.
This supports a combined EMG/impedance validation strategy and warns against
treating blood vessels as an electrically constant reference.

Access: publisher-authored abstract/PubMed and author-uploaded text; no
independent reanalysis. DOI: 10.1088/2057-1976/ad28cb.
[Original abstract](https://pubmed.ncbi.nlm.nih.gov/38350124/).

### D. Full text now verified: Liu et al., 2025

**Facial Gesture Recognition Using Bio-impedance Sensing**, AHs 2025,
pp. 491–493, DOI: 10.1145/3745900.3746120.

Authors: Mengxi Liu, Daniel Geißler, Sizhen Bian, Joanna Sorysz, Bo Zhou,
Paul Lukowicz. The user supplied the complete three-page paper. Three electrodes
(one below the mouth, one on each cheek) provide two bioimpedance channels;
there is no EIT image reconstruction. Four participants performed four active
gestures: left puff, right puff, omni puff and suck. A null class is also mentioned.
Reported mean accuracy is 93%, mean macro F1 0.92. Overlapping windows precede
an 80/20 split whose grouping is not specified; cross-participant or cross-session
generalization is not established. This raises a leakage risk, not proof of leakage.
See the follow-up review for methods, limits and implications for this project.

[Publisher/DOI](https://doi.org/10.1145/3745900.3746120),
[publisher-deposited metadata](https://api.crossref.org/works/10.1145/3745900.3746120).

### E. Ear-worn precedent, but a different target: FaceSense, 2021

**FaceSense: Sensing Face Touch with an Ear-worn System.**

The physiological subsystem used active lead-off impedance sensing and
biopotential signals. The measurement electrode was at the jaw junction over
superficial masseter, with a reference near the tragus. Face-touch deformation
changed skin/electrode contact. This is evidence for ear-adjacent sensing, but
not facial-muscle tomography; a useful task signal can itself be a contact
effect. Its exact placement still needs comparison with the user's comfort rule.

Access: original author-hosted paper, relevant methods/figures indexed.
[Author PDF](https://people.cs.umass.edu/~phuc/papers/facesense_2021.pdf).

### F. Partial-boundary mathematics: Hauptmann et al., 2017

**Direct inversion from partial-boundary data in electrical impedance tomography.**

Partial boundary access is an established inverse-problem setting. This work
studies a direct reconstruction approach and missing-boundary effects under
specific mathematical assumptions. It does not imply stable recovery of all
facial muscles with a few electrodes near the ears.

Access: author preprint/abstract. DOI: 10.1088/1361-6420/33/2/025009.
[Author version](https://arxiv.org/abs/1605.01309).

### G. Half-ring experimental evidence: Zhang, Wang & Song, 2026

**Electrical Impedance Tomography Reconstruction with Partial Boundary
Measurements**, Mathematics 14(5), 840.

Simulations and water-tank experiments compare 16-electrode three-quarter and
half-circumferential arrangements and several regularizers. This is practical
evidence that a complete electrode ring is not mandatory. It is not facial
validation. Critically, experimental RE/PSNR uses a TV reconstruction as the
reference because true conductivity is unknown; these metrics are not error
against independently measured ground truth. Regularization was manually tuned.

Access: indexed full article, methods/results checked.
[Original paper](https://www.mdpi.com/2227-7390/14/5/840).

### H. Local/open-surface muscle imaging: US/EIT, 2018 online / 2019 issue

**Towards Electrical Impedance Tomography Coupled Ultrasound Imaging for
Assessing Muscle Health.**

A local electrode array was integrated with an ultrasound probe. Ultrasound
segmentation provided anatomical constraints. Simulations, phantoms, and leg
measurements from three radiculopathy patients support investigating spatial
muscle properties with anatomical priors. A probe directly over a limb is not
equivalent to measuring a small facial muscle from the ear/jaw.

Access: original indexed full text, methods/results checked.
[Original study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6668036/).

### I. Planar wearable precedent: EITWatch, 2026 preprint

**EITWatch: Smartwatch-Integrated Planar Electrical Impedance Tomography for
Hand Gesture Recognition**, Liu, Alam & Ahuja.

Eight electrodes on the watch-back patch measured hand-related impedance
patterns; they did not surround the wrist circumference. Twelve participants
were studied. Cross-session/user performance deteriorated relative to
within-session results. This motivates testing re-donning robustness and
electrode geometry, not claiming equivalent facial performance. A planar ring
on a patch is geometrically different from a half-ring around a cross-section.

Status at review date: arXiv preprint; authors list UIST 2026, an upcoming event.
[Preprint](https://arxiv.org/abs/2608.29415),
[author project](https://xuanyouliu.com/projects/eitwatch/).

### J. Muscle-contraction bioimpedance, not face: Kusche et al., 2024

**A Wearable Dual-Channel Bioimpedance Spectrometer for Real-Time Muscle
Contraction Detection**, IEEE Sensors Journal 24(7), 11316–11327.

The authors demonstrated dynamic multifrequency muscle measurements, including
antagonistic and orthogonal arrangements. Useful methodological precedent for
phase/frequency analysis; not evidence of remote facial-muscle selectivity.
DOI: 10.1109/JSEN.2024.3359284.
[Author PDF](https://www.medical-sensors.com/papers/2024-A_Wearable_Dual-Channel_Bioimpedance_Spectrometer_for_Real-Time_Muscle_Contraction_Detection.pdf).

## 4. Phân biệt cái mình muốn đo và cái máy thật sự đo

### EIT, EIM, EMG không phải cùng một thứ

- **EMG:** ghi biopotential liên quan hoạt động điện của cơ.
- **EIM/bioimpedance:** đưa tín hiệu thăm dò vào, đo đáp ứng điện của một vùng.
- **EIT:** dùng nhiều drive–sense configurations cùng một model để ước lượng
  phân bố electrical properties. Có thể dùng dữ liệu đa kênh để classification
  mà không dựng ảnh, nhưng classification không tự chứng minh khả năng tomography.

Trong đề tài này, current injection nhằm **probe impedance**, không nhằm gây
co cơ như neuromuscular electrical stimulation. Task là do người tham gia làm.
Ba ví dụ facial ở mục A–C đủ để trả lời: đã có đưa tín hiệu điện thăm dò lên mặt;
nhưng chỉ mục A là minh chứng facial EIT trực tiếp được kiểm tra ở đây.

### Reference không phải “xóa hết mọi thứ trừ cơ”

Một cách diễn đạt conceptual:

\[
\Delta\mathbf v \approx
J_m\Delta\boldsymbol\sigma_m +
J_g\Delta\mathbf g +
J_z\Delta\mathbf z +
J_b\Delta\boldsymbol\sigma_b +\boldsymbol\epsilon.
\]

- \(\Delta\mathbf v\): vector những voltage changes đã đo; so sánh ở cùng
  drive current hoặc sau chuẩn hóa phù hợp.
- \(\Delta\boldsymbol\sigma_m\): thay đổi electrical properties vùng cơ.
- \(\Delta\mathbf g\): thay đổi hình dạng mặt/hàm và electrode positions.
- \(\Delta\mathbf z\): thay đổi tiếp xúc electrode–skin.
- \(\Delta\boldsymbol\sigma_b\): thành phần thay đổi liên quan máu/mạch.
- \(J\): **sensitivity**, tức một thay đổi nhỏ của từng yếu tố làm các kênh đo
  đổi theo mẫu nào. \(\epsilon\): noise và những phần model chưa mô tả.

Đây là mô hình tuyến tính hóa để tổ chức suy nghĩ; các thành phần có thể tương
quan, không phải những nguồn độc lập mà máy tự tách sẵn. Với AC, cần xét complex
admittivity và có thể cả anisotropy, không chỉ scalar conductivity.

Xương không cần thay đổi conductivity vẫn ảnh hưởng đường đi của current và
sensitivities. Hàm có thể chuyển động. Khi task làm các yếu tố trên thay đổi,
baseline subtraction không loại bỏ được chúng. Joint reconstruction of movement
and conductivity đã có tiền lệ; contact changes cũng đã được ước lượng cùng ảnh:
[Soleimani et al., 2006](https://pubmed.ncbi.nlm.nih.gov/16636402/),
[simultaneous contact/image reconstruction](https://pmc.ncbi.nlm.nih.gov/articles/PMC5145793/).

**Ví dụ do mình đặt để giải thích, không phải kết quả paper:** giả sử co cơ A
và kéo nhẹ da gần electrode đều tạo cùng vector đo \([1,2,1]\). Nhìn vector này
không thể biết nguyên nhân nào. Đổi từ BP sang GREIT không tự tạo thêm thông tin.
Phải thêm phép đo có sensitivity khác, reference bổ sung, hoặc một giả thiết có
thể kiểm chứng. Đây là vấn đề **identifiability**: nguyên nhân có phân biệt được
từ dữ liệu hiện có hay không?

## 5. Closed-ring, half-ring và các layout nên so sánh

**Vòng mạch điện phải có đường về; các electrodes không bắt buộc nằm thành một
vòng hình học bao kín.** Partial boundary không có nghĩa “cắt đôi khuôn mặt”
trong model rồi đặt insulating boundary ở đường cắt. Miền dẫn điện vẫn phải
mô tả đúng vùng cơ thể mà dòng thăm dò có thể đi qua.

Dưới đây là **candidate designs để mô phỏng**, chưa phải vị trí tối ưu/safe
placement được papers xác nhận cho mặt:

| Candidate | Vị trí trong vùng bạn chấp nhận | Câu hỏi cần kiểm chứng |
|---|---|---|
| L1 — distributed peripheral array | Hai bên tai/thái dương + trán + viền hàm/dưới cằm | Bổ sung các hướng đo có cải thiện phân biệt các ROI không? |
| L2 — jaw/ear U-array | Một cung dọc hàm và dưới cằm, hai đầu gần tai | Có giữ được thông tin lip/cheek tasks khi giảm coverage không? |
| L3 — ear-centered array | Chủ yếu trước/sau hai tai | Độ gọn có đánh đổi quá nhiều sensitivity hoặc tính phân biệt nguồn không? |

So sánh cùng số electrodes trước để tách ảnh hưởng **coverage** khỏi ảnh hưởng
**electrode count**. Sau đó mới thử ít electrodes hơn. Không gán thắng/thua chỉ
theo khoảng cách ngoài da. Thái dương/trán/dưới cằm cũng có cơ và chuyển động:
“không nằm trên target” không có nghĩa “không có physiological confounds”.

Mỗi layout cần đi cùng drive/sense pattern. Adjacent là baseline để so sánh,
không mặc định tối ưu cho remote sensing. Rộng khoảng cách điện cực có thể thay
đổi vùng sensitivity nhưng không tự bảo đảm đo được một cơ sâu/xa cụ thể.
Electrode optimization có cơ sở inverse-problem:
[Optimizing electrode positions in EIT](https://arxiv.org/abs/1404.7300).

## 6. Simulator hiện tại có ích gì, và chưa mô phỏng cái gì?

Kiểm tra trực tiếp `scripts/eit_sim_playground.py` cho thấy đây là 2D unit disk,
16 point electrodes, homogeneous background, ideal unit-current FEM, circular
anomalies; BP/JAC/GREIT nhận cùng synthetic data. Nó là **algorithm playground**,
chưa phải **facial-muscle simulator**.

| Trong playground | Không nên diễn giải thành |
|---|---|
| `BACKGROUND_SIGMA = 1` | Một loại mô cơ thể xác định |
| `perm = 10` | Cơ co mạnh gấp 10 lần hoặc activation tăng 900% |
| `r = 0.12` | Cơ có kích thước 0.12 cm |
| `h0 = 0.08` | Khoảng cách electrodes hay độ phân giải lâm sàng |
| Mesh nhiều nodes/elements | Có thêm independent measurements |
| Một vùng đỏ trên reconstruction | Cơ tương ứng chắc chắn đang hoạt động tốt |

Để nghiên cứu layout mặt, cần nâng cấp theo giai đoạn:

1. **Geometry:** anatomical/approximated 3D volume, electrode coordinates và
   diện tích; không ép tất cả vị trí tai–cằm–trán vào một lát cắt tròn.
2. **Tissues:** tối thiểu skin/fat, relevant muscle ROIs, bone và oral air space;
   mở rộng cấu trúc khi sensitivity analysis cho thấy cần thiết.
3. **Electrical model:** frequency-specific properties, muscle anisotropy,
   electrode-contact model. Nguồn giá trị phải ghi rõ frequency, tissue,
   phương pháp đo và uncertainty. Không có một “sigma của mặt” dùng mọi trường hợp.
4. **Task hypotheses:** conductivity-only, deformation-only, contact-only,
   vascular-only, rồi combined. Không mặc định task chỉ đổi conductivity.
5. **Model mismatch:** forward mesh và inverse mesh khác nhau; perturb geometry,
   contacts, tissue values. Không dùng cùng một model hoàn hảo làm toàn bộ chứng cứ.

Những cải tiến này là kế hoạch đề xuất, **chưa được implement** trong repo.

## 7. Các test cụ thể — ưu tiên khả năng phân biệt trước heatmap

### 7.1 Simulation tests, không cần hardware/human

| Test | Giữ cố định / thay đổi | Trả lời điều gì? |
|---|---|---|
| Null | Không thay đổi cơ; thêm measured-like noise | Thuật toán có bịa vùng hoạt động không? |
| One ROI at a time | Chỉ đổi từng ROI ở cùng mức giả định | Mỗi cơ/vùng có electrical signature riêng không? |
| Same task contrast, different layout | L1/L2/L3, cùng electrodes count và ngân sách phép đo | Layout nào chứa nhiều thông tin hữu dụng hơn? |
| Near vs far target | Di chuyển cùng anomaly từ gần electrodes ra xa | Sensitivity giảm và localisation sai thế nào? |
| Two simultaneous ROIs | Hai vùng gần nhau/cùng đổi hoặc trái dấu | Có tách được hay bị nhập thành một vùng? |
| Geometry-only | Tissue properties cố định, thay geometry/electrode positions | Có xuất hiện false muscle activation không? |
| Contact-only | Chỉ đổi một/vài contact parameters | Có nhầm contact artifact thành activity không? |
| Remount mismatch | Perturb electrode coordinates trong model thật so với inverse | Robustness sau tháo/gắn lại? |
| Frequency/noise sweep | Vary frequency-specific model và noise | Tín hiệu nào còn phân biệt được trên noise floor? |

Một sweep engineering khởi đầu có thể dùng \(\pm1,\pm5,\pm10\%\) conductivity
change quanh baseline. **Đây là các mức giả định để hỏi “cần sensitivity bao
nhiêu?”, không phải mức thay đổi cơ mặt đã được chứng minh.** Thay bằng ranges
được đo/được paper hỗ trợ khi có dữ liệu. Không dùng chúng để quy đổi activation.

Trước reconstruction, nhìn cột của ROI sensitivity matrix: hai ROI cho
patterns càng giống nhau thì càng khó tách. Đánh giá cả signal amplitude so
với measured noise; correlation thấp mà signal chìm trong noise vẫn không hữu
ích. Có thể so sánh noise-whitened sensitivities, singular values và uncertainty.

### 7.2 Chọn thuật toán thế nào cho câu hỏi mới?

- **BP:** giữ làm baseline để biết một phép xử lý đơn giản đạt tới đâu.
- **JAC/regularized inversion:** thuận tiện để kiểm tra sensitivities, anatomy
  priors và thêm nuisance parameters như movement/contact.
- **GREIT:** chỉ có ý nghĩa khi reconstruction map được dựng/huấn luyện cho
  đúng geometry, protocol và phân bố giả định; không dùng nguyên disk map cho mặt.
- **ROI model:** ban đầu cân nhắc ước lượng vài vùng thay đổi thay vì hàng nghìn
  pixel. Ít unknowns hơn, nhưng cần kiểm tra model bias và muscle co-activation.
- **Classification baseline:** thử trực tiếp measured features; so sánh với
  reconstruction-derived features. Ảnh không mặc nhiên tăng thông tin.

Đây là hướng thiết kế đề xuất, không tuyên bố một algorithm thắng trước khi có
test. So sánh cùng input, cùng data split; tune regularization trên validation,
không dùng test set. Heatmap phải có color scale rõ; các panel autoscale riêng
trong playground hiện tại không cho phép so amplitude chỉ bằng độ đỏ.

### 7.3 Bench và phantom trước human

1. Test reference resistor/RC loads để kiểm tra real/imaginary response,
   channel ordering, polarity, drift và repeatability.
2. Đo actual frame time sau khi gồm switching, settling, averaging và mọi
   frequency. ADC sample rate không phải complete-frame rate.
3. Phantom đồng nhất kiểm tra null; phantom có inclusions kiểm tra localization.
4. Với câu hỏi facial layout, thêm limited-access/3D phantom; kiểm soát riêng
   deformation và contact. Petri dish là bước hardware sanity check tốt nhưng
   không chứng minh facial feasibility.
5. Ghi actual current hoặc transfer impedance phù hợp. CN0565 dùng voltage
   excitation và đo current; simulator hiện dùng ideal unit current. Phải làm
   rõ normalization trước khi so hai loại dữ liệu.

Các điểm CN0565 được đối chiếu với
[Analog Devices circuit note](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/cn0565.html).

### 7.4 Pilot trên người — chỉ sau safety/ethics review

Đề xuất khung thiết kế, **không phải hướng dẫn kết nối hay thông số current**:

- Rest, smile, lip protrusion và lip closure là candidate tasks; thêm jaw opening
  và head motion làm confound controls. Tasks huy động nhiều cơ, không là nhãn
  ground truth tuyệt đối cho một cơ.
- Bắt đầu held poses để giảm thay đổi trong một frame; sau khi kiểm chứng temporal
  resolution mới xét dynamic/speech tasks với SLP.
- EMG cho activation-related reference; camera cho movement/landmarks. Thêm audio
  nếu nghiên cứu speech. Tất cả cần timestamps chung và kiểm tra latency.
- Kiểm tra xem EIT injection có gây artifact/saturation ở EMG không; khả năng
  đo đồng thời và an toàn của các máy nối chung phải được review.
- Đảo thứ tự tasks, lặp lại với rest, có nhiều ngày và tháo/gắn electrodes lại.
  Một người chỉ cho within-person feasibility, không cho clinical generalization.
- Tách train/test theo cả trial rồi theo session/day; không chia ngẫu nhiên
  các overlapping windows từ cùng một lần làm task vào cả train và test.
- Report cả failures, confusion matrix, macro-F1/balanced accuracy, baseline
  drift, false activity during controls và độ lặp lại. Không chỉ chọn ảnh đẹp.

**Điểm quyết định:** task recognition tốt nhưng không tách khỏi movement/contact
có thể vẫn hữu ích như wearable gesture sensor. Nó chưa đáp ứng claim
muscle-specific functional assessment. Ngược lại, muốn đi tiếp tới chức năng cơ
phải cho thấy giá trị bổ sung so với camera/contact-only explanations.

## 8. “Bao nhiêu phần trăm” cần một mẫu số

Ba số sau là ba outcomes khác nhau:

1. \(100\Delta Z/Z_0\): phần trăm impedance change của một measurement, với
   quy ước complex/magnitude/phase phải nói rõ; không phải phần trăm sức cơ.
2. EMG amplitude normalized to a defined reference task: relative EMG measure;
   không tự bằng muscle force hoặc clinical impairment.
3. Clinical loss of function: cần outcome/reference thích hợp do clinical team
   xác định, sau đó hiệu chuẩn và external validation.

Không nên đặt endpoint đầu tiên là “đo cơ yếu 30%”. Endpoint đầu tiên đề xuất:
**repeatable task-related information across sessions, with quantified nuisance
sensitivity**. Sau đó chọn regional/muscle outcome có reference kiểm chứng được.

## 9. An toàn và tự thử trên mình

CN0565 có galvanic isolation, DC-blocking capacitors và current limiting.
Đây không phải chứng nhận an toàn cho setup cuối cùng, đặc biệt khi nối thêm
PC/EMG/oscilloscope. Cần review toàn hệ thống, cables, contacts và fault conditions;
thông số trong paper không là safe setting cho thiết kế khác.
[Manufacturer documentation](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/cn0565.html).

Trước khi thử trên chính mình, cần supervisor và người có chuyên môn electrical
safety xem xét setup hoàn chỉnh, cùng quyết định của đơn vị human-research/IRB
tại trường về protocol. Self-experimentation không tự tạo exemption. Ví dụ,
Georgia Tech yêu cầu mô tả self-experimentation trong hồ sơ gửi IRB; đây là
minh họa chính sách của một trường, không thay thế chính sách trường bạn:
[Human Subject Guide, Appendix 13](https://oria.gatech.edu/sites/default/files/pdfs/IRB/irbpoliciesandprocedures_new_rule.pdf).

Trong lúc chờ review vẫn làm được simulation, sensitivity analysis và bench/
phantom. Báo cáo này không đưa amplitude/frequency hay sơ đồ nối người để thực thi.

## 10. Novelty, alternative baselines và reading order

Không viết: “No one has used EIT on the face.” Cách phát biểu thận trọng hơn:

> Prior work supports facial impedance sensing and preliminary facial EIT.
> The open question for this project is whether restricted peripheral electrode
> placement provides reproducible, muscle-informative measurements for eventual
> post-stroke speech assessment.

Đây là **candidate gap**, chưa phải xác nhận priority. Toàn văn Liu 2025 đã được
kiểm tra trong follow-up; Painometry 2020 và các nguồn mới cũng cần được tính
vào novelty. Scope paper đầu tiên đã thu gọn thành task recognition.

Không nên lập luận rằng EMG bắt buộc có electrode trên mọi target muscle.
ExGSense nghiên cứu near-eye biopotentials cho facial gestures; tuy vậy layout
của nó không mặc nhiên phù hợp constraint của bạn và gesture recognition không
đồng nghĩa muscle-specific function. Đây là comparison baseline đáng biết:
[ExGSense, 2021 — author PDF](https://xyzhang.ucsd.edu/papers/Chen.Chen_IPSN21_ExGSense.pdf).

Reading order đề xuất:

1. Visentin Ch. 6.3: phân biệt image pattern với mechanism.
2. Levit 2024: vì sao vascular effects và EMG validation quan trọng.
3. Liu 2025: đọc full text đã có; so sánh placement và evaluation split.
4. Zhang et al. 2026: partial-ring phantom, kèm giới hạn ground-truth metrics.
5. US/EIT và electrode-position optimization: anatomy và sensitivity trước
   algorithm choice.
6. Joint movement/contact reconstruction: algorithmic next steps nếu physics
   và measurement quality đủ tốt.

Search scope: facial EIT, facial bioimpedance/EIM, expression/gesture sensing,
remote/ear-worn placement, partial-boundary EIT, muscle imaging, contact/motion
compensation. Sources include primary studies, author repositories, dissertation,
manufacturer documentation and institutional guidance. Abstract-only/metadata-
only evidence is explicitly marked. No source examined here validates the entire
combination of the user's exact layout, individual-muscle percentage output,
and post-stroke dysarthria population.

## 11. Quyết định đã nhận và những gì còn mở

Người dùng đã chọn **task recognition với unobtrusive placement** trước và có
nguồn lực recruitment/lab review. Không cần hỏi lại hai quyết định đó.
Còn mở: task set, giới hạn electrode burden, exact baseline option, số người/
số buổi và trạng thái phê duyệt cụ thể. Xem `research-memory.md` để giữ riêng
câu trả lời đã xác nhận với diễn giải còn có điều kiện.
