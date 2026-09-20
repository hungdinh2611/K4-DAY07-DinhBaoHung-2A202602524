"""Section-based chunking for policy documents, with heading ancestry retained."""
import re

from .chunking import RecursiveChunker


class HeadingChunker:
    def __init__(self, chunk_size: int = 800) -> None:
        if chunk_size <= 0:
            raise ValueError('chunk_size must be positive')
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        sections = []
        headings = []
        body = []
        fence = None
        for line in text.splitlines(keepends=True):
            fence_match = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
            if fence_match:
                marker = fence_match[1]
                if fence is None:
                    fence = marker
                elif marker[0] == fence[0] and len(marker) >= len(fence):
                    fence = None
                body.append(line)
                continue
            heading = re.match(r'^(#{1,6})[ \t]+(.+?)\s*$', line) if fence is None else None
            if heading:
                if ''.join(body).strip():
                    sections.append((list(headings), ''.join(body)))
                body = []
                level = len(heading[1])
                headings = [(n, h) for n, h in headings if n < level]
                headings.append((level, line.strip()))
            else:
                body.append(line)
        if ''.join(body).strip() or headings:
            sections.append((headings, ''.join(body)))

        chunks = []
        for ancestors, content in sections:
            title = '\n'.join(h for _, h in ancestors)
            content = content.strip()
            if not content:
                if len(title) > self.chunk_size:
                    raise ValueError('Heading path exceeds chunk_size')
                if title:
                    chunks.append(title)
                continue
            prefix = title + '\n\n' if title else ''
            budget = self.chunk_size - len(prefix)
            if budget <= 0:
                raise ValueError('chunk_size must leave room after the complete heading path')
            for part in RecursiveChunker(chunk_size=budget).chunk(content):
                if part.strip():
                    chunks.append(prefix + part.strip())
        return chunks
