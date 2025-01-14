import os
from collections.abc import Generator

from docx import Document
from marko.block import BlankLine, Paragraph, CodeBlock, FencedCode, \
    BlockElement
from marko.inline import Image

from .extended_markdown import markdown, Caption
from .renderable.caption import CaptionInfo
from .renderable.renderable import Renderable
from .renderable_factory import RenderableFactory


class Parser:
    """Parses given markdown string and returns Renderable elements"""

    def __init__(self, document: Document):
        self._document = document
        self._renderables = []
        self._factory = RenderableFactory(self._document._body)
        self._caption_info: CaptionInfo | None = None

    @staticmethod
    def resolve_paths(marko_element: BlockElement, relative_dir_path: str):
        """Resolves relative paths in Marko elements"""
        if isinstance(marko_element, Paragraph):
            for child in marko_element.children:
                if isinstance(child, Image) and not child.dest.startswith(
                        "http"):
                    child.dest = os.path.join(
                        relative_dir_path, os.path.expanduser(child.dest))
        if isinstance(marko_element,
                      (CodeBlock, FencedCode)) and marko_element.extra:
            marko_element.extra = os.path.join(
                relative_dir_path, os.path.expanduser(marko_element.extra))

    def parse(self, text, relative_dir_path: str) -> None:
        marko_parsed = markdown.parse(text)
        for marko_element in marko_parsed.children:
            self.resolve_paths(marko_element, relative_dir_path)

            if isinstance(marko_element, BlankLine):
                continue

            if isinstance(marko_element, Caption):
                self._caption_info =\
                    CaptionInfo(marko_element.unique_name, marko_element.text)
                continue

            for renderable in self._factory.create(marko_element, self._caption_info):
                self._renderables.append(renderable)
            self._caption_info = None

    def get_rendered(self) -> list[Renderable]:
        return self._renderables
