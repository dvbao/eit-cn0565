# Chạy ví dụ CN0565 chính thức

## Chuẩn bị một lần

Tải bộ mã ví dụ chính thức từ nhánh `main` của `analogdevicesinc/pyadi-iio`:

```powershell
cd C:\path\to\eit-cn0565
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_official_examples.ps1
```

Mã upstream được lưu tại `examples/cn0565/`. Script wrapper không sửa file upstream trên đĩa; nó thay URI COM trong bộ nhớ lúc chạy.

## Mỗi phiên làm việc

```powershell
cd C:\path\to\eit-cn0565
.\cn0565-env\Scripts\Activate.ps1
python scripts\list_serial_ports.py
python scripts\check_connection.py --port COM7 --baud 230400
```

Chỉ tiếp tục khi thấy cả `ad5940` và `adg2128`.

## 1. Đo thử một cấu hình điện cực

Với calibration/impedance test board đã gắn đúng:

```powershell
python scripts\run_official_example.py single --port COM7 --pair 0 3 1 2
```

Thứ tự bốn số là `F+ F- S+ S-`. Kết quả gồm impedance dạng phức, magnitude, phase, real và imaginary.

## 2. Quét các cặp điện cực

```powershell
python scripts\run_official_example.py sweep --port COM7
```

Khi được hỏi có tạo CSV không, nhập `Y`. File `cn0565_example_data.csv` được tạo trong `data/raw/`.

## Cảnh báo: lỗi drop-payload của firmware ADuCM3029

Firmware IIOD trên ADuCM3029 có thể đánh rơi payload của một lệnh WRITE nếu nó
đến ngay sau command header. Mỗi lần đổi cấu hình điện cực gửi nhiều lệnh WRITE
liên tiếp (đóng 4 điểm crosspoint), nên nếu 1 lệnh bị rơi, điện cực thực sự
được đo không phải điện cực bạn chọn — biểu hiện ra ngoài là kết quả/pass-fail
đổi ngẫu nhiên giữa các lần chạy dù phần cứng không đổi.

Thêm `--proxy` vào `run_official_example.py` (mọi mode) để chèn `scripts\iiod_serial_proxy.py`
ở giữa — proxy thêm một khoảng trễ nhỏ trước khi gửi payload, né lỗi này:

```powershell
python scripts\run_official_example.py single --port COM7 --pair 0 3 1 2 --proxy
```

`scripts\startup_check.ps1` dùng proxy theo mặc định cho bước đo thử.

## 3. Kiểm tra sản xuất (pass/fail theo board hiệu chuẩn ADI)

```powershell
python scripts\run_official_example.py prodtest --port COM7 --proxy
```

Script này (`cn0565_prod_tst.py`) so khớp trở kháng đo được với các ngưỡng
hard-code theo đúng linh kiện R/C trên **board hiệu chuẩn gốc của ADI** đi kèm
CN0565. Nếu đang test bằng board tự thiết kế khác, các ngưỡng pass/fail này
không áp dụng được — chỉ dùng script này với board hiệu chuẩn gốc.

## 4. Chạy GUI EIT thời gian thực

```powershell
python scripts\run_official_example.py gui --port COM7 --electrodes 16
```

Trong GUI:

1. Chọn `COM7: USB Serial Device`.
2. Chọn 16 electrodes.
3. Chọn reconstruction `BP`, `JAC` hoặc `GREIT`.
4. Chọn dữ liệu `Real`, `Imaginary` hoặc `Magnitude`.
5. Nhấn **Connect**.
6. Đợi ảnh ổn định rồi dùng **Baseline** theo quy trình thí nghiệm.
7. Nhấn **Disconnect** trước khi đóng GUI hoặc chạy script khác.

Chỉ một chương trình được giữ COM7 tại một thời điểm.

## Bắt đầu lại từ đầu trên máy đã cài sẵn

```powershell
cd C:\path\to\eit-cn0565
.\cn0565-env\Scripts\Activate.ps1
python scripts\list_serial_ports.py
python scripts\check_connection.py --port COM7 --baud 230400
python scripts\run_official_example.py single --port COM7 --pair 0 3 1 2
```

Không cần chạy lại bootstrap, cài package hay nạp firmware nếu bước kiểm tra IIO vẫn nhận `ad5940` và `adg2128`.
