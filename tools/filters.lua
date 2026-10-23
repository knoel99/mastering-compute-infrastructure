-- Pandoc Lua filter for Mastering Compute Infrastructure.
--   ::: sol      -> <details class="sol"><summary>Corrigé</summary> ... </details>
--   ::: sol {summary="Pistes"}  -> custom summary label
--   tables       -> wrapped in <div class="tbl-wrap"> so they scroll on phones
function Div(el)
  if el.classes:includes("sol") then
    local label = el.attributes["summary"] or "Corrigé"
    local out = { pandoc.RawBlock("html", '<details class="sol"><summary>' .. label .. '</summary>') }
    for _, b in ipairs(el.content) do out[#out + 1] = b end
    out[#out + 1] = pandoc.RawBlock("html", "</details>")
    return out
  end
end

function Table(el)
  return {
    pandoc.RawBlock("html", '<div class="tbl-wrap">'),
    el,
    pandoc.RawBlock("html", "</div>"),
  }
end
