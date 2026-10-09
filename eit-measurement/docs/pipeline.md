# Quy trình end-to-end: từ thiết kế phiên đo tới báo cáo (reproducible)

Tài liệu này là **quy trình chuẩn** cho mỗi lần thu dữ liệu mặt bằng CN0565. Mỗi bước có đầu vào, lệnh
chạy và tiêu chí đạt rõ ràng, để bất kỳ ai (kể cả bạn sau 6 tháng) cũng làm lại được và ra cùng kết quả.

- Phần **thu dữ liệu** chạy trên máy Windows bằng phần mềm pilot (`cn0565_pilot.py`).
- Phần **phân tích** chạy bằng package `app.eit` trong repo này, trên macOS hoặc Windows.

> Trạng thái: pipeline phân tích đã được kiểm chứng trên 3 phiên ngày 2026-10-05. Nó tái tạo y hệt
> (sai khác < 10⁻⁹) các con số chính của báo cáo [2026-10-05](../../docs/reports/2026-10-05-three-frequency-analysis.md):
> QC, đặc trưng task, lateralization, tương quan, additivity, F8, nhận dạng và metric ảnh, liệt kê trong
> `backend/tests/fixtures/three_frequency_20261005_expected.json`. Điều này được kiểm tra tự động bằng
> `backend/tests/test_regression.py`.

---

## 0. Sơ đồ tổng quát

```
 A. Thiết kế phiên ── app design (seed) ──► lịch phiên .csv/.md
        │
 B. Kiểm tra phần cứng & kết nối (Windows) ──► IIO OK, known-load OK
        │
 C. Gắn điện cực + ghi chép (ảnh, vị trí, chất dẫn, ghi chú contact)
        │
 D. Thu dữ liệu: cn0565_pilot.py (live) + video có hiện cue ──► thư mục phiên (raw)
        │
 E. Chép thư mục phiên vào data/sessions/ (KHÔNG sửa) + xác nhận cue (trial_windows.csv)
        │
 F. app check <phiên> ──► FAIL: ghi lý do, không phân tích tiếp
        │ PASS
 G. Viết config study (JSON): phiên nào, nhãn, baseline, ngưỡng
        │
 H. app study <config> ──► tables/ figures/ slides/ clean/ manifest.json README.md
        │
 I. Đọc README tự động, diễn giải theo giới hạn ──► báo cáo ../docs/reports/ (gốc repo), slide
        │
 J. git commit: code + config + raw + docs (output tái tạo được bằng lệnh H)
```

## 1. Thư mục: cái gì nằm ở đâu

Toàn cảnh, kế hoạch và tiến độ: [architecture.md](architecture.md). Cài đặt và "sửa gì ở đâu":
[README.md](../README.md). Thời gian mỗi phép đo, sơ đồ nối dây: [hardware-mapping.md](hardware-mapping.md) §5–6.
Đường dẫn trong bảng tính từ `eit-measurement/`, trừ khi ghi (gốc repo).

| Đường dẫn | Nội dung | Ai tạo | Được sửa? |
|---|---|---|---|
| `data/hardware/` | Sơ đồ nối dây + cấu hình đo (số điện cực, khoảng cách bơm/đo, tần số, amplitude) | bạn | Có |
| `data/protocols/` | Study design: task, câu hướng dẫn, thời lượng, số vòng, seed | bạn | Có |
| `data/sessions/<session>/` | Dữ liệu thô của từng phiên (meta.json, patterns.csv, …) | phần mềm thu | **Không bao giờ** |
| `data/bench/` | Dữ liệu thô của các script bench/ví dụ ADI (định dạng cũ, không phải phiên) | `scripts/` (gốc repo) | Không |
| `data/studies/<study_id>.json` | Mô tả một study: phiên nào, nhãn, baseline, ngưỡng | bạn | Có |
| `data/results/<study_id>/` | Mọi output phân tích của study | `app study` | Không, chạy lại lệnh thay vì sửa |
| `data/results/checks/<session>/` | QC nhanh của một phiên | `app check` | Không |
| `backend/app/eit/` | Code phân tích | — | Chỉ khi sửa phương pháp, kèm test |
| `backend/app/schemas/`, `backend/app/services/` | Mô hình cấu hình/study design; lập lịch phiên | — | Chỉ khi sửa quy tắc, kèm test |
| `backend/tests/` | Unit test + test hồi quy với kết quả đã công bố | — | Có |
| `docs/pipeline.md` | Tài liệu quy trình này | — | Có |
| `../docs/reports/` (gốc repo) | Báo cáo diễn giải theo ngày | bạn/AI | Có |
| `data/protocols/schedules/` | Lịch phiên in ra cho người đo (tạo khi chạy `design --out` lần đầu) | `app design` / bạn | Có |
| `../archive/` (gốc repo) | Script/output cũ đã được thay thế (chỉ để tham khảo) | — | Không |

Có 4 lệnh, đều chạy từ **thư mục gốc repo** bằng Python của môi trường phân tích
(`.venv-sim/bin/python` trên macOS; `python` trơn không có trên máy này). **Quy ước: chạy mọi lệnh từ gốc repo
(`eit-cn0565/`)**; đường dẫn `data/…` (cả đầu vào lẫn `--out`) được hiểu là nằm trong `eit-measurement/` (chạy từ
trong `eit-measurement/` cũng được, khi đó dùng `../.venv-sim/bin/python`):

| Lệnh | Dùng khi | Thời gian |
|---|---|---|
| `.venv-sim/bin/python -m app design …` | Trước phiên: lịch phiên từ study design + cấu hình đo, có kiểm tra khả thi | < 1 s |
| `.venv-sim/bin/python -m app check <phiên>` | Ngay sau khi đo: QC một phiên | ~3 s |
| `.venv-sim/bin/python -m app study <config>` | Phân tích đầy đủ một study | ~30 s |
| `.venv-sim/bin/python -m app hash <phiên>` | In SHA-256 của file thô (provenance) | < 1 s |

Cài môi trường phân tích (một lần, macOS/Linux):

```bash
python3 -m venv .venv-sim
.venv-sim/bin/python -m pip install -r eit-measurement/requirements.txt
# cho Python biết package backend và frontend nằm ở đâu, để "python -m app" / "python -m frontend" chạy từ gốc repo:
printf "%s\n%s\n" "$PWD/eit-measurement/backend" "$PWD/eit-measurement" \
  > "$(.venv-sim/bin/python -c 'import site; print(site.getsitepackages()[0])')/eit_studio_backend.pth"
.venv-sim/bin/python -m unittest discover -s eit-measurement/backend/tests -p "test_*.py"   # phải OK
```

Trên Windows dùng môi trường đo sẵn có, sau khi tạo file `.pth` tương tự trong
`cn0565-env\Lib\site-packages\` (hai dòng: đường dẫn tuyệt đối tới `eit-measurement\backend` và tới `eit-measurement`):
`.\cn0565-env\Scripts\python.exe -m app …`. Kết quả chỉ được **đảm bảo y hệt** với các phiên bản ghim trong
`eit-measurement/backend/requirements.txt`.

---

## A. Thiết kế phiên (trước ngày đo)

Quyết định trước và ghi lại. Thiết kế đề xuất cho phiên tới khắc phục các giới hạn của pilot 2026-10-05:

| Quyết định | Đề xuất | Lý do |
|---|---|---|
| Tần số | **Một tần số cố định** (gợi ý 50 kHz) | Không lẫn tần số với phiên; 50 kHz có nhiều kênh mạnh nhất và reciprocity tốt nhất trong pilot (lý do thực tế, chưa phải sinh lý) |
| Cấu trúc | **REST → TASK → REST** cho mọi task | Tách được drift, carry-over, phục hồi |
| Thứ tự | **Ngẫu nhiên có seed**, ≥ 2 vòng | Tách task khỏi vị trí trong chuỗi |
| Mức nhiễu | **≥ 3 frame REST liên tiếp** ở đầu + **REST_CONTROL** mỗi vòng | Đo nhiễu thật thay vì giả định 2 count; REST_CONTROL là phép thử "không làm gì" cùng nhịp cue |
| Task đối chứng | Thêm `TONGUE_CHEEK_LEFT/RIGHT` | Phân biệt "không khí trong má" với "má phồng/da căng" |
| Xác nhận cử động | Video quay mặt, thấy được cue/số frame trên màn hình | Gán nhãn không chỉ dựa vào cue |

Study design là một file JSON trong `data/protocols/` (ví dụ `facial-rest-task-rest-v1.json`: 8 task kèm câu
hướng dẫn, 2 vòng, seed, 3 frame REST đầu phiên, REST_CONTROL mỗi vòng, thời lượng GET READY / RELEASE).
Cấu hình đo là một file trong `data/hardware/` (số điện cực, khoảng cách bơm/đo, tần số, amplitude, thời gian
mỗi phép đo). Sinh lịch phiên từ hai file này:

```bash
.venv-sim/bin/python -m app design \
  --design data/protocols/facial-rest-task-rest-v1.json \
  --measurement data/hardware/measurement-16el-50kHz.json \
  --out data/protocols/schedules/2026-10-06-design
```

Lệnh in số phép đo/frame và thời lượng 1 frame, rồi ghi `…-design.csv` và `…-design.md`: thứ tự khối, câu hướng
dẫn, thời lượng GET READY / HOLD / RELEASE, thời điểm ước tính và seed. **HOLD được tính từ cấu hình đo**:
HOLD = settle (2 s, chờ cử động ổn định sau cue) + số frame × thời lượng 1 frame + margin (0.5 s dự phòng)
(16 điện cực: 23.1 s; 8 điện cực: 6.5 s). Lệnh cũng kiểm tra file cấu hình đo và file nối dây (ví dụ: 8 điện cực
mà file nối dây có 16 cup sẽ bị báo lỗi). Thiết kế không khả thi thì lệnh dừng và nói lý do, ví dụ HOLD vượt mức
tối đa 30 s, hoặc một HOLD bạn tự đặt ngắn hơn mức cần đó (16 điện cực: dưới 23.1 s, dù đã dài hơn 1 frame 20.6 s).

Trong `facial-rest-task-rest-v1.json`, `release_s = 0`: sau HOLD chuyển thẳng sang GET READY của khối kế tiếp,
nên cột `release (s)` luôn là 0; khối REST được đo ngay sau mỗi task đóng vai trò phục hồi. Khối REST nối tiếp
một khối REST có GET READY = 0 (cứ giữ nguyên tư thế nghỉ).

Lối tắt không cần file study design: `--tasks SMILE_LEFT … --seed 20261006 --measurement
data/hardware/<cấu hình>.json`. Nếu bỏ `--measurement`, lệnh giả định 1 frame = 20.6 s (16 điện cực) và in ra
lời nhắc. Các cờ `--rounds`, `--frames-per-task`, … chỉ dùng với lối tắt; khi có `--design`, lệnh báo lỗi nếu bạn
dùng chúng (hãy sửa file study design). Phần mềm pilot chạy cue; hãy nhập đúng thứ tự này vào pilot. Pilot có
import trực tiếp được hay không thì cần kiểm tra trên máy Windows.

Giới hạn của pilot hiện tại (ghi trong `meta.json`): `frames_per_phase = 1` và `task_hold_cap_s = 30`.
- Khối REST nhiều frame: với 16 điện cực, 3 frame REST đầu phiên (~62 s) vượt cap 30 s nên `app design` đã tự
  tách thành 3 khối REST một frame (khối 1–3); cứ nhập đúng như lịch. Với ít điện cực hơn (ví dụ 8: 3 frame vừa
  một HOLD 14.4 s), lịch có một khối REST 3 frame; pilot chỉ có 1 frame/phase nên hãy nhập thành 3 trial REST một
  frame liên tiếp. Pipeline tự gộp các frame REST liên tiếp thành một khối.
- Muốn 2 frame mỗi task: sửa `"frames_per_task": 2` trong file study design. Với 16 điện cực, 2 frame cần HOLD
  43.7 s, vượt cap 30 s, nên lệnh từ chối; chỉ khả thi khi 1 frame ≤ 13.7 s (ví dụ 8 điện cực). Pilot hiện chỉ có
  1 frame/phase: nhập thành nhiều trial riêng thì mỗi frame bị tính là một lần lặp riêng.

`design.md` tự in ghi chú này khi có khối nhiều frame.

> Không tăng amplitude để "có tín hiệu mạnh hơn" khi chưa đo dòng thật và chưa review an toàn cho
> toàn bộ hệ thống tự lắp ([connection-checklist](../../docs/connection-checklist.md),
> [capture gates](../../docs/cn0565-capture-and-reconstruction-gates.md)).

## B. Phần cứng và kết nối (Windows, mỗi lần đo)

1. Làm theo [connection-checklist.md](../../docs/connection-checklist.md): DAPLINK → COM port → IIO context
   (`ad5940`, `adg2128`).
2. Khi **thay firmware, cáp hoặc điện cực**: kiểm tra trên **known load** (mạng điện trở) trước khi gắn lên
   người, theo [cn0565-capture-and-reconstruction-gates.md](../../docs/cn0565-capture-and-reconstruction-gates.md).
   Mục đích: xác nhận mapping, cực tính, reciprocity và mức nhiễu.
3. Trong pilot: chạy **contact QC** và **timing benchmark** (pilot lưu chúng vào `meta.json` →
   `contact_qc`, `timing_benchmark`).

## C. Gắn điện cực và ghi chép

- Dùng đúng file mapping đã version hóa (layout `C16-R-user-interleaved-TMJ5-v2-208`; X0..X15 xen kẽ
  L1, R1, …, L8, R8). Mapping được lưu nguyên vào `meta.json` của mỗi phiên.
- Ghi lại: ảnh hai bên mặt có nhãn cup, chất dẫn/paste, cách cố định, thời điểm gắn, vấn đề contact.
  Điền trường `cup_and_contact_notes` trong pilot (ở pilot 2026-10-05 trường này đang trống).
- Kiểm tra kỹ các cup có lịch sử contact kém: ở pilot trước, cặp drive **R1→L1** có gain fit ~0.45–0.48× ở
  50/80 kHz (ước lượng, chưa đo dòng).

## D. Thu dữ liệu (Windows, `cn0565_pilot.py`)

- Chế độ **live**, đúng tần số/amplitude đã chọn, protocol `perimeter208`, file mapping ở mục C.
- Bật video trước khi bắt đầu; người đo làm theo cue; ghi chú mọi sai lệch (ho, nuốt, cười lệch nhịp…).
- Kết thúc: pilot ghi một thư mục phiên. Ý nghĩa từng file:

| File | Một dòng/phần tử là gì |
|---|---|
| `meta.json` | Hồ sơ phiên: cài đặt, mapping, sequence 208 phép đo, mốc thời gian, trạng thái, QC tiếp xúc, timing |
| `plan.csv`, `schedule.csv` | Kế hoạch và thời gian **dự kiến** |
| `events.csv` | Nhật ký cue **thực tế** (`STATE_CUE`, `PHASE_START/END`, `SESSION_END`, …) |
| `frames.csv` | Một frame = 208 phép đo tuần tự (~20.6 s) |
| `patterns.csv` | **Dữ liệu chính**: một dòng = một phép đo 4 điện cực (`real_raw`, `imag_raw` = DFT count của điện áp S+−S−) |
| `configuration_checks.csv/.json` | Đọc lại cài đặt từ board trước/sau mỗi trial |
| `trial_windows.csv` | (sau khi xác nhận) khoảng thời gian bạn xác nhận đã làm đúng task |

Giải thích chi tiết từng cột và ý nghĩa vật lý: [báo cáo 2026-10-05, mục 1](../../docs/reports/2026-10-05-three-frequency-analysis.md#1-dữ-liệu-của-bạn-thực-chất-là-gì).

## E. Chuyển dữ liệu (không sửa dữ liệu thô)

1. Chép **nguyên** thư mục phiên vào `data/sessions/<session>/`. Không đổi tên file, không mở bằng
   Excel rồi lưu lại.
2. Nếu bạn đã làm đúng cue suốt mỗi phase, tạo `trial_windows.csv` bằng hàm của pilot
   (`cue_intervals(path, operator_confirmed=True)`, provenance `operator_reported_cue_following`).
   Nếu không chắc thì **đừng tạo**: nhãn sẽ được ghi là `cue_assumed`.
3. Ghi lại SHA-256 để biết sau này dữ liệu có bị thay đổi không:
   `.venv-sim/bin/python -m app hash data/sessions/<session>`. Lệnh `study` cũng tự lưu hash vào
   `manifest.json`.
4. Nếu sau khi xem video thấy một trial làm sai, sửa cột `valid` của trial đó thành `False` trong
   `trial_windows.csv` (đây là file chú thích, không phải dữ liệu đo). Pipeline sẽ bỏ các frame của trial đó
   khỏi mọi phân tích, báo số trial bị loại (`invalid_trials_excluded`) và ghi cảnh báo trong README.

## F. QC ngay sau khi đo: `app check`

```bash
.venv-sim/bin/python -m app check data/sessions/<session>
```

Lệnh in bảng tóm tắt, ghi `data/results/checks/<session>/` (timeline, bản đồ REST, gain từng cặp drive,
nhiễu REST→REST) và trả **exit code 1 nếu audit thất bại**.

| Mục | Đạt khi | Pilot 2026-10-05 |
|---|---|---|
| `audit_pass` | `True`: đủ frame × 208, không lỗi, sequence khớp meta, thời gian hợp lệ, cài đặt không đổi | True ×3 |
| `frames_inside_hold` | mọi frame nằm trọn trong cửa sổ cue | 7/7 ×3 |
| `rest_n_ge_50` (kênh mạnh) | không giảm mạnh so với phiên trước (dấu hiệu contact kém) | 73 / 82 / 73 |
| `recip_err_strong_median_pct` | càng thấp càng tốt; tăng vọt nghĩa là contact hoặc dòng không ổn định | 17.7 / 12.3 / 13.4 % |
| `drive_gain_fit_supported` | `True` = fit "một gain mỗi cặp drive" giảm reciprocity error nhiều hơn mức nó giảm được trên nhiễu thuần (`recip_fit_ratio` < `recip_fit_null_ratio_p05`). `False` thì đừng tin các gain fit | True / False / False |
| `drive_gain_min` + `_pair` | ~≥ 0.6 (heuristic), chỉ có nghĩa khi `drive_gain_fit_supported`; thấp hơn thì kiểm tra cup của cặp đó | 0.45–0.70, cặp R1-L1 hoặc R2-R1 |
| `settle_task_s_median` | cue → bắt đầu frame đầu tiên của mỗi khối task; ~2 s | 2.02 s ×3 |
| `rest_rest_rms_counts`, `rest_rest_inphase_rms_counts` | có giá trị (cần ≥ 2 frame REST liền nhau); so với ~1.2–2.9 count (RMS phức) đã đo trước | chưa đo (chỉ 1 REST) |
| `rest_across_task_pairs`, `rest_across_control_pairs` | cặp REST kẹp một task / chỉ kẹp REST_CONTROL: drift + phục hồi | 0 (chỉ 1 REST) |

Các ngưỡng "heuristic" ở trên rút ra từ một pilot, chưa phải tiêu chuẩn đã kiểm chứng. Ghi lại lý do
nếu chấp nhận một phiên có cảnh báo.

## G. Viết config cho study

Một **study** là một nhóm phiên được phân tích cùng nhau (ví dụ 3 tần số, hoặc 2 vòng cùng tần số).
Chép config mẫu [`data/studies/three-frequency-20261005.json`](../data/studies/three-frequency-20261005.json)
và sửa:

| Trường | Ý nghĩa | Ghi chú |
|---|---|---|
| `study_id` | tên thư mục output | duy nhất, có ngày |
| `sessions` | `[{"dir": …, "label": …}]` | nhãn ngắn, duy nhất (hiện trên hình) |
| `baseline` | cách chọn REST làm mốc | `initial_rest` (thiết kế 2026-10-05); `preceding_rest` hoặc `bracketing_rest` (REST trước và sau, cho thiết kế REST→TASK→REST). Pipeline cảnh báo nếu để `initial_rest` mà phiên có nhiều khối REST |
| `rest_reference_frames` | chỉ cho `preceding_rest`/`bracketing_rest`: dùng k frame REST gần task nhất (k frame cuối của khối REST trước, k frame đầu của khối sau) | `null` = cả khối. Ví dụ khối REST đầu phiên dài 3 frame (~62 s): với `null`, mốc của task đầu tiên là trung bình cả 3 frame (tâm cách task ~40 s), nên task đầu chịu drift nhiều hơn các task khác |
| `drop_first_task_frames` | bỏ bao nhiêu frame đầu mỗi khối task (frame chuyển tiếp) | 0 nếu mỗi task chỉ 1 frame |
| `tasks` | thứ tự task trên hình/bảng **và bộ lọc**: task đã đo mà không có trong danh sách sẽ bị bỏ khỏi mọi bảng/hình (có cảnh báo) | bỏ trống (`null`) = mọi task, theo thứ tự xuất hiện. Khi chép config mẫu cho phiên mới, nhớ thêm `TONGUE_CHEEK_*`, `REST_CONTROL` hoặc để `null` |
| `strong_counts` | ngưỡng kênh mạnh (count) | 50 (nhiễu ~2 count ≈ 4%) |
| `noise_counts` | độ lệch chuẩn nhiễu (count) của một hiệu hai frame, theo hướng phasor REST; dùng cho image/noise và known-target. Luôn lấy từ config, không tự thay | khi đã có REST→REST: dùng `rest_rest_inphase_rms_counts` trong `qc_summary.csv` (≈ `rest_rest_rms_counts`/√2), **không** dùng thẳng RMS phức |
| `reconstruction` | setting pyEIT (BP/JAC/GREIT), seed nhiễu, và khối known-target (`known_target`: tâm, bán kính, contrast, seed) | giống `eit_sim_playground.py`; đừng đổi giữa các study cần so sánh |
| `outputs` | bật/tắt hình báo cáo, slide, ảnh sạch | |

Pipeline xử lý thiết kế mới như sau:
- Mỗi **khối task** = các frame liên tiếp cùng trial và task. dz của khối = trung bình dz các frame
  (sau khi bỏ frame chuyển tiếp), so với REST theo `baseline`.
- Nhiều lần lặp của cùng task trong một phiên được lấy trung bình; mỗi lần lặp vẫn có trong
  `tables/changes_per_measurement.csv`. Khi study chỉ có một phiên, phép thử nhận dạng dùng
  **leave-one-repetition-out**.
- `REST_CONTROL` được phân tích như một task trong các bảng. dz của nó chính là **phân bố "không làm gì"** để
  so sánh. Các khối có chữ `CONTROL` **không** được đưa vào phép thử nhận dạng (chúng không phải một lớp cần
  nhận dạng).
- Hai frame REST **liền nhau** cho mức nhiễu (`rest_rest_pairs`). Hai REST **kẹp một task** cho drift +
  phục hồi (`rest_across_task_pairs`); hai REST chỉ kẹp REST_CONTROL được tách riêng (`rest_across_control_pairs`).
- README tự động báo số liệu chính của các task **không gồm** khối CONTROL, và in riêng giá trị của
  REST_CONTROL để so sánh: hãy so mỗi task với REST_CONTROL, không phải với 0.
- Cảnh báo thứ tự: với nhiều phiên, so thứ tự task giữa các phiên; với một phiên, so giữa các vòng
  (lần lặp). Thứ tự trùng hệt thì nhận dạng bị lẫn với vị trí trong chuỗi. `recognition.json` còn liệt kê
  các task ở cùng vị trí trong mọi vòng (`tasks_at_same_position_in_every_group`).

## H. Phân tích: `app study`

```bash
.venv-sim/bin/python -m app study data/studies/<study_id>.json
```

Output trong `data/results/<study_id>/`:

| Mục | Nội dung |
|---|---|
| `README.md` | Tóm tắt tự động: QC từng phiên, số liệu chính, **cảnh báo tự phát hiện** (1 REST, thứ tự trùng, thiếu trial_windows, voltage mode, fit gain không đáng tin, config lọc mất task, baseline không hợp thiết kế…) |
| `manifest.json` | git commit, số thay đổi chưa commit (tổng và riêng trong code: `uncommitted_code_changes`), phiên bản Python/thư viện, config đầy đủ, SHA-256 file thô, lệnh đã chạy (`python -m app …`) |
| `tables/qc_*.csv` | QC, timeline, gain từng cặp drive, nhiễu REST→REST (luôn có header, kể cả khi chưa có cặp REST nào) |
| `tables/changes_per_measurement.csv` | dz từng phép đo × task × lần lặp (Re, Im, \|dz\|, kênh mạnh, thời điểm trong frame) |
| `tables/task_features.csv`, `lateralization.csv`, `correlation_*.csv`, `additivity.csv`, `electrode_involvement.csv`, `recognition.json` | các đặc trưng |
| `tables/recon_*.csv`, `recon_images.npz` | chỉ số và ảnh BP/JAC/GREIT (exploratory) |
| `figures/` | hình báo cáo (tiếng Anh): 12 hình khi study có nhiều phiên, 10 khi chỉ có một phiên |
| `slides/` | cùng kết quả, kích thước slide 10 × 5.63 in |
| `clean/` | ảnh tái tạo không chữ để tự dàn trang (`clean/README.txt` ghi thứ tự hàng/cột) |

**Tính tái lập:** checkout đúng commit trong `manifest.json`, cài `backend/requirements.txt`, chạy lại
cùng lệnh thì ra cùng các bảng. Điều kiện: code đã được commit **trước** khi chạy. Nếu
`uncommitted_code_changes` > 0 thì commit đó không chứa đúng code đã tạo output; lệnh `study` in cảnh báo
trong trường hợp này. Mọi phép ngẫu nhiên (permutation test, nhiễu mô phỏng, known-target) đều có seed cố
định trong config; kiểm định null của fit gain dùng seed cố định trong `qc.py`.

## I. Diễn giải

- Đọc `README.md` của study trước: QC đạt chưa, cảnh báo nào được phát hiện.
- Cách đọc từng hình và giới hạn: [báo cáo 2026-10-05](../../docs/reports/2026-10-05-three-frequency-analysis.md)
  là ví dụ đầy đủ. Hai nguyên tắc chính:
  - ảnh tái tạo là **chiếu 2D**, chỉ kết luận những gì BP, JAC và GREIT cùng thấy;
  - electrode involvement là heuristic, không phải vị trí cơ.
- Nguồn nhiễu và cách nhận diện: [eit-noise-sources.md](../../docs/eit-noise-sources.md).
- Mô hình môi trường (mặt) và các công trình liên quan: [facial-environment-and-forward-models.md](../../docs/facial-environment-and-forward-models.md).
- Viết báo cáo mới trong `docs/reports/<ngày>-<tên>.md`, link hình từ `data/results/<study_id>/`.

## J. Lưu phiên bản

```bash
git add eit-measurement docs
git commit -m "Add <session> and study <study_id>"
```

- Commit **raw data + config + code + docs**. Output trong `data/results/` tái tạo được bằng lệnh H,
  nên commit hay không tùy bạn (repo này trước nay snapshot cả workspace).
- Sửa phương pháp trong `backend/app/eit/` thì phải chạy lại test. Nếu kết quả của study cũ thay đổi **có chủ
  đích**, cập nhật `tests/fixtures/…expected.json` và ghi lý do trong commit message.

---

## Còn thiếu để quy trình khép kín

- **Code thu dữ liệu chưa có trong repo**: `scripts/cn0565_pilot.py`, hướng dẫn GUI
  `docs/cn0565-pilot-gui-and-data-guide.md` và mapping `docs/protocols/user-p1-wiring-interleaved-208.json`
  đang nằm trên máy Windows. Chép chúng vào repo và commit, để bước D cũng được version hóa như phần
  phân tích. `meta.json` mỗi phiên đã ghi SHA-256 của driver pyadi-iio, nhưng chưa ghi phiên bản của
  chính pilot ngoài chuỗi `version`.
- Pilot có hỗ trợ thứ tự task tùy ý, REST_CONTROL và nhiều frame mỗi task không: cần kiểm tra trên
  Windows. Pipeline phân tích đã sẵn sàng cho các trường hợp này (có unit test với dữ liệu tổng hợp).

## Xử lý lỗi thường gặp

| Thông báo | Nguyên nhân | Cách xử lý |
|---|---|---|
| `only live recordings are analysed` | thư mục mock/thử nghiệm | dùng phiên live |
| `missing ['…']` | chép thiếu file | chép lại nguyên thư mục |
| `sessions use different measurement protocols` | khác `protocol_hash` | tách thành hai study |
| `session labels must be unique` | trùng `label` trong config | đặt nhãn khác nhau |
| `reference has zero or non-finite values` | REST có kênh = 0 | kiểm tra contact/raw; loại phiên |
| `subset formula does not reproduce pyEIT solve()` | phiên bản pyEIT khác | cài `backend/requirements.txt` |
