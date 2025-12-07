#!/bin/bash

# Script to generate PDFs for all dry homeworks
# Usage: ./generate-pdfs.sh

echo "Generating PDFs for all dry homeworks..."

# Find all .qmd files in hw* directories
for homework_dir in hw*/; do
    if [ -d "$homework_dir" ]; then
        echo "Processing $homework_dir"
        cd "$homework_dir"
        
        # Find the .qmd file (assuming one per directory)
        qmd_file=$(find . -maxdepth 1 -name "*.qmd" | head -1)
        
        if [ -n "$qmd_file" ]; then
            echo "  Rendering $qmd_file to PDF..."
            quarto render "$qmd_file" --to pdf
            
            if [ $? -eq 0 ]; then
                echo "  ✓ Successfully generated PDF"
            else
                echo "  ✗ Failed to generate PDF"
            fi
        else
            echo "  ! No .qmd file found"
        fi
        
        cd ..
    fi
done

echo "Done!"
