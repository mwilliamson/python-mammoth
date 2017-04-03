from nose.tools import assert_equal, istest

from mammoth import documents
from mammoth.transforms import get_descendants


@istest
class GetDescendantsTests(object):
    @istest
    def returns_nothing_if_element_type_has_no_children(self):
        assert_equal([], get_descendants(documents.tab()))
    
    @istest
    def returns_nothing_if_element_has_empty_children(self):
        assert_equal([], get_descendants(documents.paragraph(children=[])))
    
    @istest
    def includes_children(self):
        children = [documents.text("child 1"), documents.text("child 2")]
        element = documents.paragraph(children=children)
        assert_equal(children, get_descendants(element))
    
    @istest
    def includes_indirect_descendants(self):
        grandchild = documents.text("grandchild")
        child = documents.run(children=[grandchild])
        element = documents.paragraph(children=[child])
        assert_equal([grandchild, child], get_descendants(element))
