# Fig. 14, ba thuật toán pyEIT, và lộ trình thử medium

## Kết luận ngắn

1. Fig. 14 là **mô phỏng conductivity change**, không phải phép đo CN0565 và
   cũng không chứng minh phần cứng hoạt động. Tài liệu CN0565 không công bố
   code, vị trí, bán kính hay conductivity chính xác của bốn target, nên chỉ có
   thể tái tạo cùng nguyên lý, không thể khẳng định khớp pixel.
2. `scripts/eit_sim_playground.py` mô phỏng forward data `v0`, `v1` rồi đưa
   **cùng dữ liệu** cho BP, JAC và GREIT. Đây là difference EIT: ảnh là
   `Delta sigma`, không phải bản đồ conductivity tuyệt đối.
3. `p=0.5`, `lambda=0.01` là giá trị mặc định/minh họa của code CN0565, không
   phải hằng số vật lý và không có paper nào chứng minh chúng tối ưu cho tank,
   electrode, noise và medium cụ thể của bạn.
4. Petri dish có thể là phantom bench đầu tiên, nhưng một tank trụ với vòng
   điện cực đồng phẳng, cố định thường là phép thử định lượng tốt hơn. Qua được
   phantom không đồng nghĩa được phép thử trên người.

## 1. Sandbox đang giả lập cái gì?

Forward model giải gần đúng phương trình

```text
div(sigma grad(u)) = 0
```

trên một đĩa 2D bán kính chuẩn hóa bằng 1. Dòng đơn vị đi vào một điện cực và
đi ra điện cực khác; hiệu điện thế được lấy trên các cặp điện cực còn lại.

- `v0`: điện áp biên khi toàn medium có `sigma = 1`.
- `v1`: điện áp biên khi một số phần tử FEM được gán conductivity khác 1.
- Dữ liệu inverse: thay đổi từ `v0` sang `v1`.
- Output: ước lượng `Delta sigma`; dấu dương là dẫn điện hơn reference, dấu âm
  là dẫn điện kém hơn reference theo quy ước của solver.

Đây **không phải** là mô phỏng đầy đủ CN0565. Nó bỏ qua:

- kích thước và contact impedance của điện cực (điện cực là điểm);
- hình học 3D, độ sâu chất lỏng, vật thể nằm trên/dưới mặt phẳng điện cực;
- sai số vị trí điện cực và hình dạng tank;
- nguồn kích thích thực, R_LIMIT, TIA, ADC/DFT, calibration và saturation;
- noise theo channel, drift, nhiệt độ, electrode polarization và chuyển động;
- nếu `perm` là số thực, thành phần điện dung/phase của medium.

Paper pyEIT cũng nói forward solver dùng simple electrode model và complete
electrode model (CEM) sẽ sát vật lý hơn. Vì vậy sandbox dùng để kiểm tra logic
algorithm, không dùng để dự đoán định lượng trực tiếp một thí nghiệm sinh học.

## 2. Ý nghĩa từng tham số trong `eit_sim_playground.py`

### Hình học, điện cực và protocol

| Tham số | Đang biểu diễn | Ý nghĩa thực tế / điều không được suy diễn |
|---|---|---|
| `N_EL=16` | 16 điện cực điểm, cách đều trên biên đĩa | Phải bằng số điện cực thật và đúng thứ tự đánh số. Nhiều điện cực hơn không tự động cho độ phân giải tỷ lệ thuận. |
| `H0=0.08` | kích thước phần tử ban đầu so với bán kính miền | Chỉ là độ mịn số học. Giảm `h0` làm chậm và giảm lỗi rời rạc; không tạo thêm thông tin đo và không biến hệ 16 điện cực thành ảnh độ phân giải cao. |
| `DIST_EXC=1` | cặp bơm dòng `[i, i+1]` | Adjacent drive. Phải khớp `force_distance` của CN0565. `8` với 16 điện cực là opposite drive. |
| `STEP_MEAS=1` | hiệu điện thế giữa `[j+1, j]` | Adjacent voltage measurement. Phải khớp `sense_distance`. |
| `PARSER_MEAS="std"` | bắt đầu thứ tự sense từ electrode 0 và bỏ cặp chạm điện cực drive | Thứ tự hàng của vector data phải khớp tuyệt đối giữa hardware và `protocol_obj`; đúng length nhưng sai order vẫn cho ảnh giả. |
| `BACKGROUND_SIGMA=1` | conductivity reference chuẩn hóa | Không mặc định là `1 S/m` hay `1 ohm`. Đây là tỷ lệ chuẩn hóa. Muốn gắn đơn vị phải đo conductivity của medium và dùng mô hình hình học/điện cực phù hợp. |

Với `N_EL=16`, adjacent drive/measure và parser `std`, phiên bản pyEIT trong
repo tạo 16 excitation x 13 voltage differences = **208 giá trị/frame**. Hệ số
`192.0` trong example BP cũ không nên được coi là định luật vật lý.

### Target/anomaly

| Tham số | Ý nghĩa |
|---|---|
| `center=[x,y]` | tọa độ chuẩn hóa theo bán kính tank. `[0.5,0.5]` có khoảng cách đến tâm `sqrt(0.5)=0.707R`, không phải `0.5R`. |
| `r` | bán kính target chia cho bán kính tank. `r=0.2` nghĩa là target có bán kính `0.2R`. |
| `perm` | trong mô phỏng real-valued này là conductivity/admittivity tương đối, dù API dùng tên “permittivity”. `perm=10` nghĩa là dẫn điện gấp 10 background; resistivity xấp xỉ `1/10`. Nó không có nghĩa là impedance bằng 10 ohm. |

Các target mặc định của preset `fig14` chỉ là ước lượng từ hình công bố. Nên
dùng preset này để tái tạo bố cục bốn contrast; dùng preset `single` và các
contrast nhỏ hơn để đánh giá thuật toán nghiêm túc.

### Reference, normalization và noise

| Tham số/call | Thực sự làm gì |
|---|---|
| `v0 = forward.solve_eit()` | forward data của background đồng nhất. |
| `v1 = forward.solve_eit(perm=...)` | forward data sau khi đặt target. |
| `jac_normalized=True` | chia từng hàng Jacobian cho `abs(v0[i])`. |
| JAC/GREIT `solve(..., normalize=True)` | dùng `(v1-v0)/abs(v0)`. |
| BP `solve(..., normalize=True)` | pyEIT BP override công thức và chia cho `sign(real(v0))`, không giống normalization của JAC/GREIT. |
| `--noise-rel q` | thêm Gaussian noise độc lập vào cả `v0` và `v1`, với standard deviation `q * RMS(v)`. Đây chỉ là noise trắng toàn cục, chưa giống noise theo channel của hardware. |

Trên phần cứng, baseline phải là nhiều frame của **chính tank và electrode
configuration đó**, lấy trung bình sau khi hệ ổn định. `v0 = ones(...)` trong
một số example riêng lẻ không phải baseline vật lý hợp lệ cho phantom.

## 3. Ba thuật toán làm gì và khác nhau vì sao?

### BP - back projection

pyEIT dựng một smear matrix: mỗi phép đo “tô” thay đổi điện áp ngược lên vùng
có điện thế forward nằm giữa hai điện cực sense, rồi cộng chồng các vùng.

```text
Delta sigma_hat = -B.T Delta v
```

- Ưu: rất đơn giản, nhanh, dễ thấy lỗi data dạng streak.
- Nhược: blur/streak, amplitude và position phụ thuộc vị trí, không giải inverse
  problem có regularization rõ ràng.
- `weight="none"`: không hiệu chỉnh theo bán kính.
- `weight="simple"`: nhân trọng số gần 1 ở tâm và gần 0 ở biên để giảm ảnh
  hưởng biên. Đây là heuristic, không phải tham số vật lý.

### JAC - one-step linearized inverse

Quanh reference, forward model được tuyến tính hóa:

```text
Delta v ~= J Delta sigma
H = inv(J.T J + lambda R) J.T
Delta sigma_hat = -H Delta v
```

Trong `jac.JAC(...).solve()` của pyEIT, đây là **one-step linear solve** với
matrix `H` tính trước; nó không phải vòng lặp Gauss-Newton. Hàm `JAC.gn()` mới
là iterative static solver và CN0565 example không gọi hàm đó.

Regularization:

| `method` | `R` trong pyEIT 1.2.4 | Vai trò của `p` |
|---|---|---|
| `"kotre"` | `diag(diag(J.T J) ** p)` | có tác dụng; `p=0` gần DGN, `p=1` gần LM/NOSER, `p=0.5` là compromise heuristic. |
| `"lm"` | `diag(diag(J.T J))` | bị bỏ qua. |
| `"dgn"` | identity | bị bỏ qua. Bất kỳ string khác cũng rơi vào nhánh này trong code hiện tại. |

`lambda` lớn hơn thường giảm noise/ringing nhưng tăng bias, blur và giảm
amplitude. `lambda` nhỏ hơn giữ chi tiết hơn nhưng khuếch đại noise và model
mismatch. Code pyEIT dùng `+ lambda R`, trong khi paper thường viết
`+ lambda^2 R`; do đó không copy giá trị số giữa công thức/thư viện mà không
kiểm tra convention.

### GREIT - bản triển khai “distribution method” của pyEIT

Paper GREIT 2009 định nghĩa một reconstruction matrix được fit từ:

- forward targets ở nhiều vị trí;
- desired images có resolution/amplitude mong muốn;
- electronic noise và electrode-movement samples;
- các mục tiêu AR, PE, RES, SD, RNG và NF.

Nhưng class `pyeit.eit.greit.GREIT` 1.2.4 trong repo là phiên bản đơn giản:

```text
H = W.T J.T inv(J J.T + lambda diag(diag(J J.T)**p))
```

`W` ở đây là sigmoid mapping từ element centres sang grid ảnh. Vì vậy không
nên nói class này đã “train từ real stick data” chỉ vì tên là GREIT.

| Tham số | Ý nghĩa trong đúng code đang cài |
|---|---|
| `p` | exponent của diagonal regularizer trong measurement space `J J.T`; không đơn giản là “noise covariance = p”. |
| `lambda` | trọng số regularization trong inverse ở measurement space. Xu hướng bias-noise giống JAC nhưng giá trị không tương đương trực tiếp. |
| `n=32` | output grid `32 x 32`. Tăng `n` chỉ thêm sample/pixel hiển thị, không thêm độ phân giải vật lý. Paper GREIT chọn 32 x 32 như output specification. |
| `ratio=0.1` | bán kính support mong muốn của sigmoid mapping theo khoảng cách chuẩn hóa. Tăng lên thường làm blob rộng hơn. |
| `s=20` | độ dốc sigmoid. Tăng `s` làm biên weighting gắt hơn; giảm làm chuyển tiếp rộng hơn. |
| `perm=1` | conductivity distribution dùng để tính reference Jacobian. |
| `jac_normalized=True` | chuẩn hóa từng hàng `J` bằng `abs(v0)`. |
| `method="dist"` | lựa chọn duy nhất được hỗ trợ. |
| `w` | được nhận và lưu nhưng **không được dùng** trong `_compute_h()` của pyEIT 1.2.4; thay nó sẽ không đổi kết quả. |

### Kỳ vọng quan sát

- BP: blur/streak, đặc biệt gần biên; dễ thấy data artefact.
- JAC: localization/resolution có thể tốt, nhưng dễ ringing và nhạy noise khi
  regularization yếu.
- GREIT: blob đồng đều hơn theo vị trí, ít ringing hơn, thường hy sinh một ít
  peak resolution. Paper 2009 quan sát đúng trade-off này khi các thuật toán
  được tune về cùng noise figure.

Không nên so bằng cảm giác khi mỗi subplot có colorbar tự động. Script in
`min/max` raw ra terminal; đánh giá amplitude phải scale/calibrate thống nhất.

## 4. Bộ test phân biệt ba thuật toán

Giữ nguyên một forward dataset cho cả ba algorithm. Mỗi test chỉ đổi một yếu
tố và chạy ít nhất 30 seed noise khi có noise.

### Test A - zero/null

Đặt `v1 = v0`. Mọi ảnh phải gần zero. Nếu không, lỗi nằm ở data ordering,
baseline, normalization hoặc implementation trước khi bàn tới image quality.
Chạy trực tiếp bằng `--preset null`.

### Test B - point-spread theo vị trí

- Một target nhỏ, contrast nhẹ: `perm=1.1`, `r=0.05` đến `0.1`.
- Đặt lần lượt ở `r/R = 0, 0.25, 0.5, 0.7` và nhiều góc.
- Đo: amplitude response (AR), position error (PE), resolution (RES), shape
  deformation (SD), ringing (RNG).

Đây là test quan trọng nhất để thấy BP bị biến dạng gần biên và GREIT cố làm
response đồng đều theo vị trí.

### Test C - contrast và giới hạn tuyến tính

Giữ vị trí/kích thước, quét `perm = 0.9, 1.1, 0.5, 2, 0.1, 10`.

- `0.9/1.1`: vùng tuyến tính nhỏ, phù hợp để kiểm tra JAC/GREIT.
- `0.1/10`: contrast rất lớn, tốt để minh họa nhưng dễ phá giả định tuyến tính.

Vẽ reconstructed peak hoặc integrated amplitude theo true `Delta sigma`.
Đường cong lệch tuyến tính cho biết không thể diễn giải màu như conductivity
tuyệt đối.

### Test D - noise/regularization

Quét `--noise-rel 0, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2`, rồi với JAC/GREIT quét:

```text
p      = 0, 0.25, 0.5, 0.75, 1
lambda = 1e-4, 1e-3, 1e-2, 1e-1, 1
```

Chọn tham số trên held-out noise runs bằng PE/RES/RNG/NF, không chọn ảnh “đẹp
nhất” trên đúng sample dùng để tune. `p=0.5`, `lambda=0.01` chỉ là điểm bắt đầu.

### Test E - hai target và resolution

Đặt hai target cùng dấu rồi giảm khoảng cách; lặp lại với hai target trái dấu.
Ghi khoảng cách nhỏ nhất mà hai peak còn phân biệt. Tăng `n` của GREIT không
được tính là cải thiện resolution nếu hai peak vật lý vẫn không tách được.

### Test F - model mismatch

Sinh data bằng geometry/electrode positions khác geometry reconstruction:

- ellipse forward, circle inverse;
- lệch một electrode;
- đổi kích thước/độ sâu target ngoài mô hình 2D;
- dùng `dist_exc`/`step_meas` sai có chủ ý.

Test này thường gần thực tế hơn việc tiếp tục làm mesh nhỏ hơn trong một mô
hình hoàn hảo.

## 5. Từ simulation sang medium thật

### Gate 0 - electronics

1. Chạy production/test board với các R/C đã biết.
2. Xác nhận calibration, repeatability, real/imaginary, phase và không
   saturation ở nhiều frequency/amplitude.
3. Với cùng một cấu hình, lưu raw complex data chứ không chỉ PNG.

### Gate 1 - empty phantom

Một petri dish dùng được để smoke test, nhưng tank trụ thường tốt hơn cho mô
hình circle 2D. Yêu cầu quan trọng hơn tên dụng cụ:

- biên tròn đã đo đường kính;
- electrode cùng loại, cùng kích thước, cách đều, cùng cao độ và cố định;
- liquid depth và lượng medium lặp lại được;
- conductivity và temperature được đo/ghi lại;
- dây không di chuyển giữa baseline và target frame.

Thu nhiều frame empty tank để đo mean, standard deviation và covariance theo
channel. Đây là noise model thực cần dùng khi tune regularization.

### Gate 2 - known inclusions

Đặt target ở một grid vị trí biết trước. Bắt đầu bằng một target cách điện có
hình học ổn định; sau đó dùng target dẫn điện có conductivity được đo. Metal
có thể gây electrode polarization/field distortion rất mạnh, nên không coi nó
là “mô phỏng mô người” chỉ vì ảnh hiện rõ.

Với mỗi vị trí:

1. baseline empty tank;
2. đặt target, không đổi electrode/dây;
3. lấy nhiều frame;
4. bỏ target và kiểm tra hệ có quay về baseline;
5. lặp lại ngày khác/người thao tác khác.

Chạy cùng bộ AR/PE/RES/SD/RNG/NF như simulation. Sau đó mới quét frequency và
medium conductivity.

### Gate 3 - model matching

Đưa kích thước tank, vị trí electrode, reference conductivity và protocol thật
vào forward model. Nếu dùng petri dish nông, ảnh hưởng 3D và đáy/mặt thoáng có
thể lớn; một circle mesh 2D không tự động đại diện đúng dish.

### Gate 4 - người

**Không** chuyển thẳng từ petri dish sang người. CN0565 là reference/evaluation
design; việc circuit note nhắc IEC current limits và basic isolation không phải
chứng nhận rằng toàn bộ setup, firmware, điện cực, cáp, host và quy trình của
bạn là medical device an toàn.

Trước human study cần tối thiểu:

- đánh giá electrical safety/leakage/isolation của toàn hệ thống theo standard
  áp dụng và worst-case fault;
- risk management, giới hạn dòng độc lập, kiểm tra firmware/hardware failure;
- phê duyệt ethics/IRB của cơ sở, informed consent và người có chuyên môn giám
  sát;
- protocol nghiên cứu xác định trước; không dùng ảnh thử nghiệm để chẩn đoán.

## 6. Cái gì được paper hỗ trợ, cái gì không?

- CN0565 Circuit Note: xác nhận ba thuật toán example, adjacent measurement,
  yêu cầu calibration và phụ thuộc vào electrode placement/measurement
  accuracy. Nó không công bố parameter tạo Fig. 14.
- Liu et al. 2018 (pyEIT): hỗ trợ cấu trúc forward FEM, `set_perm`, scan pattern,
  dynamic difference imaging và giới hạn simple electrode model.
- Adler, Dai & Lionheart 2007: giải thích one-step GN, regularization, vai trò
  `lambda`, và lựa chọn heuristic `p=0.5` giữa dồn noise ra biên (`p=0`) và vào
  tâm (`p=1`). Đây không phải proof rằng `p=0.5` tối ưu cho CN0565 của bạn.
- Adler et al. 2009: định nghĩa AR/PE/RES/SD/RNG/NF và cho thấy GREIT có response
  đồng đều/ít ringing hơn trong benchmark đã chuẩn hóa noise. Paper cũng nói
  noise thật phụ thuộc hardware/patient connection và khuyến nghị tune theo hệ
  đo cụ thể.

## 7. Chạy sandbox

### macOS/Linux (`zsh`/`bash`)

`cn0565-env` trong repo là virtual environment của Windows và không thể chạy
trên macOS/Linux. Tạo environment native một lần:

```bash
python3 -m venv .venv-sim
source .venv-sim/bin/activate
python -m pip install -r requirements-sim.txt
```

Sau đó chạy bằng dấu `/`, không dùng `python.exe` hoặc dấu `\`:

```bash
# Bốn target, cả ba thuật toán
python scripts/eit_sim_playground.py

# Một target để học response
python scripts/eit_sim_playground.py --preset single

# Null test: không có target, output phải bằng 0 khi noise-rel=0
python scripts/eit_sim_playground.py --preset null

# Thêm noise
python scripts/eit_sim_playground.py --noise-rel 0.001 --seed 1
```

Không muốn activate lại thì dùng `.venv-sim/bin/python` thay cho `python`.

### Windows PowerShell

```powershell
# Bốn target, cả ba thuật toán
cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py

# Một target để học response
cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py --preset single

# Null test: không có target, output phải bằng 0 (khi noise-rel=0)
cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py --preset null

# Thêm noise và lưu hình
cn0565-env\Scripts\python.exe scripts\eit_sim_playground.py `
  --noise-rel 0.001 --seed 1 --save eit-measurement\data\results\fig14-noise-001.png --no-show
```

Đổi `P_VAL`, `LAMB_VAL`, `JAC_METHOD`, `GREIT_N`, `GREIT_S`, `GREIT_RATIO`,
`H0`, protocol hoặc danh sách anomaly ở đầu file; mỗi run chỉ đổi một nhóm biến
và ghi lại config cùng raw metric.

## Tài liệu nguồn trong repo

- [`reference/cn0565 rev. a.pdf`](../reference/cn0565%20rev.%20a.pdf), Fig. 14 và phần Image
  Reconstruction Algorithms.
- [`reference/papers/reconstructing_alg/1-s2.0-S2352711018301407-main.pdf`](../reference/papers/reconstructing_alg/1-s2.0-S2352711018301407-main.pdf),
  pyEIT framework.
- [`reference/papers/reconstructing_alg/Adler_2007_Physiol._Meas._28_S1.pdf`](../reference/papers/reconstructing_alg/Adler_2007_Physiol._Meas._28_S1.pdf),
  one-step GN và regularization.
- [`reference/papers/reconstructing_alg/Adler_2009_Physiol._Meas._30_S35.pdf`](../reference/papers/reconstructing_alg/Adler_2009_Physiol._Meas._30_S35.pdf),
  GREIT và performance figures of merit.
