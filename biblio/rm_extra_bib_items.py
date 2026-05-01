import os
import regex

from pathlib import Path

def find_tex_files(directory):
    return list(Path(directory).glob('*.tex'))

def find_citations(tex_files):
    citations = set()
    for file_name in tex_files:
        with open(file_name, 'r', encoding='utf-8') as f:
            content = f.read()
            cited_keys = regex.findall(r"(?<!\\)%.+(*SKIP)(*FAIL)|\\(?:no)?citep?\{(?P<author>(?!\*)[^{}]+)\}", content)
            for keys in cited_keys:
                keys = regex.sub(r'\s+', '', keys)  # Remove any whitespace within the citation keys
                citations.update(keys.split(','))
    return citations

def process_bib_file(bib_file, citations):
    with open(bib_file, 'r', encoding='utf-8') as f:
        content = f.read()

    citation_keys = {citation.lower() for citation in citations}
    entries = regex.split(r'(?m)(?=^@\w+\s*\{)', content)
    updated_entries = []

    for entry in entries:
        match = regex.match(r'(?s)^@(?P<type>\w+)\s*\{\s*(?P<id>[^,\s]+)', entry.strip())
        if match and match.group('id').lower() in citation_keys:
            updated_entries.append(entry.strip())

    with open(f"{bib_file}.new", 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(updated_entries))
        f.write('\n')

def main():
    bib_file = "bibliography.bib"
    tex_directory = "../chapters"

    tex_files = find_tex_files(tex_directory)
    print(f"Searching for citations in files: {', '.join(map(str, tex_files))}")
    citations = find_citations(tex_files)
    print(f"Number of citations found: {len(citations)}")
    print(f"Found citations: {', '.join(citations)}")
    process_bib_file(bib_file, citations)

if __name__ == '__main__':
    main()
