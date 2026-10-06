# 01 - Measure: latency baseline

Model `Qwen3.5 0.8B` · host `Windows-AMD64` · llama.cpp `b10488`
Settings: `threads=10` `ngl=0` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `Q4_K_M` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| Q4_K_M | 0.50 | 2139 | 646 / 736 | 20.2 / 21.8 | 1886 / 2017 / 2017 | 49.5 |
| UD-Q2_K_XL | 0.39 | 2020 | 713 / 1402 | 21.1 / 24.7 | 2010 / 2903 / 2903 | 47.3 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.05x SLOWER** than `Q4_K_M` here, despite being 0.11 GB smaller. That is a real result, not a mistake: fewer bits only buys speed when decode is limited by memory bandwidth. On a machine that is compute-limited instead — few cores, no GPU offload — the extra dequantization work of a heavily-quantized format can cost more than the bytes it saves. Say which case yours is.

## Your observation 

Nhận xét: Bản UD-Q2_K_XL (2-bit) nhỏ hơn khoảng 0.11 GB (0.39 GB so với 0.50 GB của Q4_K_M), nhưng tốc độ decode (TPOT) gần như không đổi (~48.2 tok/s so với ~48.6 tok/s). Vì tốc độ không được cải thiện đáng kể và RAM dư dả cho model 0.5 GB, bản Q4_K_M (4-bit) sẽ là lựa chọn tốt hơn do giữ được chất lượng câu trả lời tốt mà không bị giảm tốc độ decode.
