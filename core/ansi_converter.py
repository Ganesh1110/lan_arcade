"""
ANSI to safe HTML converter.
Converts ANSI SGR escape sequences into safe HTML spans with whitelisted classes.
All input text is strictly HTML-escaped to prevent XSS attacks.
"""
import html
import re

SGR_CLASSES = {
    "1": "ansi-bold",
    "2": "ansi-dim",
    "3": "ansi-italic",
    "4": "ansi-underline",
    # Standard foreground colors
    "30": "ansi-fg-black",
    "31": "ansi-fg-red",
    "32": "ansi-fg-green",
    "33": "ansi-fg-yellow",
    "34": "ansi-fg-blue",
    "35": "ansi-fg-magenta",
    "36": "ansi-fg-cyan",
    "37": "ansi-fg-white",
    # High-intensity foreground colors
    "90": "ansi-fg-bright-black",
    "91": "ansi-fg-bright-red",
    "92": "ansi-fg-bright-green",
    "93": "ansi-fg-bright-yellow",
    "94": "ansi-fg-bright-blue",
    "95": "ansi-fg-bright-magenta",
    "96": "ansi-fg-bright-cyan",
    "97": "ansi-fg-bright-white",
    # Standard background colors
    "40": "ansi-bg-black",
    "41": "ansi-bg-red",
    "42": "ansi-bg-green",
    "43": "ansi-bg-yellow",
    "44": "ansi-bg-blue",
    "45": "ansi-bg-magenta",
    "46": "ansi-bg-cyan",
    "47": "ansi-bg-white",
    # High-intensity background colors
    "100": "ansi-bg-bright-black",
    "101": "ansi-bg-bright-red",
    "102": "ansi-bg-bright-green",
    "103": "ansi-bg-bright-yellow",
    "104": "ansi-bg-bright-blue",
    "105": "ansi-bg-bright-magenta",
    "106": "ansi-bg-bright-cyan",
    "107": "ansi-bg-bright-white",
}

# Regex to match ANSI escape sequences
# Group 1: parameters, Group 2: command character
_ANSI_RE = re.compile(r"\x1b\[([0-9;]*)([a-zA-Z])")


def ansi_to_html(raw_text: str) -> str:
    """
    Convert an ANSI-styled text string into safe HTML with <span class="..."> tags.
    Strips non-SGR escape sequences, escapes all HTML characters, and only emits
    whitelisted CSS classes.
    """
    if not raw_text:
        return ""

    out = []
    last_idx = 0
    span_open = False
    current_styles = {}  # category -> class_name

    for match in _ANSI_RE.finditer(raw_text):
        start, end = match.span()
        # Escape preceding plain text chunk
        if start > last_idx:
            chunk = raw_text[last_idx:start]
            out.append(html.escape(chunk, quote=True))

        params_str, cmd = match.group(1), match.group(2)
        last_idx = end

        # Only 'm' is SGR (Select Graphic Rendition); strip all other commands
        if cmd != "m":
            continue

        raw_codes = params_str.split(";") if params_str else ["0"]
        for code in raw_codes:
            code = code.strip()
            if not code or code == "0":
                # Reset all styles
                current_styles.clear()
            elif code in SGR_CLASSES:
                cls = SGR_CLASSES[code]
                if cls.startswith("ansi-fg-"):
                    current_styles["fg"] = cls
                elif cls.startswith("ansi-bg-"):
                    current_styles["bg"] = cls
                elif cls in ("ansi-bold", "ansi-dim"):
                    current_styles["weight"] = cls
                elif cls == "ansi-underline":
                    current_styles["underline"] = cls
                elif cls == "ansi-italic":
                    current_styles["italic"] = cls

        # Close existing span if one was open
        if span_open:
            out.append("</span>")
            span_open = False

        # Open new span if there are active styles
        if current_styles:
            classes = " ".join(sorted(current_styles.values()))
            out.append(f'<span class="{classes}">')
            span_open = True

    # Escape trailing text
    if last_idx < len(raw_text):
        out.append(html.escape(raw_text[last_idx:], quote=True))

    if span_open:
        out.append("</span>")

    return "".join(out)
