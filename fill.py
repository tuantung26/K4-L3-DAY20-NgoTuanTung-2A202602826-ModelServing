import os
import codecs
import re

def fix_file(filepath, replacement_text):
    try:
        with codecs.open(filepath, 'r', 'utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with codecs.open(filepath, 'r', 'cp1252') as f:
            content = f.read()
    
    # Replace anything after '## Your ... (required -- replace this line)'
    match = re.search(r'(## Your [^\n]+ \(required -- replace this line\))', content)
    if match:
        content = content[:match.end()] + '\n\n' + replacement_text + '\n'
        
    with codecs.open(filepath, 'w', 'utf-8') as f:
        f.write(content)

obs_01 = "Nhận xét: Bản UD-Q2_K_XL (2-bit) nhỏ hơn khoảng 0.11 GB (0.39 GB so với 0.50 GB của Q4_K_M), nhưng tốc độ decode (TPOT) gần như không đổi (~48.2 tok/s so với ~48.6 tok/s). Vì tốc độ không được cải thiện đáng kể và RAM dư dả cho model 0.5 GB, bản Q4_K_M (4-bit) sẽ là lựa chọn tốt hơn do giữ được chất lượng câu trả lời tốt mà không bị giảm tốc độ decode."
fix_file('benchmarks/01-quickstart-results.md', obs_01)

obs_02 = "Nhận xét: Server bão hòa ở dưới mức 50 user. Bằng chứng là khi số lượng user tăng 5 lần (từ 10 lên 50), thông lượng (throughput) chỉ đạt 0.95x so với kỳ vọng tuyến tính, và độ trễ P95 tăng vọt gấp 3.83 lần. Effective concurrency đạt 30.1 vượt xa số lượng slot (--parallel 4). Điều này chứng tỏ lượng tải dư thừa đã biến thành thời gian xếp hàng (queue time). Để tăng goodput, nên tăng thông số `--parallel` (số lượng batching slot) vì hiện tại server đang bị giới hạn số lượng request được xử lý song song, dẫn tới ứ đọng nhiều ở hàng đợi."
fix_file('benchmarks/02-server-results.md', obs_02)

obs_batch = "Nhận xét: Đỉnh của batch width (n_busy_slots_per_decode) đạt 3.88 trên 4 slots (97%). Con số này rất sát với giới hạn 4 slot và đồng nhất với effective concurrency lớn (30.1) được đo ở `02-server-results.md`. Cả hai số liệu này đều chứng minh hệ thống đang phải gom gần tối đa công suất các slot để giải quyết lượng request bị quá tải."
fix_file('benchmarks/02-server-batching-u50.md', obs_batch)

obs_integ = """- N16 Cloud/IaC: stub
- N17 Data pipeline: stub
- N18 Lakehouse: stub
- N19 Vector + features: stub

Nhận xét: Công đoạn chiếm nhiều thời gian nhất là `llm` (100% thời gian) đúng như kỳ vọng vì embed và retrieve hiện đang chạy local keyword search (0.0ms). Nếu phải giảm độ trễ pipeline đi một nửa, tôi sẽ tập trung vào việc giảm độ trễ của phần `llm` bằng cách chuyển sang các quantization nhẹ hơn, tối ưu thread/batching size hoặc áp dụng semantic cache cho server."""
fix_file('benchmarks/03-integration-results.md', obs_integ)

obs_tune = "Nhận xét: Điểm uốn (knee) của đường cong tốc độ nằm ở `10 threads` (tương đương đúng số core vật lý của máy). Từ 1 đến 10 threads, tốc độ tăng rất rõ (từ 14.9 lên 48.3 tok/s). Tuy nhiên khi vượt quá 10 lên 16 (số core logic) hay 32 (oversubscribe), tốc độ decode lại tụt mạnh. Điều này là do giai đoạn decode bị giới hạn bởi Memory Bandwidth chứ không phải Compute. Khi có quá nhiều thread dư thừa (logical cores chia sẻ tài nguyên với physical cores), chúng không giúp tính toán thêm được gì mà chỉ gây ra hiện tượng tranh chấp (contention) khi cùng truy xuất vào các memory channel, dẫn đến throughput tổng thể bị giảm."
fix_file('benchmarks/01-tuning-tg128.md', obs_tune)
