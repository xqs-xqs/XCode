# Exported run results

One row per run and cell. `resolved` is decided by hidden tests on a fresh tree; `claimed` counts runs that ended with stop_reason=completed. A run still in progress shows fewer tasks than its set.

| run | cell | developer | reviewer | resolved | claimed | tokens/run | total tokens |
|---|---|---|---|---:|---:|---:|---:|
| lite-v1-t1 | pipeline | deepseek/deepseek-v4-flash | glm/glm-5.3 | 25/25 | 18 | 144805 | 3620121 |
| lite-v1-t1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 24/25 | 25 | 37992 | 949793 |
| lite-v1-t1 | single-review | deepseek/deepseek-v4-flash | glm/glm-5.3 | 24/25 | 23 | 49939 | 1248479 |
| hard-probe-single-1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 11/12 | 6 | 30192 | 362310 |
| probe-nothink-single-1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 37/37 | 37 | 37270 | 1378976 |
| audit-v2-t1 | pipeline | deepseek/deepseek-v4-flash | glm/glm-5.3 | 12/12 | 4 | 191953 | 2303435 |
| audit-v2-t1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 12/12 | 12 | 115497 | 1385964 |
| audit-v2-t1 | single-review | deepseek/deepseek-v4-flash | glm/glm-5.3 | 12/12 | 9 | 122128 | 1465540 |
| audit-v2-nothink-single-1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 12/12 | 12 | 84238 | 1010859 |
| weak-qwen3.8-flash-single-1 | single | bailian/qwen3.8-flash | glm/glm-5.3 | 12/12 | 12 | 124612 | 1495340 |
| weak-glm-5.3-flash-single-1 | single | bailian/glm-5.3-flash | glm/glm-5.3 | 11/12 | 10 | 50100 | 601194 |
| swe-strong-single-1 | single | deepseek/deepseek-v4-flash | glm/glm-5.3 | 13/26 | 25 | 362196 | 9417092 |
| swe-weak-qwen-single-1 | single | qwen3.8-flash |  | 5/16 | 12 | 364371 | 5829936 |
| swe-weak-qwen-single-review-1 | single-review | qwen3.8-flash |  | 2/9 | 2 | 406999 | 3662991 |
