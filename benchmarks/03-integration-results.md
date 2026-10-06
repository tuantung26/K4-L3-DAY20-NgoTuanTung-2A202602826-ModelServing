# 03 - Integrate: RAG pipeline run

Host `Windows-AMD64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.1 | 7040.5 | 7040.6 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.0 | 4583.1 | 4583.2 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.0 | 5921.6 | 5921.7 |

Mean per stage (ms): embed **0.0** · retrieve **0.0** ·
llm **5848.4** · total **5848.5**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Based on the provided context, **Goodput** is more useful than raw throughput because it focuses on **SLOs (Service Level Objects)** and **saturation**.

Here is the breakdown of why this makes Goodput superior:

*   **SLOs:** Goodput counts only requests per second that met specific targets (TTFT and TPOT). This ensures the system only processes requests that satisfy the agreed-upon quality stand

**What problem does PagedAttention actually solve?**

> PagedAttention solves the problem of **internal fragmentation in GPU memory** caused by storing key-value pairs in non-contiguous pages.

By using non-contiguous pages (often called "paged" or "paged attention"), the model avoids the wasted space that would otherwise exist if all KV cache entries were stored contiguously in a single contiguous block of memory. This allows the model to utilize more

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps when the **prefill operation is compute-bound** (requiring significant CPU/GPU cycles for the initial token generation) and the **decode operation is memory-bandwidth-bound** (requiring significant memory bandwidth for the final output).

In this scenario, the system can utilize **RadixAttention** to cache keys by token prefix in a trie structure. This allows the


## Which N16-N19 pieces are real 

_List each of N16, N17, N18, N19 as real or stubbed. Stubbing costs no points;
misrepresenting it does. Then answer: is the dominant stage above what you expected?
If you had to halve this pipeline's latency, which stage would you attack and why?_
