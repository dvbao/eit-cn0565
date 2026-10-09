# Prompt chuyển tiếp — phân tích 3 phiên 10 / 50 / 80 kHz (2026-10-05)

Copy phần dưới vào model mới. Nếu model không đọc được file local, upload: 3 thư mục phiên (ít nhất
`patterns.csv`, `events.csv`, `frames.csv`, `meta.json`), `scripts/cn0565_pilot.py`,
`docs/cn0565-pilot-gui-and-data-guide.md`, `docs/protocols/user-p1-wiring-interleaved-208.json`.

---

Bạn là EIT/bioimpedance data analyst và reviewer khó tính. Giải thích bằng tiếng Việt, giữ English
terminology, kèm câu tiếng Anh để tôi trình bày với giáo sư. Mọi con số phải tính từ file; mọi diễn
giải phải nói rõ giới hạn. Không lặp lại các bước phần cứng đã xác minh.

## Dữ liệu

Repo: `C:\Users\dvb22\Documents\eit-cn0565` (Windows, Python `.\cn0565-env\Scripts\python.exe`;
dùng hàm có sẵn trong `scripts/cn0565_pilot.py`: `load_recording`, `audit_recording`,
`trial_timeline`, `plot_timeline`, `analyze_recording`, `interpret_features`, `plot_analysis`).

| Phiên | Thư mục `data/raw/pilot/` | Hz | Amplitude | Bắt đầu (UTC) | trial_windows.csv |
|---|---|---|---|---|---|
| 1 | `session-1-20261005-10000Hz-600mV` | 10 000 | 600 | 05:58:33 | có |
| 2 | `session-2-20261005-50000Hz-600mV` | 50 000 | 600 | 06:20:44 | **chưa** |
| 3 | `session-3-20261005-80000Hz-600mV` | 80 000 | 600 | 06:26:45 | **chưa** |

Cùng một người, cùng một lần gắn 16 gold cups (P1 X0–X15 xen kẽ L1,R1,…,L8,R8), voltage mode,
protocol `perimeter208` (208 pattern/frame: 16 cặp force liền kề × 13 cặp sense liền kề), routing đã
sửa (`cn0565-first-pilot-v5-verified-routing`: F+ Y0, S+ Y6, S− Y7, F− Y3; driver index (x+12) mod 24).
Thiết kế `state_sequence`: REST (1 frame, ~20.6 s) rồi SMILE_LEFT, SMILE_RIGHT, SMILE_BOTH,
PUFF_LEFT, PUFF_RIGHT, PUFF_BOTH liên tiếp, mỗi state 1 frame; cue → 2 s settle → quét 20.6 s;
giữ ≈ 22.8 s; không có REST giữa các task; cùng thứ tự ở cả 3 phiên; mỗi task 1 lần/phiên.
Cả 3 phiên: status complete, audit pass, 7/7 frame × 208.

Mỗi dòng `patterns.csv` = một phép đo: `task, pattern_id (0–207), f_plus…f_minus` (X index),
`*_site` (L1…R8), `real_raw, imag_raw` = DFT count phức của điện áp AIN2−AIN3 ở tần số kích thích
(chưa hiệu chuẩn volt/ohm), `start_s/end_s`. Bỏ qua mọi thư mục có `meta.json` → `source = mock`.

Mức nền đã đo (phiên khác, 10 kHz, amplitude 800, REST→REST cách ~23 s, cùng lần gắn):
pattern mạnh (|V| ≥ 100 count) đổi 0.36–0.96 %; RMS 1.2–2.9 count. Dữ liệu:
`session-20261005T040628-a0a874`.

## Kết quả sơ bộ tôi đã tính (hãy kiểm chứng lại, đừng tin mù)

- REST |V| trung vị: 26.9 / 31.2 / 30.6 count (10/50/80 kHz); 73 / 82 / 73 pattern có |V| ≥ 50.
- Pha thô của REST lệch theo tần số (trung vị −68.5° / +91.2° / −121.9°) → **so sánh khác tần số phải
  dùng đại lượng bất biến pha**: thay đổi tương đối phức **ΔZ = (v_task − v_REST) / v_REST**, hoặc
  |v| và Δpha. Tương quan Δ thô giữa 10k và 50k ra −0.9 chỉ vì lệch pha này.
- Trung vị % thay đổi trên pattern mạnh (10/50/80 kHz): SMILE_LEFT 1.85/2.98/2.25; SMILE_RIGHT
  1.83/3.05/2.38; SMILE_BOTH 3.65/5.05/4.46; PUFF_LEFT 3.08/3.84/4.52; PUFF_RIGHT 2.75/3.63/3.20;
  PUFF_BOTH 2.76/3.79/2.61.
- Lệch bên (pattern chỉ gồm cup L trừ pattern chỉ gồm cup R, điểm %): SMILE_LEFT +2.95/+3.82/+3.05;
  SMILE_RIGHT −0.47/−0.50/−0.67; PUFF_LEFT +1.00/+2.31/+2.00; PUFF_RIGHT −0.06/+0.26/+0.95.
- Tương quan ΔZ của cùng task giữa các tần số: 0.83–0.98 (rất lặp lại).
- Ma trận tương quan ΔZ giữa task (10 kHz): SMILE_BOTH~SMILE_LEFT 0.62, ~SMILE_RIGHT 0.71;
  PUFF_BOTH~PUFF_LEFT 0.71, ~PUFF_RIGHT 0.71; nhóm smile vs puff ≈ −0.2…0.27; SMILE_LEFT~SMILE_RIGHT 0.10.

## Việc cần làm (theo thứ tự)

1. **QC & timing từng phiên**: audit, `configuration_checks.csv` (Hz/amp không đổi), `trial_timeline`
   + `timeline.png` (hold, settle, `frames_inside_hold`). Phiên 2 và 3 chưa có `trial_windows.csv`:
   hỏi tôi đã làm đúng cue chưa trước khi tạo bằng `cue_intervals(path, operator_confirmed=True)`.
2. **Bảng đặc trưng mỗi phiên**: `analyze_recording(..., min_stable_frames=1, label_mode='cue_assumed')`
   + `interpret_features`; xuất bằng `export_analysis` vào `data/processed/pilot/`.
3. **Phân tích chéo 3 tần số** (script mới `scripts/analysis/three_frequency_report.py`, không sửa
   dữ liệu raw), tạo các bảng/hình:
   - T1 QC/timing; T2 đặc trưng task × tần số (RMS, % trung vị, % pattern mạnh, số pattern > ngưỡng);
     T3 lateralization (L, R, LI = (L−R)/(L+R)); T4 tương quan cross-frequency của ΔZ.
   - F1 timeline 3 phiên. F2 bản đồ baseline: |v_REST| dạng ma trận 16 cặp force × 13 vị trí sense
     (theo thứ tự perimeter) cho mỗi tần số + tỉ lệ 50k/10k, 80k/10k; pha REST. F3 heatmap |ΔZ| (%):
     6 task × 208 pattern (sắp theo cặp force), 3 panel tần số, cùng thang màu; thêm bản ma trận
     16×13 cho từng task. F4 bar lateralization L vs R theo task × tần số. F5 ma trận tương quan
     6×6 giữa task (mỗi tần số) và ma trận 18×18 (task × tần số). F6 Re(ΔZ) vs Im(ΔZ) (thay đổi
     biên độ vs pha) mỗi task. F7 hiệu ứng theo tần số (đường 10→50→80 kHz mỗi task). F8 "electrode
     involvement" heuristic: tổng |ΔZ| của các pattern có chứa từng cup, vẽ trên sơ đồ 16 vị trí —
     ghi rõ KHÔNG phải định vị cơ. F9 nhận dạng task thử nghiệm: coi 3 phiên như 3 lần lặp,
     leave-one-session-out nearest-centroid/tương quan trên ΔZ → confusion matrix 6×6, có cảnh báo.
4. **Giải thích cho tôi** từng bảng/hình: đọc thế nào, kết luận được gì, không kết luận được gì, và
   câu tiếng Anh cho giáo sư.
5. **Đề xuất phiên tiếp theo** để khắc phục giới hạn: rest→task→rest từng task (chế độ gốc của
   notebook), thứ tự ngẫu nhiên, ≥ 2 vòng, cùng tần số; REST-only control trong cùng phiên.

## Giới hạn bắt buộc phải nói

- Chỉ một REST ở đầu mỗi phiên; không có REST giữa task → không tách được drift (task cuối đo sau
  REST ~137 s), carryover giữa task liên tiếp, không có recovery.
- Thứ tự task giống nhau ở 3 phiên → tương quan cao giữa phiên có thể một phần do cùng thứ tự/drift;
  cấu trúc tương quan giữa task (smile vs puff gần 0) phản bác drift chung đơn thuần nhưng chưa loại trừ.
- 3 phiên khác tần số nên không phải lặp lại thuần; mỗi task 1 frame/phiên; 1 người, 1 lần gắn.
- Count chưa hiệu chuẩn; so sánh % trong phiên; pattern ID là cấu hình 4 điện cực, không phải pixel;
  không có video/EMG xác nhận cử động; không phải % hoạt hóa cơ, không phải tín hiệu một cơ.
- Amplitude 600 là giá trị lệnh (thang no-OS DacVoltPP/800 × 2047); biên độ/dòng thật chưa đo.
