import csv

for tag in ('full', 'bbq'):
    print(f'--- {tag}: adaptive poison@k ---')
    rows = list(csv.DictReader(open(f'results/{tag}/adaptive.csv', encoding='utf-8')))
    lams = sorted({float(r['lambda']) for r in rows})
    print('  defense'.ljust(20) + ''.join(f'{l:>8.2f}' for l in lams))
    for d in ('multi_query', 'manifold', 'repr_conserving'):
        sub = {float(r['lambda']): r for r in rows if r['defense'] == d}
        vals = ''.join(f"{float(sub[l]['poison_in_topk']):>8.3f}" for l in lams)
        print(f'  {d:<18s}' + vals)
    # usage is a property of lambda, not of the defense
    sub = {float(r['lambda']): r for r in rows if r['defense'] == 'multi_query'}
    if 'usage' in rows[0]:
        print('  usage (cos to orig)'.ljust(20)
              + ''.join(f"{float(sub[l]['usage']):>8.3f}" for l in lams))
    print()
