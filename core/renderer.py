"""
Terminal rendering helpers for banners, menus, and dashboards.
"""
from config import paint


def render_header(title, width=50):
    border = paint("=" * width, "1;36")
    centered_title = paint(f"{title:^{width}}", "1;36")
    return f"{border}\n{centered_title}\n{border}"


def render_menu(title, options, prompt="Select option: "):
    lines = [render_header(title), ""]
    for i, opt in enumerate(options, 1):
        lines.append(f"  {i}. {opt}")
    lines.append("")
    lines.append(paint("=" * 50, "1;36"))
    return "\n".join(lines)
