-- tikz_to_svg.lua
-- A Pandoc Lua Filter that intercepts raw TikZ blocks and converts them to SVG for HTML output.

if FORMAT:match 'latex' or FORMAT:match 'pdf' then
    return nil -- Do nothing for PDF/LaTeX output, keep the raw text.
end

function RawBlock(el)
    -- Quarto parses \begin{tikzpicture} lines as 'tex' or 'latex' RawBlocks
    if el.format == "tex" or el.format == "latex" then
        if el.text:match("^\\begin{tikzpicture}") then
            -- 1. Create a hash to cache the SVG (only recompiles if the TikZ code changes)
            local hash = pandoc.sha1(el.text)
            local svg_file = "tikz-" .. hash .. ".svg"
            local tex_file = "tikz-" .. hash .. ".tex"
            local pdf_file = "tikz-" .. hash .. ".pdf"

            -- Determine document name (ignoring the directory since Quarto uses /tmp/ directories)
            local input_file = nil
            if PANDOC_STATE and PANDOC_STATE.input_files and #PANDOC_STATE.input_files > 0 then
                input_file = PANDOC_STATE.input_files[1]
            elseif quarto and quarto.doc and quarto.doc.input_file then
                input_file = quarto.doc.input_file
            end

            local docname = "document"
            if input_file then
                -- Extract just the filename, ignoring the /tmp/ path
                local base = input_file:match("([^/]+)$") or input_file
                -- Strip away the extensions (e.g., 'hw02.html.md' -> 'hw02')
                docname = base:match("([^%.]+)") or base
            end

            -- Force the output to the current working directory (next to the .qmd file)
            local target_dir = "./" .. docname .. "_cache_files"

            -- Print to terminal so you can verify exactly where it's saving during Quarto render
            print("[TikZ Filter] Generating/Checking cache at: " .. target_dir)

            -- create the directory if it doesn't exist
            os.execute('mkdir -p "' .. target_dir .. '"')

            local svg_path = target_dir .. "/" .. svg_file
            local tex_path = target_dir .. "/" .. tex_file
            local pdf_path = target_dir .. "/" .. pdf_file

            -- 2. Check if the SVG is already cached
            local f = io.open(svg_path, "r")
            if f ~= nil then
                local svg_data = f:read("*all")
                f:close()
                return pandoc.RawBlock("html", '<div style="text-align: center;">\n' .. svg_data .. '\n</div>')
            end

            -- 3. Write the standalone TeX document (with the required packages!)
            local tex_doc = string.format([[
  \PassOptionsToPackage{dvipsnames,svgnames}{xcolor}
  \documentclass[tikz, border=2pt]{standalone}
  \usepackage{amsmath}
  \usepackage{amssymb}
  \usepackage{circuitikz}
  \begin{document}
  %s
  \end{document}
  ]], el.text)

            local tf = io.open(tex_path, "w")
            tf:write(tex_doc)
            tf:close()

            -- 4. Compile the PDF and convert to SVG
            os.execute('pdflatex -interaction=nonstopmode -output-directory="' ..
            target_dir .. '" "' .. tex_path .. '" > /dev/null 2>&1')
            os.execute('pdftocairo -svg "' .. pdf_path .. '" "' .. svg_path .. '" > /dev/null 2>&1')

            -- 5. Read the generated SVG and return it as an HTML block
            local sf = io.open(svg_path, "r")
            if sf ~= nil then
                local svg_data = sf:read("*all")
                sf:close()
                return pandoc.RawBlock("html", '<div style="text-align: center;">\n' .. svg_data .. '\n</div>')
            else
                return pandoc.RawBlock("html", '<div style="color: red;"><b>Error compiling TikZ code</b></div>')
            end
        end
    end
end
