import pandas as pd

# Read HTML table from a webpage or an HTML file
html_table = pd.read_html("index.html")[0]  # Change the file name or URL as needed

# Convert HTML table to Markdown format
markdown_table = html_table.to_markdown(index=False)

markdown_file_name = "qcrypto.md"

with open(markdown_file_name, "w", encoding="utf-8") as file:
    file.write(markdown_table)