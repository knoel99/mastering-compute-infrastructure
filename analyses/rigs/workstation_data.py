H = 3 * 8760
E = 0.2001

CONFIGS = [
    ("1 GPU · Qwen3.8-27B", 22801.67, 0.55, [(720, 8)], "#1f77b4"),
    ("2 GPU · Qwen3.8-Flash-Next", 40924.17, 0.80, [(1610, 32)], "#ff7f0e"),
    ("3 GPU · GLM-5.3-Flash", 59114.17, 1.10, [(451, 8)], "#2ca02c"),
    ("4 GPU · GLM-5.3-Flash (EXL3)", 73075, 1.40, [(1087, 16)], "#9467bd"),
    (
        "DGX Station · Qwen3.8-27B BF16",
        105000,
        1.60,
        [(3218.9, 3218.9 / 68.0), (4211.7, 4211.7 / 34.9)],
        "#d62728",
    ),
]


def load_rows():
    rows = []
    for name, price, kilowatts, points, color in CONFIGS:
        hourly = price / H + kilowatts * E
        curve = sorted((total / users, total * 3600 / hourly / 1e6) for total, users in points)
        rows.append((name, color, hourly, curve))
    return rows
