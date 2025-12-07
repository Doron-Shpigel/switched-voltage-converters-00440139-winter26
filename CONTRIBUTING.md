# Contributing to Course Materials

This guide helps you add and maintain content in the course website.

## Quick Start

```bash
# Preview the website locally
quarto preview

# Build the website
quarto render

# The website will be in the _site/ directory
```

## Adding Content

### Adding a Lecture

1. Create a new `.qmd` file in `Lectures/`:
   ```bash
   touch Lectures/lecture-01.qmd
   ```

2. Add content using this template:
   ```yaml
   ---
   title: "Lecture 1: Introduction to Switched Converters"
   date: today
   format:
     html:
       toc: true
   ---
   
   ## Overview
   
   Your lecture content here...
   ```

3. Link it from `Lectures/index.qmd`

### Adding a Tutorial

Same process as lectures, but in the `Tutorials/` folder.

### Adding a Dry Homework

Follow the detailed instructions in `Homeworks/dry/README.md`.

Quick version:
1. Create folder: `mkdir Homeworks/dry/hw03`
2. Create file: `touch Homeworks/dry/hw03/hw03.qmd`
3. Copy template from existing homework
4. Update `Homeworks/dry/index.qmd`

### Adding a Wet Homework

1. Create a new `.qmd` file in `Homeworks/wet/`:
   ```bash
   touch Homeworks/wet/assignment-01.qmd
   ```

2. Add content and link from `Homeworks/wet/index.qmd`

### Adding Reference Books/Materials

1. Create a new `.qmd` file in `books/`:
   ```bash
   touch books/power-electronics-handbook.qmd
   ```

2. Add information about the book or reference material
3. Link it from `books/index.qmd`

## LaTeX Math Support

### Inline Math

Use single dollar signs: `$V_{out} = 5V$`

### Display Math

Use double dollar signs:
```latex
$$
D = \frac{V_{out}}{V_{in}}
$$
```

### Common Symbols

- Subscripts: `$V_{out}$`
- Superscripts: `$x^2$`
- Greek letters: `$\alpha, \beta, \gamma, \Delta$`
- Fractions: `$\frac{a}{b}$`
- Square root: `$\sqrt{x}$`
- Integrals: `$\int_0^1 f(x) dx$`

See `Homeworks/dry/README.md` for more LaTeX examples.

## File Organization

```
.
├── _quarto.yml              # Main configuration
├── index.qmd                # Homepage
├── styles.css               # Custom styling
├── Lectures/
│   ├── index.qmd           # Lectures landing page
│   └── *.qmd               # Individual lectures
├── Tutorials/
│   ├── index.qmd           # Tutorials landing page
│   └── *.qmd               # Individual tutorials
├── Homeworks/
│   ├── dry/
│   │   ├── index.qmd       # Dry homeworks landing page
│   │   ├── README.md       # Detailed instructions
│   │   ├── _quarto.yml     # PDF configuration
│   │   ├── generate-pdfs.sh
│   │   └── hw*/            # Individual homework folders
│   │       └── *.qmd
│   └── wet/
│       ├── index.qmd       # Wet homeworks landing page
│       └── *.qmd           # Individual assignments
└── books/
    ├── index.qmd           # Books landing page
    └── *.qmd               # Reference materials
```

## Updating Navigation

To add a new section to the navigation menu, edit `_quarto.yml`:

```yaml
website:
  navbar:
    left:
      - text: "New Section"
        href: new-section/index.qmd
```

## Styling

Custom styles are in `styles.css`. You can:
- Adjust colors
- Change fonts
- Modify spacing
- Customize the navbar

## Building PDFs

### For Dry Homeworks

Individual homework:
```bash
cd Homeworks/dry/hw01
quarto render hw01.qmd --to pdf
```

All homeworks:
```bash
cd Homeworks/dry
./generate-pdfs.sh
```

### Prerequisites

Install TinyTeX (first time only):
```bash
quarto install tinytex
```

Or use your system's TeX distribution (TeXLive, MiKTeX, etc.).

## Common Issues

### LaTeX Not Rendering

- Check that math is enclosed in `$...$` or `$$...$$`
- Escape special characters: `\$`, `\%`, `\&`
- Test in HTML first: `quarto render file.qmd`

### PDF Generation Fails

- Install TinyTeX: `quarto install tinytex`
- Check for LaTeX errors in the output
- Simplify complex equations and retry

### Changes Not Appearing

- Make sure you're previewing: `quarto preview`
- Or rebuild: `quarto render`
- Clear browser cache

## Best Practices

1. **Test frequently**: Preview your changes before committing
2. **Use descriptive titles**: Help students find content easily
3. **Add dates**: Use `date: today` in frontmatter
4. **Link between pages**: Create a connected learning experience
5. **Keep equations readable**: Break complex derivations into steps
6. **Add context**: Don't assume prior knowledge
7. **Use consistent formatting**: Follow existing patterns

## Getting Help

- Quarto documentation: https://quarto.org/docs/
- LaTeX math: https://www.overleaf.com/learn/latex/Mathematical_expressions
- GitHub Issues: Report problems with the course site structure

## Version Control

When adding content:

1. Create descriptive commit messages
2. Don't commit build artifacts (`_site/`, `.quarto/`)
3. Don't commit PDFs unless necessary (they're generated files)
4. Do commit source `.qmd` files

The `.gitignore` is configured to exclude build artifacts automatically.
