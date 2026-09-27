# Cấu hình, luồng tái tạo ảnh, và "medium"

Tài liệu này trả lời 3 câu hỏi: các tham số nằm ở đâu và ảnh hưởng gì, các
file/thuật toán tái tạo ảnh gọi nhau thế nào, và "medium" (miền đo) là gì với
cách tùy biến nó. Dùng sau khi `docs/connection-checklist.md` đã xác nhận kết
nối OK.

## 1. Luồng file khi chạy GUI (`main.py`)

```
main.py (RealtimeEIT)
  -> tạo adi.cn0565(uri=...)                          [hardware handle]
  -> CN0565_Worker.run()                              [examples/cn0565/cn0565_worker.py]
       intf.excitation_frequency = freq                -> ghi xuống AD5940 qua IIO
       intf.electrode_count / force_distance / sense_distance -> ghi xuống ADG2128 crossbar
       mesh_obj = pyeit.mesh.create(n_el, h0)          -> hình học FEM giả định (xem mục 3)
       protocol_obj = pyeit.eit.protocol.create(...)   -> cách DIỄN GIẢI thứ tự phép đo
       vòng lặp:
         voltages = intf.all_voltages                  -> đọc thật từ phần cứng (adi/cn0565.py)
         solver(v0, v1, protocol_obj)
           bp.BP(mesh_obj, protocol_obj).solve(...)     hoặc
           jac.JAC(mesh_obj, protocol_obj).solve(...)   hoặc
           greit.GREIT(mesh_obj, protocol_obj).solve(...)
         -> ds (mảng giá trị trên mesh)
         -> matplotlib vẽ lên self.figure
```

Điểm mấu chốt: **mesh_obj chỉ được tạo ra một lần khi bấm Connect** (đầu
`run()`), không đổi trong lúc đo. Đổi `el`/`h0` chỉ có tác dụng ở lần
Connect kế tiếp, không phải real-time.

## 2. Tham số phần cứng (đo được cái gì)

| Tham số | Khai báo ở | Ảnh hưởng | Cách thử nghiệm |
|---|---|---|---|
| `excitation_frequency` | `intf.excitation_frequency`, [adi/cn0565.py](../work/upstream-download/extracted/pyadi-iio-main/adi/cn0565.py) (kế thừa từ `ad5940`) | Tần số kích thích AD5940, 10k–80kHz | Đo cùng 1 cặp điện cực ở nhiều tần số (10k/20k/40k/80k), so sánh magnitude/phase — vật liệu có thành phần điện dung sẽ đổi phase theo tần số, vật liệu thuần trở thì không |
| `electrode_count` | `intf.electrode_count` | Số điện cực (8/16/32) | Đổi số điện cực, so thời gian 1 khung hình và độ chi tiết ảnh |
| `force_distance` | `intf.force_distance` | Khoảng cách giữa 2 điện cực bơm dòng (F+/F-) | Phải đổi cùng lúc với `dist_exc` ở mục 3, không đổi riêng |
| `sense_distance` | `intf.sense_distance` | Khoảng cách giữa 2 điện cực đo áp (S+/S-) | Phải đổi cùng lúc với `step_meas` ở mục 3, không đổi riêng |

## 3. Tham số protocol (diễn giải phép đo)

`pyeit.eit.protocol.create(n_el, dist_exc, step_meas, parser_meas)`:

| Tham số | Ý nghĩa | Mặc định trong `cn0565_worker.py` |
|---|---|---|
| `dist_exc` | khoảng cách A→B của cặp bơm dòng; `1` = kề nhau ("adjacent"), `n_el/2` = đối xứng ("apposition") | `1` |
| `step_meas` | khoảng cách giữa 2 điện cực đo áp | `1` |
| `parser_meas` | định dạng khung đo, `"std"` mặc định | `"std"` |

**Cảnh báo quan trọng**: `dist_exc`/`step_meas` (phần mềm, dùng để dựng ma
trận Jacobian) phải khớp với `force_distance`/`sense_distance` (phần cứng,
dùng để đóng crossbar thật) trong [adi/cn0565.py:switch_sequence](../work/upstream-download/extracted/pyadi-iio-main/adi/cn0565.py). Nếu
đổi một bên mà quên đổi bên kia, phần mềm vẫn chạy không báo lỗi nhưng sẽ
diễn giải sai cặp điện cực nào ứng với dòng dữ liệu nào → ảnh tái tạo sai
mà không có dấu hiệu cảnh báo.

## 4. Tham số thuật toán tái tạo ảnh

| Thuật toán | `setup()` tham số | Ý nghĩa |
|---|---|---|
| **BP** | `weight="none"` | Trọng số ma trận back-projection; `perm` nếu muốn cung cấp phân bố conductivity giả định trước |
| **JAC** | `p=0.20`, `lamb=0.001`, `method="kotre"` (hoặc `"lm"`, `"dgn"`), `perm`, `jac_normalized` | `p`/`lamb` là hệ số regularization (điều chỉnh độ mượt vs. độ nhạy nhiễu); `method` chọn công thức regularize |
| **GREIT** | `method="dist"`, `w`, `p=0.20`, `lamb=1e-2`, `n=32`, `s=20.0`, `ratio=0.1`, `perm`, `jac_normalized` | `p` là hệ số hiệp phương sai nhiễu giả định, `lamb` là regularization, `n`/`s`/`ratio` điều khiển lưới ảnh đầu ra GREIT |

**Giới hạn đã biết**: trong [examples/cn0565/cn0565_worker.py:157-173](../examples/cn0565/cn0565_worker.py), `solver()` gọi
`self.eit.setup(p=0.5, lamb=0.01, ...)` **hard-code**, còn hai thanh trượt
`sldr_p`/`sldr_lambda` trên GUI chỉ cập nhật `self.pVal`/`self.lambdaVal` mà
`solver()` không hề đọc lại — kéo thanh trượt hiện **không có tác dụng
thật**. Đây là file thuộc `examples/cn0565/` (bản mirror upstream, bị
`setup_official_examples.ps1` ghi đè nếu chạy lại), nên khi cần sửa, nói để
làm theo đúng cách project này đang dùng: viết một wrapper không đụng file
gốc, giống cách `scripts/run_official_example.py` đang làm với URI.

## 5. "Medium" là gì và cách tùy biến

`mesh.create()` không đo hình dạng thật từ phần cứng — nó là một **giả định
hình học** dùng để: (a) tính ma trận Jacobian cho JAC/GREIT, (b) làm khung để
vẽ ảnh. Chữ ký đầy đủ (`cn0565-env/Lib/site-packages/pyeit/mesh/wrapper.py:311`):

```python
mesh.create(n_el=16, fd=shape.circle, fh=shape.area_uniform, h0=0.1, p_fix=None, bbox=None)
```

| Tham số | Ý nghĩa | Tùy biến |
|---|---|---|
| `fd` | hàm khoảng cách định nghĩa **biên miền đo** | mặc định `shape.circle` (đĩa tròn bán kính 1). pyEIT có sẵn `shape.ellipse`, `shape.rectangle`, `shape.thorax` (mặt cắt lồng ngực), `shape.fd_polygon` (đa giác tùy ý). Nếu bể/đối tượng thật của bạn không tròn, đổi `fd` cho khớp |
| `p_fix` | tọa độ cố định của điện cực trên biên | mặc định giả định N điện cực cách đều nhau trên hình `fd`. Nếu điện cực thật không cách đều (do cơ khí board của bạn), truyền tọa độ thật vào đây |
| `bbox` | hộp giới hạn lưới | phải khớp kích thước với `fd` khi đổi hình dạng |
| `h0` | mật độ lưới FEM | không ảnh hưởng vật lý, chỉ ảnh hưởng độ mịn ảnh/tốc độ tính |

Muốn thử thuật toán với một "vật thể" đã biết trước (kiểm tra JAC/GREIT có
tái tạo đúng không, trước khi tin vào dữ liệu phần cứng), dùng
`pyeit.mesh.set_perm` để gán độ dẫn giả định cho từng phần tử mesh rồi mô
phỏng — đây là cách để tách bạch "thuật toán tái tạo sai" khỏi "phần cứng đo
sai" khi debug.

Tham khảo thêm cách pyEIT tự tổ chức mesh ở
[pyEIT/pyeit/mesh trên GitHub](https://github.com/eitcom/pyEIT/tree/master/pyeit/mesh)
(bạn đã có link này) — các hàm `shape.py` ở trên chính là nơi để đọc trước
khi tùy biến.

## 6. Trình tự học có hệ thống (đề xuất)

Làm theo thứ tự, mỗi bước chỉ đổi **một biến** so với bước trước để biết
chính xác cái gì gây ra thay đổi bạn thấy:

1. **Xác nhận phần cứng ổn định trước khi đụng phần mềm tái tạo**: chạy
   `scripts\startup_check.ps1 -Port COM7` nhiều lần liên tiếp, kết quả đo
   sanity check phải giống nhau. Chưa ổn ở bước này thì mọi kết luận về
   thuật toán tái tạo sau đó đều không đáng tin.
2. **Quét `single` qua tần số**: giữ nguyên 1 cặp điện cực, đổi
   `excitation_frequency` (sửa trực tiếp trong `cn0565_example_single.py`
   hoặc gọi `adi.cn0565` từ một script riêng), ghi lại real/imag mỗi tần số
   → hiểu đặc tính trở kháng của mẫu/medium bạn đang đo.
3. **`sweep` toàn bộ cặp ở 1 tần số cố định**: xem `data/raw/cn0565_example_data.csv`
   để hiểu cấu trúc dữ liệu thô trước khi đưa vào pyEIT.
4. **GUI với mesh mặc định (đĩa tròn)**: chạy `gui`, dùng **Baseline** trên
   một trạng thái đã biết, rồi so sánh BP vs JAC vs GREIT trên cùng một thay
   đổi vật lý (ví dụ nhúng một vật vào bể) để thấy 3 thuật toán khác nhau ở
   đâu.
5. **Chỉ sau khi quen bước 4**, mới đụng tới `p`/`lamb`/`method` (sau khi sửa
   giới hạn ở mục 4) hoặc tùy biến `fd`/`p_fix` ở mục 5 — đổi mesh trước khi
   hiểu rõ hành vi mặc định sẽ khiến không biết ảnh xấu đi là do mesh sai hay
   do bạn đọc nhầm.
