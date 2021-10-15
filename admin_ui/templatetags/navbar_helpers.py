from typing import List
from django import template
from django.template.loader import get_template


register = template.Library()
draft_view = lambda view: f"{view}-list-draft"
published_view = lambda view: f"{view}-list-published"


def is_quoted(text: str):
    return text[0] == text[-1] and text[0] in ('"', "'")


@register.inclusion_tag("snippets/sidebar/activelink_navitem.html", takes_context=True)
def nav_link(context, title, view):
    return {
        **context.flatten(),
        "title": title,
        "view": draft_view(view),
        "links": " || ".join(f(view) for f in [draft_view, published_view]),
    }


@register.tag
def collapsable_menu(parser, token):
    """
    Builds a folding navigation structure utilizing Bootstrap 4's Collapse functionality
    and Django Active Link's active_link functionality. This makes it simple to build out
    a collapsable menu that is un-collapsed when you are on a view linked from the menu.

    The first argument must be a unique title for the menu entry, wrapped within quotes. All
    subsequent arguments represent models for which list views are linked.  E.g. if "doi" is
    presented, the menu will be shown as active if the user is viewing either a "doi-list-draft"
    or "doi-list-published" routes.

    https://getbootstrap.com/docs/4.0/components/collapse/
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag, title, *views = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[0]
        )

    if not all(is_quoted(text) for text in [title, *views]):
        raise template.TemplateSyntaxError(
            "%r tag's arguments should be in quotes" % tag
        )

    nodelist = parser.parse(("endcollapsable_menu",))
    parser.delete_first_token()
    return FoldingNavNode(
        nodelist,
        title=title[1:-1],
        views=views,
    )


class FoldingNavNode(template.Node):
    def __init__(self, nodelist, *, title: str, views: List[str]):
        self.nodelist = nodelist
        self.title = title
        self.views = views

    def render(self, context):
        t = get_template("snippets/sidebar/collapsable_navgroup.html")
        return t.render(
            {
                **context.flatten(),
                "title": self.title,
                "identifier": self.title.lower().replace(" ", "-"),
                "active_views": " || ".join(
                    f(view[1:-1]) for view in self.views for f in [draft_view, published_view]
                ),
                "children": self.nodelist.render(context),
            }
        )
