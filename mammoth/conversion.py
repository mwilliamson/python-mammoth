# coding=utf-8

from __future__ import unicode_literals

from functools import partial

import copy

import cobble

from . import documents, results, html_paths, images, writers, html
from .debug import is_debug_mode
from .docx.files import InvalidFileReferenceError
from .html import ForceWrite, Element as HTMLElement
from .attributes import compose_attributes, compose_style
from .lists import find_index


LIST_ELEMENT_TAG_NAMES = (['ul', 'ol'], ['ul'], ['ol'])
SKIP_PARAGRAPH_TAG_NAMES = (['ul', 'ol'], ['ul'], ['ol'], ['a'], ['tr'], ['td'], ['strong'], ['em'])


def convert_document_element_to_html(element,
        style_map=None,
        convert_image=None,
        id_prefix=None,
        output_format=None,
        ignore_empty_paragraphs=True
        ):

    if style_map is None:
        style_map = []

    if id_prefix is None:
        id_prefix = ""

    if convert_image is None:
        convert_image = images.data_uri

    if isinstance(element, documents.Document):
        comments = dict(
            (comment.comment_id, comment)
            for comment in element.comments
        )
    else:
        comments = {}

    messages = []
    converter = _DocumentConverter(
        messages=messages,
        style_map=style_map,
        convert_image=convert_image,
        id_prefix=id_prefix,
        ignore_empty_paragraphs=ignore_empty_paragraphs,
        note_references=[],
        comments=comments
    )
    context = _ConversionContext(is_table_header=False)
    nodes = converter.visit(element, context)

    writer = writers.writer(output_format)
    html.write(writer, html.collapse(html.strip_empty(nodes)))
    return results.Result(writer.as_string(), messages)


@cobble.data
class _ConversionContext(object):
    is_table_header = cobble.field()

    def copy(self, **kwargs):
        return cobble.copy(self, **kwargs)


class _DocumentConverter(documents.element_visitor(args=1)):
    def __init__(self, messages, style_map, convert_image, id_prefix, ignore_empty_paragraphs, note_references,
                 comments):
        self._messages = messages
        self._style_map = style_map
        self._id_prefix = id_prefix
        self._ignore_empty_paragraphs = ignore_empty_paragraphs
        self._note_references = note_references
        self._referenced_comments = []
        self._convert_image = convert_image
        self._comments = comments

    def visit_image(self, image, context):
        try:
            return self._convert_image(image)
        except InvalidFileReferenceError as error:
            self._messages.append(results.warning(str(error)))
            return []

    def visit_document(self, document, context):
        nodes = self._visit_all(document.children, context)
        notes = [
            document.notes.resolve(reference)
            for reference in self._note_references
        ]
        notes_list = html.element("ol", {}, self._visit_all(notes, context))
        comments = html.element("dl", {}, [
            html_node
            for referenced_comment in self._referenced_comments
            for html_node in self.visit_comment(referenced_comment, context)
        ])
        return nodes + [notes_list, comments]

    def visit_paragraph(self, paragraph, context):
        def children():
            content = self._visit_all(paragraph.children, context)
            if self._ignore_empty_paragraphs:
                return content
            else:
                return [html.force_write] + content

        initial_attributes = compose_style(paragraph.formatting)
        attributes = compose_attributes(paragraph, initial_attributes)

        html_path = self._find_html_path_for_paragraph(paragraph)
        html_path = html_path.wrap(children)

        self._update_path_with_attributes(html_path, SKIP_PARAGRAPH_TAG_NAMES, attributes=attributes)
        return html_path

    def _update_path_with_attributes(self, html_path, skip_tags=[], attributes={}):
        for e in html_path:
            if not isinstance(e, HTMLElement):
                continue

            skip = e.tag.tag_names in skip_tags
            children = e.children
            first_child = children[0] if len(children) else None
            is_child_element = not first_child is None and isinstance(first_child, HTMLElement)
            is_child_list = is_child_element and first_child.tag.tag_names in LIST_ELEMENT_TAG_NAMES

            if skip or is_child_list:
                pass  # Skips the case in which we have a list inside a list but because of proper HTML we had to insert
                      # a list item in between.
            else:
                e.attributes.update(attributes)
            self._update_path_with_attributes(e.children, skip_tags, attributes)

    def visit_run(self, run, context):
        nodes = lambda: self._visit_all(run.children, context)
        paths = []
        if run.highlight is not None:
            style = self._find_style(Highlight(color=run.highlight), "highlight")
            if style is not None:
                paths.append(style.html_path)
        if run.is_small_caps:
            paths.append(self._find_style_for_run_property("small_caps"))
        if run.is_all_caps:
            paths.append(self._find_style_for_run_property("all_caps"))
        if run.is_strikethrough:
            paths.append(self._find_style_for_run_property("strikethrough", default="s"))
        if run.is_underline:
            paths.append(self._find_style_for_run_property("underline"))
        if run.vertical_alignment == documents.VerticalAlignment.subscript:
            paths.append(html_paths.element(["sub"], fresh=False))
        if run.vertical_alignment == documents.VerticalAlignment.superscript:
            paths.append(html_paths.element(["sup"], fresh=False))
        if run.is_italic:
            paths.append(self._find_style_for_run_property("italic", default="em"))
        if run.is_bold:
            paths.append(self._find_style_for_run_property("bold", default="strong"))
        paths.append(self._find_html_path_for_run(run))

        for path in paths:
            nodes = partial(path.wrap, nodes)

        return nodes()

    def _find_style_for_run_property(self, element_type, default=None):
        style = self._find_style(None, element_type)
        if style is not None:
            return style.html_path
        elif default is not None:
            return html_paths.element(default, fresh=False)
        else:
            return html_paths.empty

    def visit_text(self, text, context):
        return [html.text(text.value)]


    def visit_hyperlink(self, hyperlink, context):
        if hyperlink.anchor is None:
            href = hyperlink.href
        else:
            href = "#{0}".format(self._html_id(hyperlink.anchor))

        attributes = compose_attributes(hyperlink, {"href": href})
        nodes = self._visit_all(hyperlink.children, context)
        return [html.collapsible_element("a", attributes, nodes)]


    def visit_checkbox(self, checkbox, context):
        attributes = compose_attributes(checkbox, {"type": "checkbox"})
        return [html.element("input", attributes)]


    def visit_bookmark(self, bookmark, context):
        element = html.collapsible_element(
            "a",
            {"id": self._html_id(bookmark.name)},
            [html.force_write])
        return [element]


    def visit_tab(self, tab, context):
        return [html.text("\t")]

    _default_table_path = html_paths.path([html_paths.element(["table"], fresh=True)])

    def visit_table(self, table, context):
        initial_attributes = compose_style(table.formatting)
        default_path = html_paths.path([html_paths.element(
            ["table"],
            compose_attributes(table, initial_attributes),
            fresh=True)])
        return self._find_html_path(table, "table", default_path) \
            .wrap(lambda: self._convert_table_children(table, context))

    def _convert_table_children(self, table, context):
        body_index = find_index(
            lambda child: not isinstance(child, documents.TableRow) or not child.is_header,
            table.children,
        )
        if body_index is None:
            body_index = len(table.children)

        if body_index == 0:
            children = self._visit_all(table.children, context.copy(is_table_header=False))
        else:
            head_rows = self._visit_all(table.children[:body_index], context.copy(is_table_header=True))
            body_rows = self._visit_all(table.children[body_index:], context.copy(is_table_header=False))
            children = [
                html.element("thead", {}, head_rows),
                html.element("tbody", {}, body_rows),
            ]

        return [html.force_write] + children


    def visit_table_row(self, table_row, context):
        return [
            html.element("tr",
                         compose_attributes(table_row, compose_style(table_row.formatting)),
                         [html.force_write] + self._visit_all(table_row.children, context)
                         )
        ]


    def visit_table_cell(self, table_cell, context):
        if context.is_table_header:
            tag_name = "th"
        else:
            tag_name = "td"
        initial_attributes = compose_style(table_cell.formatting)
        attributes = compose_attributes(table_cell, initial_attributes)
        nodes = [html.force_write] + self._visit_all(table_cell.children, context)
        return [
            html.element(tag_name, attributes, nodes)
        ]


    def visit_break(self, break_, context):
        return self._find_html_path_for_break(break_).wrap(lambda: [])


    def _find_html_path_for_break(self, break_):
        style = self._find_style(break_, "break")
        if style is not None:
            return style.html_path
        elif break_.break_type == "line":
            return html_paths.path([html_paths.element("br", fresh=True)])
        else:
            return html_paths.empty


    def visit_note_reference(self, note_reference, context):
        self._note_references.append(note_reference)
        note_number = len(self._note_references)
        return [
            html.element("sup", {}, [
                html.element("a", {
                    "href": "#" + self._note_html_id(note_reference),
                    "id": self._note_ref_html_id(note_reference),
                }, [html.text("[{0}]".format(note_number))])
            ])
        ]


    def visit_note(self, note, context):
        note_body = self._visit_all(note.body, context) + [
            html.collapsible_element("p", {}, [
                html.text(" "),
                html.element("a", {"href": "#" + self._note_ref_html_id(note)}, [
                    html.text(_up_arrow)
                ]),
            ])
        ]
        return [
            html.element("li", {"id": self._note_html_id(note)}, note_body)
        ]

    def visit_comment_reference(self, reference, context):
        def nodes():
            comment = self._comments[reference.comment_id]
            count = len(self._referenced_comments) + 1
            label = "[{0}{1}]".format(_comment_author_label(comment), count)
            self._referenced_comments.append((label, comment))
            return [
                # TODO: remove duplication with note references
                html.element("a", {
                    "href": "#" + self._referent_html_id("comment", reference.comment_id),
                    "id": self._reference_html_id("comment", reference.comment_id),
                }, [html.text(label)])
            ]

        html_path = self._find_html_path(
            None,
            "comment_reference",
            default=html_paths.ignore,
        )

        return html_path.wrap(nodes)

    def visit_comment(self, referenced_comment, context):
        label, comment = referenced_comment
        # TODO remove duplication with notes
        body = self._visit_all(comment.body, context) + [
            html.collapsible_element("p", {}, [
                html.text(" "),
                html.element("a", {"href": "#" + self._reference_html_id("comment", comment.comment_id)}, [
                    html.text(_up_arrow)
                ]),
            ])
        ]
        return [
            html.element(
                "dt",
                {"id": self._referent_html_id("comment", comment.comment_id)},
                [html.text("Comment {0}".format(label))],
            ),
            html.element("dd", {}, body),
        ]

    def _visit_all(self, elements, context):
        return [
            html_node
            for element in elements
            for html_node in self.visit(element, context)
        ]

    def _find_html_path_for_paragraph(self, paragraph):
        default = html_paths.path([html_paths.element("p", fresh=True)])
        html_path = self._find_html_path(paragraph, "paragraph", default, warn_unrecognised=True)
        return html_path

    def _find_html_path_for_run(self, run):
        return self._find_html_path(run, "run", default=html_paths.empty, warn_unrecognised=True)

    def _find_html_path(self, element, element_type, default, warn_unrecognised=False):
        style = self._find_style(element, element_type)
        if style is not None:
            return copy.deepcopy(style.html_path)

        if warn_unrecognised and getattr(element, "style_id", None) is not None:
            self._messages.append(results.warning(
                "Unrecognised {0} style: {1} (Style ID: {2})".format(
                    element_type, element.style_name, element.style_id)
            ))

        return default

    def _find_style(self, element, element_type):
        for style in self._style_map:
            document_matcher = style.document_matcher
            if _document_matcher_matches(document_matcher, element, element_type):
                return style

    def _note_html_id(self, note):
        return self._referent_html_id(note.note_type, note.note_id)

    def _note_ref_html_id(self, note):
        return self._reference_html_id(note.note_type, note.note_id)

    def _referent_html_id(self, reference_type, reference_id):
        return self._html_id("{0}-{1}".format(reference_type, reference_id))

    def _reference_html_id(self, reference_type, reference_id):
        return self._html_id("{0}-ref-{1}".format(reference_type, reference_id))

    def _html_id(self, suffix):
        return "{0}{1}".format(self._id_prefix, suffix)


@cobble.data
class Highlight:
    color = cobble.field()


def _document_matcher_matches(matcher, element, element_type):
    if matcher.element_type in ["underline", "strikethrough", "all_caps", "small_caps", "bold", "italic", "comment_reference"]:
        return matcher.element_type == element_type
    elif matcher.element_type == "highlight":
        return (
            matcher.element_type == element_type and
            (matcher.color is None or matcher.color == element.color)
        )
    elif matcher.element_type == "break":
        return (
            matcher.element_type == element_type and
            matcher.break_type == element.break_type
        )
    else: # matcher.element_type in ["paragraph", "run"]:
        return (
            matcher.element_type == element_type and (
                matcher.style_id is None or
                matcher.style_id == element.style_id
            ) and (
                matcher.style_name is None or
                element.style_name is not None and (matcher.style_name.matches(element.style_name))
            ) and (
                element_type != "paragraph" or
                matcher.numbering is None or
                matcher.numbering == element.numbering
            )
        )


def _comment_author_label(comment):
    return comment.author_initials or ""


_up_arrow = "↑"
