with open('properties/broker_views.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with 'unread_count': 0,    })
# Keep everything up to and including the return statement
# Delete everything after that until the next function definition (starting with @login_required)

new_lines = []
skip = False
found_return = False

for i, line in enumerate(lines):
    if "'unread_count': 0," in line:
        new_lines.append(line)
        if i + 1 < len(lines) and '})' in lines[i + 1]:
            new_lines.append(lines[i + 1])
            skip = True
            found_return = True
            continue
    elif skip and line.strip().startswith('@'):
        skip = False
        new_lines.append(line)
    elif skip:
        continue
    else:
        new_lines.append(line)

with open('properties/broker_views.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Removed dead code after return statement')
