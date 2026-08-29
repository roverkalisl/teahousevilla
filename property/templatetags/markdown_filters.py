import bleach
import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

ALLOWED_TAGS = [
    "a",
    "abbr",
    "b",
    "blockquote",
    "br",
    "code",
    "dd",
    "del",
    "div",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "sub",
    "sup",
    "ul",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title"],
    "div": ["class"],
    "span": ["class"],
}


@register.filter(name="markdownify")
def markdownify(value):
    if not value:
        return ""

    html = md.markdown(
        value,
        extensions=["extra", "sane_lists", "nl2br", "toc"],
        output_format="html5",
    )
    sanitized = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip_comments=True,
        protocols=["http", "https", "mailto"],
    )
    return mark_safe(sanitized)
