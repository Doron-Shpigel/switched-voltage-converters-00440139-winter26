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

      -- 2. Determine document name by bypassing Quarto's temp files
      local docname = "document"
      
      -- Ask the Linux OS for the .qmd file in the current directory
      local handle = io.popen("ls *.qmd 2>/dev/null | head -n 1")
      if handle then
        local file_str = handle:read("*l")
        handle:close()
        if file_str and file_str ~= "" then
          -- Extract just the name without the .qmd extension (e.g., 'hw02')
          docname = file_str:match("([^/]+)%.qmd$") or "document"
        else
          -- Fallback: Use the current directory name just in case
          local dhandle = io.popen("basename \"$PWD\" 2>/dev/null")
          if dhandle then
            local dname = dhandle:read("*l")
            dhandle:close()
            if dname and dname ~= "" then docname = dname end
          end
        end
      end

      -- Force output to the unified cache directory
      local target_dir = "./" .. docname .. "_cache_files"
      
      -- create the directory if it doesn't exist
      os.execute('mkdir -p "' .. target_dir .. '"')

      local svg_path = target_dir .. "/" .. svg_file
      local tex_path = target_dir .. "/" .. tex_file
      local pdf_path = target_dir .. "/" .. pdf_file

      -- 3. Check if the SVG is already cached
      local f = io.open(svg_path, "r")
      if f ~= nil then
        f:close()
        -- FIX: Use an <img> tag instead of embedding raw SVG data to prevent ID clashing
        return pandoc.RawBlock("html", '<div style="text-align: center;">\n<img src="' .. svg_path .. '" alt="TikZ diagram" />\n</div>')
      end

      -- 4. Write the standalone TeX document (with the required packages!)
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

      -- 5. Compile the PDF and convert to SVG
      os.execute('pdflatex -interaction=nonstopmode -output-directory="' .. target_dir .. '" "' .. tex_path .. '" > /dev/null 2>&1')
      os.execute('pdftocairo -svg "' .. pdf_path .. '" "' .. svg_path .. '" > /dev/null 2>&1')

      -- 6. Read the generated SVG and return it as an HTML block via <img> tag
      local sf = io.open(svg_path, "r")
      if sf ~= nil then
        sf:close()
        return pandoc.RawBlock("html", '<div style="text-align: center;">\n<img src="' .. svg_path .. '" alt="TikZ diagram" />\n</div>')
      else
        return pandoc.RawBlock("html", '<div style="color: red;"><b>Error compiling TikZ code</b></div>')
      end
    end
  end
end