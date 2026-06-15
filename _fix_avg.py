import sys

filepath = "app/mock_mongo.py"
with open(filepath, "r") as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if i == 341 and "final_groups = []" in line:
        new_lines.append(line)
        new_lines.append("                    avg_fields = set()\n")
    elif i == 345 and "real_field = f[2:-10]" in line:
        new_lines.append(line)
        new_lines.append("                            avg_fields.add(real_field)\n")
    elif i == 348 and "if vals:" in line:
        new_lines.append(line)
        new_lines.append("                            else:\n")
        new_lines.append("                                clean[real_field] = 0\n")
    elif i == 350 and "else:" in line.strip():
        new_lines.append("                       elif f not in avg_fields:\n")
    else:
        new_lines.append(line)
    i += 1

with open(filepath, "w") as f:
    f.writelines(new_lines)

print("FIXED_OK")
