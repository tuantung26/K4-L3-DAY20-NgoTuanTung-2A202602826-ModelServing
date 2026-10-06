# 02 - Serve: load test + saturation reading

Host `Windows-AMD64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=10` ·
`ngl=0`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 53 | 1.04 | 8200 | 12000 | 14000 | 8.5 | 0.0% |
| 50 | 57 | 0.99 | 31000 | 46000 | 50000 | 30.1 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **0.95x** (19% of linear) |
| P95 latency | **3.83x** |
| Effective concurrency at 50 users | 30.1 vs `--parallel 4` slots (occupancy/slot ratio 7.52) |

**Saturated.** Throughput delivered only 0.95x for 5x the offered load, and effective concurrency (30.1) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 0.95x while P95 moved 3.83x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

## Your reading 

Nhận xét: Server bão hòa ở dưới mức 50 user. Bằng chứng là khi số lượng user tăng 5 lần (từ 10 lên 50), thông lượng (throughput) chỉ đạt 0.95x so với kỳ vọng tuyến tính, và độ trễ P95 tăng vọt gấp 3.83 lần. Effective concurrency đạt 30.1 vượt xa số lượng slot (--parallel 4). Điều này chứng tỏ lượng tải dư thừa đã biến thành thời gian xếp hàng (queue time). Để tăng goodput, nên tăng thông số `--parallel` (số lượng batching slot) vì hiện tại server đang bị giới hạn số lượng request được xử lý song song, dẫn tới ứ đọng nhiều ở hàng đợi.
