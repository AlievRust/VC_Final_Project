"""Делит текст по абзацам и предложениям, сохраняя небольшой контекст."""

import re


def _pieces(text: str, size: int) -> list[str]:
    pieces: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        paragraph = " ".join(paragraph.split())
        if not paragraph:
            continue
        if len(paragraph) <= size:
            pieces.append(paragraph)
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            if len(sentence) <= size:
                pieces.append(sentence)
            else:
                words = sentence.split()
                current = ""
                for word in words:
                    if current and len(current) + len(word) + 1 > size:
                        pieces.append(current)
                        current = ""
                    if len(word) > size:
                        if current:
                            pieces.append(current)
                            current = ""
                        pieces.extend(word[i : i + size] for i in range(0, len(word), size))
                    else:
                        current = f"{current} {word}".strip()
                if current:
                    pieces.append(current)
    return pieces


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Объединяет короткие фрагменты; overlap добавляет хвост предыдущего chunk."""
    if size < 8 or not 0 <= overlap <= size - 3:
        raise ValueError("Некорректные параметры chunking")
    result: list[str] = []
    current = ""
    for piece in _pieces(text, size - overlap - 2 if overlap else size):
        candidate = f"{current}\n\n{piece}" if current else piece
        if current and len(candidate) > size:
            result.append(current)
            prefix = ""
            if overlap:
                tail = current[-overlap:]
                if len(current) > overlap and current[-overlap - 1].isalnum() and tail[0].isalnum():
                    tail = tail.partition(" ")[2]
                prefix = tail.strip()
            current = f"{prefix}\n\n{piece}".strip() if prefix else piece
        else:
            current = candidate
    if current:
        result.append(current)
    return result
