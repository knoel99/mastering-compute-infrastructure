-- Pandoc Lua filter for Mastering Compute Infrastructure.
--   ::: sol      -> <details class="sol"><summary>Corrigé</summary> ... </details>
--   ::: sol {summary="Pistes"}  -> custom summary label
--   tables       -> wrapped in <div class="tbl-wrap"> so they scroll on phones
--   numbered: true (front matter) -> "1. Title" on h2 and "1.2. Title" on h3 (course modules number
--                   their chapters by hand and do not set it; .unnumbered headings are skipped)
--   in-page contents ("Sommaire") inserted before the first section when the page has at least four
--                   h2 sections, with the h3 sub-sections nested, as in the LLGA and MVA course pages;
--                   toc-inline: false (front matter) turns it off
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

local function truthy(v)
  if v == nil then return nil end
  if type(v) == "boolean" then return v end
  local s = pandoc.utils.stringify(v)
  if s == "true" or s == "yes" then return true end
  if s == "false" or s == "no" then return false end
  return nil
end

local function starts_with_number(h)
  local first = h.content[1]
  return first ~= nil and first.t == "Str" and first.text:match("^%d") ~= nil
end

local function number_headings(blocks)
  local n, k = 0, 0
  for _, b in ipairs(blocks) do
    if b.t == "Header" and (b.level == 2 or b.level == 3) and not b.classes:includes("unnumbered")
       and not starts_with_number(b) then
      local label
      if b.level == 2 then
        n, k = n + 1, 0
        label = tostring(n) .. "."
      elseif n > 0 then
        k = k + 1
        label = tostring(n) .. "." .. tostring(k) .. "."
      end
      if label then
        b.content:insert(1, pandoc.Space())
        b.content:insert(1, pandoc.Str(label))
      end
    elseif b.t == "Header" and b.level == 2 then
      k = 0
    end
  end
end

local function has_link(inlines)
  local found = false
  pandoc.Inlines(inlines):walk({ Link = function() found = true end })
  return found
end

local function entry(h)
  local text = has_link(h.content) and { pandoc.Str(pandoc.utils.stringify(h.content)) } or h.content
  return { pandoc.Plain({ pandoc.Link(text, "#" .. h.identifier) }) }
end

local function contents(blocks)
  local items, current = {}, nil
  local h2 = 0
  for _, b in ipairs(blocks) do
    if b.t == "Header" and b.identifier ~= "" and b.identifier ~= "sommaire" then
      if b.level == 2 then
        h2 = h2 + 1
        current = { entry(b), {} }
        items[#items + 1] = current
      elseif b.level == 3 and current then
        current[2][#current[2] + 1] = entry(b)
      end
    end
  end
  if h2 < 4 then return nil end
  local list = {}
  for _, it in ipairs(items) do
    local item = { it[1][1] }
    if #it[2] > 0 then item[#item + 1] = pandoc.BulletList(it[2]) end
    list[#list + 1] = item
  end
  return pandoc.Div({
    pandoc.Header(2, { pandoc.Str("Sommaire") }, pandoc.Attr("sommaire", { "unnumbered" })),
    pandoc.BulletList(list),
  }, pandoc.Attr("", { "toc-inline" }))
end

function Pandoc(doc)
  if truthy(doc.meta["numbered"]) then
    number_headings(doc.blocks)
  end
  if truthy(doc.meta["toc-inline"]) ~= false then
    local toc = contents(doc.blocks)
    if toc then
      local pos = 1
      for i, b in ipairs(doc.blocks) do
        if b.t == "Header" and b.level == 2 then pos = i; break end
      end
      doc.blocks:insert(pos, toc)
    end
  end
  return doc
end
