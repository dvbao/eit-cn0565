# EIT Measurement Studio: bức tranh tổng quát, pipeline và tiến độ

File này là **bản đồ chính** của ứng dụng. Mỗi bước xây xong thì cập nhật mục 4 (tiến độ) và mục 6 (nhật ký).

- Cài đặt, lệnh và "sửa gì ở đâu": [README.md](../README.md)
- Quy tắc dự án: [AGENTS.md](../AGENTS.md) · Phần cứng đã kiểm chứng: [hardware-mapping.md](hardware-mapping.md)
- Quy trình đo/phân tích hiện tại (với phần mềm pilot trên Windows): [pipeline.md](pipeline.md)
- Tài liệu nền (nhiễu, forward model, báo cáo pilot): [docs/README.md](../../docs/README.md) (gốc repo)

## 1. Bức tranh tổng quát: một app desktop Python, 4 tầng + 1 nguồn cấu hình

Quyết định 2026-10-09: **app desktop Python (PySide6)**, sau này đóng gói thành **một file cài đặt** cho người
khác dùng. Không có trình duyệt, không có web server, không có API: giao diện gọi thẳng hàm Python của backend, và
backend báo ngược lên giao diện bằng **signal** của Qt.

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│ data/  (một nguồn cấu hình; thư mục do backend/app/core/config.py quyết định)      │
│  hardware/   số điện cực, khoảng cách bơm/đo, tần số, amplitude, nối dây           │
│  protocols/  study design: task, câu hướng dẫn, GET READY / RELEASE, vòng, seed    │
└────────────────────────────────────────────────────────────────────────────────────┘
                                          │
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 1. GIAO DIỆN   frontend/   Python + PySide6 (một chương trình với backend)         │
│    main_window.py: header (trạng thái thiết bị, đồng hồ) + 3 tab              ✓    │
│    Measurement: cột cấu hình (chỉ đọc) ✓ · màn hình hướng dẫn lớn (trống) ✓        │
│    Results, Sessions: trạng thái trống ✓ · nội dung ○                              │
└────────────────────────────────────────────────────────────────────────────────────┘
        │ gọi hàm Python trực tiếp                ▲ Qt signal (từ luồng chạy nền)
┌────────────────────────────────────────────────────────────────────────────────────┐
│ 2. BACKEND   backend/app/                                                          │
│    services/   configuration ✓ · protocol_runner: lập lịch ✓, chạy cue ○           │
│                acquisition ○ (đo, timestamp) · session_manager ○ (lưu phiên)       │
│    schemas/    cấu hình đo, nối dây, study design                         ✓        │
│    core/       thư mục dữ liệu (EIT_DATA_ROOT)                             ✓       │
│    eit/        PHÂN TÍCH: QC, dz, đặc trưng, ảnh, báo cáo                 ✓        │
└────────────────────────────────────────────────────────────────────────────────────┘
        │ gọi xuống phần cứng                          │ đọc/ghi
┌──────────────────────────────────────────┐  ┌──────────────────────────────────────┐
│ 3. PHẦN CỨNG  backend/app/hardware/  ○   │  │ 4. DỮ LIỆU  data/sessions/  ✓        │
│    cn0565.py (thật), mock.py (demo)      │  │    data/results/  ✓                  │
│    + proxy serial chạy trong app         │  │                                      │
└──────────────────────────────────────────┘  └──────────────────────────────────────┘
        │ pyadi-iio → libiio → proxy (chờ trước mỗi lệnh ghi: pilot 10 ms)
        ▼ → COMx (pilot: COM7), 230400 baud → firmware ADICUP3029
          → AD5940 (SPI) + 2 × ADG2128 (I²C) → 16 cup trên mặt
```

`✓` đã có và có test · `○` sẽ xây cùng nhau theo mục 4. Mọi thời gian trong tài liệu (0.099 s mỗi phép đo,
20.6 s mỗi frame) đo với proxy chờ 10 ms; script proxy mặc định 100 ms, nên khi app tự chạy proxy sẽ đặt 10 ms
hoặc đo lại thời gian mỗi phép đo.

Chiều gọi nhau (AGENTS.md §8.7): giao diện → services → hardware và eit. `eit/` và `backend/` không bao giờ import
giao diện; giao diện không bao giờ chạm vào pyadi-iio hay cổng COM.

## 2. Pipeline: một phiên đo đi từ đầu đến cuối

| # | Bước | Người dùng làm / thấy gì | Code chịu trách nhiệm | Trạng thái |
|---|---|---|---|---|
| 1 | Cấu hình phần cứng | Chọn số điện cực, tần số, amplitude, sơ đồ nối dây; thấy ngay **số phép đo/frame và thời lượng 1 frame** | `data/hardware/*.json`, `schemas/models.py`, `services/configuration.py` | ✓ hiển thị (chỉ đọc) trong app + lệnh `app design`; sửa trong app ○ |
| 2 | Soạn study design | Nhập task, câu hướng dẫn, thời lượng GET READY / RELEASE, số vòng, seed; HOLD **tự tính** từ bước 1 | `data/protocols/*.json`, `schemas/models.py` | ✓ file + tóm tắt trong app; trình soạn ○ |
| 3 | Kiểm tra + xem lịch phiên | Số khối, HOLD, tổng thời gian; báo lỗi nếu không khả thi | `services/protocol_runner.py` (`expand`, `validate`, `schedule_summary`) | ✓ |
| 4 | Kết nối board | Connect; đọc lại tần số/amplitude/chế độ đo từ board; kiểm tra contact | `hardware/cn0565.py` + device service | ○ (cần `cn0565_pilot.py`) |
| 5 | Chạy phiên | Màn hình hướng dẫn lớn: GET READY → **HOLD (đo ở đây)** → RELEASE, đếm ngược, Stop | `services/protocol_runner.py` (phần chạy, luồng nền), `services/acquisition.py`, `frontend/` | ○ |
| 6 | Lưu phiên | Thư mục `data/sessions/<phiên>/` (meta.json, patterns.csv, frames.csv, events.csv, …) | `services/session_manager.py` | ○ (định dạng đã cố định theo pilot) |
| 7 | QC ngay sau đo | Đạt/không đạt, timeline, bản đồ REST | `eit/qc.py`, lệnh `app check` | ✓ |
| 8 | Phân tích | Bảng, hình, ảnh BP/JAC/GREIT, README tự động | `eit/`, lệnh `app study` → `data/results/` | ✓ |
| 9 | Xem lại | Results + Sessions trong app | `frontend/features/results`, `sessions` | ○ (đang là trạng thái trống) |

Khi chưa có các phần ○, các bước này làm thủ công theo [pipeline.md](pipeline.md): 1–3 ↔ A, 4 ↔ B, 5 ↔ C–D,
6 ↔ E, 7 ↔ F, 8 ↔ G–H, 9 ↔ I.

**Hai quy tắc của EIT xuyên suốt pipeline:**
- Một frame là các phép đo **nối tiếp**: n × (n − 3) phép đo khi bơm và đo kề nhau (16 điện cực → 208 phép đo
  ≈ 20.6 s; 8 điện cực → 40 ≈ 4 s; khoảng cách khác thì ít hơn, ví dụ 16 điện cực bơm cách 2 → 192). Vì vậy
  HOLD = settle + số frame × thời lượng frame + margin, và đổi số điện cực là đổi toàn bộ thời gian phiên.
- REST là **khối được đo** (mốc so sánh), khác với RELEASE (nghỉ chuyển tiếp, không đo).

## 3. Giao tiếp giữa các tầng: qua hàm nào

`✓` code có thật · `○` thiết kế dự kiến, tên chốt khi xây bước tương ứng.

| Giữa | Cách | Ví dụ (hàm thật hoặc dự kiến) |
|---|---|---|
| Giao diện → backend | gọi hàm Python trực tiếp | `configuration.describe_measurement(path)` ✓, `configuration.describe_design(design, measurement)` ✓; sau này `DeviceService.connect(uri)` ○, `SessionService.start(config, design)` ○ |
| Backend → giao diện | **Qt signal** phát từ luồng chạy nền, Qt chuyển sang luồng giao diện | `device_status("connected")` ○, `stage_changed(task, stage, start, duration)` ○, `measurement_progress(37, 208)` ○, `error(...)` ○ |
| Services → phần cứng | gọi phương thức Python | `device.measure(f_plus, f_minus, s_plus, s_minus)` → số phức + thời điểm ○ |
| Phần cứng → pyadi-iio → libiio | Python → thư viện C | `adi.cn0565(uri)`, `intf.excitation_frequency = f`, `intf._xline[x][y] = True`, `intf.channel["voltage0"].raw` ✓ |
| libiio → firmware | lệnh chữ IIOD qua proxy → serial | `WRITE iio:device0 excitation_frequency 5` + `50000`; `READ iio:device0 INPUT voltage0 raw` ✓ |
| Firmware → chip | SPI (AD5940), I²C (ADG2128), qua bộ cách ly | thanh ghi chip ✓ |
| Backend → phân tích | gọi hàm Python | `eit.report.check_session`, `run_study` ✓ |

Vì sao cần luồng chạy nền: một frame 16 điện cực mất 20.6 s. Nếu đo ngay trong luồng giao diện, cửa sổ sẽ "đơ"
suốt thời gian đó. Vì vậy phần đo chạy ở luồng riêng và báo tiến độ lên giao diện bằng signal.

## 4. Kế hoạch xây cùng nhau, từng bước

Mỗi bước nhỏ, có thứ để **nhìn thấy** và để **kiểm tra**, xong mới sang bước sau.

| # | Bước | Bạn sẽ thấy | Kiểm tra | Trạng thái |
|---|---|---|---|---|
| 0 | Phân tích pilot, pipeline tái lập được | bảng, hình, báo cáo 3 tần số | test hồi quy khớp số cũ tới 1e-9 | xong |
| 1 | Tìm hiểu driver, firmware, transport, định dạng dữ liệu | `docs/hardware-mapping.md` | đối chiếu mã driver + 3 phiên pilot | xong |
| 2 | Cấu hình đo + study design biến động theo số điện cực | lệnh `app design` in lịch phiên | chuỗi đo (phần toán) cho 8/16/32 điện cực trùng driver ADI và pyEIT; board tối đa 24, cáp hiện tại 16 | xong |
| 3 | Tổ chức repo: mọi thứ của ứng dụng trong `eit-measurement/` | cây thư mục ở README | 41 test backend + 8 test `scripts/test_cn0565_capture.py` đạt; kiểm chứng độc lập: không mất file, link hợp lệ | xong (2026-10-08) |
| 4 | **Khung frontend (PySide6)**: header (tên, "Disconnected", đồng hồ), 3 tab, trang Measurement 2 cột: cột cấu hình chỉ đọc (gọi backend) + màn hình hướng dẫn lớn ở trạng thái trống | `python -m frontend` mở cửa sổ | 5 test giao diện (offscreen) + 2 test service cấu hình | xong (2026-10-09) |
| 5 | **Panel cấu hình đo**: chọn file, sửa số điện cực/tần số/amplitude; backend kiểm tra; số phép đo/frame và thời lượng frame đổi ngay | sửa và thấy kết quả ngay trong app | test validate + test giao diện | tiếp theo |
| 6 | **Thử đóng gói sớm** (Windows): PyInstaller với app khung + liệt kê cổng COM + mở context IIO | một file `.exe` chạy trên máy khác | chạy trên máy Windows sạch | chưa làm |
| 7 | **Trình soạn study design + xem lịch phiên** | sửa task/thời lượng, thấy HOLD và tổng thời gian | test expand/validate | chưa làm |
| 8 | **Board giả + Connect/Disconnect**: device service, signal trạng thái | nút Connect hoạt động với board giả (nhãn DEMO) | test máy trạng thái thiết bị | chưa làm |
| 9 | **Chạy phiên** (luồng nền + signal): GET READY → HOLD → RELEASE, màn hình hướng dẫn lớn, pop-up, Stop | chạy một phiên demo trọn vẹn | test máy trạng thái, Stop, signal | chưa làm |
| 10 | **Lưu phiên đúng định dạng** | phiên demo lưu riêng, đúng định dạng pilot | `app check` đọc được (thêm tùy chọn cho phiên demo) | chưa làm |
| 11 | **Board thật**: `CN0565Device` + proxy chạy trong app; đọc lại cài đặt; đo thử 1 frame | 208 (hoặc 40) số phức thật | trên máy Windows, với board test/known load trước | chưa làm (cần `cn0565_pilot.py`) |
| 12 | **Results + Sessions** | QC và ảnh của phiên ngay trong app | so với `app study` | chưa làm |
| 13 | **Bộ cài 1 file** (Inno Setup), thư mục dữ liệu người dùng | `EIT-Measurement-Studio-Setup.exe` | cài trên máy khác, chạy demo | chưa làm |
| 14 | Đo trên người theo study design | phiên thật | QC + phân tích | chưa làm |

## 5. Quyết định thiết kế đã chốt (và bước thực hiện)

1. **App desktop Python (PySide6)**, không web, không API (2026-10-09). PySide6 vì giấy phép LGPL cho phép phát
   hành bộ cài. Logic nằm hết trong `backend/`, nên sau này vẫn có thể thêm giao diện web mà không đổi backend.
2. **Study design gọn, lịch chi tiết được sinh ra.** Hàm `expand()` trong `services/protocol_runner.py` mở rộng
   study design thành lịch từng khối với các stage (dạng AGENTS.md §8.5); bản lịch được lưu kèm mỗi phiên. Trường
   pop-up (`displaySeconds`, `leadInSeconds`) thêm ở bước 7.
3. **Định dạng phiên** giữ theo pilot (meta.json, patterns.csv…) để phiên cũ và mới phân tích chung được.
4. **Thư mục dữ liệu** do `backend/app/core/config.py` quyết định (`EIT_DATA_ROOT`); app đã cài sẽ dùng thư mục
   của người dùng.
5. **Bộ công cụ Windows** (`scripts/`, `examples/`, `bootstrap-cn0565-env.ps1`) còn ở gốc repo; dữ liệu thô của nó
   ghi vào `data/bench/`. Ở bước 11, proxy và kiểm tra kết nối chuyển vào `backend/app/hardware/`.

## 6. Nhật ký thay đổi

| Ngày | Thay đổi |
|---|---|
| 2026-10-05 | Phân tích 3 phiên pilot 10/50/80 kHz; package phân tích `eitpilot` |
| 2026-10-06 | Sửa theo kiểm chứng độc lập; kiểm định null cho fit gain; tài liệu nhiễu và forward model |
| 2026-10-08 | Số điện cực, khoảng cách bơm/đo biến động; cấu hình đo + study design dạng file; lệnh `design` kiểm tra khả thi |
| 2026-10-08 | Tổ chức theo AGENTS.md; gom ứng dụng vào `eit-measurement/` (`eitpilot` → `backend/app/eit`); AGENTS.md chỉnh cho khớp dự án |
| 2026-10-09 | Sửa theo kiểm chứng độc lập lần 2: `app design` kiểm tra cấu hình đo + nối dây; `--out` luôn tính từ `eit-measurement/`; `magnitude_mode` phải tắt; manifest ghi đúng phiên bản pyEIT; dữ liệu bộ công cụ Windows → `data/bench/` |
| 2026-10-09 | Chọn app desktop PySide6 (sau này đóng gói bộ cài); AGENTS.md đổi stack, giao tiếp (gọi hàm + Qt signal), cây thư mục, thêm mục đóng gói; **bước 4 xong**: khung frontend `python -m frontend`, `core/config.py` (thư mục dữ liệu), `services/configuration.py` |
| 2026-10-09 | `CLAUDE.md` (gốc repo) + `docs/handoffs/2026-10-09-eit-measurement-studio.md` để tiếp tục trên máy khác; commit + push lên `main` |
