# Nguồn nhiễu và sai số trong EIT: chúng là gì, ảnh hưởng dữ liệu mặt thế nào, đo ra sao

Tài liệu này trả lời: *trong EIT/bioimpedance có những loại "nhiễu" (noise) và sai số hệ thống (error) nào,
chúng để lại dấu vết gì trong dữ liệu, và mỗi loại ảnh hưởng tới các phiên đo mặt bằng CN0565 đến đâu.*
Số liệu "của bạn" lấy từ 3 phiên 2026-10-05
([báo cáo](reports/2026-10-05-three-frequency-analysis.md)) và từ phép thử REST→REST trước đó.
Tài liệu tham khảo ở cuối; mỗi tài liệu đều đã được kiểm tra là tồn tại (Europe PMC, DOI hoặc PDF trong `reference/papers/`).

> **Hai ý quan trọng nhất**
> 1. Trong EIT, "nhiễu" không chỉ là nhiễu điện tử ngẫu nhiên. Phần lớn sai số trên người đến từ
>    **điện cực** (tiếp xúc thay đổi, điện cực di chuyển) và từ **mô hình** (hình học sai). Các nguồn này
>    có cấu trúc, không ngẫu nhiên, nên lấy trung bình nhiều lần đo cũng không triệt tiêu được.
> 2. Với task trên mặt (cười, phồng má), **nhiều khả năng chính cử động là nguồn sai số lớn nhất**: da căng,
>    cup bị kéo, hình dạng mặt thay đổi. Đây là **giả thuyết**, vì thiết kế hiện tại chưa tách được cử động khỏi
>    thay đổi độ dẫn thật (§2.3). Mô hình chỉ có độ dẫn điện sẽ hiểu mọi thay đổi hình học thành "độ dẫn thay đổi".

---

## 1. Bản đồ các nguồn nhiễu/sai số

Dấu vết trong dữ liệu (cột 3) là cách nhận ra từng nguồn; cột 4 là mức ảnh hưởng tới dữ liệu 2026-10-05.

| # | Nguồn | Dấu vết trong dữ liệu | Ảnh hưởng tới dữ liệu của bạn |
|---|---|---|---|
| 1 | **Nhiễu điện tử / lượng tử hóa** (amplifier, ADC, DFT) | ngẫu nhiên, không cấu trúc; tương đối lớn ở kênh yếu | **Lớn ở kênh yếu**: nhiễu ~2 count, trong khi 126–135/208 kênh chỉ có \|V\| ~1–50 count (trung vị 17–21) nên bị loại |
| 2 | **Contact impedance của cup bơm dòng** (voltage mode) | mọi phép đo của cùng một cặp drive cùng tăng/giảm theo một hệ số | **Lớn**: reciprocity lệch 12–18%. Fit "một gain mỗi cặp drive" giải thích phần lớn ở 10 kHz, chưa kết luận được ở 50/80 kHz. Gain fit của R1→L1 ~0.45–0.48× (ước lượng, chưa đo dòng) |
| 3 | **Contact impedance thay đổi theo thời gian** (mồ hôi, gel khô, áp lực, băng dính) | trôi chậm; hoặc nhảy khi cup bị chạm | Chưa đo được (mỗi phiên chỉ 1 REST) |
| 4 | **Điện cực di chuyển / mặt đổi hình dạng** | thay đổi lớn, có cấu trúc, ở các kênh gần vùng cử động | **Giả thuyết: có thể là nguồn chính.** Task thật: 1.8–5.1% (trung vị, kênh mạnh); một vùng +50% độ dẫn trong mô hình đĩa 2D: 1.6% (một mô phỏng duy nhất) |
| 5 | **Dây dẫn/cáp di chuyển** (điện dung, tiếp xúc connector) | gai/nhảy bất thường, thường ở một vài cặp | Chưa đánh giá |
| 6 | **Drift** (nhiệt độ, mô ổn định sau khi gắn, thay đổi da) | xu hướng đơn điệu theo thời gian | Không tách được: task cuối đo sau REST ~137 s |
| 7 | **Sinh lý nền**: thở, mạch đập, nuốt, trương lực cơ | dao động theo nhịp, có ở mọi state kể cả REST | Một phần của "nhiễu REST→REST" 0.36–0.96% đã đo (ở một phiên khác) |
| 8 | **Điện dung ký sinh, common-mode, crosstalk của switch** | tăng theo tần số; lệch pha | Có thể góp phần vào phần reciprocity **còn lại sau fit gain** ở 50/80 kHz (chưa kiểm chứng) |
| 9 | **EMI / nhiễu nguồn điện** | ở 10–80 kHz thường nhỏ nhờ giải điều chế tại tần số kích thích | Chưa thấy dấu hiệu |
| 10 | **Thu tuần tự** (208 phép đo trong 20.6 s) | các kênh của cùng một frame được đo ở các thời điểm khác nhau | **Quan trọng**: bên trái đo trước bên phải ~11 s; cử động có thể nhạt dần |
| 11 | **Sai số mô hình** (đĩa 2D, vị trí điện cực, điện cực điểm) | ảnh có cặp đỏ/xanh xen kẽ, đốm ở giữa, thay đổi theo thuật toán | **Lớn** với ảnh tái tạo (ρ = 0.65–0.67 giữa REST và mô hình đĩa) |
| 12 | **Thực hiện task không lặp lại** (mức độ, đối xứng, mỏi) | cùng task nhưng mỗi lần một khác | Chưa đo được (mỗi task 1 lần/phiên) |

---

## 2. Từng nguồn, giải thích dễ hiểu

### 2.1 Nhiễu điện tử và lượng tử hóa

- **Là gì:** mọi bộ khuếch đại và ADC đều có nhiễu ngẫu nhiên; giá trị DFT còn được làm tròn thành số nguyên
  (count). Lấy trung bình nhiều lần đo thì nhiễu này giảm.
- **Dấu vết:** cùng một độ lớn tuyệt đối (khoảng vài count) cho mọi kênh, nên **tính theo % thì kênh yếu bị ảnh
  hưởng rất nặng**: 2 count trên kênh 10 count là 20%, nhưng trên kênh 400 count chỉ là 0.5%.
- **Ở dữ liệu của bạn:** REST→REST cho RMS 1.2–2.9 count và 0.36–0.96% trên kênh ≥ 100 count. Lưu ý: số này
  lấy từ **một phiên khác** (10 kHz, amplitude 800, hai frame REST cách ~23 s), nên đã gồm cả một ít drift. Các
  phiên 2026-10-05 chạy ở 600 mV; nếu nhiễu cộng theo count thì mức nền tính theo % sẽ cao hơn một chút khi tín
  hiệu nhỏ hơn. Đây là lý do pipeline loại kênh < 50 count và dùng trọng số theo nhiễu khi tái tạo ảnh.
- **Đo thế nào:** ≥ 3 frame REST liên tiếp ở đầu phiên (`app check` báo `rest_rest_rms_counts`); trên bench
  dùng mạng điện trở cố định để tách nhiễu thiết bị khỏi nhiễu người.

### 2.2 Contact impedance và dòng bơm (voltage mode)

- **Là gì:** CN0565 là **nguồn áp** nối tiếp điện trở hạn dòng 1 kΩ (circuit note CN0565). Dòng chạy qua mặt
  phụ thuộc trở kháng tiếp xúc của 2 cup bơm, mà trở kháng tiếp xúc khác nhau giữa các cup và thay đổi theo
  thời gian [McAdams 1996; Rosell 1988]. Phép đo 4 điện cực loại được trở kháng của **cup đo** (đầu vào trở kháng
  cao) nhưng **không loại được ảnh hưởng của cup bơm lên dòng** khi dòng không được đo.
- **Dấu vết:** tất cả 13 phép đo của một cặp drive cùng nhân với một hệ số. Kéo theo đó là **reciprocity error**:
  đo (bơm AB, đo MN) và (bơm MN, đo AB) lẽ ra bằng nhau.
- **Ở dữ liệu của bạn:** reciprocity lệch 17.7 / 12.3 / 13.4% (10/50/80 kHz). Mô hình "mỗi cặp drive một hệ
  số" có tối đa 15 tham số tự do (16 gain, tổng cố định) cho 27–31 cặp reciprocal, nên tự nó đã "ăn" bớt một phần
  nhiễu. Pipeline kiểm tra điều này bằng cách fit cùng mô hình lên nhiễu ngẫu nhiên có cùng cấu trúc
  (`recip_fit_null_ratio_*` trong `qc_summary.csv`): với nhiễu thuần, phần dư còn ~0.66–0.72 lần (5–95%: ~0.5–0.9).
  Dữ liệu thật:
  - 10 kHz: 17.7% → 4.9% (0.28 lần), thấp hơn hẳn mức của nhiễu, nên **ủng hộ** giả thuyết dòng bơm khác nhau;
  - 50/80 kHz: 12.3% → 7.2% (0.59 lần) và 13.4% → 8.9% (0.66 lần), nằm trong khoảng của nhiễu thuần, nên **chưa
    kết luận được**.

  Các nguồn khác chỉ là *khả năng*: điện dung ký sinh (2.7) tăng theo tần số; còn thời điểm đo khác nhau của
  hai phép đo đảo vai (2.9) thì giống hệt nhau ở mọi tần số, nên không giải thích được vì sao phần dư ở 50/80 kHz
  lớn hơn. Cặp **R1→L1** có gain fit ~0.45–0.48× ở 50/80 kHz. Đây là **ước lượng từ fit**, đúng ở hai tần số mà
  fit chưa kết luận được, **không phải dòng đo được** (impedance_mode đang tắt).
- **Tại sao dz vẫn dùng được:** hệ số cố định của mỗi cặp drive bị triệt tiêu trong `v_task / v_REST`. Chỉ phần
  **thay đổi** dòng giữa REST và task còn lại. Theo cùng fit gain (ước lượng, không phải dòng đo được), thay đổi
  này < 2% ở 93% các trường hợp, lớn nhất ~12% (cặp R1→L1, SMILE_BOTH ở 80 kHz).
- **Đo/khắc phục:** chạy `impedance_mode` để đo dòng qua TIA và nhận Z = V/I. Kiến trúc nguồn áp có đo dòng là
  một cách làm đã được mô tả cho EIT [Saulnier 2006]. Kiểm tra contact trước khi đo, như nghiên cứu đột quỵ của
  UCL: đo contact impedance ở 1 kHz, mài da lại tới khi đạt 1–3 kΩ, và kiểm tra lại sau khi đo [Goren 2018].
  Theo dõi chất lượng dữ liệu theo thời gian thực bằng một chỉ số [Mamatjan 2013]. Tự phát hiện điện cực hỏng
  [Asfaw & Adler 2005; Hartinger 2009].

### 2.3 Điện cực di chuyển và mặt đổi hình dạng

- **Là gì:** EIT giả định điện cực đứng yên và chỉ có độ dẫn thay đổi. Trên ngực, mô phỏng FEM cho thấy giãn nở
  lồng ngực chiếm tới **20%** biên độ ảnh tái tạo và gây artifact ở giữa ảnh. Phần đóng góp này ít phụ thuộc độ sâu
  hít vào và biến thiên tuyến tính theo thay đổi trở kháng, nên có thể bỏ qua khi chỉ quan tâm *mức* hoạt động
  sinh lý; nhưng tác giả kết luận vẫn phải tính tới nó khi diễn giải ảnh [Adler 1996]. Mô phỏng 3D ngực
  cho thấy giãn nở và dịch chuyển cơ quan góp phần đáng kể vào thay đổi ảnh [Zhang & Patterson 2005]. Trong mô
  phỏng FEM/CEM [Boyle & Adler 2011]:
  - hình dạng biên dưới điện cực thay đổi gây méo ảnh **có cấu trúc**;
  - contact impedance hoặc diện tích điện cực thay đổi khác nhau giữa các điện cực gây artifact **rải khắp ảnh**;
  - contact impedance trung bình tăng đều thì không gây artifact.
- **Ở mặt:** khi cười hay phồng má, da căng, khoảng cách giữa các cup đổi, cup có thể trượt. Đây là **thay đổi
  hình học**, không phải độ dẫn. Thay đổi trở kháng tiếp xúc do cử động đã được đo trực tiếp và phụ thuộc tần số
  [Cömert & Hyttinen 2014].
- **Dấu vết ở dữ liệu của bạn:**
  - thay đổi lớn tập trung ở các kênh quanh hàm/cằm, nơi da bị kéo nhiều nhất;
  - trong mô hình đĩa 2D, một vùng +50% độ dẫn chỉ tạo 1.6% thay đổi trung vị (trên cùng tập kênh mạnh của phiên
    10 kHz), trong khi task thật tạo 1.8–5.1% (trung vị, kênh mạnh). Đây chỉ là **một** mô phỏng (một vị trí, một
    kích thước), trên một mô hình chỉ khớp REST ở mức ρ = 0.65–0.67, và task yếu nhất (1.8%) chỉ nhỉnh hơn 1.6%.
    Vì vậy đây là gợi ý, chưa phải bằng chứng;
  - smile (không có khí) cũng cho vùng "kém dẫn" ở cằm như puff.
- **Không tách được bằng thiết kế hiện tại.** Các cách tách:
  - video có đánh dấu cup để đo dịch chuyển;
  - task đối chứng: đẩy lưỡi vào má (phồng nhưng không có khí); chạm nhẹ vào cup mà không cử động cơ;
  - cố định cup tốt hơn;
  - về lâu dài: tái tạo **đồng thời** độ dẫn và dịch chuyển điện cực [Soleimani 2006; Gómez-Laberge & Adler
    2008; Dai 2008].

### 2.4 Cáp di chuyển

- **Là gì:** dây dài treo lủng lẳng, khi đầu hay hàm cử động thì dây chuyển động, làm thay đổi điện dung giữa các
  dây và lực kéo lên cup. Điện cực chủ động (active electrode: khuếch đại ngay tại điện cực) là một hướng phần cứng
  để giảm ảnh hưởng của dây dài; ví dụ một hệ EIT như vậy là [Gaggero 2012]. Bài này lấy động lực từ chất lượng
  tiếp xúc và việc đặt điện cực, không trực tiếp chứng minh lợi ích với dây di chuyển.
- **Đo/khắc phục:** gom và cố định dây dọc cổ/vai; ghi chú khi dây bị chạm; xem các cặp có gai bất thường trong
  `tables/changes_per_measurement.csv`.

### 2.5 Drift theo thời gian

- **Là gì:** sau khi gắn, trở kháng tiếp xúc tiếp tục thay đổi (gel thấm, da ấm lên, mồ hôi). Độ dẫn của mô cũng
  phụ thuộc nhiệt độ. Đo kéo dài còn bị sai số khi gắn lại điện cực (tới 5% giá trị gốc) và khi đổi tư thế
  [Lozano 1995].
- **Ở dữ liệu của bạn:** không tách được, vì chỉ có 1 REST ở đầu và task cuối cách REST ~137 s.
  SMILE_LEFT~SMILE_RIGHT ≈ 0 (đo cách nhau 23 s) cho thấy drift không phải nguồn chính của *hình dạng* thay đổi,
  nhưng chưa loại trừ được phần *độ lớn*.
- **Đo:** REST→TASK→REST; cặp REST kẹp task (`rest_across_task_pairs` trong QC); REST_CONTROL mỗi vòng; vài phút
  REST sau khi gắn cup trước khi bắt đầu.

### 2.6 Sinh lý nền

- Mạch đập, thở, nuốt và trương lực cơ làm trở kháng dao động ngay cả khi "nghỉ". Ở mặt dưới, dữ liệu EIT đường
  thở bị nhiễm artifact do cử động thở, dòng máu động mạch cảnh và cử động cổ [Ayoub et al. 2019, trích lại theo
  Piccin 2023; chưa đọc bài gốc]. Trên ngực, thành phần do tim nhỏ hơn thành phần do thở [Frerichs 2017].
- Trong một frame 20.6 s, các dao động này rơi vào những kênh khác nhau một cách ngẫu nhiên. Chúng là một phần
  của "nhiễu REST→REST".

### 2.7 Điện dung ký sinh, common-mode, crosstalk

- **Là gì:** ở tần số càng cao, điện dung của cáp, của switch (ADG2128 ~18.5 pF, giá trị điển hình theo
  CN0565) và của mạch càng cho dòng rò đi đường khác, làm sai biên độ và pha. Common-mode của điện cực đo cũng gây sai số. Đây là chủ đề trung tâm
  của thiết kế phần cứng EIT [Boone & Holder 1996; McEwan 2007; Wu 2021].
- **Ở dữ liệu của bạn:** pha thô lệch rất lớn theo tần số (−68.5° / +91.2° / −121.9°). Đó là độ trễ của mạch, bị
  triệt tiêu trong dz. Reciprocity thô xấu nhất ở 10 kHz (17.7%), nhưng phần còn lại sau fit gain thì lớn hơn ở
  50/80 kHz (7.2–8.9% so với 4.9%). Phần còn lại này có thể do điện dung ký sinh. Đây là **giả thuyết, chưa kiểm
  chứng**, và fit ở 50/80 kHz bản thân nó cũng chưa kết luận được (§2.2).
- **Đo:** mạng điện trở/phantom điện trở đã biết, dễ mở rộng [Hahn 2008; Gagnon 2010]; quy trình hiệu chuẩn
  multi-frequency [Oh 2007]; đưa sai lệch phần cứng vào thuật toán [Hartinger 2007].

### 2.8 EMI

Board giải điều chế bằng DFT đúng tại tần số kích thích (10–80 kHz), nên nhiễu điện lưới 50/60 Hz và hài bậc thấp
bị loại phần lớn. Vẫn nên tránh để dây song song với dây nguồn, adapter hay màn hình.

### 2.9 Thu tuần tự (một frame kéo dài 20.6 s)

- **Là gì:** 208 phép đo không cùng lúc. Nếu cơ thể thay đổi trong lúc quét, các kênh đo sớm và đo muộn "thấy"
  những trạng thái khác nhau. Trên dữ liệu thở, độ trễ giữa hai phép đo đảo vai tương quan với **độ dao động theo
  thời gian (SD)** của reciprocity error, và hiệu chỉnh theo thời điểm đo làm giảm sai số này [Yerworth & Bayford
  2013]. Thứ tự quét giống nhau ở mọi tần số, nên cơ chế này không giải thích được khác biệt giữa các tần số.
- **Ở dữ liệu của bạn:** các kênh chỉ dùng cup trái được đo trung bình lúc 4.1 s, chỉ dùng cup phải lúc 15.2 s.
  Nếu cử động nhạt dần trong 22 s giữ, **phía trái sẽ trông mạnh hơn với bất kỳ task nào**. `patterns.csv` có
  thời điểm của từng phép đo, nên có thể kiểm tra sau.
- **Khắc phục:** đảo thứ tự quét ở một nửa số trial; rút ngắn frame (chỉ giữ kênh mạnh); nhiều frame mỗi task.

### 2.10 Sai số mô hình (khi tái tạo ảnh)

- **Không mô hình 2D nào khớp được dữ liệu đo trên một vật thể 3D** [Lionheart 1999, theo Grychtol 2012]; mô hình
  2D không mô tả được phân bố dòng thật trong cơ thể [Adler 2009]. Dùng hình tròn thay cho hình dạng thật làm chất
  lượng ảnh giảm nặng. Với ngực người/lợn, sai lệch hình dạng ΔS ≤ ~4% thì các thuật toán còn chịu được. ΔS là
  diện tích hiệu đối xứng giữa hai đường biên (chia cho π), đo trên mô hình ngực đùn từ đường biên 2D với 16 điện
  cực cách đều. Chính tác giả lưu ý ngưỡng 4% này **không phải điều kiện đủ hay cần** [Grychtol 2012].
- Kích thước/vị trí điện cực và hình dạng biên là những nguồn khó nhất cho **ảnh tĩnh** (mô phỏng 2D)
  [Kolehmainen 1997; Blott 1998, theo Kao 2006]. Với ảnh hiệu (dz) như của bạn, một phần sai số này triệt tiêu.
  Mô hình 3D là cần thiết khi muốn diễn giải giải phẫu [Lionheart 2004].
- **Ở dữ liệu của bạn:** mô hình đĩa 2D, 16 điện cực cách đều, khớp REST chỉ ρ = 0.65–0.67. Ảnh JAC có các cặp
  đỏ/xanh xen kẽ; ba thuật toán chỉ giống nhau ở mức r ≈ 0.3–0.7. Chi tiết: [facial-environment-and-forward-models.md](facial-environment-and-forward-models.md).

### 2.11 Thực hiện task không lặp lại

Ngay ở người khỏe, cùng một biểu cảm làm lại cũng hơi khác: trong cùng buổi, sai khác trung bình của các điểm mốc
từ 0.74 mm (REST, lặp lại tốt nhất) tới 1.12 mm (**phồng má, kém lặp lại nhất**), và người làm **không giữ cùng
mức đối xứng** giữa các lần. Tuy vậy, chính các tác giả kết luận độ lặp lại trong buổi là **cao** và khác biệt
giữa các buổi là nhỏ [Johnston 2003, 30 người, camera 3D]. Với EIT, một sai khác ~1 mm ngay dưới cup có thể tạo
thay đổi đáng kể; việc nó có lớn hơn nhiễu điện tử hay không là **giả thuyết của chúng ta**, chưa có số đo. Cách
đo duy nhất là **lặp lại** (≥ 2 vòng) kèm **video**.

### 2.12 Thay đổi sinh lý thật của cơ (tín hiệu bạn muốn)

Để so sánh: khi cơ gấp ngón tay co đẳng trường, trở kháng ở 50 kHz của cẳng tay tăng (cả R và X). Các tác giả
cho rằng đó chủ yếu là thay đổi sinh lý trong cơ chứ không phải hình thái, và thay đổi xuất hiện trước cả khi lực
được tạo ra [Shiffman 2003, 6 người khỏe]. Như vậy **tín hiệu cơ là có thật, nhưng nhỏ**: độ nhạy điển hình chỉ
cỡ **0.0x% cho mỗi newton** lực ("a few hundredths of a per cent per newton"). Với lực nhỏ của cơ mặt, tín hiệu này có thể thấp hơn mức nền REST→REST
0.36–0.96% và nhỏ hơn hiệu ứng hình học. Trên mặt, nó còn bị trộn với các nguồn ở mục 2.2–2.5 và 2.11. Thiết kế
thí nghiệm phải tách được chúng.

---

## 3. Xếp hạng ưu tiên cho dữ liệu mặt của bạn

1. **Điện cực di chuyển / hình dạng mặt (2.3)**: giả thuyết là nguồn lớn nhất của thay đổi đo được (chưa tách
   được); quyết định ta có thể nói gì về "cơ".
2. **Thực hiện task không lặp lại (2.11)** và **drift/thứ tự (2.5)**: quyết định độ tin cậy của nhận dạng task.
3. **Dòng bơm không được đo (2.2)**: làm sai reciprocity, và mọi so sánh tuyệt đối.
4. **Thu tuần tự (2.9)**: làm lệch đánh giá trái/phải.
5. **Nhiễu điện tử (2.1)**: đã kiểm soát được bằng cách bỏ kênh yếu, nhưng giới hạn số kênh hữu ích (~1/3).
6. **Sai số mô hình (2.10)**: chỉ quan trọng khi muốn kết luận từ ảnh.

## 4. Protocol đo nhiễu cho phiên tới

| Mục tiêu | Cách làm | Ghi ở đâu |
|---|---|---|
| Nhiễu thiết bị | Bench: mạng điện trở cố định, ≥ 10 frame liên tiếp, cùng cài đặt | `app check` trên phiên bench |
| Nhiễu + sinh lý nền trên người | ≥ 3 frame REST liên tiếp ngay đầu phiên | `rest_rest_rms_counts`, `rest_rest_median_pct_ge100` |
| Drift + phục hồi | REST→TASK→REST; cặp REST kẹp task | `rest_across_task_pairs` |
| Phân bố "không làm gì" cùng nhịp cue | REST_CONTROL mỗi vòng (`app design`) | dz của REST_CONTROL trong `task_features.csv` |
| Dòng bơm | thử `impedance_mode` trên bench rồi trên người | `qc_drive_gain.csv`, reciprocity |
| Dịch chuyển cup / hình dạng | video có đánh dấu cup; task đối chứng đẩy lưỡi vào má | ghi chú phiên + video |
| Thứ tự quét | đảo thứ tự cặp drive ở một nửa số trial (nếu pilot cho phép) | so sánh LI hai nửa |
| Lặp lại task | thứ tự ngẫu nhiên, ≥ 2 vòng | recognition leave-one-repetition-out |
| Contact | đo contact impedance trước/sau phiên; ghi cup nào yếu | `cup_and_contact_notes` |

> *For the professor:* "In our pilot facial data, the dominant errors are probably not electronic noise but
> electrode-related and model-related: a 12–18 % reciprocity error, which at 10 kHz is largely explained by
> per-drive current differences in voltage mode (the fit is inconclusive at 50/80 kHz); skin stretch and electrode
> movement during the task (a hypothesis we cannot yet separate from conductivity change); sequential acquisition
> over 20.6 s; and the 2-D model mismatch. The next session therefore measures each of them explicitly: several
> consecutive rest frames for the noise floor, rest–task–rest blocks for drift, rest-only controls, impedance mode
> for the current, video for electrode movement, and a tongue-in-cheek control for the cheek-puff air hypothesis."

---

## Tài liệu tham khảo (đã kiểm tra tồn tại; DOI)

- Adler A, Guardo R, Berthiaume Y (1996). Impedance imaging of lung ventilation: do we need to account for chest expansion? *IEEE TBME* 43:414–420. [10.1109/10.486261](https://doi.org/10.1109/10.486261)
- Adler A, Arnold JH, Bayford R, et al. (2009). GREIT: a unified approach to 2D linear EIT reconstruction of lung images. *Physiol Meas* 30:S35–55. [10.1088/0967-3334/30/6/S03](https://doi.org/10.1088/0967-3334/30/6/S03)
- Asfaw Y, Adler A (2005). Automatic detection of detached and erroneous electrodes in EIT. *Physiol Meas* 26:S175–183. [10.1088/0967-3334/26/2/017](https://doi.org/10.1088/0967-3334/26/2/017)
- Ayoub G et al. (2019), lower-face EIT artefacts: cited only via Piccin 2023 (secondary; not read). The same group's related paper: Ayoub G, Dang TH, Oh TI, Kim SW, Woo EJ (2020). Feature extraction of upper airway dynamics during sleep apnea using EIT. *Sci Rep* 10:1637. [10.1038/s41598-020-58450-4](https://doi.org/10.1038/s41598-020-58450-4)
- Blott BH, Daniell GJ, Meeson S (1998). EIT with compensation for electrode positioning variations. *Phys Med Biol* 43:1731–1739. [10.1088/0031-9155/43/6/025](https://doi.org/10.1088/0031-9155/43/6/025)
- Boone KG, Holder DS (1996). Current approaches to analogue instrumentation design in EIT. *Physiol Meas* 17:229–247. [10.1088/0967-3334/17/4/001](https://doi.org/10.1088/0967-3334/17/4/001)
- Boyle A, Adler A (2011). The impact of electrode area, contact impedance and boundary shape on EIT images. *Physiol Meas* 32:745–754. [10.1088/0967-3334/32/7/S02](https://doi.org/10.1088/0967-3334/32/7/S02)
- Cömert A, Hyttinen J (2014). Impedance spectroscopy of changes in skin-electrode impedance induced by motion. *BioMed Eng OnLine* 13:149. [10.1186/1475-925X-13-149](https://doi.org/10.1186/1475-925X-13-149)
- Dai T, Gómez-Laberge C, Adler A (2008). Reconstruction of conductivity changes and electrode movements based on EIT temporal sequences. *Physiol Meas* 29:S77–88. [10.1088/0967-3334/29/6/S07](https://doi.org/10.1088/0967-3334/29/6/S07)
- Frerichs I et al. (2017). Chest EIT examination, data analysis, terminology, clinical use and recommendations: TREND consensus. *Thorax* 72:83–93. [10.1136/thoraxjnl-2016-208357](https://doi.org/10.1136/thoraxjnl-2016-208357)
- Gaggero PO, Adler A, Brunner J, Seitz P (2012). EIT system based on active electrodes. *Physiol Meas* 33:831–847. [10.1088/0967-3334/33/5/831](https://doi.org/10.1088/0967-3334/33/5/831)
- Gagnon H, Cousineau M, Adler A, Hartinger AE (2010). A resistive mesh phantom for assessing the performance of EIT systems. *IEEE TBME* 57:2257–2266. [10.1109/TBME.2010.2052618](https://doi.org/10.1109/TBME.2010.2052618)
- Gómez-Laberge C, Adler A (2008). Direct EIT Jacobian calculations for conductivity change and electrode movement. *Physiol Meas* 29:S89–99. [10.1088/0967-3334/29/6/S08](https://doi.org/10.1088/0967-3334/29/6/S08)
- Goren N et al. (2018). Multi-frequency EIT and neuroimaging data in stroke patients. *Sci Data* 5:180112. [10.1038/sdata.2018.112](https://doi.org/10.1038/sdata.2018.112)
- Grychtol B, Lionheart WRB, Bodenstein M, Wolf GK, Adler A (2012). Impact of model shape mismatch on reconstruction quality in EIT. *IEEE TMI* 31:1754–1760. [10.1109/TMI.2012.2200904](https://doi.org/10.1109/TMI.2012.2200904)
- Hahn G, Just A, Dittmar J, Hellige G (2008). Systematic errors of EIT systems determined by easily-scalable resistive phantoms. *Physiol Meas* 29:S163–172. [10.1088/0967-3334/29/6/S14](https://doi.org/10.1088/0967-3334/29/6/S14)
- Hartinger AE, Gagnon H, Guardo R (2007). Accounting for hardware imperfections in EIT image reconstruction algorithms. *Physiol Meas* 28:S13–27. [10.1088/0967-3334/28/7/S02](https://doi.org/10.1088/0967-3334/28/7/S02)
- Hartinger AE, Guardo R, Adler A, Gagnon H (2009). Real-time management of faulty electrodes in EIT. *IEEE TBME* 56:369–377. [10.1109/TBME.2008.2003103](https://doi.org/10.1109/TBME.2008.2003103)
- Johnston DJ, Millett DT, Ayoub AF, Bock M (2003). Are facial expressions reproducible? *Cleft Palate Craniofac J* 40:291–296. [10.1597/1545-1569_2003_040_0291_AFER_2.0.CO_2](https://doi.org/10.1597/1545-1569_2003_040_0291_AFER_2.0.CO_2)
- Kao T-J, Isaacson D, Newell JC, Saulnier GJ (2006). A 3D reconstruction algorithm for EIT using a handheld probe for breast cancer detection. *Physiol Meas* 27:S1–11. [10.1088/0967-3334/27/5/S01](https://doi.org/10.1088/0967-3334/27/5/S01) (local PDF in `reference/papers/electrodes_placement/`)
- Kolehmainen V, Vauhkonen M, Karjalainen PA, Kaipio JP (1997). Assessment of errors in static EIT with adjacent and trigonometric current patterns. *Physiol Meas* 18:289–303. [10.1088/0967-3334/18/4/003](https://doi.org/10.1088/0967-3334/18/4/003)
- Lionheart WRB (1999). Uniqueness, shape, and dimension in EIT. *Ann N Y Acad Sci* 873:466–471. [10.1111/j.1749-6632.1999.tb09495.x](https://doi.org/10.1111/j.1749-6632.1999.tb09495.x)
- Lionheart WRB (2004). EIT reconstruction algorithms: pitfalls, challenges and recent developments. *Physiol Meas* 25:125–142. [10.1088/0967-3334/25/1/021](https://doi.org/10.1088/0967-3334/25/1/021)
- Lozano A, Rosell J, Pallás-Areny R (1995). Errors in prolonged electrical impedance measurements due to electrode repositioning and postural changes. *Physiol Meas* 16:121–130. [10.1088/0967-3334/16/2/004](https://doi.org/10.1088/0967-3334/16/2/004)
- Mamatjan Y, Grychtol B, Gaggero P, Justiz J, Koch VM, Adler A (2013). Evaluation and real-time monitoring of data quality in EIT. *IEEE TMI* 32:1997–2005. [10.1109/TMI.2013.2269867](https://doi.org/10.1109/TMI.2013.2269867)
- McAdams ET, Jossinet J, Lackermeier A, Risacher F (1996). Factors affecting electrode-gel-skin interface impedance in EIT. *Med Biol Eng Comput* 34:397–408. [10.1007/BF02523842](https://doi.org/10.1007/BF02523842)
- McEwan A, Cusick G, Holder DS (2007). A review of errors in multi-frequency EIT instrumentation. *Physiol Meas* 28:S197–215. [10.1088/0967-3334/28/7/S15](https://doi.org/10.1088/0967-3334/28/7/S15)
- Oh TI, Lee KH, Kim SM, Koo H, Woo EJ, Holder D (2007). Calibration methods for a multi-channel multi-frequency EIT system. *Physiol Meas* 28:1175–1188. [10.1088/0967-3334/28/10/004](https://doi.org/10.1088/0967-3334/28/10/004)
- Piccin VS et al. (2023). Feasibility of neck EIT to monitor upper airway dynamics during sleep. *Front Sleep* 2:1238508. [10.3389/frsle.2023.1238508](https://doi.org/10.3389/frsle.2023.1238508)
- Rosell J, Colominas J, Riu P, Pallàs-Areny R, Webster JG (1988). Skin impedance from 1 Hz to 1 MHz. *IEEE TBME* 35:649–651. [10.1109/10.4599](https://doi.org/10.1109/10.4599)
- Saulnier GJ, Ross AS, Liu N (2006). A high-precision voltage source for EIT. *Physiol Meas* 27:S221–236. [10.1088/0967-3334/27/5/S19](https://doi.org/10.1088/0967-3334/27/5/S19)
- Shiffman CA, Aaron R, Rutkove SB (2003). Electrical impedance of muscle during isometric contraction. *Physiol Meas* 24:213–234. [10.1088/0967-3334/24/1/316](https://doi.org/10.1088/0967-3334/24/1/316)
- Soleimani M, Gómez-Laberge C, Adler A (2006). Imaging of conductivity changes and electrode movement in EIT. *Physiol Meas* 27:S103–113. [10.1088/0967-3334/27/5/S09](https://doi.org/10.1088/0967-3334/27/5/S09)
- Wu Y, Hanzaee FF, Jiang D, Bayford R, Demosthenous A (2021). EIT for biomedical applications: circuits and systems review. *IEEE Open J Circuits Syst* 2:380–397. [10.1109/OJCAS.2021.3075302](https://doi.org/10.1109/OJCAS.2021.3075302)
- Yerworth R, Bayford R (2013). The effect of serial data collection on the accuracy of EIT images. *Physiol Meas* 34:659–669. [10.1088/0967-3334/34/6/659](https://doi.org/10.1088/0967-3334/34/6/659)
- Zhang J, Patterson RP (2005). EIT images of ventilation: what contributes to the resistivity changes? *Physiol Meas* 26:S81–92. [10.1088/0967-3334/26/2/008](https://doi.org/10.1088/0967-3334/26/2/008)
- Analog Devices. CN-0565 Circuit Note, Rev. A (local: `reference/cn0565 rev. a.pdf`).
