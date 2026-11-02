#!/usr/bin/env python3
"""Add the "what did you think?" field to a build of I Saw That.

Written as a script rather than hand edits because the feature now has to
land in two places — the live app and the multi-user build — and they must
not drift. Run it against either file; it is idempotent.
"""
import sys, re

def patch(path):
    s = open(path).read()
    if 'data-field="impressions"' in s:
        print(f"  {path}: already has it, nothing to do")
        return False
    n = 0

    # carried on the draft
    old = '    castText: castToText(base.cast), understudyText: castToText(base.understudies), notes: base.notes||"",'
    assert old in s, "draft shape"
    s = s.replace(old, old + '\n    impressions: base.impressions||"",'); n += 1

    # its own box in the form, below the practical notes
    old = """    + '<label><span>Notes</span><input type="text" data-field="notes" value="'+esc(d.notes)+'" placeholder="Understudy on, seats, who came along"></label>'"""
    assert old in s, "form"
    s = s.replace(old, old + """
    + '<label><span>What did you think?</span><textarea rows="6" data-field="impressions" placeholder="Worth writing down now \\u2014 it is the part you will not remember in ten years.">'+esc(d.impressions)+'</textarea></label>'"""); n += 1

    # saved with the record
    old = "    understudies:textToCast(d.understudyText), notes:d.notes,"
    assert old in s, "save"
    s = s.replace(old, '    understudies:textToCast(d.understudyText), notes:d.notes, impressions:(d.impressions||"").trim(),'); n += 1

    # shown in the entry, set apart from the facts
    old = """  if(e.notes) h += '<div class="small dim" style="margin-top:8px">'+esc(e.notes)+'</div>';"""
    assert old in s, "detail"
    s = s.replace(old, old + """
  if(e.impressions) h += '<div class="impressions">' + esc(e.impressions).replace(/\\n+/g, '</p><p>').replace(/^/, '<p>') + '</p></div>';"""); n += 1

    # searchable
    before = s
    s = s.replace("[e.title,e.venue,e.city,e.company,e.notes,e.addedByName,e.kind,e.director]",
                  "[e.title,e.venue,e.city,e.company,e.notes,e.impressions,e.addedByName,e.kind,e.director]")
    assert s != before, "search"; n += 1
    s = s.replace('placeholder="Search titles, people, venues, notes"',
                  'placeholder="Search titles, people, venues, what you wrote"')

    # in the spreadsheet
    s = s.replace('"Cast","Understudies","Notes","Filed by"',
                  '"Cast","Understudies","Notes","What you thought","Filed by"')
    old = '(e.understudies||[]).map(c => c.actor + (c.role?" as "+c.role:"")).join("; "), e.notes, e.addedByName]));'
    assert old in s, "csv"
    s = s.replace(old, '(e.understudies||[]).map(c => c.actor + (c.role?" as "+c.role:"")).join("; "), e.notes, e.impressions||"", e.addedByName]));'); n += 1

    # merging must never discard something somebody wrote
    old = """  const dn = (drop.notes||"").replace(/Imported from calendar[^.]*\\.?/i,"").trim();"""
    assert old in s, "mergePair"
    s = s.replace(old, """  // never lose something somebody wrote
  if(!(merged.impressions||"").trim() && (drop.impressions||"").trim()) merged.impressions = drop.impressions;
  else if((drop.impressions||"").trim() && !(merged.impressions||"").includes(drop.impressions.trim()))
    merged.impressions = (merged.impressions || "").trim() + "\\n\\n" + drop.impressions.trim();
""" + old); n += 1

    old = """    d.notes = (m.notes && !/Imported from calendar/i.test(m.notes) && m.notes !== d.notes)"""
    assert old in s, "scan merge"
    s = s.replace(old, """    if(!(d.impressions||"").trim() && (m.impressions||"").trim()) d.impressions = m.impressions;
""" + old); n += 1

    # styling: the personal part of an entry should not look like another credit line
    anchor = '  .hr{height:0;border-top:1px solid var(--line);margin:18px 0}'
    assert anchor in s, "style anchor"
    s = s.replace(anchor, """  /* what you thought: the one part of an entry nobody else could have written */
  .impressions{margin:16px 0 0;padding:2px 0 2px 16px;border-left:2px solid var(--brassDim)}
  .impressions p{font-family:var(--display);font-size:16.5px;line-height:1.6;margin:0 0 .7em;color:var(--paper)}
  .impressions p:last-child{margin-bottom:0}
  .wrote{position:absolute;right:2px;top:12px;font-family:var(--display);font-size:30px;
    line-height:1;color:var(--brassDim);opacity:.55}
""" + anchor); n += 1

    # a mark in the log so you can see which nights you wrote about
    old = """      + (names ? '<span class="players truncate">'+esc(names)+'</span>' : '')"""
    assert old in s, "stub"
    s = s.replace(old, old + """
      + (e.impressions ? '<span class="wrote">\\u201c</span>' : '')"""); n += 1
    s = s.replace('.stub{display:flex;align-items:flex-start;',
                  '.stub{position:relative;display:flex;align-items:flex-start;')

    open(path, 'w').write(s)
    print(f"  {path}: {n} edits applied")
    return True

for p in sys.argv[1:]:
    patch(p)
