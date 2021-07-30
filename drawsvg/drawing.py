
from io import StringIO
import base64
import urllib.parse
import re
from collections import defaultdict

from . import Raster
from . import elements as elements_module


STRIP_CHARS = ('\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11'
               '\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')


class Drawing:
    ''' A canvas to draw on

        Supports iPython: If a Drawing is the last line of a cell, it will be
        displayed as an SVG below. '''
    def __init__(self, width, height, origin=(0,0), id_prefix='d',
                 display_inline=True, **svg_args):
        assert float(width) == width
        assert float(height) == height
        self.width = width
        self.height = height
        if origin == 'center':
            self.view_box = (-width/2, -height/2, width, height)
        else:
            origin = tuple(origin)
            assert len(origin) == 2
            self.view_box = origin + (width, height)
        self.view_box = (self.view_box[0], -self.view_box[1]-self.view_box[3],
                         self.view_box[2], self.view_box[3])
        self.elements = []
        self.ordered_elements = defaultdict(list)
        self.other_defs = []
        self.pixel_scale = 1
        self.render_width = None
        self.render_height = None
        self.id_prefix = str(id_prefix)
        self.display_inline = display_inline
        self.svg_args = {}
        for k, v in svg_args.items():
            k = k.replace('__', ':')
            k = k.replace('_', '-')
            if k[-1] == '-':
                k = k[:-1]
            self.svg_args[k] = v
        self.id_index = 0
    def set_render_size(self, w=None, h=None):
        self.render_width = w
        self.render_height = h
        return self
    def set_pixel_scale(self, s=1):
        self.render_width = None
        self.render_height = None
        self.pixel_scale = s
        return self
    def calc_render_size(self):
        if self.render_width is None and self.render_height is None:
            return (self.width * self.pixel_scale,
                    self.height * self.pixel_scale)
        elif self.render_width is None:
            s = self.render_height / self.height
            return self.width * s, self.render_height
        elif self.render_height is None:
            s = self.render_width / self.width
            return self.render_width, self.height * s
        else:
            return self.render_width, self.render_height
    def draw(self, obj, *, z=None, **kwargs):
        if obj is None:
            return
        if not hasattr(obj, 'write_svg_element'):
            elements = obj.to_drawables(elements=elements_module, **kwargs)
        else:
            assert len(kwargs) == 0
            elements = (obj,)
        self.extend(elements, z=z)
    def append(self, element, *, z=None):
        if z is not None:
            self.ordered_elements[z].append(element)
        else:
            self.elements.append(element)
    def extend(self, iterable, *, z=None):
        if z is not None:
            self.ordered_elements[z].extend(iterable)
        else:
            self.elements.extend(iterable)
    def insert(self, i, element):
        self.elements.insert(i, element)
    def remove(self, element):
        self.elements.remove(element)
    def clear(self):
        self.elements.clear()
    def index(self, *args, **kwargs):
        return self.elements.index(*args, **kwargs)
    def count(self, element):
        return self.elements.count(element)
    def reverse(self):
        self.elements.reverse()
    def draw_def(self, obj, **kwargs):
        if not hasattr(obj, 'write_svg_element'):
            elements = obj.to_drawables(elements=elements_module, **kwargs)
        else:
            assert len(kwargs) == 0
            elements = (obj,)
        self.other_defs.extend(elements)
    def append_def(self, element):
        self.other_defs.append(element)
    def all_elements(self):
        ''' Returns self.elements and self.ordered_elements as a single list. '''
        output = list(self.elements)
        for z in sorted(self.ordered_elements):
            output.extend(self.ordered_elements[z])
        return output
    def as_svg(self, output_file=None):
        return_string = output_file is None
        if return_string:
            output_file = StringIO()
        img_width, img_height = self.calc_render_size()
        start_str = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{}" height="{}" viewBox="{} {} {} {}"'''.format(
            img_width, img_height, *self.view_box)
        end_str = '</svg>'
        output_file.write(start_str)
        elements_module.write_xml_node_args(self.svg_args, output_file)
        output_file.write('>\n<defs>\n')
        # Write definition elements
        def id_gen(base=''):
            id_str = self.id_prefix + base + str(self.id_index)
            self.id_index += 1
            return id_str
        prev_set = set((id(defn) for defn in self.other_defs))
        def is_duplicate(obj):
            nonlocal prev_set
            dup = id(obj) in prev_set
            prev_set.add(id(obj))
            return dup
        for element in self.other_defs:
            try:
                element.write_svg_element(id_gen, is_duplicate, output_file,
                                          False)
                output_file.write('\n')
            except AttributeError:
                pass
        all_elements = self.all_elements()
        for element in all_elements:
            try:
                element.write_svg_defs(id_gen, is_duplicate, output_file, False)
            except AttributeError:
                pass
        output_file.write('</defs>\n')
        # Generate ids for normal elements
        prev_def_set = set(prev_set)
        for element in all_elements:
            try:
                element.write_svg_element(id_gen, is_duplicate, output_file,
                                          True)
            except AttributeError:
                pass
        prev_set = prev_def_set
        # Write normal elements
        for element in all_elements:
            try:
                element.write_svg_element(id_gen, is_duplicate, output_file,
                                          False)
                output_file.write('\n')
            except AttributeError:
                pass
        output_file.write(end_str)
        if return_string:
            return output_file.getvalue()
    def save_svg(self, fname):
        with open(fname, 'w') as f:
            self.as_svg(output_file=f)
    def save_png(self, fname):
        self.rasterize(to_file=fname)
    def rasterize(self, to_file=None):
        if to_file:
            return Raster.from_svg_to_file(self.as_svg(), to_file)
        else:
            return Raster.from_svg(self.as_svg())
    def _repr_svg_(self):
        ''' Display in Jupyter notebook '''
        if not self.display_inline:
            return None
        return self.as_svg()
    def _repr_html_(self):
        ''' Display in Jupyter notebook '''
        if self.display_inline:
            return None
        prefix = b'data:image/svg+xml;base64,'
        data = base64.b64encode(self.as_svg().encode())
        src = (prefix+data).decode()
        return '<img src="{}">'.format(src)
    def as_data_uri(self, strip_chars=STRIP_CHARS):
        ''' Returns a data URI with base64 encoding. '''
        data = self.as_svg()
        search = re.compile('|'.join(strip_chars))
        data_safe = search.sub(lambda m: '', data)
        b64 = base64.b64encode(data_safe.encode())
        return 'data:image/svg+xml;base64,' + b64.decode(encoding='ascii')
    def as_utf8_data_uri(self, unsafe_chars='"', strip_chars=STRIP_CHARS):
        ''' Returns a data URI without base64 encoding.

            The characters '#&%' are always escaped.  '#' and '&' break parsing
            of the data URI.  If '%' is not escaped, plain text like '%50' will
            be incorrectly decoded to 'P'.  The characters in `strip_chars`
            cause the SVG not to render even if they are escaped. '''
        data = self.as_svg()
        unsafe_chars = (unsafe_chars or '') + '#&%'
        replacements = {
            char: urllib.parse.quote(char, safe='')
            for char in unsafe_chars
        }
        replacements.update({
            char: ''
            for char in strip_chars
        })
        search = re.compile('|'.join(map(re.escape, replacements.keys())))
        data_safe = search.sub(lambda m: replacements[m.group(0)], data)
        return 'data:image/svg+xml;utf8,' + data_safe
