from lxml.html import document_fromstring


__all__ = 'assert_contain_text',


def assert_contain_text(text, expr, data):
    def traverse(elements):
        for element in elements:
            if text in element.text_content():
                return True
        else:
            return False

    tree = document_fromstring(str(data)).cssselect(expr)
    assert tree
    assert traverse(tree)
