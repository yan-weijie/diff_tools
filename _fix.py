f = open(r'd:\working\xiTest\demo\app.py', 'r', encoding='utf-8')
lines = f.readlines()
f.close()

# Fix lines 150-152 (0-indexed: 149-151): broken regex
# Replace 3 broken lines with 1 correct line
new_line = "        idx_m = _re.match(r'^\\[(\\d+)\\]$', token)\n"
lines[149:152] = [new_line]

f = open(r'd:\working\xiTest\demo\app.py', 'w', encoding='utf-8')
f.writelines(lines)
f.close()
print('Fixed. Total lines:', len(lines))