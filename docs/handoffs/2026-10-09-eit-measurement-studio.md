# Handoff 2026-10-09: EIT Measurement Studio (chuyển sang máy mới)

Viết cho phiên chat tiếp theo (người hoặc AI) để tiếp tục đúng chỗ. Đọc cùng `CLAUDE.md` (gốc repo),
`eit-measurement/AGENTS.md` và `eit-measurement/docs/architecture.md`.

## 1. Câu dán vào chat mới

> Đọc `CLAUDE.md`, `docs/handoffs/2026-10-09-eit-measurement-studio.md`, rồi `eit-measurement/docs/architecture.md`
> (mục 1, 3, 4). Kiểm tra môi trường bằng cách chạy 3 bộ test trong CLAUDE.md. Sau đó tiếp tục cùng tôi
> **từng bước**: [chọn một] (a) bước 2 của phần giải thích "frontend → phần cứng" (lệnh IIOD đi qua proxy và
> serial như thế nào), hoặc (b) bước 5 của kế hoạch: panel cấu hình đo trong app.

## 2. Đã làm (2026-10-05 → 2026-10-09)

1. **Phân tích pilot 3 tần số** (10/50/80 kHz, 2026-10-05): báo cáo `docs/reports/2026-10-05-three-frequency-analysis.md`;
   tài liệu `docs/eit-noise-sources.md`, `docs/facial-environment-and-forward-models.md` (đã kiểm chứng độc lập 2 lần).
2. **Package phân tích** `eitpilot` → nay là `eit-measurement/backend/app/eit/`, lệnh `python -m app
   {design,check,study,hash}`. Test hồi quy khớp số của báo cáo tới 1e-9.
3. **Mọi thứ biến động theo cấu hình**: số điện cực, khoảng cách bơm/đo (`eit/protocol.py`, trùng driver ADI và
   pyEIT cho 8/16/32), cấu hình đo `data/hardware/measurement-*.json`, sơ đồ nối dây 16 cup (chép nguyên văn từ
   meta.json pilot), study design `data/protocols/facial-rest-task-rest-v1.json`; HOLD tự tính từ thời lượng frame.
4. **Tổ chức repo**: toàn bộ ứng dụng trong `eit-measurement/` (AGENTS.md, frontend, backend, data, docs); tài
   liệu tham khảo → `reference/`, slide → `presentations/`, đồ cũ → `archive/`. Kiểm chứng độc lập: không mất
   file (đối chiếu hash với bản sao lưu và git), lệnh chạy được từ gốc repo lẫn từ `eit-measurement/`.
5. **AGENTS.md** (quy tắc dự án do người dùng đưa vào) đã chỉnh cho khớp dự án: trạng thái hiện tại, sự thật phần
   cứng đã kiểm chứng, 6 quy tắc đo của EIT (frame nối tiếp, HOLD được tính, REST là khối được đo ≠ RELEASE, …),
   định dạng lưu phiên = định dạng pilot, stack desktop, mục đóng gói §8.12.
6. **Khung app desktop** (bước 4): `eit-measurement/frontend/` (PySide6 6.10.3): header (trạng thái thiết bị,
   đồng hồ), đúng 3 tab, trang Measurement 2 cột (cột cấu hình chỉ đọc gọi `services/configuration.py`; vùng
   hướng dẫn lớn ở trạng thái trống, không có đồng hồ giả). `backend/app/core/config.py`: thư mục dữ liệu
   (`EIT_DATA_ROOT`).

Kiểm tra lần cuối: 43 test backend + 5 test frontend + 8 test script đạt; 106 link tài liệu hợp lệ.

## 3. Quyết định đã chốt (và lý do)

| Quyết định | Lý do |
|---|---|
| **App desktop Python + PySide6**, không web/API (2026-10-09) | Một ngôn ngữ, ít tầng, gọi thẳng code đã có → người dùng hiểu và kiểm soát được. PySide6 (LGPL) cho phép phát hành bộ cài; không dùng PyQt (GPL) |
| Sau này **đóng gói 1 file cài đặt** (PyInstaller + Inno Setup, Windows) | Người dùng muốn gửi app cho người khác cài. Quy tắc từ bây giờ: logic chỉ ở backend; mọi đường dẫn dữ liệu qua `core/config.py`; proxy chạy trong app; thử đóng gói sớm (bước 6) vì DLL libiio dễ hỏng |
| Giao tiếp: giao diện **gọi hàm** backend; backend báo lên bằng **Qt signal** từ luồng chạy nền | Một frame 16 điện cực mất 20.6 s, không được làm đơ cửa sổ |
| Study design gọn → `protocol_runner.expand()` sinh lịch chi tiết | Người dùng soạn task/thời lượng/vòng/seed; lịch từng khối được lưu kèm phiên |
| Định dạng phiên giữ theo pilot (meta.json, patterns.csv, …) | Phiên cũ và mới phân tích chung bằng `app check/study` |
| Không dùng `adi.cn0565.all_voltages` cho phiên đo | Nó nhớ danh sách phép đo từ lần đầu, không dừng được giữa frame, và dùng đường Y1/Y2 khác với pilot (Y6/Y7, `driver_index = (X+12) % 24`) |
| Bộ công cụ Windows (`scripts/`, `examples/`, …) giữ ở gốc repo | Script PowerShell trên máy Windows gọi nhau bằng đường dẫn cố định |

## 4. Phần giải thích cho người dùng (đang đi từng bước)

Người dùng muốn hiểu toàn bộ chuỗi giao diện → backend → pyadi-iio → libiio → firmware → chip.
- **Bước 1 đã giải thích:** `adi.cn0565(uri)`; property setter = lệnh ghi (`intf.excitation_frequency = 50000` →
  `WRITE iio:device0 excitation_frequency 5` + `50000`); `electrode_count` chỉ là biến Python; một phép đo =
  reset switch (`gpio1_toggle`) → 4 lệnh `direct_reg_access` (ví dụ `0x71 0x8001` = đóng X0–Y0 của chip 0x71) →
  `READ iio:device0 INPUT voltage0 raw`; 5 ghi + 3 đọc mỗi phép đo → ~0.099 s → 20.6 s/frame. Đã chứng minh bằng
  cách chạy code pyadi-iio thật với một module `iio` giả (script nằm trong thư mục tạm của máy cũ, **không có trong
  repo**; viết lại nhanh được nếu cần: module `iio` giả có `Context`, device `ad5940`/`adg2128`, ghi log mỗi lần
  đọc/ghi `attrs[...].value`).
- **Bước 2 chưa làm:** dòng lệnh IIOD đi qua TCP → `scripts/iiod_serial_proxy.py` (`serve_client`, chờ `delay_ms`
  trước payload WRITE vì firmware có thể làm mất payload) → serial 230400 → TinyIIOD trả lời (độ dài + giá trị cho
  READ, mã kết quả cho WRITE); xem `scripts/raw_iiod_attr_test.py`.
- Sau đó: firmware → AD5940 (SPI) / ADG2128 (I²C), và đường dữ liệu đi ngược lên `patterns.csv`.

## 5. Việc còn mở

1. **`cn0565_pilot.py`** (phần mềm đo pilot), hướng dẫn GUI và file mapping vẫn ở máy Windows → cần chép vào repo
   trước bước 11 (board thật).
2. Firmware đang nạp trên board chưa được ghi nhận (`firmware_id = unknown`); quy tắc chỉ số driver và đường Y6/Y7
   mới suy ra từ netlist, cần thử trên known load (`eit-measurement/docs/hardware-mapping.md` §7).
3. Xác nhận cue-following (`trial_windows.csv`) cho phiên 2 và 3 nếu người dùng chắc chắn đã làm đúng cue.
4. Kế hoạch tiếp theo: bước 5 panel cấu hình → 6 thử đóng gói trên Windows → 7 trình soạn study design → 8 board
   giả + Connect → 9 chạy phiên + màn hình hướng dẫn → 10 lưu phiên → 11 board thật → 12 Results/Sessions →
   13 bộ cài → 14 đo trên người.
5. Ghi nhớ của AI trên máy cũ (thư mục memory của Claude Code) không đi theo repo; các sở thích quan trọng đã chép
   vào `CLAUDE.md`.
