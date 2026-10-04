# Pilot 01 — facial bioimpedance với 16 electrodes

**Version 0.3 (2026-10-02), draft cho lab review; chưa được phê duyệt đo trên người.** User đã chốt **hai phiên/layout riêng, mỗi phiên 16 gold-cup electrodes**: D16-M đặt trên vùng cơ làm near-muscle comparator, C16-R ở tai–hàm/trán để kiểm tra unobtrusive sensing. Đây **không phải 32 electrodes cùng lúc**. [Bản 24 C24/P12 cũ](archive/facial-bioimpedance-pilot-01-24-v0.1.md) không áp dụng. [Manifest C16-R](protocols/facial-pilot-01-design.json) và [manifest D16-M](protocols/facial-pilot-01-direct-muscle-design.json) là drafts, không điều khiển hardware.

## 1. Câu hỏi và mức kết luận

Cùng một participant và task set, layout **trên/gần cơ D16-M** có tạo task-associated BioZ khác layout **remote C16-R** không, và C16-R còn phân biệt task lặp lại được sau remount hay không? Đây là task-recognition/placement feasibility. Pilot **không** chứng minh từng cơ nào yếu, phần trăm activation, EIT image hay 3D reconstruction. Một lần đo mỗi layout chỉ cho signal comparison thăm dò, chưa tách được layout effect khỏi order/time/remount drift.

Ký hiệu: **[E]** điều nguồn đã chứng minh; **[P]** đề xuất; **[V]** phải kiểm chứng. Liu et al. [S3] đã đo facial BioZ gần má/miệng; không chứng minh layout remote này. Kim et al. [S4] dùng head/neck EIT với ROI khác; không chứng minh các vị trí sau là tối ưu. Atlas Schumann [S2] hỗ trợ chọn task, không chứng minh một task chỉ kích hoạt một cơ.

## 2. Chọn layout theo câu hỏi nghiên cứu: không đánh tráo “vùng” thành “cơ”

**Sửa lỗi phiên bản 0.2:** C16-R ở phần dưới là layout *remote*, không phải 16 contacts đặt trên 16 cơ. Tên cơ không thể được gán cho một contact chỉ vì nó ở cùng nửa mặt. Cơ là một **hypothesized physiological source / target of interest**; cup là **skin contact**; phép đo four-terminal có sensitivity phân bố theo cả đường dòng và vị trí sense. Ba khái niệm này khác nhau. Ghi “L3 = zygomaticus major” khi L3 ở trước tai sẽ là sai.

[Schumann et al. 2021, Fig. 1](https://doi.org/10.1371/journal.pone.0254932.g001) dùng **44 điện cực sEMG** đối xứng trên 10 nhóm mimic muscles (và đo masseter/temporalis làm chewing controls), điện cực **Ag/AgCl đường kính 4 mm**, reference ở dái tai và ground tại mastoid. [Table 1](https://doi.org/10.1371/journal.pone.0254932.t001) là bằng chứng *muscle activity during tasks*, **không phải** bằng chứng BioZ/EIT placement, electrode size cho gold cups, current field, hoặc signal attribution. Figure 1 chỉ có thể là **anatomical placement comparator** khi ta quyết định chấp nhận contacts trên phần trước mặt. Reference/ground của monopolar sEMG trong bài cũng **không được sao chép** sang CN0565 four-terminal.

Hai layout đã được user chọn để đo ở **hai phiên riêng**, nhưng **không thể dùng cùng một claim**:

| Layout | Contacts nằm ở đâu | Điều có thể kiểm tra | Điều không được claim |
|---|---|---|---|
| C16-R, remote candidate | Trán ngoài, thái dương, quanh tai, bờ hàm, dưới cằm; tránh cơ quanh má/miệng | Task recognition dưới ràng buộc unobtrusive | Đã đặt trực tiếp trên zygomaticus/orbicularis; định vị riêng từng cơ |
| D16-M, near-muscle comparator candidate | 16 contacts chia hai bên, trên da phủ các vùng cơ chọn từ Fig. 1 | Kiểm tra near-muscle signal và loss/gain khi chuyển sang C16-R | Paper EMG chứng minh EIT sensitivity, hoặc một cup đo riêng một cơ |

**Giới hạn đếm:** atlas đã theo dõi 10 nhóm mimic muscles hai bên, chưa kể hai chewing-muscle controls. Với 16 contacts không thể mặc nhiên “một contact trên mỗi muscle ở cả hai bên” cho toàn bộ atlas; còn phép đo EIT cần bốn contact trong **một configuration**. Phải chọn cơ ưu tiên theo tasks, giải thích cơ nào bị bỏ và test sensitivity. Nếu dùng gold cups lớn hơn đĩa 4 mm của paper, không thể copy từng chấm trong Fig. 1 mà không kiểm tra khoảng cách, cản trở biểu cảm và current path.

## 3. Layout remote C16-R [P,V]: từng contact và cơ liên quan

Không đặt trực tiếp trên phần trước má/môi hoặc trên orbicularis oris/zygomaticus. 8 trái + 8 phải = **16 contacts**. Không gán số mm khi chưa biết kích thước cup, paste và fixation. Trước mỗi run, chụp ảnh front/left/right, gắn nhãn site và landmark; ghi vị trí thật, cup diameter, paste, tóc và khả năng dính. Nếu hai cup chạm nhau hoặc không giữ được, phải sửa và version layout **trước** khi xem task results.

| Contacts (mỗi mã L/R là **một cup riêng**) | Vị trí da [P] | Cơ ở gần / điều được phép ghi, không phải nguồn tín hiệu đã chứng minh | Target task để test |
|---|---|---|---|
| L1 và R1 | Trán ngoài | Có thể trên vùng **frontalis** theo Fig. 1; phải verify vị trí thực trên ảnh. Không phải upper-lip sensor | T24 brow raise làm positive task/control; core oral tasks có thể kéo trán theo |
| L2 và R2 | Thái dương | Gần **temporalis** (chewing control của atlas); vị trí da phải verify, không gán cho zygomaticus | Jaw clench exploratory/control |
| L3 và R3 | Trước tai | **Không có muscle label đơn nhất từ atlas**; gần temporomandibular/parotid region, movement/contact confound. Không phải zygomaticus major | T22/T23 smile trái/phải là test *remote sensitivity*, không phải local muscle sensing |
| L4 và R4 | Sau tai | **Không có target muscle trong Fig. 1** cho vị trí này; dùng để thử posterior current path, tóc/contact quan trọng | Null, remount và mọi task |
| L5 và R5 | Dưới góc hàm | Không gọi là masseter: Fig. 1 đặt masseter trên vùng mặt bên của hàm, **không phải mặc nhiên dưới bờ hàm** | Jaw-open/clench control; smile/purse exploratory |
| L6 và R6 | Giữa bờ dưới hàm | Không ở trên **depressor anguli oris** hay **depressor labii inferioris** của Fig. 1; là lower-face remote contact | T8/T10/T11 trong giai đoạn exploratory |
| L7 và R7 | Bờ hàm trước, dưới/ngoài vùng quanh miệng | Không gọi là **mentalis** hoặc **orbicularis oris** nếu cup không thật sự ở trên cằm trước/vòng môi; phải chụp ảnh landmark | T14 purse, T22/T23 smile |
| L8 và R8 | Dưới cằm hai bên | Không có muscle label đơn nhất trong atlas; floor-of-mouth/jaw/neck motion có thể cùng ảnh hưởng | T14 purse, T15 puff, jaw control |

Các nhãn L/R phải tương ứng **bên trái/phải của participant**, không phải trái/phải khi nhìn ảnh. Hai vị trí cùng hàng phải được mirror theo landmark và ghi khoảng cách thực; “đối xứng” không có nghĩa cùng sensitivity. Đặc biệt L3–L8 **không thể** được paper sEMG dùng để chứng minh đo trực tiếp zygomaticus, orbicularis oris, levator labii, depressors hay mentalis. Đây là lý do bài toán unobtrusive có novelty nhưng cũng có risk feasibility.

## 4. Layout D16-M: tám vùng cơ mỗi bên [P,V], phiên comparator riêng

**DL/DR = trái/phải của participant**; mỗi hàng là *hai* gold cups, một bên trái và một bên phải. Đây là tên vùng cơ **dưới/về gần cup dự kiến**, không phải kết luận rằng tín hiệu BioZ của cup chỉ đến từ cơ đó. Chọn tám vùng theo core oral/smile tasks và jaw control; đánh dấu trên mặt thật cùng Fig. 1, chụp ảnh, rồi nhờ người có chuyên môn anatomy/clinical EMG kiểm tra. Hình atlas **không cung cấp tọa độ mm** để dán cup.

| Cup trái/phải | Vùng cơ cần đặt trên da phủ [P] | Atlas support và task để verify | Vì sao/giới hạn |
|---|---|---|---|
| DL1/DR1 | **Zygomaticus major** trên má ngoài | Fig. 1 có major/minor; T9/T22/T23 ghi “zygomatic” | Chọn major vì vùng ứng viên accessible hơn [P]; Table 1 **không tách** major khỏi minor |
| DL2/DR2 | **Levator labii superioris** phía bên mũi–môi trên | T12; Fig. 1 phân biệt levator labii superioris và alaeque nasi | Hai cơ sát nhau; một gold cup không chứng minh tách được chúng |
| DL3/DR3 | **Orbicularis oris**, vùng quanh môi trên | T14 và T7; Fig. 1 | Cup/gel có thể cản pursing và nói, phải kiểm tra fit |
| DL4/DR4 | **Orbicularis oris**, vùng quanh môi dưới | T14; T10/T20 nêu inferior oris | Cùng một cơ vòng với DL3/DR3, **không** tính là cơ thứ hai |
| DL5/DR5 | **Depressor anguli oris**, dưới góc miệng | T7/T8/T9/T11 | Nhỏ, gần depressor labii và oris; cup footprint có thể phủ nhiều cơ |
| DL6/DR6 | **Depressor labii inferioris**, dưới môi dưới lệch bên | T10/T11/T20 | Cần phân biệt ảnh vị trí với mentalis/DAO |
| DL7/DR7 | **Mentalis**, cằm trước hai bên đường giữa | T11/T15/T18 | Hai cup có thể quá sát nhau; nếu overlap thì layout fail, không ép đặt |
| DL8/DR8 | **Masseter**, mặt bên góc hàm | Fig. 1: chewing-muscle **control**, không phải cơ mimic chính | Jaw clench control; không đồng nhất với remote L5/R5 dưới bờ hàm |

Frontalis, orbicularis oculi, zygomaticus minor, temporalis và vùng levator labii superioris alaeque nasi **không có cup riêng** trong D16-M; đây là lựa chọn tài nguyên theo task chứ không phải nói chúng không quan trọng. DL3/DL4 (và DR3/DR4) có thể không đặt vừa gold cups quanh môi; **không có phiên D16-M hợp lệ nếu cups chạm nhau, cản task hoặc vùng cơ không được xác nhận**. Cần đo đường kính/footprint của cup và khoảng cách thật trước khi chốt; nếu thay cơ/site, version lại manifest và task hypotheses. **Không tái dùng M08 patterns** của C16-R trên D16-M: geometry/current fields khác.

### Atlas task–muscle matrix: nguồn gốc của lựa chọn cơ, không phải BioZ ground truth

Các tên dưới đây là **“muscles with highest sEMG activity” trong Table 1** của 30 nam tình nguyện viên khỏe mạnh, không phải cơ duy nhất hoạt động hay cơ được EIT định vị. “Zygomatic” trong bảng không phân biệt major/minor. Paper **không đo buccinator**, dù có task phồng/hóp má. Sáu nguyên âm T1–T6 là nguyên âm tiếng Đức, không tự động tương đương danh sách nguyên âm khác.

| Task atlas | Cơ được Table 1 báo hoạt động sEMG cao nhất | Ý nghĩa cho D16-M / C16-R |
|---|---|---|
| T14 pursing lips | Orbicularis oris | D16-M DL3/DL4 là vùng gần cơ; C16-R chỉ test remote detection |
| T22 right smile, T23 left smile | “Zygomatic” | D16-M DR1/DL1 là candidate; không claim zygomaticus major đơn độc |
| T9 bilateral smile | Zygomatic, orbicularis oris, mentalis, depressor labii, depressor anguli oris | Mixed task; so signal pattern, không gọi single-muscle anchor |
| T7 pressing lips; T8 corners down | T7: orbicularis oris, depressor anguli oris, mentalis, depressor labii, zygomatic. T8: inferior orbicularis oris, depressor anguli oris, depressor labii, mentalis | D16-M có nhiều vùng liên quan; không quy ΔZ một cơ |
| T10 lower-lip depression; T11 lower-lip protrusion | T10: inferior orbicularis oris, depressor labii, mentalis. T11: mentalis, depressor anguli oris, depressor labii, orbicularis oris | Có thể thêm exploratory nếu video kiểm tra đúng động tác |
| T12 upper-lip lift | Levator labii superioris alaeque nasi, levator labii superioris, orbicularis oris | D16-M DL2 là một vùng; không tách hai levators |
| T15 puff cheeks; T16 suck cheeks | Orbicularis oris, mentalis, depressor labii | **Buccinator không được paper này ghi đo**; khí/áp suất là confound |
| T18 jaw open with closed lips | Mentalis, orbicularis oris, depressor labii, depressor anguli oris | Không suy jaw-opening muscles từ bảng sEMG này |
| T24 brow raise | Frontalis | C16-R L1/R1 là vùng gần cơ, có thể dùng control |

**Thiết kế paired comparison đã được user chọn:** cùng participant, cùng task script, duration/cues, cùng gold-cup type và acquisition settings đã lab duyệt; hai phiên layout D16-M và C16-R **không ghép hai vị trí vào một frame**. Ghi session ID, order, thời gian nghỉ, remount, ảnh vị trí và contact quality. Nếu chỉ một phiên mỗi layout, kết quả bị lẫn với order/day/contact drift — báo exploratory. Để ước lượng layout effect đáng tin hơn, lặp lại một ngày khác với thứ tự đảo ngược, hoặc counterbalance order giữa participants ở study nhiều người; protocol này **chưa chứng minh** được hiệu ứng từ một cặp phiên. So sánh chính là trial-level task/rest SNR, repeatability và held-out-session classification, **không** so trực tiếp giá trị ΔZ của hai geometries như cùng một kênh sinh học.

**Không có paper nào chứng minh chính xác layout C16-R.** Lý do khoa học là sensitivity phụ thuộc geometry, ROI và electrode/contact [S5,S10]; tính hữu ích của layout phải được test bằng known loads, null/motion controls, repeatability và nếu cần comparator gần mặt trong study riêng.

## 5. Wiring, force/sense và 8 patterns ứng viên

Mỗi phép đo four-terminal dùng **F+, F−** để drive và **S+, S−** để sense differential voltage. Một electrode có thể đổi vai trò qua các phép đo do switch matrix. F− là current return, S− là cực đo voltage âm; **không phải body ground** hoặc reference state. Không thêm body-bias/ground electrode trong bản này; không nối participant tới GND_ISO/USB earth. Nếu lab xác định wiring khác, phải sửa protocol và safety review trước human use.

Theo CN0565 schematic Rev B [S1], P1 pins **3–14 = X0–X11**, **17–28 = X12–X23**; pins **1, 2, 15, 16, 29, 30 = GND_ISO**, không dùng làm site đo. 16 cups sẽ dùng 16 trong 24 X lines, còn 8 không nối người. **Chưa có bảng site → physical lead → P1 pin → X → Python index được verify.** Lập bảng đó bằng continuity/known-load bench check, đối chiếu chiều pin 1 trên connector; không suy từ số thứ tự site.

**M08 [P,V]**, tám configurations dưới đây dùng đủ 16 contacts. Không gọi là optimized EIT protocol hay 8 simultaneous measurements.

| ID | F+ | F− | S+ | S− | Ý định |
|---|---|---|---|---|---|
| M01 | L3 | L7 | L5 | L6 | Lower face trái |
| M02 | R3 | R7 | R5 | R6 | Lower face phải |
| M03 | L4 | L8 | L5 | L7 | Sau tai–dưới cằm trái |
| M04 | R4 | R8 | R5 | R7 | Sau tai–dưới cằm phải |
| M05 | L1 | L5 | L2 | L3 | Upper/lateral trái |
| M06 | R1 | R5 | R2 | R3 | Upper/lateral phải |
| M07 | L5 | R5 | L7 | R7 | Lower face hai bên |
| M08 | L1 | R1 | L8 | R8 | Upper–inferior hai bên |

Mỗi pattern phải qua kiểm tra mapping, current path, signal range, settling và frame duration. Nếu thay pattern sau khi xem kết quả sẽ gây selection bias: version manifest trước thu primary data. 16×13 = 208 chỉ là số của **một** adjacent-drive/cyclic scheme cụ thể, không phải số phép đo bắt buộc của 16 contacts trên mặt. M08 cho tám phép đo **tuần tự**/frame. Nếu sau này cần electrode subset optimization, một pool patterns rộng hơn có thể cần thiết; M08 không chứng minh subset tối ưu.

## 6. Bench và human-use gate

**Không thử trên người cho đến khi lab review toàn hệ thống**: CN0565 firmware, nguồn/USB/isolation, leakage/DC/fault current, limits của current qua từng intended path, leads/cups/gel, các thiết bị nối đồng thời, consent và quy trình human-use. Tự thử trên mình vẫn là human-use. Không copy amplitude/current “an toàn” từ thiết bị của paper khác. Dừng khi đau, nóng/rát, co bất thường hoặc khó chịu; không tăng excitation chỉ để tạo tín hiệu.

Trên resistor/RC known load và fixture/phantom: (1) verify từng line, F/S polarity, units, calibration, real/imaginary phase và đáp ứng với load change; (2) log static noise/drift, cross-talk, switching transient, settling và start/end timestamps mỗi M01–M08 **cho C16-R**; (3) test movement, contact reapplication, no-target drift; (4) kiểm tra compliance/clipping, measured current và complete-frame rate. ADC rate không bằng frame rate. **D16-M chưa có pattern panel được bench-verify**, nên chưa phải acquisition-ready; phải thiết kế/kiểm tra riêng trước khi so hai layouts. Nếu 5 s task không chứa đủ complete frames thì đổi timing hoặc panel và version trước đo người.

**20, 50, 100 kHz chỉ là các bench candidates [P]**: CN0565 [S1] có characterization ở 20 kHz, upper-airway EIT [S4] dùng 50 kHz, facial BioZ [S3] dùng 100 kHz. Không thể suy một tần số tối ưu cho layout này. **Human frequency, excitation amplitude/current, RTIA/gain, DFT averaging và settling = TBD**, chốt từ bench data + lab approval. CN0565 drive bằng voltage và đo current, nên cùng DAC amplitude không có nghĩa cùng current qua các đường. Nếu output chỉ là raw voltage, phân tích **ΔV**, không gọi là ΔZ. Cần kiểm tra local collector: all_voltages đặt impedance_mode=False và demo sample_plot dùng reference toàn 1, không phải human rest.

## 7. Reference state và điều mà phép trừ cho biết

Đo nhiều neutral-rest frames **ngay trước mỗi trial**, cùng participant, mount, pattern, frequency và calibration. Với pattern m và trial r:

**b(m,r) = trung bình valid pre-task rest frames; ΔZ(m,t) = Z(m,t) − b(m,r).**

Nếu chỉ có voltage: **ΔV(m,t) = V(m,t) − mean pre-task V(m)** và lưu drive current nếu có. Giữ cả absolute baseline, complex real/imaginary và magnitude/phase; không chỉ lưu ảnh màu. Rest mean bị trừ đi **không xóa anatomy**: skull/fat/blood/air/fluid, geometry và contacts vẫn định sensitivity. Khi task, jaw/tongue/air volume, blood flow, pressure, skin contact và lead tension cũng đổi. Vì thế ΔZ không phải “pure muscle activation” [S5,S6,S8]. Claim đúng ở pilot chỉ là **task-associated electrical change**, nếu vượt rest/motion variation và lặp lại. Video và EMG tạm thời giúp QC/đối chiếu, không tự chứng minh spatial muscle specificity.

## 8. Study design n=1, hai layout [P,V]

Sau human-use gate: đo **D16-M và C16-R ở hai phiên riêng**, mỗi phiên đúng 16 cups. Với n=1, một cặp phiên cho feasibility thăm dò; nếu muốn nói layout nào tốt hơn, lặp một ngày khác với **thứ tự đảo ngược**, đồng thời lưu timing/contact/remount. Trong mỗi layout cần ít nhất một lần tháo–gắn lại nếu feasible để ước lượng mounting variance. Không ghép D16-M và C16-R vào một ảnh hay một frame. Mỗi phiên có placement photos, calibration, measured complete-frame timing và task order lưu lại. Core conditions đề xuất:

| Condition | Hướng dẫn | Giới hạn diễn giải |
|---|---|---|
| REST | Mặt thư giãn, nhìn thẳng, môi nghỉ, thở tự nhiên | Không phải physiology bằng zero |
| PURSE | Chu môi nhẹ, không thổi | [S2] task anchor; không cô lập oris |
| SMILE_L | Cười/nhếch bên trái, không xoay đầu | Nhiều cơ đồng hoạt động |
| SMILE_R | Tương tự bên phải | Unilateral ability cần QC video |
| PUFF_BOTH | Phồng hai má, giữ hơi | [S3] liên quan, air/pressure confound lớn |

**Coverage audit trước khi ghi “D16-M placement đã được test”:** core recognition set trên không cố ý kích hoạt tối đa mọi vùng đã đặt cup. Thêm một **anatomical challenge block** tách riêng khỏi primary classifier: T12 upper-lip lift (DL2/DR2), T10 lower-lip depression (DL4/DL6/DL7 và bên phải), T8 corners down (DL5/DR5), jaw clench nhẹ (DL8/DR8; **không** có trong Table 1 như một chứng cứ cơ masseter), và nếu giữ remote forehead contacts thì T24 brow raise. Các mã cơ trong ngoặc là **hypothesized affected regions**, không phải positive ground truth cho BioZ. Video cần xác nhận tư thế; nếu muốn xác nhận điện sinh lý của từng cơ thì dùng sEMG reference theo protocol riêng, không suy từ BioZ. Ghi rõ các controls/challenge này **không cộng vào accuracy của core tasks**. Số repetitions và timing của block này phải chốt trước; tránh kéo dài tới mức fatigue làm đổi signal.

Timing **đề xuất, không phải paper-proven optimum**: 5 s pre-rest + 5 s task + 5 s post-rest, 5 repetitions mỗi action mỗi run; randomize action order theo block; video/cue ghi actual onset/offset. Chỉ dùng complete frames nằm trong state ổn định. Rest giữa tasks phải đủ về baseline; 10 s không phải magic number. Controls thăm dò riêng: xoay đầu nhẹ và há hàm không nói để thấy motion/jaw confounds; không gọi là “pure control”. Ngoài challenge block vừa nêu, các task lip press, vowels, jaw-open variants và suck cheeks để exploratory sau khi chốt exact instruction và timing; vowel không tương đương một hold tĩnh 5 s. Không diễn giải unilateral smile là isolated zygomaticus.

## 9. Dataset, analysis và go/no-go

Lưu subject/session/**layout ID**/layout order/run/trial/task/cue/onset; timestamps **từng configuration**; site photo, gold-cup model/diameter/paste/fixation, remount; site–lead–P1–X–software mapping; F/S order; raw complex voltage/DFT, measured current và calibrated complex Z nếu có; excitation/frequency/RTIA/gain/averaging/settling/firmware/calibration; video/EMG sync, quality flags và deviations. Thiếu mapping, timestamp hoặc valid rest sẽ làm difference khó giải thích.

Báo cáo riêng từng layout: raw traces, rest noise/drift, **từng trial Δ traces**, pattern×time heatmap (**không phải facial image**), within-run/remount/day repeatability và motion controls. So sánh hai layouts bằng task/rest SNR, repeatability, tỷ lệ usable trials và held-out-session task discrimination khi đủ phiên; không so ΔZ cùng chỉ số pattern như thể cùng geometry. Nếu làm classifier, split theo trial/session/person, không random windows chồng lấn từ một trial [S12]. Negative result chỉ giới hạn tested layout/pattern/settings/tasks. n=1 không hỗ trợ claim generalization, dysarthria diagnosis hay % cơ yếu.

**Go** để mở rộng: **cả hai** layouts bench/safety pass, đủ full frames/task, signal vượt rest variation và lặp sau remount, task được video xác nhận, không bị motion/contact giải thích hiển nhiên. Nếu fail, sửa thiết kế và preregister version mới; không tuyên bố mọi facial BioZ bất khả thi.

## 10. Provenance và những việc chưa chốt

**16 mỗi phiên và hai layouts riêng** là quyết định user. **Các vị trí 8+8 ở mỗi layout và remote M08** là engineering proposals, không có paper “prove” tối ưu. **5 s/5 reps và phiên đảo thứ tự/remount** là đề xuất, phải điều chỉnh dựa trên actual frame rate và logistics. **20/50/100 kHz** là bench candidates từ các nguồn/ROI khác nhau; human settings chưa chốt.

Cần user/lab chốt: exact gold-cup model/diameter/paste và fit quanh môi/cằm; anatomical placement review của D16-M; pattern panel D16-M; core tasks/khả năng unilateral smile; collector script và known-load data; camera/EMG synchronization; remount/day logistics; người phụ trách human-use safety/approval. Các mục này phải xác nhận **trước** main data, không điền theo kết quả.

Nguồn:

- [S1 Analog Devices CN0565](https://www.analog.com/en/resources/reference-designs/circuits-from-the-lab/CN0565.html), cùng schematic trong cn0565-designsupport/: architecture, connector, calibration; không chứng nhận setup người.
- [S2 Schumann et al., facial muscle activation atlas](https://doi.org/10.1371/journal.pone.0254932): task–muscle patterns, không phải isolation.
- [S3 Liu et al., Facial Gesture Recognition Using Bio-impedance Sensing](https://doi.org/10.1145/3745900.3746120): facial task feasibility với contacts gần má/miệng, không phải remote C16.
- [S4 Kim et al., upper-airway EIT](https://doi.org/10.5664/jcsm.7714): anatomy-linked head/neck layout, khác ROI/hardware.
- [S5 Boyle & Adler, contact/boundary artifacts](https://aboyle.ca/pubs/boyle2011a-elec_mvmt.pdf): changes về electrode/contact/shape gây EIT artifacts.
- [S6 Schooling et al., lateral-tongue EIM](https://doi.org/10.1088/1361-6579/abcb9b): layered tissue, geometry và repeatability.
- [S8 Levit et al., facial soft-electrode IPG](https://doi.org/10.1088/2057-1976/ad28cb): vascular contributions, không chứng minh pure muscle BioZ.
- [S10 Hyvönen et al., EIT electrode-position optimization](https://doi.org/10.1137/140966174): model/ROI-specific optimization, không cung cấp ready facial layout.
- [S12 Dehghani et al., sliding-window validation](https://doi.org/10.3390/s19225026): methodological warning về leakage, không phải facial BioZ evidence.
