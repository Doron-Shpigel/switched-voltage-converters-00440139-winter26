# Dry Homeworks - LaTeX-Based Theoretical Exercises

This folder contains theoretical homework exercises written in Quarto with LaTeX support. Each homework is in its own subfolder (e.g., `hw01/`, `hw02/`).

## Structure

```
dry/
├── hw01/
│   └── hw01.qmd       # Homework 1 content
├── hw02/
│   └── hw02.qmd       # Homework 2 content
├── _quarto.yml        # PDF rendering configuration
├── generate-pdfs.sh   # Script to generate all PDFs
└── index.qmd          # Index page listing all homeworks
```

## Creating a New Homework

1. Create a new folder:
   ```bash
   mkdir hw03
   ```

2. Create a `.qmd` file in the folder:
   ```bash
   cd hw03
   touch hw03.qmd
   ```

3. Use this template:
   ```yaml
   ---
   title: "Homework 3 - Your Title"
   subtitle: "Course 00440139 - Winter 2026"
   date: today
   author: "Your Name"
   format:
     html:
       toc: true
       toc-depth: 2
       number-sections: true
   ---
   
   ::: {.callout-note}
   ## PDF Export
   To generate a PDF version of this homework, run:
   ```bash
   quarto render hw03.qmd --to pdf
   ```
   Note: Requires TeX installation (TinyTeX, TeXLive, or similar).
   :::
   
   ## Problem 1
   
   Your content here with LaTeX equations:
   
   Inline: $V_{out} = 5V$
   
   Display:
   $$
   D = \frac{V_{out}}{V_{in}}
   $$
   ```

4. Update `index.qmd` to add a link to the new homework:
   ```markdown
   - [Homework 3](hw03/hw03.qmd)
   ```

## Generating PDFs

### Prerequisites

You need a TeX installation to generate PDFs. Options:

1. **TinyTeX** (recommended for Quarto):
   ```bash
   quarto install tinytex
   ```

2. **TeXLive** (full installation):
   ```bash
   # Ubuntu/Debian
   sudo apt-get install texlive-full
   
   # macOS
   brew install --cask mactex
   ```

3. **MiKTeX** (Windows):
   Download from https://miktex.org/

### Single Homework PDF

To generate a PDF for a specific homework:

```bash
cd hw01
quarto render hw01.qmd --to pdf
```

This will create `hw01.pdf` in the same folder.

### All Homeworks at Once

To generate PDFs for all homeworks:

```bash
./generate-pdfs.sh
```

This script will:
- Find all homework folders (hw01, hw02, etc.)
- Render each `.qmd` file to PDF
- Report success or failure for each homework

## PDF Configuration

The `_quarto.yml` file in this directory configures PDF output settings:

- **Document class**: article
- **Paper size**: A4
- **Table of contents**: enabled
- **Section numbering**: enabled
- **Margins**: 1 inch all around
- **TeX source**: kept for debugging

You can customize these settings by editing `_quarto.yml`.

## LaTeX Features

### Common Math Symbols

- Inline math: `$V_{in}$` → $V_{in}$
- Display math: `$$E = mc^2$$` → Centered equation
- Fractions: `$\frac{a}{b}$` → $\frac{a}{b}$
- Subscripts: `$V_{out}$` → $V_{out}$
- Superscripts: `$x^2$` → $x^2$
- Greek letters: `$\alpha, \beta, \gamma$` → $\alpha, \beta, \gamma$

### Advanced Features

- **Aligned equations**:
  ```latex
  $$
  \begin{align}
  x &= y + z \\
  a &= b + c
  \end{align}
  $$
  ```

- **Matrices**:
  ```latex
  $$
  \begin{bmatrix}
  a & b \\
  c & d
  \end{bmatrix}
  $$
  ```

- **Cases**:
  ```latex
  $$
  f(x) = \begin{cases}
  x^2 & \text{if } x \geq 0 \\
  -x^2 & \text{if } x < 0
  \end{cases}
  $$
  ```

## Troubleshooting

### PDF Generation Fails

1. **Error: "No TeX installation detected"**
   - Install TinyTeX: `quarto install tinytex`
   - Or install TeXLive/MiKTeX manually

2. **Error: "Missing LaTeX package"**
   - TinyTeX will auto-install missing packages
   - For manual TeX: Install the required package using your TeX distribution's package manager

3. **Math not rendering**
   - Check that equations are properly enclosed in `$...$` or `$$...$$`
   - Escape special characters: `\$`, `\%`, `\&`, etc.

### Website Preview Issues

To preview the website with live reload:

```bash
cd ../..  # Go to project root
quarto preview
```

This will show the HTML version of the homeworks with properly rendered LaTeX.

## Tips

- **Test frequently**: Render to HTML first (`quarto render hw01.qmd`) to check formatting
- **Use comments**: Add `<!-- comments -->` for notes that won't appear in output
- **Keep it simple**: Use standard LaTeX packages available in TinyTeX
- **Version control**: Commit `.qmd` files, not generated PDFs (unless specifically needed)
