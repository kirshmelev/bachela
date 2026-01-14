# Copilot Instructions for BMSTU Diploma LaTeX Template

This repository is a LaTeX template for BMSTU diploma and presentation, designed for Russian academic standards. It automates builds, bibliography, and release workflows for both Linux and Windows environments.

## Project Architecture
- **Main files:**
  - `diploma.tex`: Main thesis file
  - `presentation.tex`: Presentation file
- **Chapters:** Located in `chapters/` (e.g., `chapter_1.tex`, `introduction.tex`).
- **Bibliography:**
  - `biblio/bibliography.bib`: Main bibliography file
  - `biblio/gost2008n.bst`: GOST 2008 BibTeX style
  - `biblio/rm_extra_bib_items.py`: Python utility to clean unused bib entries
- **Settings:** `settings/preamble.tex` contains LaTeX preamble and customizations.
- **Images:** All figures and logos in `images/`.
- **Build scripts:**
  - `Makefile` (Linux/macOS)
  - `makewin.bat` (Windows)
  - `install/install.sh`: Linux setup script
  - `install/Dockerfile`: Containerized build environment

## Developer Workflows
- **Linux Build:**
  - Run `sudo bash install/install.sh` to set up dependencies.
  - Use `make`, `make diploma`, or `make presentation` to build outputs.
- **Windows Build:**
  - Install Docker Desktop and Ubuntu (see README).
  - Run `makewin.bat` to build all outputs.
  - For single output, move other `.tex` files to `extra/` or edit `makewin.bat`.
- **Bibliography Management:**
  - Add sources to `biblio/bibliography.bib` using DOI as entry key.
  - Run `python biblio/rm_extra_bib_items.py` to clean unused entries (output: `bibliography.bib.new`).
- **Release Workflow:**
  - Tag a commit with `v*` (e.g., `v1.0`) and push to trigger GitHub Actions release.

## Project-Specific Conventions
- **No spaces in `.tex` filenames.**
- **Use Times New Roman font.**
- **Bibliography must follow GOST 2008 standard.**
- **DOI as BibTeX entry key is required for deduplication.**
- **All builds are containerized; local LaTeX installation is not required.**

## Integration Points
- **Docker:** Used for reproducible builds and GitHub Actions releases.
- **GitHub Actions:** Automated release creation on tag push.
- **Python:** Used for bibliography cleanup.

## Key Files & Directories
- `diploma.tex`, `presentation.tex`: Entry points for builds
- `chapters/`: All thesis chapters
- `biblio/`: Bibliography and utilities
- `settings/preamble.tex`: LaTeX configuration
- `Makefile`, `makewin.bat`: Build automation
- `install/`: Container setup scripts

## Example Patterns
- To cite a source: `... в работе~\cite{DOI}`
- To clean bibliography: `python biblio/rm_extra_bib_items.py`
- To build on Linux: `make diploma`
- To build on Windows: run `makewin.bat`

---
For unclear or incomplete sections, please provide feedback to improve these instructions.