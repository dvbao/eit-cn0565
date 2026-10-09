# Pilot đầu tiên: rest → task → rest, xem dữ liệu thay đổi thế nào

Mục tiêu hiện tại theo yêu cầu của giáo sư: **thu reference khi nghỉ, thu khi
thực hiện task, rồi xem điện áp có khác nhau và khác biệt có lặp lại không**.
Đầu ra đầu tiên là dữ liệu và biểu đồ, chưa cần một ảnh facial EIT chính xác.
Đây là kế hoạch phân tích/đề xuất pilot, không xác nhận thiết bị tự lắp đã an
toàn để inject current lên người. Frequency/amplitude/current thực tế chưa
được xác minh; không suy ra giá trị an toàn từ một lệnh chạy được.

## 1. Những thứ giữ cố định

- Một layout 16 cups trong cả session: không đổi vị trí/dây giữa rest và task.
  Nếu dùng C16-R đang đề xuất: mỗi bên tám vị trí, từ trán ngoài → thái dương
  → trước tai → sau tai → dưới góc hàm → giữa bờ dưới hàm → phía trước bờ dưới
  hàm → dưới cằm bên. L/R là bên trái/phải của người được đo. Ghi ảnh vị trí,
  cup size, contact medium, khoảng cách tới landmarks, cách cố định dây.
  Xem [map dây/P1](protocols/c16r-p1-wiring-proposal.json).
- Các vị trí này là **candidate layout**, chưa được paper chứng minh tối ưu
  cho facial EIT. Lý do thử là khảo sát tín hiệu quanh vùng mặt và giữ vùng
  má/môi trống; pilot sẽ kiểm tra mức hữu dụng, không giả định nó đã có.
- Cùng frequency, excitation amplitude, force/sense sequence và cách gắn cup.
  Lưu settings trong metadata, không điều chỉnh giữa một trial.
- 16 cups đều được switch luân phiên làm F+/F−/S+/S−; không có cup nào là
  reference cố định như sEMG. **Reference state là một vector dữ liệu lúc
  nghỉ**, không phải dây reference. Không tự thêm dây body-ground vào P1 GND.
  Schematic mapping cần kiểm tra chiều connector và continuity thực tế.

CN0565 cung cấp phép đo voltage qua `all_voltages`; collector hiện lưu real
và imaginary raw, chưa khẳng định đơn vị volt hoặc impedance đã hiệu chuẩn.
Nguồn: [official pyadi-iio CN0565 API](https://analogdevicesinc.github.io/pyadi-iio/devices/adi.cn0565.html).
Các giá trị này chịu ảnh hưởng của current thực tế: excitation voltage cố định
không đảm bảo current không đổi. Nếu muốn diễn giải ΔZ hoặc đưa vào inverse
model, phải kiểm tra current/calibration riêng.

## 2. Timing trước, task sau

Một frame là 208 phép đo **tuần tự**, không phải 208 kênh đồng thời. Collector
ghi khoảng `[start, end]` của từng frame, cue giữa các frame, và hai loại timing:

- `frame_duration_p95_s`: 95th percentile thời gian gọi đọc một frame.
- `frame_start_interval_p95_s`: 95th percentile khoảng cách giữa hai lần
  bắt đầu frame, **gồm cả overhead ghi file/cue**. Đây là chỉ số hữu ích hơn
  khi ước lượng thu được bao nhiêu frame trong một hold.

P95/T95 là thống kê của lần chạy, không phải deadline bảo đảm hoặc timing
chính xác của từng electrode. Đo trên cấu hình/connection thật bằng known
load trước; thời gian mock không dùng để quyết định thời gian hold.

Mục tiêu kỹ thuật đề xuất: ít nhất **3 complete stable frames** cho mỗi state.
Nếu khoảng cách frame là khoảng τ giây, phần hold ổn định cần cỡ 3τ, cộng
thời gian chuyển động và căn biên frame. Ví dụ τ=1 s chỉ là minh họa, không
phải tốc độ đã đo của CN0565. Sau thu, tính chính xác độ dài từng frame từ CSV.
Nếu 5 s không chứa đủ stable frames, không mặc định giữ lâu đến mệt; phải
điều chỉnh kế hoạch/pattern set trước, hoặc chấp nhận pilot ít frame hơn và
báo hạn chế. Không thay pattern set mà vẫn giả định 208.

Ghi video nhìn thấy mặt **và cue/frame counter trên terminal** hoặc một marker
đồng bộ có thể đối chiếu. Video quay mặt đơn độc mà không có clock/marker
chung chưa đủ để align chính xác. Chọn frame chỉ khi **toàn bộ khoảng đọc**
nằm trong đoạn nghỉ/hold ổn định. Frame chứa onset/offset bị loại khỏi median.
Không cần người làm task phản ứng đúng lúc electrode đầu tiên inject.

## 3. Một task, lặp lại trước khi thêm nhiều task

Đề xuất khởi đầu **purse lips — chúm môi**, với jaw và tư thế đầu nhất quán.
Task này có trong atlas facial sEMG; atlas giúp định nghĩa task và các cơ có
thể tham gia, **không chứng minh placement EIT hay isolated orbicularis oris**.
Nguồn: [Schumann et al., 2021 — full paper](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0254932).

Mỗi trial: `pre-rest → purse-lips hold → post-rest`. Pre-rest: mặt thư giãn,
tư thế đầu cố định, jaw/lips ở một trạng thái đã mô tả; không nói chuyện.
Không gọi đây là “không có hoạt động sinh học”: tim, hô hấp và trương lực cơ
vẫn tồn tại. Post-rest trở về cùng pose, đợi ổn định trước khi chọn frames.

Lặp **5 trials** là đề xuất engineering pilot, không phải sample-size chứng
minh đủ power. Thêm một **rest → rest → rest** với cùng timing/cue nhưng không
làm task, để đo mức thay đổi khi không làm gì. Sau khi một task có dữ liệu
ổn định, mới thêm smile trái/phải hoặc task khác. Không làm toàn bộ task list
trước khi biết tốc độ scan và chất lượng dữ liệu.

Lưu trial ID, cue, task onset/offset quan sát trên video, frames bị loại và
lý do, lead movement/contact issues. Dùng baseline gần ngay trước **mỗi** trial;
không lấy một baseline đầu buổi cho mọi task.

## 4. Từ CSV đến biểu đồ

Luồng file: `cn0565_capture.py → PREFIX.{voltages,frames,events}.csv + meta.json
→ cn0565_prepare_difference.py → trial.json → cn0565_plot_difference.py → trial.png`.

Chạy thử hoàn toàn offline trên macOS, **không kết nối board/không inject**:

```sh
python3 scripts/cn0565_capture.py --mock --frames 12 \
  --output-prefix eit-measurement/data/bench/software-check-01

python3 scripts/cn0565_prepare_difference.py \
  --input-prefix eit-measurement/data/bench/software-check-01 \
  --rest-frames 0,1,2 --task-frames 4,5,6 --post-rest-frames 9,10,11 \
  --output eit-measurement/data/results/software-check-01.json

.venv-sim/bin/python scripts/cn0565_plot_difference.py \
  --comparison eit-measurement/data/results/software-check-01.json \
  --output eit-measurement/data/results/software-check-01.png
```

Nếu environment có matplotlib nằm ở nơi khác, dùng interpreter của environment
đó cho lệnh plot. Collector/preparation mock chỉ cần Python standard library.
Không chạy lại cùng prefix/output: scripts từ chối overwrite. **Mock này tăng
điện áp theo frame để kiểm tra file format; không mô phỏng sinh học hay task.**

Với dữ liệu thật, `--uri`, `--frequency-hz`, `--amplitude-mv` phải là cấu hình
đã xác minh của board; chưa có thông tin này để viết lệnh live chính xác.
Có thể dùng `--frames N` ghi liên tục, hoặc schedule có terminal cues. Xem
[hướng dẫn collector](cn0565-capture-and-reconstruction-gates.md#3-raw-logger-and-timing-bench-check).
Thay frame IDs trong preparation bằng các frame ổn định thật đã đối chiếu video.

Với mỗi pattern m, tính componentwise median riêng real/imag:

`v0[m] = median(pre-rest frames); v1[m] = median(task frames); Δv[m] = v1[m] − v0[m]`.

Median giảm tác động của một số outliers, không loại bỏ contact artifact có
hệ thống. Không lấy 208 readings của một frame làm 208 trials độc lập.

Biểu đồ có ba phần:

1. **Time course:** khoảng cách RMS complex của từng complete frame so với
   baseline; thanh ngang thể hiện khoảng scan. RMS ≥0, thể hiện độ lớn thay
   đổi, không phải hướng conductivity hay phần trăm cơ hoạt động.
2. **Real difference:** signed task−rest của 208 patterns, thêm post-rest−rest.
3. **Imaginary difference:** tương tự cho thành phần imaginary.

Trục pattern ID là **cấu hình bốn điện cực**, không phải vị trí pixel trên mặt.
Không gắn dấu dương/âm trực tiếp với tăng/giảm conductivity tại một cơ.

## 5. Báo kết quả gì với giáo sư?

So sánh cùng task giữa 5 trials, rest-only control và recovery:

| Quan sát | Diễn giải thận trọng / bước tiếp |
|---|---|
| Task thay đổi rõ hơn rest-only, pattern tương tự qua trials, post-rest trở gần baseline | Evidence ban đầu của repeatable task-associated voltage changes với layout này |
| Rest-only thay đổi tương đương task hoặc mọi state trôi dần | Chưa tách được task khỏi drift/noise; kiểm tra contacts/settings |
| Spike chỉ ở chuyển động onset, stable hold gần rest | Có thể chủ yếu motion/contact hoặc dynamic effect; giữ onset và stable-hold analysis riêng |
| Không thấy khác biệt đáng kể so với biến thiên nghỉ | Chưa phát hiện với setup hiện tại; không chứng minh cơ không hoạt động |

Không áp ngưỡng “gấp X là thành công” khi chưa đo noise/repeatability. Metrics
JSON chỉ mô tả. Các residual của pre-rest so với median chính nó có thể thấp
hơn variation thật; rest-only control ở đoạn độc lập quan trọng hơn.

Câu báo cáo tiếng Anh: “We tested whether a fixed 16-electrode configuration
produces repeatable task-associated boundary-voltage changes relative to
nearby resting baselines. We examined rest-only variation and post-task
recovery. These measurements do not yet establish muscle-specific activation
or anatomically accurate facial EIT images.”

Mục tiêu facial EIT vẫn giữ: dữ liệu đã lưu exact sequence và pin map để
phát triển model-matched reconstruction về sau. BP/JAC/GREIT trên disk mesh
không phải phép kiểm chứng một thay đổi nằm ở cơ nào trên mặt.
