import cobble
from nose.tools import assert_equal, istest

from mammoth import documents, transforms
from mammoth.transforms import get_descendants, get_descendants_of_type, _each_element


@istest
class ParagraphTests(object):
    @istest
    def paragraph_is_transformed(self):
        paragraph = documents.paragraph(children=[])
        result = transforms.paragraph(lambda _: documents.tab())(paragraph)
        assert_equal(documents.tab(), result)
        
    @istest
    def non_paragraph_elements_are_not_transformed(self):
        run = documents.run(children=[])
        result = transforms.paragraph(lambda _: documents.tab())(run)
        assert_equal(documents.run(children=[]), result)


@istest
class RunTests(object):
    @istest
    def run_is_transformed(self):
        run = documents.run(children=[])
        result = transforms.run(lambda _: documents.tab())(run)
        assert_equal(documents.tab(), result)
        
    @istest
    def non_paragraph_elements_are_not_transformed(self):
        paragraph = documents.paragraph(children=[])
        result = transforms.run(lambda _: documents.tab())(paragraph)
        assert_equal(documents.paragraph(children=[]), result)


@istest
class EachElementTests(object):
    @istest
    def all_descendants_are_transformed(self):
        @cobble.data
        class Count(documents.HasChildren):
            count = cobble.field()
        
        root = Count(count=None, children=[
            Count(count=None, children=[
                Count(count=None, children=[]),
            ]),
        ])
        
        current_count = [0]
        def set_count(node):
            current_count[0] += 1
            return node.copy(count=current_count[0])
        
        result = _each_element(set_count)(root)
        
        assert_equal(Count(count=3, children=[
            Count(count=2, children=[
                Count(count=1, children=[]),
            ]),
        ]), result)


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


@istest
class GetDescendantsOfTypeTests(object):
    @istest
    def filters_descendants_to_type(self):
        tab = documents.tab()
        run = documents.run(children=[])
        element = documents.paragraph(children=[tab, run])
        assert_equal([run], get_descendants_of_type(element, documents.Run))
