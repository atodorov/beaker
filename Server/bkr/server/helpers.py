from kid import Element
import turbogears, sys
from turbogears.database import session

def make_link(url, text, **kwargs):
    # make an <a> element
    a = Element('a', {'class': 'list'}, href=turbogears.url(url))
    a.text = text
    if kwargs.get('elem_class', None):
        a.attrib['class']=kwargs.get('elem_class')
    return a

def make_edit_link(name, id):
    # make an edit link
    return make_link(url  = 'edit?id=%s' % id,
                     text = name)

def make_remove_link(id):
    # make a remove link
    return make_link(url  = 'remove?id=%s' % id,
                     text = 'Remove (-)')

def make_fake_link(name=None,id=None,text=None,attrs=None):
    # make something look like a href
    a  = Element('a')
    a.attrib['class'] = "link"
    a.attrib['style'] = "color:#22437f;cursor:pointer"
    if name is not None:
        a.attrib['name'] = name
    if id is not None:
        a.attrib['id'] = id
    if text is not None:
        a.text = '%s ' % text
    if attrs is not None:
        for k,v in attrs.items():
            a.attrib[k] = v
    return a
