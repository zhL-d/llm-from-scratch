import re
import ast

with open('temp-diff.txt', 'r', encoding='utf-8') as f:
    content = f.read()

sections = content.split('---------------------')
if len(sections) < 2:
    print("Not enough sections found.")
    exit(1)

def extract_pair_counts(section):
    match = re.search(r'pair_counts:\s*({.*?})', section, re.DOTALL)
    if match:
        return ast.literal_eval(match.group(1))
    return {}

dict1 = extract_pair_counts(sections[0])
dict2 = extract_pair_counts(sections[1])

# Find keys only in dict1, only in dict2, and keys with different values
only_in_1 = {k: dict1[k] for k in dict1 if k not in dict2}
only_in_2 = {k: dict2[k] for k in dict2 if k not in dict1}
diff_values = {k: (dict1[k], dict2[k]) for k in dict1 if k in dict2 and dict1[k] != dict2[k]}

print("Keys only in first section:", only_in_1)
print("Keys only in second section:", only_in_2)
print("Keys with different values:", diff_values)