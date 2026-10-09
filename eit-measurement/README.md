# EIT Measurement Studio

Phần mềm chạy và xem lại thí nghiệm EIT trên mặt với board CN0565: cấu hình phần cứng, thiết kế phiên đo, hướng
dẫn người tham gia từng bước, ghi phép đo và phân tích. Đây là **app desktop Python (PySide6)**; sau này được đóng
gói thành một file cài đặt cho người khác dùng (AGENTS.md §8.12).

- Bức tranh tổng quát, pipeline và tiến độ: [docs/architecture.md](docs/architecture.md)
- Quy trình đo và phân tích từng bước: [docs/pipeline.md](docs/pipeline.md)
- Sự thật đã kiểm chứng về phần cứng (transport, thuộc tính, nối dây, thời gian): [docs/hardware-mapping.md](docs/hardware-mapping.md)
- Quy tắc dự án cho người và AI: [AGENTS.md](AGENTS.md)
- Tài liệu nền (nhiễu, forward model, báo cáo pilot): [../docs/README.md](../docs/README.md) (gốc repo)

## Bản đồ thư mục

`✓` đã có và có test · `○` sẽ xây từng bước (xem docs/architecture.md §4)

```
eit-measurement/
├── AGENTS.md                      ✓ quy tắc dự án
├── README.md                      ✓ file này
├── requirements.txt               ✓ mọi package app cần (backend + PySide6)
├── frontend/                      ✓ GIAO DIỆN desktop PySide6 (khung): chạy bằng python -m frontend
│   ├── main_window.py             ✓ header (trạng thái thiết bị, đồng hồ) + 3 tab Measurement / Results / Sessions
│   ├── theme.py                   ✓ màu, chữ, khoảng cách (một nguồn duy nhất)
│   ├── features/measurement/      ✓ cột cấu hình (chỉ đọc) + màn hình hướng dẫn lớn (trạng thái trống)
│   ├── features/results/, sessions/ ✓ trạng thái trống; nội dung ○
│   └── tests/                     ✓ 5 test (chạy không cần màn hình)
├── backend/
│   ├── requirements.txt           ✓ các package phân tích, ghim phiên bản
│   ├── app/
│   │   ├── __main__.py            ✓ lệnh: python -m app {design, check, study, hash}
│   │   ├── core/config.py         ✓ thư mục dữ liệu (EIT_DATA_ROOT, mặc định data/)
│   │   ├── schemas/models.py      ✓ cấu hình đo, nối dây, study design (hợp đồng dữ liệu)
│   │   ├── services/
│   │   │   ├── configuration.py   ✓ liệt kê và mô tả cấu hình/study design cho giao diện
│   │   │   ├── protocol_runner.py ✓ study design -> lịch phiên; ○ chạy cue trực tiếp
│   │   │   ├── acquisition.py     ○ chạy từng phép đo, ghi thời điểm từng phép đo
│   │   │   └── session_manager.py ○ ghi phiên vào data/sessions/ đúng định dạng phân tích
│   │   ├── hardware/              ○ adapter CN0565 (pyadi-iio / libiio / proxy chạy trong app) + adapter demo
│   │   └── eit/                   ✓ phân tích: chuỗi đo, QC, dz, đặc trưng, BP/JAC/GREIT, báo cáo
│   └── tests/                     ✓ 43 test (unit, cấu hình, service, pipeline tổng hợp, hồi quy)
├── data/
│   ├── hardware/                  ✓ sơ đồ nối dây (16 cup) + cấu hình đo (16 điện cực, 50 kHz)
│   ├── protocols/                 ✓ study design facial-rest-task-rest-v1 (8 task, 2 vòng, REST_CONTROL)
│   ├── studies/                   ✓ cấu hình phân tích
│   ├── sessions/                  ✓ dữ liệu đo thô (3 phiên pilot 2026-10-05), không bao giờ sửa
│   ├── results/                   ✓ kết quả phân tích, tạo lại bằng `python -m app study`
│   └── bench/                     ○ dữ liệu thô của các script Windows (bench, ví dụ ADI), tạo khi dùng lần đầu
├── packaging/                     ○ PyInstaller + Inno Setup (bộ cài 1 file)
└── docs/                          ✓ architecture.md, pipeline.md, hardware-mapping.md
```

## Cài đặt (một lần, macOS)

Từ gốc repo (`eit-cn0565/`):

```bash
python3 -m venv .venv-sim
.venv-sim/bin/python -m pip install -r eit-measurement/requirements.txt
# cho môi trường biết hai package (backend và frontend) nằm ở đâu, để chạy được từ mọi thư mục:
printf "%s\n%s\n" "$PWD/eit-measurement/backend" "$PWD/eit-measurement" \
  > "$(.venv-sim/bin/python -c 'import site; print(site.getsitepackages()[0])')/eit_studio_backend.pth"
.venv-sim/bin/python -m unittest discover -s eit-measurement/backend/tests -p "test_*.py"    # phải OK
.venv-sim/bin/python -m unittest discover -s eit-measurement/frontend/tests -p "test_*.py"   # phải OK
```

## Lệnh

Chạy từ gốc repo. Đường dẫn `data/...` (cả đầu vào lẫn `--out`) được hiểu là nằm trong `eit-measurement/`; chạy
từ trong `eit-measurement/` với `../.venv-sim/bin/python` cũng được.

| Lệnh | Làm gì |
|---|---|
| `.venv-sim/bin/python -m frontend` | **Mở app** (cửa sổ EIT Measurement Studio) |
| `.venv-sim/bin/python -m app design --design data/protocols/<design>.json --measurement data/hardware/<settings>.json` | Lịch phiên từ study design và cấu hình đo. Lệnh kiểm tra cấu hình đo + file nối dây, và từ chối thiết kế không khả thi: HOLD ngắn hơn settle + số frame × thời lượng frame + margin (23.1 s với 16 điện cực), hoặc HOLD của task dài hơn 30 s |
| `.venv-sim/bin/python -m app check data/sessions/<session>` | QC một phiên đã đo (exit code 1 nếu audit không đạt) |
| `.venv-sim/bin/python -m app study data/studies/<study>.json` | Phân tích đầy đủ một nhóm phiên → `data/results/<study>/` |
| `.venv-sim/bin/python -m app hash data/sessions/<session>` | SHA-256 của các file thô (provenance) |

## Muốn sửa gì thì sửa ở đâu

| Tôi muốn đổi… | Sửa file |
|---|---|
| Số điện cực, khoảng cách bơm/đo, tần số, amplitude | `data/hardware/measurement-*.json` (đổi số điện cực thì cần file nối dây tương ứng trong trường `wiring`) |
| Cup nào nối dây nào, tên vị trí | `data/hardware/<wiring>.json` |
| Task, câu hướng dẫn, thời lượng GET READY / HOLD / RELEASE, số vòng, seed | `data/protocols/<design>.json` |
| Phiên nào phân tích chung, baseline, ngưỡng | `data/studies/<study>.json` |
| Cách tính chuỗi phép đo | `backend/app/eit/protocol.py` |
| Phân tích, QC, hình | `backend/app/eit/` |
| Quy tắc kiểm tra cấu hình / study design | `backend/app/schemas/models.py`, `backend/app/services/protocol_runner.py` |
| Giao diện: header, tab | `frontend/main_window.py` |
| Giao diện: màu, cỡ chữ | `frontend/theme.py` |
| Giao diện: trang Measurement | `frontend/features/measurement/measurement_page.py` |
| Thư mục dữ liệu | `backend/app/core/config.py` (hoặc biến môi trường `EIT_DATA_ROOT`) |
| Kết nối phần cứng, phiên đo trực tiếp | `backend/app/{hardware,services}` + `frontend/features/...` (chưa xây) |
