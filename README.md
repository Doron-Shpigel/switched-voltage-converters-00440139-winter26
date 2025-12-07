# Switched Voltage Converters (00440139) - Winter 2026

This repository contains course materials for the course Switched Voltage Converters (00440139) - Winter 2026, organized using [Quarto](https://quarto.org/).

## Repository Structure

```
├── Lectures/           # Course lecture materials and notes
├── Tutorials/          # Tutorial sessions and exercises
├── Homeworks/
│   ├── dry/           # Theoretical exercises (LaTeX-based)
│   │   ├── hw01/      # Homework 1
│   │   ├── hw02/      # Homework 2
│   │   └── ...        # Additional homeworks
│   └── wet/           # Practical assignments
├── books/             # Reference materials and textbooks
├── _quarto.yml        # Quarto configuration
├── index.qmd          # Home page
└── styles.css         # Custom CSS styles
```

## Features

- **Web-based View**: All course materials are rendered as a navigable website
- **LaTeX Support**: Dry homeworks are written with LaTeX equations and formatting
- **PDF Export**: Each homework can be exported to PDF format
- **Organized Structure**: Clear separation between lectures, tutorials, and homework types

## Getting Started

### Prerequisites

1. Install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
2. Install [Quarto](https://quarto.org/docs/get-started/)
3. (Optional) For PDF export, install [TinyTeX](https://yihui.org/tinytex/):
   ```bash
   quarto install tinytex
   ```

### Setting Up the Environment

Create and activate the conda environment with all required packages:

```bash
# Create the environment from the environment.yml file
conda env create -f environment.yml

# Activate the environment
conda activate switched-voltage-converters
```

The environment includes:
- **Jupyter**: Interactive notebook environment
- **Matplotlib**: 2D plotting library
- **Plotly**: Interactive visualization library
- **SymPy**: Symbolic mathematics library
- **NumPy**: Numerical computing library
- **Lcapy**: Linear circuit analysis library (includes GUI support via Jupyter)

To deactivate the environment:

```bash
conda deactivate
```

To update the environment after changes to `environment.yml`:

```bash
conda env update -f environment.yml --prune
```

### Building the Website

To render the entire website:

```bash
quarto render
```

The output will be generated in the `_site/` directory.

### Preview the Website

To preview the website locally with live reload:

```bash
quarto preview
```

This will start a local server and open the website in your browser.

## Working with Dry Homeworks

Each dry homework is in its own folder under `Homeworks/dry/` (e.g., `hw01/`, `hw02/`).

### Creating a New Homework

1. Create a new folder: `Homeworks/dry/hw03/`
2. Create a Quarto markdown file: `hw03.qmd`
3. Use the following template:

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
```

4. Write your homework using LaTeX math notation:
   - Inline math: `$V_{out} = 5V$`
   - Display math: `$$D = \frac{V_{out}}{V_{in}}$$`

5. Update `Homeworks/dry/index.qmd` to link to the new homework

### Generating PDF for a Homework

To generate a PDF for a specific homework:

```bash
cd Homeworks/dry/hw01
quarto render hw01.qmd --to pdf
```

This requires a TeX installation (TinyTeX, TeXLive, or similar).

## Adding Course Content

### Lectures

Add lecture materials as `.qmd` files in the `Lectures/` directory.

### Tutorials

Add tutorial materials as `.qmd` files in the `Tutorials/` directory.

### Wet Homeworks

Add practical assignments as `.qmd` files in the `Homeworks/wet/` directory.

### Books and References

Add reference materials to the `books/` directory.

## Customization

- **Navigation**: Edit `_quarto.yml` to modify the website navigation
- **Styling**: Edit `styles.css` to customize the appearance
- **Theme**: Change the theme in `_quarto.yml` (default is `cosmo`)

## Deployment

The website can be deployed to:
- **GitHub Pages**: Use `quarto publish gh-pages`
- **Netlify**: Connect your repository to Netlify
- **Other hosting**: Deploy the `_site/` directory to any static hosting service

## License

Course materials © 2026. All rights reserved.
