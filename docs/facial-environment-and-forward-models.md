# Biểu diễn "môi trường đo" (khuôn mặt) cho EIT, và cách các công trình khác biểu diễn môi trường của họ

Câu hỏi: *môi trường mình muốn đo là khuôn mặt; vậy phải mô hình hóa (represent) nó thế nào, trình bày (present)
nó thế nào? Các nghiên cứu EIT khác (phổi, cơ cánh tay, đầu, cổ…) biểu diễn môi trường của họ ra sao?*

Tài liệu bổ sung cho [facial-bioimpedance-models-placement-novelty.md](facial-bioimpedance-models-placement-novelty.md)
(mục 3.3, 12, 19) và [eit-noise-sources.md](eit-noise-sources.md). Mọi nguồn trích dẫn đã được kiểm tra là tồn
tại (DOI/Europe PMC, hoặc PDF trong `reference/papers/`). Bảng tính chất mô lấy trực tiếp từ hai cơ sở dữ liệu ở mục 3.

---

## 0. Trả lời ngắn

Trong EIT, "môi trường" chính là **mô hình thuận (forward model)**. Nó gồm 5 thành phần:

1. **Hình học** (geometry): miền tính toán và biên ngoài. Hiện tại: đĩa tròn 2D. Thực tế: đầu/mặt 3D.
2. **Vật liệu**: độ dẫn điện (và hằng số điện môi) của từng loại mô, phụ thuộc tần số, có thể dị hướng (cơ dẫn
   điện tốt hơn theo thớ).
3. **Điện cực**: vị trí thật, kích thước, trở kháng tiếp xúc. Mô hình chuẩn là **complete electrode model (CEM)**
   [Cheng 1989; Somersalo 1992].
4. **Cách đo**: protocol 208 phép đo, đo theo time-difference so với REST.
5. **Cái gì thay đổi khi làm task**: độ dẫn (cơ co, máu, khí trong má) **và** hình học (da căng, cup dịch chuyển).

Ma trận độ nhạy (Jacobian) và mọi ảnh tái tạo đều tính từ mô hình này. Mô hình sai thì ảnh sai, dù dữ liệu tốt:
**không mô hình 2D nào khớp được dữ liệu đo trên vật thể 3D** [Lionheart 1999, theo Grychtol 2012], vì mô hình 2D
không mô tả được phân bố dòng thật trong cơ thể [Adler 2009]. Ngay với mô hình 3D, dùng hình tròn thay cho hình
dạng thật cũng làm chất lượng ảnh giảm nặng [Grychtol 2012].

Pilot hiện tại đang ở mức **L1** trong bậc thang ở mục 2 (đĩa 2D, điện cực điểm, đồng nhất). Vì vậy chỉ kết luận
được cấu trúc thô (nửa trên/dưới; bên trái/phải **có điều kiện**, xem ghi chú dưới bảng mục 2). Các công trình mạnh
trong lĩnh vực thường **(a) dùng hình học khớp với
cơ thể thật, (b) nói rõ mô hình ở mức nào, và (c) kiểm chứng bằng phantom hoặc ảnh y khoa (CT/MRI/nội soi)**.

---

## 1. Vì sao mô hình quyết định cái gì "nhìn thấy" được

- **Độ nhạy:** mỗi phép đo 4 điện cực nhạy nhất ở vùng gần các điện cực của nó. Độ nhạy tại một điểm tỉ lệ với
  tích vô hướng của hai "trường dẫn" (lead field), một của cặp bơm và một của cặp đo [Geselowitz 1971].
  Hình dạng của vùng nhạy phụ thuộc hình học và độ dẫn của mô.
- **Ví dụ định lượng (cơ chi):** trong mô hình FEM 4 lớp (da 3 mm / mỡ 2–20 mm / cơ 20 mm / xương), với 6 mm mỡ
  dưới da, đóng góp của cơ vào phép đo chỉ **8%** với dãy điện cực nhỏ nhưng **32%** với dãy lớn. Mỡ còn có vùng
  độ nhạy âm [Rutkove 2017]. Nghĩa là: *đặt điện cực và lớp da/mỡ quyết định phép đo "nhìn" thấy cơ đến đâu*.
- **Ngực:** EIT ngực nhạy với một lát cắt dày khoảng **một nửa bề rộng lồng ngực**, không phải một mặt phẳng mỏng
  [Frerichs 2017]. Ở mặt cũng vậy: các cup trên trán, thái dương, quanh tai, hàm "nhìn" một thể tích 3D, gồm cả
  xương hàm, khoang miệng, lưỡi.
- **Time-difference** (task so với REST) giảm được nhiều sai số mô hình nhưng **không loại hết**. Ngay trên ngực,
  sự giãn nở lồng ngực đã chiếm tới 20% biên độ ảnh [Adler 1996].

---

## 2. Bậc thang biểu diễn môi trường mặt

| Mức | Biểu diễn | Cần gì / công cụ | Được phép kết luận | Không được kết luận |
|---|---|---|---|---|
| **L0** | Không dựng ảnh: chỉ dz từng phép đo, điểm số điện cực (F8), nhận dạng task | `app.eit` (đã có) | Có thay đổi lặp lại, đặc thù task; phép đo đi qua cup nào thay đổi nhiều | Vị trí bên trong mặt |
| **L1** | Đĩa 2D, 16 điện cực cách đều theo thứ tự vòng, đồng nhất, điện cực điểm (**hiện tại**) | pyEIT (đã có) | Cấu trúc thô mà BP/JAC/GREIT đều đồng ý: nửa trên/dưới; bên trái/phải chỉ khi đủ điều kiện (xem dưới bảng) | Vị trí giải phẫu, độ sâu, dấu đỏ/xanh |
| **L2** | Mô hình đầu 3D **mẫu** (template), cup đặt theo landmark | **MIDA** [Iacono 2015]: mô hình đầu–cổ miễn phí, 153 cấu trúc, đã tách riêng cơ gò má lớn/nhỏ, cơ mút má, cơ hạ góc miệng, cơ hạ môi, tuyến mang tai/dưới lưỡi, niêm mạc, mỡ dưới da, xương hàm; có thêm hướng sợi từ DTI. Hoặc đầu chuẩn New York Head [Huang 2016], segmentation CHARM [Puonti 2020]; mesh bằng Netgen [Schöberl 1997], Gmsh [Geuzaine 2009] hoặc iso2mesh [Fang 2009]; giải bằng EIDORS [Adler & Lionheart 2006] | Bản đồ độ nhạy thật hơn; thay đổi ở "vùng má trái", "vùng dưới hàm" ở mức thô | Định vị chính xác cho từng người |
| **L3** | Biên ngoài **của chính người đo** (quét 3D/photogrammetry) + tọa độ cup đo thật | Quét 3D mặt; EIDORS/pyEIT 3D; như Kim 2019 đã làm cho mặt dưới/cổ | Bớt được sai số do hình dạng. (Ở ngực, Grychtol 2012 thấy sai lệch đường biên ΔS ≤ ~4% còn chịu được, nhưng ΔS đo trên lát cắt 2D của mô hình ngực đùn với 16 điện cực cách đều, và chính tác giả nói ngưỡng này không phải điều kiện đủ hay cần; không áp dụng thẳng cho mặt 3D.) | Mô bên trong (vẫn đồng nhất) |
| **L4** | Nhiều lớp mô (MRI/CT): da, mỡ, cơ **dị hướng**, xương sọ, xương hàm, răng, lưỡi, khoang miệng (khí), tuyến nước bọt, mạch máu; điện cực **CEM** | MRI/CT + segmentation; CEM [Cheng 1989; Vauhkonen 1999]; mô hình hóa sai số điện cực [Jehl 2015] | Giả thuyết theo vùng mô; mô phỏng dấu vết của từng cơ chế (mục 4) | "Cơ X yếu Y%": cần thêm EMG, validation lâm sàng |

Ghi chú công cụ:
- pyEIT 1.2.4 (đang dùng) tạo được mesh 3D tứ diện, nhưng chỉ có **điện cực điểm**: mã nguồn (`pyeit/eit/fem.py`)
  ghi "CEM (complete electrode model) is under development". Muốn dùng CEM thì EIDORS (MATLAB/Octave) là lựa chọn phổ biến.
- CHARM (SimNIBS) phân đoạn 15 loại mô đầu. Cơ (kể cả cơ mặt) và mỡ bị gộp thành một lớp "other tissues"; da và
  niêm mạc là nhãn riêng nhưng dùng chung mô hình cường độ, và trong bài được gán cùng độ dẫn với da đầu
  [Puonti 2020]. New York Head [Huang 2016] cũng không tách cơ mặt. Vì vậy, nếu dùng hai mô hình này thì phải tự
  thêm cơ mặt; còn **MIDA** [Iacono 2015] đã tách sẵn các cơ mặt chính và tuyến nước bọt, nên là điểm xuất phát
  tự nhiên cho L2.

**Khi nào được kết luận trái/phải ở L1.** Ba thuật toán cùng đảo ngược một frame, nên việc chúng đồng ý không
loại được ba nguồn sai lệch trái/phải sau:
- Kênh chỉ dùng cup trái được đo ở ~4.1 s, kênh chỉ dùng cup phải ở ~15.2 s của frame 20.6 s, tức cách nhau ~11 s.
  Một tương phản trái/phải vì vậy lẫn với thời điểm trong frame (đang bắt đầu, đang giữ, hay đang thả lỏng).
- Mô hình đĩa chỉ khớp REST ở mức Spearman 0.65–0.67.
- Gain fit của cặp drive R1→L1 (bắc qua hai bên) chỉ ~0.45–0.48× ở 50/80 kHz (ước lượng, chưa đo dòng).

Vì vậy chỉ nên nói "bên trái/phải" khi task được giữ ổn định suốt frame, và khi điều đó đã được kiểm tra bằng
nhiều frame lặp lại hoặc bằng thứ tự quét đảo ngược.

---

## 3. Tính chất điện của các mô vùng mặt ở 10 / 50 / 80 kHz

Độ dẫn σ (S/m). Hai nguồn, ghi rõ để thấy **độ bất định lớn**:

- **Gabriel 1996 (mô hình tham số)**: tính bằng máy tính IFAC-CNR (dựa trên mô hình 4 Cole–Cole của Gabriel và
  cộng sự); giá trị đã được tính lại độc lập từ tham số và khớp.
- **IT'IS v5.0 "low frequency conductivity"**: trung bình ± SD của các phép đo được tổng hợp, áp dụng cho tần số
  dưới 1 MHz [IT'IS 2025].

| Mô | Gabriel 10 kHz | Gabriel 50 kHz | Gabriel 80 kHz | IT'IS LF (tb ± SD, n) |
|---|---|---|---|---|
| Da khô | 0.0002 | 0.0003 | 0.0004 | 0.148 ± 0.042 (7) |
| Da ướt / niêm mạc | 0.0029 | 0.029 | 0.052 | niêm mạc: 0.461 ± 0.244 (24)* |
| Mỡ | 0.024 | 0.024 | 0.024 | 0.078 ± 0.093 (91) |
| Cơ (không xét hướng) | 0.341 | 0.352 | 0.358 | 0.461 ± 0.244 (24) |
| Cơ dọc thớ / ngang thớ | — | — | — | 0.415 / 0.132 (55) |
| Lưỡi | 0.280 | 0.284 | 0.286 | 0.461 ± 0.244 (24)* |
| Tuyến (gland) / tuyến nước bọt | 0.530 | 0.534 | 0.536 | 0.559 ± 0.291 (6) |
| Xương vỏ (xương hàm, răng; IT'IS "Bone (Cortical)") | 0.020 | 0.021 | 0.021 | 0.0063 ± 0.0034 (6) |
| Sọ: lớp vỏ / cả sọ (IT'IS riêng cho sọ) | — | — | — | 0.00645 ± 0.00254 (57) / 0.0179 ± 0.0238 (74) |
| Xương xốp | 0.083 | 0.083 | 0.084 | 0.080 ± 0.094 (5) |
| Máu | 0.700 | 0.701 | 0.702 | 0.662 ± 0.107 (33) |
| Khí (khoang miệng khi phồng má) | 0 | 0 | 0 | 0 |

\* IT'IS gán cho lưỡi và niêm mạc đúng giá trị của cơ (muscle), tức là một giá trị thay thế (proxy), không phải
phép đo riêng của hai mô này.

Cách đọc và lưu ý:
- **Da khác nhau hàng trăm lần giữa hai nguồn** (≈ 400–730 lần tùy tần số). Chính IT'IS cũng cảnh báo giá trị độ
  dẫn da của họ "should be used with caution". Mô hình Gabriel cho da khô bị lớp sừng (stratum corneum) chi phối và
  rất cách điện; giá trị IT'IS là trung bình đo của mô da. Chính Gabriel 1996 viết rằng mô hình **chỉ dùng được
  một cách tin cậy ở tần số trên 1 MHz**; dưới đó dữ liệu ít, bất định lớn, và chỉ nên coi là "ước lượng tốt
  nhất" [Gabriel 1996].
- **Cơ dị hướng mạnh.** IT'IS cho dọc/ngang ≈ 3:1. Các nghiên cứu được Gabriel 2009 tổng hợp cho tỉ lệ từ **1.8
  đến 15**; tác giả kết luận mô hình cơ tương thích với tỉ lệ khoảng 10 nhưng không phải lúc nào cũng quan sát
  được [Gabriel 2009]. Trên mặt, thớ cơ chạy theo nhiều hướng (cơ cười gò má, cơ mút má, cơ cắn…). Hướng thớ
  thay đổi khi cơ co, nên một task có thể làm đổi độ dẫn **hiệu dụng** ngay cả khi vật liệu không đổi.
- **In vivo khác ex vivo.** EIT kết hợp siêu âm (ảnh tái tạo SR-ST) cho cơ ≈ 0.36 ± 0.018 S/m và lớp da/mỡ
  ≈ 0.071 ± 0.027 S/m. Đây là trung bình trên 8 trường hợp đo ở 3 bệnh nhân, gộp mọi tần số đo (10–80 kHz)
  [Murphy 2019]. Các con số này nằm trong khoảng của hai bảng trên.
- **Hệ quả cho mô hình:** dùng bảng như **khoảng giá trị**, và làm phân tích độ nhạy: thay da/mỡ/cơ trong khoảng
  này rồi xem dấu vết mô phỏng thay đổi ra sao. Đừng chọn một con số rồi coi là đúng.

---

## 4. Một task thay đổi "môi trường" như thế nào, và mô hình nào biểu diễn được

| Cơ chế khi làm task | Ví dụ | Mô hình "chỉ độ dẫn, time-difference" (hiện tại) | Cần mô hình gì |
|---|---|---|---|
| Cơ co → độ dẫn/dị hướng của cơ đổi | Trở kháng cơ cẳng tay ở 50 kHz tăng khi co đẳng trường, chủ yếu do thay đổi sinh lý [Shiffman 2003] | **Biểu diễn được** (đúng loại thay đổi mô hình giả định) | L4 để biết thay đổi ở cơ nào |
| Cơ dày lên, đổi hình dạng | Má/khóe miệng khi cười | Bị hiểu thành thay đổi độ dẫn | Hình học thay đổi theo task |
| **Da căng, cup dịch chuyển** | Cup quanh hàm/cằm bị kéo khi cười, phồng má | **Không biểu diễn được**: thành artifact. Ở ngực, giãn nở thành ngực gây tới 20% biên độ ảnh [Adler 1996] | Tái tạo đồng thời độ dẫn + dịch chuyển điện cực [Soleimani 2006; Dai 2008] |
| Khí trong khoang miệng, thành má mỏng ra | Phồng má | Biểu diễn được *nếu* mô hình có khoang miệng; trên đĩa 2D chỉ là "vùng kém dẫn" chung chung | L4 có khoang miệng; task đối chứng đẩy lưỡi vào má |
| Lượng máu thay đổi | Mạch thái dương, máu trong cơ | Biểu diễn được (độ dẫn máu ~0.7 S/m) | Levit 2024 ghi nhận trở kháng liên quan động mạch thái dương nông |
| Trở kháng tiếp xúc đổi | Mồ hôi, áp lực lên cup | Không (làm đổi dòng bơm ở voltage mode). Trong mô phỏng CEM, thay đổi khác nhau giữa các điện cực gây artifact rải khắp ảnh, còn tăng đều thì không [Boyle & Adler 2011] | CEM ước lượng đồng thời ảnh và trở kháng tiếp xúc theo thời gian [Boverman 2017]; đo dòng |

**Giả thuyết** (chưa kiểm chứng): các dòng in đậm chiếm phần lớn thay đổi đo được. Lý do:
- trong mô hình đĩa 2D, một vùng +50% độ dẫn chỉ tạo 1.6% thay đổi trung vị (trên cùng tập kênh mạnh của phiên
  10 kHz), trong khi task thật tạo 1.8–5.1% (trung vị, kênh mạnh);
- smile (không có khí) cũng cho vùng "kém dẫn" ở cằm như puff;
- trong nghiên cứu ảnh EIT mặt duy nhất chúng tôi tìm được, tác giả cũng quy thay đổi trên ảnh cho cử động điện
  cực [Visentin 2017, §6.3.2].

Nhưng đây chưa phải bằng chứng:
- 1.6% đến từ **một** mô phỏng (một vị trí, một kích thước) trên mô hình đĩa đồng nhất với điện cực điểm, mà mô
  hình này chỉ khớp REST ở mức Spearman 0.65–0.67;
- trên mặt 3D, độ nhạy cao nhất ngay cạnh cup, nên một thay đổi độ dẫn gần cup có thể tạo tín hiệu lớn hơn nhiều;
- task yếu nhất (1.8%) chỉ nhỉnh hơn 1.6%.

Cách kiểm tra là mô phỏng thuận trên mô hình 3D (mục 6).

---

## 5. Các công trình khác biểu diễn môi trường của họ thế nào

| Ứng dụng | Công trình | Hình học | Mô / độ dẫn | Điện cực | Tái tạo / so sánh | Kiểm chứng |
|---|---|---|---|---|---|---|
| **Phổi** (đồng thuận) | TREND [Frerichs 2017] | Ảnh 2D của lát cắt qua mặt phẳng điện cực; độ nhạy là lát dày ~½ bề rộng ngực; ảnh tròn hoặc theo đường viền ngực | Time-difference so với frame tham chiếu | Thường 16 điện cực, một mặt phẳng ngang | GREIT, FEM Newton–Raphson… | So với CT trong các nghiên cứu được trích dẫn |
| Phổi | Grychtol 2012 | Đường viền ngực người/lợn **từ CT**, tạo các mô hình 3D tròn dần | Đồng nhất, time-difference | — | 4 thuật toán | Dữ liệu thật + mô phỏng: hình tròn làm ảnh kém hẳn; sai lệch ≤ ~4% chịu được |
| Phổi | Ferrario 2012 | Mô hình theo giải phẫu | Time-difference, chuỗi theo thời gian | — | Tự động tìm vùng tim/phổi | So với CT trên lợn |
| Phổi 3D | Grychtol 2016 | 3D, **hai lớp** điện cực | — | 2 lớp | GREIT 3D | Độ nhạy đều hơn trong vùng ngực |
| Phổi (nguồn sai số) | Adler 1996; Zhang & Patterson 2005 | FEM / mô hình người 3D | Có giãn nở ngực, cơ quan dịch chuyển | — | Mô phỏng | Giãn nở ngực tạo artifact đáng kể |
| **Cẳng tay** (cử chỉ tay) | Tomo [Zhang & Harrison 2015] | Không mô hình giải phẫu; vòng 8 điện cực đồng quanh cổ tay | — | 8, two-pole | 28 phép đo two-pole + 378 hiệu từng cặp = 406 feature → SVM; ảnh linear back-projection **chỉ để hiển thị** | Nghiên cứu người dùng |
| Cẳng tay | Tomo-2 [Zhang, Xiao & Harrison 2016] | Vòng 32 điện cực thép; **hiệu chuẩn baseline bằng vật đồng nhất (Jell-O)** | Đồng nhất | 8/16/32, two-/four-pole | EIDORS, one-step Gauss–Newton (nút) → ảnh 16×16 = 256 feature → SVM | 10 người; leave-one-round-out; 94.3% (11 cử chỉ, 32 điện cực, four-pole) |
| Cổ tay | EITWatch [arXiv 2608.29415, 2026] | Mảng **phẳng** 8 điện cực trong vòng 31 mm (mặt lưng đồng hồ) | — | 8 | 35 phép đo, 48 khung/s | 12 người |
| Tay giả | Wu 2018 | — | — | — | EIT làm giao diện người–máy điều khiển tay giả | — |
| **Cơ (EIM)** | Rutkove 2017 (cùng hướng: Jafarpoor 2013) | **Tấm phẳng 4 lớp** (da/mỡ/cơ/xương), FEM COMSOL | Từ Gabriel 1996; cơ dị hướng σ_dọc = 2σ_ngang | Dải điện cực có kích thước thật | Mô phỏng độ nhạy | Mô phỏng |
| Cơ | Murphy 2019 | **2.5D**, các lớp lấy từ **siêu âm** (gel, da, mỡ, cơ) làm prior | Giá trị tham chiếu theo vùng, theo tần số | CEM, 3D FEM (Gmsh) | Gauss–Newton, Tikhonov tổng quát | Phantom gel; 3 bệnh nhân |
| Lưỡi | Schooling 2020 | Mô hình EIM mặt bên lưỡi | — | — | Mô hình và phân tích | — |
| **Đầu / não** | Tidswell 2001 | **Khối cầu đồng nhất** | Đồng nhất | Điện cực trên da đầu | Tái tạo 3D trên mô hình cầu | 39 người (hoạt động thị giác, cảm giác thân thể hoặc vận động); ảnh nhiễu |
| Đầu / não | Bagshaw 2003 | Mesh FEM đầu **3D thật** có các lớp ngoài não (da đầu, sọ…) | Nhiều lớp | Điện cực trên da đầu | FEM 3D | Bể nước muối hình cầu/hình đầu (sọ thạch cao hoặc sọ người thật) + phân tích lại dữ liệu người của Tidswell 2001 |
| Đầu / não | Tizzard 2005; Malone 2014; Jehl 2015 | Mesh đầu 3D thật | Nhiều lớp | Mô hình hóa và hiệu chỉnh sai số điện cực (Jehl 2015) | FEM 3D | Mô phỏng / bể nước muối |
| Đầu (dữ liệu đột quỵ) | Goren 2018 | MRI/CT của từng bệnh nhân đi kèm dữ liệu | — | 32 điện cực EEG; contact 1–3 kΩ ở 1 kHz | MF-EIT | Bộ dữ liệu công khai |
| **Cổ / đường thở** | Kim 2019 (PDF trong `reference/papers/`) | 16 điện cực quanh mặt dưới/cổ theo landmark MRI; **biên lấy bằng máy quét 3D → FEM** | Time-difference (đường thở mở làm tham chiếu) | 16 | — | **MRI đồng thời** khi nuốt; người khỏe và bệnh nhân OSA |
| Cổ | Piccin 2023 | **Mesh 3D chung** từ CT của một tình nguyện viên (62 500 phần tử) | Time-difference | 32, hai dải zig-zag | Dựa trên ma trận độ nhạy, lọc Gauss | **Nội soi đồng thời** (n = 6); 21 bệnh nhân |
| Nuốt | Hughes 1996 | — | — | — | EIT | Videofluoroscopy đồng thời |
| Đầu dò cầm tay (vú) | Kao 2006 (PDF trong `reference/papers/`) | Mảng phẳng 25 điện cực, **nửa không gian** | Đồng nhất, tuyến tính hóa | 25 | Tái tạo 3D | Bể nước với vật đã biết |
| **Mặt** | Visentin 2017 | **Đĩa 2D tròn**, 8 điện cực một bên mặt (cả má, quanh miệng) | Đồng nhất | 8 | Gauss–Newton một bước, difference | 1 tình nguyện viên; chỉ "A" và smile phân biệt rõ |
| Mặt | Liu 2025 | Không dựng ảnh; 3 điện cực (dưới miệng, hai má) | — | 2 kênh | ML trên tín hiệu | 4 người; 93% |
| Mặt | Painometry [Truong 2020] | Không dựng ảnh; quét tần số 10–100 kHz | Mô hình mạch tương đương | Điện cực trên vùng cơ cau mày (corrugator) | ML | 23 người |
| Mặt | Levit 2024 | Không dựng ảnh; điện cực mềm | — | 4-contact impedance + EMG | — | Liên quan động mạch thái dương nông |

**Nhận xét:**
1. Các nghiên cứu **tuyên bố về giải phẫu** mạnh nhất (phổi, đường thở, não) **thường** dùng **hình học thật**
   (CT/MRI/quét 3D), hoặc ít nhất đường viền thật, **và** đối chiếu với một phương pháp ảnh khác (CT, MRI, nội soi,
   videofluoroscopy). Ngoại lệ: Tidswell 2001 dùng khối cầu đồng nhất; Malone 2014 và Jehl 2015 chỉ mô phỏng;
   Bagshaw 2003 kiểm chứng bằng bể nước muối chứ không bằng ảnh khác; EIT phổi thường ngày dựng lát cắt 2D trên
   hình tròn hoặc hình ngực chung.
2. Ứng dụng nào chỉ cần **nhận dạng** (Tomo, EITWatch, Liu 2025, Painometry) thì không cần mô hình giải phẫu. Ảnh,
   nếu có, chỉ để hiển thị (Tomo) hoặc làm feature (Tomo-2). Tomo-2 còn hiệu chuẩn baseline bằng một vật đồng nhất, và đánh giá **theo vòng** để
   tránh rò rỉ giữa các mẫu gần nhau về thời gian.
3. Trong các nguồn đã rà soát, chỉ Visentin 2017 dựng ảnh EIT cho cử động mặt, và dùng **đĩa 2D tròn**, giống
   pilot của bạn (Kim 2019 dựng ảnh vùng mặt dưới/cổ nhưng cho đường thở, không cho cơ mặt). Vì vậy cách trình bày
   đúng cho kết quả hiện tại là **"2-D projection, exploratory"**.

---

## 6. Lộ trình đề xuất cho dự án

| Giai đoạn | Biểu diễn | Việc cần làm | Trả lời câu hỏi |
|---|---|---|---|
| Bây giờ (paper 1: nhận dạng task) | **L0** chính, **L1** minh họa | Đặc trưng dz; ảnh đĩa 2D có nhãn exploratory | Có tín hiệu lặp lại, đặc thù task? |
| Phiên tới | Thêm **dữ liệu hình học** | Chụp ảnh nhiều góc mặt có cup (photogrammetry bằng điện thoại) hoặc quét 3D; đo tọa độ cup | Chuẩn bị cho L3 |
| Tiếp theo | **L2/L3** | Mesh 3D (template hoặc mặt thật) + cup ở vị trí thật; tính bản đồ độ nhạy của 208 phép đo | Mỗi phép đo "nhìn" vùng nào |
| Song song | **Kiểm chứng giả thuyết trong không gian dữ liệu** | Mô phỏng thuận từng cơ chế (khí trong má, da căng/cup dịch, cơ dày lên) trên mô hình 3D; so **dấu vết mô phỏng** với dz đo được | Cơ chế nào giải thích dữ liệu, *mà chưa cần dựng ảnh* |
| Kiểm chứng | Phantom | Phantom đầu bằng gel/saline có vật đã biết vị trí (và một vật cách điện mô phỏng khí) | Thuật toán + mô hình có đặt đúng chỗ không |
| Dài hạn | **L4** + CEM + đo dòng | MRI/CT, nhiều lớp mô, cơ dị hướng, impedance mode | Giả thuyết theo vùng mô; tiền đề cho đánh giá cơ |

"Kiểm chứng trong không gian dữ liệu" là bước rẻ nhất mà có sức thuyết phục cao. Thay vì tin vào ảnh, ta hỏi:
*mô hình 3D có tạo ra đúng dấu vết dz mà ta đo được không?*

---

## 7. Cách **trình bày** môi trường trong báo cáo/slide

1. **Ảnh thật + sơ đồ vị trí cup** với landmark (đã có trong slide 7–8).
2. **Hình mô hình** đang dùng, ghi rõ mức: hiện tại là đĩa 2D với chú thích "model, not anatomy"; sau này là mesh 3D
   có cup.
3. **Bảng tính chất mô** (mục 3) kèm nguồn và tần số, nói rõ là khoảng giá trị.
4. **Bản đồ độ nhạy** của một vài phép đo tiêu biểu: mỗi phép đo "nhìn" vùng nào.
5. **Mô phỏng thuận** cho từng giả thuyết cơ chế, đặt cạnh dữ liệu đo.
6. **Kiểm chứng**: phantom với vật đã biết, reciprocity, mức nhiễu.
7. Một câu nói rõ **mô hình ở mức nào và vì thế được kết luận gì** (bảng mục 2).

> *For the professor:* "In EIT the 'environment' is the forward model: geometry, tissue properties, electrodes and
> what changes during the task. Our current model is a 2-D homogeneous disk with point electrodes, the same model
> type as the only prior facial EIT imaging study we found (Visentin 2017, one volunteer). We therefore report
> only coarse, algorithm-independent structure. Left/right contrasts are conditional, because left-only and
> right-only measurements are sampled about 11 s apart within each 20.6 s frame. The strongest anatomical
> studies in lung, airway or brain EIT typically use CT, MRI or 3-D-scan geometry and validate against another
> imaging modality. Our next steps are to capture the subject's face geometry and electrode
> coordinates, build a 3-D model, compare simulated signatures of candidate mechanisms with the measured
> changes, and validate on a phantom."

---

## Tài liệu tham khảo

**Mô hình, công cụ, điện cực**
- Adler A et al. (2009). GREIT: a unified approach to 2D linear EIT reconstruction of lung images. *Physiol Meas* 30:S35–55. [10.1088/0967-3334/30/6/S03](https://doi.org/10.1088/0967-3334/30/6/S03) (local PDF)
- Adler A, Lionheart WRB (2006). Uses and abuses of EIDORS: an extensible software base for EIT. *Physiol Meas* 27:S25–42. [10.1088/0967-3334/27/5/S03](https://doi.org/10.1088/0967-3334/27/5/S03)
- Boverman G et al. (2017). Efficient simultaneous reconstruction of time-varying images and electrode contact impedances in EIT. *IEEE TBME* 64:795–806. [10.1109/TBME.2016.2578646](https://doi.org/10.1109/TBME.2016.2578646)
- Boyle A, Adler A (2011). The impact of electrode area, contact impedance and boundary shape on EIT images. *Physiol Meas* 32:745–754. [10.1088/0967-3334/32/7/S02](https://doi.org/10.1088/0967-3334/32/7/S02)
- Cheng KS, Isaacson D, Newell JC, Gisser DG (1989). Electrode models for electric current computed tomography. *IEEE TBME* 36:918–924. [10.1109/10.35300](https://doi.org/10.1109/10.35300)
- Dai T, Gómez-Laberge C, Adler A (2008). Reconstruction of conductivity changes and electrode movements based on EIT temporal sequences. *Physiol Meas* 29:S77–88. [10.1088/0967-3334/29/6/S07](https://doi.org/10.1088/0967-3334/29/6/S07)
- Fang Q, Boas DA (2009). Tetrahedral mesh generation from volumetric binary and grayscale images (iso2mesh). *Proc IEEE ISBI*. [10.1109/ISBI.2009.5193259](https://doi.org/10.1109/ISBI.2009.5193259)
- Geselowitz DB (1971). An application of electrocardiographic lead theory to impedance plethysmography. *IEEE TBME* 18:38–41. [10.1109/TBME.1971.4502787](https://doi.org/10.1109/TBME.1971.4502787)
- Geuzaine C, Remacle J-F (2009). Gmsh: a 3-D finite element mesh generator. *Int J Numer Methods Eng* 79:1309–1331. [10.1002/nme.2579](https://doi.org/10.1002/nme.2579)
- Grychtol B, Lionheart WRB, Bodenstein M, Wolf GK, Adler A (2012). Impact of model shape mismatch on reconstruction quality in EIT. *IEEE TMI* 31:1754–1760. [10.1109/TMI.2012.2200904](https://doi.org/10.1109/TMI.2012.2200904)
- Huang Y, Parra LC, Haufe S (2016). The New York Head: a precise standardized volume conductor model for EEG source localization and tES targeting. *NeuroImage* 140:150–162. [10.1016/j.neuroimage.2015.12.019](https://doi.org/10.1016/j.neuroimage.2015.12.019)
- Iacono MI, Neufeld E, Akinnagbe E, et al. (2015). MIDA: a multimodal imaging-based detailed anatomical model of the human head and neck. *PLoS One* 10:e0124126. [10.1371/journal.pone.0124126](https://doi.org/10.1371/journal.pone.0124126)
- Jehl M, Avery J, Malone E, Holder D, Betcke T (2015). Correcting electrode modelling errors in EIT on realistic 3D head models. *Physiol Meas* 36:2423–2442. [10.1088/0967-3334/36/12/2423](https://doi.org/10.1088/0967-3334/36/12/2423)
- Lionheart WRB (1999). Uniqueness, shape, and dimension in EIT. *Ann N Y Acad Sci* 873:466–471. [10.1111/j.1749-6632.1999.tb09495.x](https://doi.org/10.1111/j.1749-6632.1999.tb09495.x)
- Liu B et al. (2018). pyEIT: a Python based framework for EIT. *SoftwareX* 7:304–308. [10.1016/j.softx.2018.09.005](https://doi.org/10.1016/j.softx.2018.09.005)
- Puonti O et al. (2020). Accurate and robust whole-head segmentation from MR images for individualized head modeling (CHARM). *NeuroImage* 219:117044. [10.1016/j.neuroimage.2020.117044](https://doi.org/10.1016/j.neuroimage.2020.117044)
- Schöberl J (1997). NETGEN: an advancing front 2D/3D-mesh generator based on abstract rules. *Comput Vis Sci* 1:41–52. [10.1007/s007910050004](https://doi.org/10.1007/s007910050004)
- Soleimani M, Gómez-Laberge C, Adler A (2006). Imaging of conductivity changes and electrode movement in EIT. *Physiol Meas* 27:S103–113. [10.1088/0967-3334/27/5/S09](https://doi.org/10.1088/0967-3334/27/5/S09)
- Somersalo E, Cheney M, Isaacson D (1992). Existence and uniqueness for electrode models for electric current computed tomography. *SIAM J Appl Math* 52:1023–1040. [10.1137/0152060](https://doi.org/10.1137/0152060)
- Vauhkonen PJ, Vauhkonen M, Savolainen T, Kaipio JP (1999). Three-dimensional EIT based on the complete electrode model. *IEEE TBME* 46:1150–1160. [10.1109/10.784147](https://doi.org/10.1109/10.784147)

**Tính chất mô**
- Gabriel S, Lau RW, Gabriel C (1996). The dielectric properties of biological tissues: III. Parametric models for the dielectric spectrum of tissues. *Phys Med Biol* 41:2271–2293. [10.1088/0031-9155/41/11/003](https://doi.org/10.1088/0031-9155/41/11/003). Values computed with the IFAC-CNR calculator (niremf.ifac.cnr.it/tissprop), which implements this model.
- Gabriel C, Peyman A, Grant EH (2009). Electrical conductivity of tissue at frequencies below 1 MHz. *Phys Med Biol* 54:4863–4878.
- IT'IS Foundation (2025). Tissue Properties Database V5.0. [10.13099/VIP21000-05-0](https://doi.org/10.13099/VIP21000-05-0). Low-frequency conductivity table: file `lowfrequencyparametercurrent20240604.xls` (dated 2024-06-04), accessed 2026-10-05.
- Murphy EK, Skinner J, Martucci M, Rutkove SB, Halter RJ (2019). Toward EIT coupled ultrasound imaging for assessing muscle health. *IEEE TMI* 38:1409–1419. [10.1109/TMI.2018.2886152](https://doi.org/10.1109/TMI.2018.2886152)
- Shiffman CA, Aaron R, Rutkove SB (2003). Electrical impedance of muscle during isometric contraction. *Physiol Meas* 24:213–234. [10.1088/0967-3334/24/1/316](https://doi.org/10.1088/0967-3334/24/1/316)

**Phổi / ngực**
- Adler A, Guardo R, Berthiaume Y (1996). Impedance imaging of lung ventilation: do we need to account for chest expansion? *IEEE TBME* 43:414–420. [10.1109/10.486261](https://doi.org/10.1109/10.486261)
- Ferrario D et al. (2012). Toward morphological thoracic EIT: major signal sources correspond to respective organ locations in CT. *IEEE TBME* 59:3000–3008. [10.1109/TBME.2012.2209116](https://doi.org/10.1109/TBME.2012.2209116)
- Frerichs I et al. (2017). TREND consensus statement. *Thorax* 72:83–93. [10.1136/thoraxjnl-2016-208357](https://doi.org/10.1136/thoraxjnl-2016-208357)
- Grychtol B, Müller B, Adler A (2016). 3D EIT image reconstruction with GREIT. *Physiol Meas* 37:785–800. [10.1088/0967-3334/37/6/785](https://doi.org/10.1088/0967-3334/37/6/785)
- Zhang J, Patterson RP (2005). EIT images of ventilation: what contributes to the resistivity changes? *Physiol Meas* 26:S81–92. [10.1088/0967-3334/26/2/008](https://doi.org/10.1088/0967-3334/26/2/008)

**Cẳng tay / cơ**
- Jafarpoor M, Li J, White JK, Rutkove SB (2013). Optimizing electrode configuration for electrical impedance measurements of muscle via the finite element method. *IEEE TBME* 60:1446–1452. [10.1109/TBME.2012.2237030](https://doi.org/10.1109/TBME.2012.2237030)
- Rutkove SB, Pacheck A, Sanchez B (2017). Sensitivity distribution simulations of surface electrode configurations for electrical impedance myography. *Muscle Nerve* 56:887–895. [10.1002/mus.25561](https://doi.org/10.1002/mus.25561)
- Schooling CN et al. (2020). Modelling and analysis of electrical impedance myography of the lateral tongue. *Physiol Meas* 41:125008. [10.1088/1361-6579/abcb9b](https://doi.org/10.1088/1361-6579/abcb9b)
- Wu Y, Jiang D, Liu X, Bayford R, Demosthenous A (2018). A human-machine interface using EIT for hand prosthesis control. *IEEE TBioCAS* 12:1322–1333. [10.1109/TBCAS.2018.2878395](https://doi.org/10.1109/TBCAS.2018.2878395)
- Zhang Y, Harrison C (2015). Tomo: wearable, low-cost EIT for hand gesture recognition. *Proc ACM UIST 2015* (PDF: chrisharrison.net/projects/tomo/tomo.pdf).
- Zhang Y, Xiao R, Harrison C (2016). Advancing hand gesture recognition with high resolution EIT. *Proc ACM UIST 2016*, 843–850. [10.1145/2984511.2984574](https://doi.org/10.1145/2984511.2984574)
- EITWatch: smartwatch-integrated planar EIT for hand gesture recognition (2026). arXiv:2608.29415.

**Đầu / não**
- Bagshaw AP et al. (2003). EIT of human brain function using reconstruction algorithms based on the finite element method. *NeuroImage* 20:752–764. [10.1016/S1053-8119(03)00301-X](https://doi.org/10.1016/S1053-8119(03)00301-X)
- Goren N et al. (2018). Multi-frequency EIT and neuroimaging data in stroke patients. *Sci Data* 5:180112. [10.1038/sdata.2018.112](https://doi.org/10.1038/sdata.2018.112)
- Malone E, Jehl M, Arridge S, Betcke T, Holder D (2014). Stroke type differentiation using spectrally constrained multifrequency EIT: feasibility in a realistic head model. *Physiol Meas* 35:1051–1066. [10.1088/0967-3334/35/6/1051](https://doi.org/10.1088/0967-3334/35/6/1051)
- Tidswell T, Gibson A, Bayford RH, Holder DS (2001). Three-dimensional EIT of human brain activity. *NeuroImage* 13:283–294. [10.1006/nimg.2000.0698](https://doi.org/10.1006/nimg.2000.0698)
- Tizzard A, Horesh L, Yerworth RJ, Holder DS, Bayford RH (2005). Generating accurate finite element meshes for the forward model of the human head in EIT. *Physiol Meas* 26:S251–261. [10.1088/0967-3334/26/2/024](https://doi.org/10.1088/0967-3334/26/2/024)

**Cổ / đường thở / nuốt / đầu dò**
- Hughes TA, Liu P, Griffiths H, Lawrie BW, Wiles CM (1996). Simultaneous EIT and videofluoroscopy in the assessment of swallowing. *Physiol Meas* 17:109–119. [10.1088/0967-3334/17/2/005](https://doi.org/10.1088/0967-3334/17/2/005)
- Kao T-J, Isaacson D, Newell JC, Saulnier GJ (2006). A 3D reconstruction algorithm for EIT using a handheld probe for breast cancer detection. *Physiol Meas* 27:S1–11. [10.1088/0967-3334/27/5/S01](https://doi.org/10.1088/0967-3334/27/5/S01) (local PDF)
- Kim YE, Woo EJ, Oh TI, Kim S-W (2019). Real-time identification of upper airway occlusion using EIT. *J Clin Sleep Med* (local PDF). [10.5664/jcsm.7714](https://doi.org/10.5664/jcsm.7714)
- Piccin VS et al. (2023). Feasibility of neck EIT to monitor upper airway dynamics during sleep. *Front Sleep* 2:1238508. [10.3389/frsle.2023.1238508](https://doi.org/10.3389/frsle.2023.1238508)

**Mặt** (chi tiết ở [facial-bioimpedance-models-placement-novelty.md](facial-bioimpedance-models-placement-novelty.md) mục 2)
- Levit et al. (2024). Soft electrodes for simultaneous bio-potential and bio-impedance study of the face. *Biomed Phys Eng Express* 10:025036. [10.1088/2057-1976/ad28cb](https://doi.org/10.1088/2057-1976/ad28cb)
- Liu M et al. (2025). Facial gesture recognition using bio-impedance sensing. *AHs 2025*, 491–493. [10.1145/3745900.3746120](https://doi.org/10.1145/3745900.3746120)
- Truong et al. (2020). Painometry. *ACM MobiSys 2020* (PDF: people.cs.umass.edu/~phuc/papers/Painometry_2020.pdf).
- Visentin F (2017). An electrical tomographic approach to detect deformation over soft and flexible materials. PhD thesis, University of Tsukuba, §6.3. [PDF](https://tsukuba.repo.nii.ac.jp/record/43368/files/DA08090.pdf)
