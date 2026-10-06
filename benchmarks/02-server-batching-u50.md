# 02 - Continuous batching under load (u50)

Host `Windows-AMD64` · `--parallel 4` · 13 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.88 of 4 slots (97%) |
| `requests_processing` | 4 |
| `requests_deferred` | 53 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 7497 |

Highest sampled value was **3.88 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Your observation 

Nhận xét: Đỉnh của batch width (n_busy_slots_per_decode) đạt 3.88 trên 4 slots (97%). Con số này rất sát với giới hạn 4 slot và đồng nhất với effective concurrency lớn (30.1) được đo ở `02-server-results.md`. Cả hai số liệu này đều chứng minh hệ thống đang phải gom gần tối đa công suất các slot để giải quyết lượng request bị quá tải.
