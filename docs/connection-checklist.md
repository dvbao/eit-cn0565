# Quy trình kết nối CN0565 + ADICUP3029 trên Windows

## Ba lớp kết nối cần phân biệt

1. **DAPLINK drive**: xác nhận PC thấy mạch nạp/debug; dùng để nạp file `.hex`.
2. **COM port**: xác nhận đường UART qua DAPLink, ví dụ `COM7`.
3. **IIO context**: xác nhận firmware đang chạy và libIIO thấy `ad5940` cùng `adg2128`. Đây mới là trạng thái sẵn sàng đo EIT.

## Thiết lập một lần

- Python 3.11 và môi trường `cn0565-env` đã được cài.
- libIIO native và các Python package đã được cài.
- Firmware CN0565 IIOD đã được nạp vào ADICUP3029.

Không cần nạp lại firmware sau mỗi lần khởi động Windows. Chỉ nạp lại khi firmware bị thay đổi, bị ghi đè hoặc kiểm tra UART cho thấy firmware không khởi động.

## Mỗi lần kết nối hoặc sau khi khởi động lại Windows

1. Rút USB trước khi lắp hoặc tháo shield.
2. Stack CN0565 thẳng hàng, chắc chắn trên các Arduino headers của ADICUP3029.
3. Đặt `S2 = USB` và `S5 = WALL/USB`.
4. Giữ jumper P7 trên CN0565 ở cấu hình mặc định, pins 1–2 được nối.
5. Cắm micro-USB vào P10 của ADICUP3029.
6. Xác nhận:
   - ổ `DAPLINK` xuất hiện;
   - DS2 trên CN0565 sáng xanh ổn định;
   - không có chương trình khác đang giữ COM port.
7. Mở PowerShell và chạy:

   ```powershell
   cd C:\path\to\eit-cn0565
   .\cn0565-env\Scripts\Activate.ps1
   python scripts\list_serial_ports.py
   ```

8. Dùng COM port của thiết bị `USB VID:PID=0D28:0204`. Hiện tại máy này gán `COM7`.
9. Kiểm tra IIO:

   ```powershell
   python scripts\check_connection.py --port COM7 --baud 230400
   ```

Kết nối đạt yêu cầu khi thấy:

```text
OK: IIO context is open (serial).
Devices:
  - ad5940 (id: iio:device0)
  - adg2128 (id: iio:device1)
```

## Lệnh dùng nhanh

Một lệnh duy nhất chạy cả 3 bước (liệt kê cổng, kiểm tra IIO context, đo thử 1 cặp điện cực qua proxy) và dừng ngay tại bước lỗi với hướng dẫn tiếp theo:

```powershell
cd C:\path\to\eit-cn0565
.\scripts\startup_check.ps1 -Port COM7
```

Không cần kích hoạt `cn0565-env` trước — script gọi thẳng `cn0565-env\Scripts\python.exe`. Nếu muốn đo thử không qua UART timing proxy, thêm `-NoProxy` (xem cảnh báo drop-payload trong `docs/run-official-examples.md`).

Từng bước riêng lẻ tương đương (khi cần chẩn đoán sâu hơn):

```powershell
cd C:\path\to\eit-cn0565
.\cn0565-env\Scripts\Activate.ps1
python scripts\list_serial_ports.py
python scripts\check_connection.py --port COM7 --baud 230400
```

Nếu PowerShell chặn việc kích hoạt môi trường, chỉ áp dụng cho cửa sổ hiện tại:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\cn0565-env\Scripts\Activate.ps1
```

## Reset và baud rate

- Boot banner được in ở `115200` baud.
- IIO client kết nối ở `230400` baud, `8N1`, không flow control.
- Sau khi nạp firmware, nhấn `3029_RESET`/S1 hoặc power-cycle P10 vì DAPLink báo `Auto Reset: 0`.
- Không giữ nút `3029_BOOT`; thao tác đó đưa MCU vào UART download mode.
- Không chạy `capture_boot.py`, Tera Term hoặc một serial monitor đồng thời với chương trình IIO.

## Khi bị timeout

Thực hiện theo thứ tự:

1. Đóng mọi chương trình đang sử dụng COM port.
2. Chạy lại `list_serial_ports.py` vì số COM có thể thay đổi.
3. Kiểm tra `S2 = USB`, `S5 = WALL/USB`, DS2 trên CN0565 màu xanh.
4. Nhấn S1 một lần rồi thử lại ở 230400.
5. Nếu cần xác nhận firmware đang chạy, mở UART ở 115200 rồi nhấn S1:

   ```powershell
   python scripts\capture_boot.py --port COM7 --baud 115200
   ```

   Banner `Running IIOD server...` xác nhận MCU, firmware và UART đang hoạt động. Đợi script đóng COM trước khi chạy lại IIO.
6. Chỉ nạp lại `.hex` khi không có boot banner hoặc firmware đã bị thay đổi. Sau khi nạp, kiểm tra DAPLINK không có `FAIL.TXT`/`LASTFAIL.TXT`.

## Kết thúc phiên đo

Đóng script/GUI đang dùng COM port trước, sau đó mới rút P10. Dữ liệu thô lưu vào `data/raw/`; dữ liệu đã xử lý và ảnh tái tạo lưu vào `data/processed/`.
