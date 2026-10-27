import json
import sys

with open(sys.argv[1], encoding='utf-8') as f:
    result = json.load(f)
print('# 强排自动回归报告\n')
print('数据类型：合成测试地块；非官方案例。\n')
print('| 范式 | 倾向 | 容积率 | 栋数 | 日照 |')
print('|---|---|---:|---:|---|')
for s in result['schemes']:
    m = s['metrics']
    print(f"| {s['mode']} | {s['objective']} | {m['achieved_far']:.4f} | {m['building_count']} | 未验证 |")
print('\n注意：几何初筛不代表法规、日照或消防合规。')
