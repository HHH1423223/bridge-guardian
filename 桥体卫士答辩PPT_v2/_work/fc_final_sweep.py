# -*- coding: utf-8 -*-
"""FACTCHECK final round: wildcard + 39-pattern sweep on the terminal build."""
import io, re, sys

P = r'C:\Users\CX\Documents\GitHub\bridge guardian\桥体卫士答辩PPT_v2\_work\pptx_text_r7.txt'
L = io.open(P, encoding='utf-8').read().splitlines()
raw = next(i for i, l in enumerate(L) if 'RAW XML SWEEP' in l)


def blk(ln):
    s = 0
    for j in range(ln):
        m = re.match(r'SLIDE (\d+)', L[j])
        if m:
            s = int(m.group(1))
    return s


print('=' * 72)
print('A. WILDCARD PATTERNS (regex, real CJK)')
print('=' * 72)
WILD = [
    r'同一.{0,4}生效参数',
    r'同一.{0,2}参数',
    r'口径一致',
    r'口径统一',
    r'分级口径统一',
    r'三端',
    r'同一份.{0,6}',
    r'15\.38',
    r'passed',
    r'全绿',
    r'0\s*failed',
    r'0\s*skipped',
    r'0\s*失败',
    r'0\s*跳过',
    r'零失败',
    r'零跳过',
    r'全部通过',
    r'判严重，',
    r'只存哈希',
    r'密码哈希',
    r'串口连续超时',
    r'同一份数据',
    r'同一份生效',
]
bad = 0
for w in WILD:
    vis = [(i + 1, L[i]) for i in range(raw) if re.search(w, L[i])]
    tot = [(i + 1, L[i]) for i in range(len(L)) if re.search(w, L[i])]
    tag = 'HIT ' if vis else 'ok  '
    if vis:
        bad += 1
    print('%s%-26s visible=%d raw_mirror=%d' % (tag, w, len(vis), len(tot) - len(vis)))
    for ln, t in vis:
        print('       L%-5d p%-2d %s' % (ln, blk(ln - 1), t.strip()[:130]))

print()
print('=' * 72)
print('B. 39-PATTERN SWEEP (substring, visible + notes)')
print('=' * 72)
PATS = ['15.38', '101 passed', 'passed in', '全绿', '0 failed', '0 skipped', '0 失败', '0 跳过',
        '零失败', '零跳过', '全部通过', '只存哈希', '明文', '密码哈希', '同一份数据',
        '同一份生效参数', '同一生效参数', '串口连续超时', '判严重，', '口径统一', '分级口径统一',
        '数字孪生', '机器学习', '人工智能', '大数据', '微应变', '高精度', '工程级精度',
        '真实桥梁应变监测', '我们', '团队', '领先', '革命性', '预测', '深度学习', '智能算法',
        '3D', '正常/预警/报警/严重/离线/恢复', '参数集中在 rules.py', '示意波形', '主跨 1420']
hits = 0
for p in PATS:
    vis = [(i + 1, L[i]) for i in range(raw) if p in L[i]]
    if vis:
        hits += 1
        print('HIT %-30r' % p)
        for ln, t in vis:
            print('       L%-5d p%-2d %s' % (ln, blk(ln - 1), t.strip()[:135]))
    else:
        print('ok  %-30r' % p)
print()
print('39-pattern sweep: patterns with visible hits = %d' % hits)
print('wildcard block  : patterns with visible hits = %d' % bad)
