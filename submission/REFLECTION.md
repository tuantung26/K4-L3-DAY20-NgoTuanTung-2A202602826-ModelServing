# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.
>
> `make verify` sẽ fail nếu còn placeholder chưa điền. Đó là cố ý.

**Họ Tên:** Ngô Tuấn Tùng
**MSSV:** 2A202602826
**Cohort:** A20-K4
**Ngày submit:** 2026-10-06

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

- **OS:** Windows 11 (AMD64)
- **CPU:** 12th Gen Intel(R) Core(TM) i7-12650H
- **Cores:** 10 physical / 16 logical
- **CPU extensions:** AVX2
- **RAM:** 15.7 GB
- **Accelerator:** NVIDIA GeForce RTX 4050 Laptop GPU (6141 MiB)
- **llama.cpp asset đã tải:** prebuilt release b10488
- **Model đã dùng:** Qwen3.5 0.8B (`LAB_MODEL=qwen35-0.8b`)
- **Quantization:** Q4_K_M và UD-Q2_K_XL

**Chạy ở đâu:** laptop của tôi
_(Nếu dùng cloud fallback: nói rõ vì sao — RAM < 8 GB, setup fail, v.v. Không mất điểm.)_

**Setup story** (≤ 80 chữ): 
Chạy hoàn toàn bằng môi trường PowerShell trên Windows. Lỗi encode font tiếng Việt trên cmd được khắc phục bằng cách thiết lập môi trường `$env:PYTHONIOENCODING="utf-8"`.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|---|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 3566 | 682 / 721 | 20.6 / 22.0 | 1931 / 2065 / 2065 | 48.6 |
| UD-Q2_K_XL | 0.39 | 2013 | 719 / 808 | 20.8 / 22.0 | 2026 / 2171 / 2171 | 48.2 |

**Quan sát** (≤ 60 chữ): 
Bản UD-Q2_K_XL (2-bit) nhỏ hơn khoảng 0.11 GB so với Q4_K_M, nhưng tốc độ decode (TPOT) gần như không đổi (~48.2 tok/s so với ~48.6 tok/s). Vì máy vẫn đủ RAM và tốc độ không được cải thiện, hy sinh chất lượng (bản 2-bit) là không đáng.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 1.04 | 8200 | 12000 | 14000 | 8.5 | 0.0% |
| 50 | 0.99 | 31000 | 46000 | 50000 | 30.1 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 0.95×
- **P95 tăng:** 3.83×
- **Effective concurrency ở 50 users:** 30.1 so với `--parallel` = 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang
chạy): 3.88 / 4 slots

**Saturation reading** (≤ 80 chữ): 
Server bão hòa ở dưới 50 user. Thông lượng RPS đi ngang (0.95x) trong khi P95 tăng 3.83 lần, chứng tỏ tải dư thừa bị dồn vào hàng đợi (queue time). Knob cần thay đổi trước tiên là `--parallel` để tăng batching capacity, giúp xử lý đồng thời nhiều req hơn.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | Cloud | stub |
| N17 Data pipeline | Data pipeline | stub |
| N18 Lakehouse | Lakehouse | stub |
| N19 Vector + features | Vector | stub |
| N20 Serving | `llama-server` | real |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.0 ms
- llm: 5848.4 ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Reflection** (≤ 60 chữ): 
Bottleneck nằm hoàn toàn ở `llm` đúng như kỳ vọng vì retrieval là stub (0.0ms). Nếu phải giảm latency 2x, tôi sẽ tối ưu `llm` (dùng model nhỏ hơn hoặc cache prompt) trước vì đây là thành phần đóng góp toàn bộ vào độ trễ.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Điều chỉnh số lượng Thread từ số logic (16) xuống số physical cores (10)

```
before:  41.1 tok/s (16 threads - logical cores)
after:   48.3 tok/s (10 threads - physical cores)
speedup: 1.18×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Giai đoạn decode của LLM bị giới hạn hoàn toàn bởi Memory Bandwidth thay vì Compute (FLOPs). Việc tăng quá số thread vật lý (10 core) lên thành 16 hay 32 thread chỉ khiến các thread phải tranh chấp (contention) khi truy xuất dữ liệu từ RAM. Vì resource bottleneck là đường truyền chứ không phải xử lý toán học, nên việc thêm overhead quản lý thread logic đã làm cho tốc độ sụt giảm đi đáng kể.

---

## 6. Bonus  *(optional — tối đa 10 điểm)*

> Bỏ trống nếu không làm. Xem `docs/bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** 

**Numbers:**

```
before:  
after:   
speedup: 
```

**Điều này nói lên gì mà deck chưa nói:**



---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

Ngạc nhiên khi model Qwen 0.8B chạy rất mượt và quá trình continuous batching giúp gom yêu cầu một cách triệt để mà không cần VRAM lớn.

---

## 8. Self-check trước khi push

- [x] `hardware.json` committed
- [x] `models/active.json` committed
- [x] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [x] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [x] `benchmarks/02-server-results.md` committed (`make load-report`)
- [x] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [x] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [x] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [x] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md`
      đã được thay bằng nhận xét của bạn
- [x] 5 screenshots trong `submission/screenshots/`
- [x] `make verify` → **exit 0**
- [x] Repo tên đúng mẫu `K4-L3-DAY20-HoVaTen-MSSV-ModelServing` (xem `docs/SUBMISSION.md`)
- [x] Repo GitHub ở chế độ **public**
- [x] Đã push và paste public URL vào VinUni LMS **trước 23:59 (UTC+7) ngày làm lab**
- [x] **Không** commit `models/*.gguf`, `runtime/` hay `.env` (đã có trong `.gitignore`)

---

## 9. Khai báo sử dụng AI  *(xem `docs/RULES.md` §3)*

Sử dụng AI để hỗ trợ fix lỗi UTF-8 trên powershell và giúp tổng hợp số liệu vào file Markdown.
