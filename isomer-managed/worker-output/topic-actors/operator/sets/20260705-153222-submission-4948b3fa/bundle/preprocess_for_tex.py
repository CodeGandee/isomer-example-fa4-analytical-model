import re

in_path = 'revised-draft.md'
out_path = 'revised-draft-for-tex.md'

with open(in_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract title from first level-1 heading
title = None
if lines and lines[0].startswith('# '):
    title = lines[0][2:].strip()
    lines = lines[1:]

out_lines = []
if title:
    out_lines.append('---\n')
    out_lines.append(f'title: "{title}"\n')
    out_lines.append('---\n')
    out_lines.append('\n')

# Process remaining lines
for line in lines:
    # Shift heading levels down by one and strip leading numbers
    if line.startswith('## '):
        text = line[3:].rstrip('\n')
        # Strip leading section number like "1 Introduction" → "Introduction"
        text = re.sub(r'^(\d+\.?\d*\s+)', '', text)
        if text.lower() == 'abstract':
            out_lines.append(f'# {text} {{.unnumbered}}\n')
        else:
            out_lines.append(f'# {text}\n')
    elif line.startswith('### '):
        text = line[4:].rstrip('\n')
        text = re.sub(r'^(\d+\.\d+\s+)', '', text)
        out_lines.append(f'## {text}\n')
    elif line.startswith('#### '):
        text = line[5:].rstrip('\n')
        text = re.sub(r'^(\d+\.\d+\.\d+\s+)', '', text)
        out_lines.append(f'### {text}\n')
    else:
        out_lines.append(line)

# Join and apply replacements
text = ''.join(out_lines)
text = text.replace('.svg', '.pdf')
# Remove baked-in figure numbers from image alt text so LaTeX numbers figures automatically
text = re.sub(r'!\[Figure \d+: ', '![', text)
text = text.replace('≤', 'LEQ_SIGN')
text = text.replace('≥', 'GEQ_SIGN')
text = text.replace('μ', 'MU_SIGN')

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(text)

print(f'wrote {out_path}')
