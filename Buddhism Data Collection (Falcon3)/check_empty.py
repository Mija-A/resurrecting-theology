import csv
with open('results/wvs_Buddhist_Yin_Shun_falcon3-7b_1rounds.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['numeric_response'].strip() == '':
            print(f"qid={row['question_id']} raw={row['raw_response'][:50]!r}")
