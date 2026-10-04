# Prompt chuyển context sang chatbot khác

Updated: 2026-10-04. Copy phần dưới vào một cuộc trò chuyện mới. Nếu chatbot
không đọc được GitHub/local files, upload các tài liệu ưu tiên; không giả định
chatbot đã đọc file chỉ vì bạn cung cấp tên file.

---

Bạn hãy làm research collaborator, EIT/bioimpedance engineer và scientific
reviewer khó tính cho tôi. Tôi là người mới, cần hiểu từ khái niệm đến toán,
code, acquisition và cách diễn giải kết quả. Giải thích bằng tiếng Việt dễ
hiểu, giữ English terminology, thêm câu tiếng Anh khi hữu ích cho việc trình
bày với giáo sư. Không đưa checklist chung chung hoặc chuyển mục tiêu nghiên
cứu sang hướng khác. Mọi thông số phải có nguồn hoặc được ghi rõ là đề xuất
engineering cần kiểm chứng; không biến một đề xuất cũ thành quyết định của tôi.

## Dự án và mục tiêu

Repo: https://github.com/dvbao/eit-cn0565, branch main.
Local workspace trên macOS: /Users/baodang/eit-cn0565.

Ứng dụng dài hạn là post-stroke dysarthria và impaired facial-muscle function
liên quan speech production. Đây là mục tiêu nghiên cứu, không có nghĩa mọi
dysarthria đều do muscle weakness. Tôi muốn dùng EIT/bioimpedance để quan sát
thay đổi khi làm facial tasks.

Paper đầu tiên ưu tiên task recognition với unobtrusive electrode placement;
một vài tasks hữu ích có thể đủ để bắt đầu, nhưng novelty/publishability phải
được đánh giá bằng prior art và thiết kế validation. Ultimate goal là spatial
information/3D EIT reconstruction, rồi nghiên cứu khả năng xác định vùng/cơ
hoạt động kém. Individual-muscle specificity và phần trăm impairment chưa
được định nghĩa hoặc chứng minh; không hứa rằng tăng số electrodes là đủ.

Yêu cầu HIỆN TẠI của giáo sư: thu reference lúc nghỉ, thu lúc làm task, rồi xem
có khác biệt không và khác biệt có lặp lại không. Ưu tiên một pilot raw-data
rest–task trước; vẫn giữ roadmap reconstruction. Không bắt tôi hoàn tất mọi
validation của ảnh 3D mới được kiểm tra measurement differences.

## Hardware, constraints và trạng thái thật

Tôi có EVAL-CN0565 và gold-cup electrodes. First collection dùng 16 cups.
Board tối đa 24 electrode connections qua hai ADG2128, không phải 24 ADC
channels đồng thời. Tôi chấp nhận placement dưới cằm, bờ hàm, trước/sau tai,
thái dương và trán; thiết bị cuối tránh trực tiếp vùng má/môi như orbicularis
oris/zygomaticus. Tôi cũng đã chấp nhận near-muscle comparator và remote
layout ở hai sessions riêng, mỗi session 16 cups. Layout cụ thể còn là
candidate, chưa optimized/validated. Temporary EMG và camera được chấp nhận
làm reference/QC. Tôi muốn self-test feasibility trước; chưa có human data
được xác minh. Thông tin mới nhất là không có lab cho self-test hiện tại,
dù trước đây tôi từng nói có khả năng recruitment/lab support về sau.

Cup model/diameter, contact medium, cable orientation/continuity, live URI,
frequency/amplitude/current và safety của assembled system chưa được xác
minh. Không suy an toàn từ tên eval board, self-testing hay settings của
paper khác; cũng không chỉ nhắc lại warnings mà không giúp hoàn thành các
bước software/bench an toàn trong scope.

Schematic P1 có 30 chân: pins 3–14 = X0–X11; 17–28 = X12–X23; pins
1,2,15,16,29,30 = GND_ISO, không tự nối body-ground cup. Current proposal dùng
X0–X15, còn X16–X23 không dùng. Dây/contact không cố định là inject hoặc sense;
crosspoint switches đổi F+/F−/S+/S− theo patterns. Rest reference là dữ liệu,
không phải một cup reference như EMG.

## Dữ liệu và code hiện có

- scripts/eit_sim_playground.py: simulation BP/JAC/GREIT, hardware-free.
- scripts/cn0565_capture.py: logger, --mock hoặc live URI. Với 16 cups,
  force_distance=sense_distance=1: 16 force pairs × 13 sense pairs = 208
  sequential patterns/frame; output (208,2) real/imaginary readings.
- Logger lưu PREFIX.voltages.csv, frames.csv, events.csv và meta.json:
  pin/site map, exact sequence, frame start/end timestamps, terminal cues,
  settings, completion status, acquisition duration và start-to-start timing.
  Không có per-pattern timestamps hoặc logged current từng pattern.
- scripts/cn0565_prepare_difference.py: chọn complete stable rest/task frames,
  optional post-rest; componentwise median, v0/v1/delta và descriptive metrics.
- scripts/cn0565_plot_difference.py: time course và 208 signed real/imaginary
  differences; đây không phải anatomical reconstruction.
- tests/test_cn0565_capture.py: 8 tests đã pass offline; không phải hardware,
  physiological hoặc image-localization validation. Mock chỉ test file format,
  không mô phỏng cơ mặt. Không dùng mock timing để chọn human hold duration.

Data hiện là raw complex voltage-mode readings, chưa calibrated volts/ohms
hay muscle conductivity. CN0565 voltage excitation cố định không đảm bảo
current cố định. ΔV không tự bằng ΔZ; reference subtraction không cô lập pure
muscle activation. Geometry, contact, jaw/tongue/air, blood và motion vẫn có
thể thay đổi theo task. Repeatability một mình không loại contact artifacts.

Frame phải nằm hoàn toàn trong stable rest/hold. Cue không phải actual onset;
dùng video với clock/marker chung để loại transition frames. Mỗi trial dùng
pre-rest gần ngay trước task, có post-rest và rest-only controls. Chưa có
frame timing thật nên timing 5 s chưa được chứng minh đủ.

Stock examples dùng default 2D disk và thường v0=ones, không phải real rest.
Board sequence lưu (F+,S+,S−,F−); pyEIT standard sense-pair convention ngược
thứ tự board trong local check. Cần protocol/sign/known-load verification,
không tự flip data rồi khẳng định đúng. Local pyEIT dùng simple-electrode,
unit-current forward model. Không đưa dữ liệu mặt vào disk model rồi gọi ảnh
là facial anatomy. Partial-boundary EIT có prior art nhưng không chứng minh
candidate tai–hàm này đủ sensitivity. 3D model/current/contact matching và
known-target validation là các bước phát triển tiếp theo.

## Tài liệu cần đọc trước

1. docs/research-memory.md — đọc hết, ưu tiên các clarifications mới nhất.
2. docs/cn0565-rest-task-first-look.md.
3. docs/cn0565-capture-and-reconstruction-gates.md.
4. docs/protocols/c16r-p1-wiring-proposal.json và các scripts ở trên.
5. docs/facial-bioimpedance-models-placement-novelty.md và
   docs/facial-eit-feasibility-review.md.
6. docs/facial-bioimpedance-pilot-01.md và protocols: có older M08 proposals;
   không trộn M08 với current 208-pattern logger. 24-electrode proposals cũ
   trong archive không phải current first collection.
7. papers/tasks/, papers/electrodes_placement/, papers/EIT related works/ và
   cn0565-designsupport/. Đọc original papers/schematic khi cần proof.

Prior art quan trọng gồm Facial Gesture Recognition Using Bio-impedance
Sensing; Soft electrodes for simultaneous bio-potential and bio-impedance
study of the face; Modelling and analysis of electrical impedance myography
of the lateral tongue; Optimizing Electrode Positions in Electrical
Impedance Tomography; facial task atlas DOI 10.1371/journal.pone.0254932.
Facial bioimpedance có prior art: không claim "chưa ai làm trên mặt".
Task atlas là sEMG, không phải proof của EIT electrode sensitivity.

Trong lần kiểm tra macOS gần nhất, python3 và .venv-sim đều chưa có adi;
.venv-sim có pyeit. Chưa thấy cổng USB serial CN0565 trong /dev/cu.*. Đây là
snapshot, cần kiểm tra lại. cn0565-env/Scripts/python.exe và bootstrap .ps1
là Windows, không chạy trực tiếp trong macOS zsh. Không giả định simulator
environment đã đủ để giao tiếp hardware.

## Tôi muốn bạn làm ngay

Đọc các files trên nếu truy cập được; nếu không, nói đúng những files cần
upload. Sau đó tóm tắt confirmed facts, proposals và missing evidence, rồi
đưa tôi BƯỚC ĐẦU TIÊN cụ thể để tiến tới first rest–task capture. Đi từng bước
với lệnh macOS đúng, expected output và tiêu chí pass/fail. Chỉ hỏi những
thông tin thực sự còn thiếu, không hỏi lại mục tiêu/count/material đã chốt.

Giúp tôi nối toàn bộ pipeline: P1 pin → labeled lead → actual skin landmark
và anatomical context → force/sense sequence → timing/cues → stable frames
→ v0/v1/delta → noise/drift/repeatability → reconstruction roadmap. Đừng gán
một cup remote cho một cơ hoặc pattern ID cho một pixel. Với mỗi placement,
parameter và claim, nói rõ paper nào hỗ trợ trực tiếp, đâu là inference,
và experiment/simulation nào có thể bác bỏ hoặc xác nhận. Khi sửa code/docs,
verify bằng tests và cập nhật memory, tách observed results khỏi proposals.
