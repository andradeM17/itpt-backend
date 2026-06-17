def generate_tmx(alignment, srclang="ga", tgtlang="en"):
    """
    alignment = [
        {"source": "...", "target": "..."},
        ...
    ]
    Returns TMX XML text.
    """

    header = f'''<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header
    creationtool="ITPT"
    creationtoolversion="1.0"
    segtype="sentence"
    adminlang="en"
    srclang="{srclang}"
    datatype="PlainText">
  </header>
  <body>
'''

    body = ""
    for pair in alignment:
        src = pair["source"].replace("&", "&amp;").replace("<", "&lt;")
        tgt = pair["target"].replace("&", "&amp;").replace("<", "&lt;")

        body += f'''    <tu>
      <tuv xml:lang="{srclang}"><seg>{src}</seg></tuv>
      <tuv xml:lang="{tgtlang}"><seg>{tgt}</seg></tuv>
    </tu>
'''

    footer = """  </body>
</tmx>
"""

    return header + body + footer
