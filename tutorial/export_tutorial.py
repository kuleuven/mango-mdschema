import re
import nbformat
from nbconvert import MarkdownExporter
from nbconvert.filters import strip_ansi

exporter = MarkdownExporter()

# Read the notebook file
with open('README.ipynb', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# Convert the notebook to a markdown
body, resources = exporter.from_notebook_node(nb)

# strip ansi escape sequences from the markdown output
output = strip_ansi(body)
# strip the xmode statements from the markdown output
output = output.replace("%xmode Minimal\n", '')
# strip extranaeous newlines from the markdown output
output = re.sub('\n{3,}', '\n\n', output)

# Write the markdown to REAMDE.md
with open('README.md', 'w', encoding='utf-8') as f:
    f.write(output)
