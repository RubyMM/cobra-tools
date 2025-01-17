import os

from .BaseClass import BaseClass
from codegen.naming_conventions import clean_comment_str, name_module


class Module:

    def __init__(self, parser, element):
        self.parser = parser
        self.element = element
        self.read(element)
        self.write(parser.path_dict[name_module(element.attrib["name"])])

    def read(self, element):
        self.comment_str = clean_comment_str(element.text, indent="", class_comment='"""')[2:]
        self.priority = int(element.attrib.get("priority", "0"))
        self.depends = [name_module(module) for module in element.attrib.get("depends", "").split()]
        self.custom = bool(eval(element.attrib.get("custom", "false").replace(
            "true", "True").replace("false", "False"), {}))

    def write(self, module_path):
        init_path = os.path.join(BaseClass.get_out_path(os.path.join(module_path, "__init__")))
        with open(init_path, "w", encoding=self.parser.encoding) as file:
            file.write(self.comment_str)
            file.write(f'\n\n__priority__ = {repr(self.priority)}')
            file.write(f'\n__depends__ = {repr(self.depends)}')
            file.write(f'\n__custom__ = {repr(self.custom)}')
            file.write(f'\n')
