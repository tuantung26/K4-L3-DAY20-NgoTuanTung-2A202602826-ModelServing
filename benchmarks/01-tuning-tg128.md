# 01 - Tune: thread-count sweep

Model `Qwen3.5-0.8B-Q4_K_M.gguf` · host `Windows-AMD64` · llama.cpp `b10488`
CPU: **10 physical · 16 logical** cores · `ngl=0` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 14.9 | 31% |
| 5 | 47.0 | 97% |
| 10 | 48.3 | 100% |
| 16 | 41.1 | 85% |
| 32 | 16.9 | 35% |

**Best**: `-t 10` at 48.3 tok/s
**Slowest tested**: `-t 1` at 14.9 tok/s (3.24x spread)
**Against the physical-core default** (`-t 10`, 48.3 tok/s): 1.00x

Use this in your run:

```bash
LAB_N_THREADS=10 make bench
```

## Your explanation 

Nhận xét: Điểm uốn (knee) của đường cong tốc độ nằm ở `10 threads` (tương đương đúng số core vật lý của máy). Từ 1 đến 10 threads, tốc độ tăng rất rõ (từ 14.9 lên 48.3 tok/s). Tuy nhiên khi vượt quá 10 lên 16 (số core logic) hay 32 (oversubscribe), tốc độ decode lại tụt mạnh. Điều này là do giai đoạn decode bị giới hạn bởi Memory Bandwidth chứ không phải Compute. Khi có quá nhiều thread dư thừa (logical cores chia sẻ tài nguyên với physical cores), chúng không giúp tính toán thêm được gì mà chỉ gây ra hiện tượng tranh chấp (contention) khi cùng truy xuất vào các memory channel, dẫn đến throughput tổng thể bị giảm.
