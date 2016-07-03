from .. import lists
from .. import documents
from .. import results


def create_comments_reader(body_reader):
    def read_comments_xml_element(element):
        comment_elements = element.find_children("w:comment")
        return results.combine(lists.map(_read_comment_element, comment_elements))


    def _read_comment_element(element):
        return body_reader.read_all(element.children).map(lambda body:
            documents.comment(
                comment_id=element.attributes["w:id"],
                body=body
            ))

    return read_comments_xml_element
