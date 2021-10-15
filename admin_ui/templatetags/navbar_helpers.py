from typing import List
from django import template
from django.template.loader import get_template


register = template.Library()
build_draft_view = lambda view: f"{view}-list-draft"
build_published_view = lambda view: f"{view}-list-published"


def is_quoted(text: str):
    return text[0] == text[-1] and text[0] in ('"', "'")


@register.inclusion_tag("snippets/sidebar/activelink_navitem.html", takes_context=True)
def nav_link(context, title, view):
    return {
        **context.flatten(),
        "title": title,
        "view": build_draft_view(view),
        "links": " || ".join(f(view) for f in [build_draft_view, build_published_view]),
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
        tag, title, *model_names = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two arguments" % token.contents.split()[0]
        )

    if not all(is_quoted(text) for text in [title, *model_names]):
        raise template.TemplateSyntaxError(
            "%r tag's arguments should be in quotes" % tag
        )

    nodelist = parser.parse(("endcollapsable_menu",))
    parser.delete_first_token()
    return FoldingNavNode(
        nodelist,
        # Trim quotes
        title=title[1:-1],
        model_names=[model_name[1:-1] for model_name in model_names],
    )


class FoldingNavNode(template.Node):
    def __init__(self, nodelist, *, title: str, model_names: List[str]):
        self.nodelist = nodelist
        self.title = title
        self.model_names = model_names

    def render(self, context):
        t = get_template("snippets/sidebar/collapsable_navgroup.html")
        return t.render(
            {
                **context.flatten(),
                "title": self.title,
                "identifier": self.title.lower().replace(" ", "-"),
                "active_views": " || ".join(
                    func(model_name)
                    for model_name in self.model_names
                    for func in [build_draft_view, build_published_view]
                ),
                "children": self.nodelist.render(context),
            }
        )
