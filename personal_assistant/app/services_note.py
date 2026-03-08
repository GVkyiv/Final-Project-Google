from datetime import datetime
from typing import List, Optional

from .exceptions import NotFoundError
from .models import Note
from .utils import normalize_tags, now_iso
from .validators import validate_required


class NoteService:
    def __init__(self, facade) -> None:
        self.facade = facade

    @property
    def data(self):
        return self.facade.data

    @staticmethod
    def _safe_dt(raw: str) -> datetime:
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return datetime.fromtimestamp(0)

    def _note_index(self, note_id: int) -> int:
        for index, note in enumerate(self.data.notes):
            if note.id == note_id:
                return index
        raise NotFoundError(f"Note not found: {note_id}")

    def get_note(self, note_id: int) -> Note:
        return self.data.notes[self._note_index(note_id)]

    def list_notes(
        self,
        query: str = "",
        tag: str = "",
        filter_by: str = "all",
        sort_by: str = "updated",
    ) -> List[Note]:
        query_l = query.strip().lower()
        tag_l = tag.strip().lower()
        notes = list(self.data.notes)

        if query_l:
            notes = [
                note
                for note in notes
                if query_l in note.title.lower() or query_l in note.content.lower()
            ]

        if tag_l:
            notes = [note for note in notes if tag_l in note.tags]

        if filter_by == "pinned":
            notes = [note for note in notes if note.pinned]
        elif filter_by == "favorites":
            notes = [note for note in notes if note.favorite]

        if sort_by == "title":
            notes.sort(key=lambda item: item.title.lower())
        elif sort_by == "created":
            notes.sort(key=lambda item: self._safe_dt(item.created_at), reverse=True)
        else:
            notes.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)

        return notes

    def add_note(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        pinned: bool = False,
        favorite: bool = False,
        color_label: str = "default",
    ) -> Note:
        prepared_title = validate_required(title, "Title")
        prepared_content = validate_required(content, "Content")

        stamp = now_iso()
        note = Note(
            id=self.data.next_note_id,
            title=prepared_title,
            content=prepared_content,
            tags=normalize_tags(tags or []),
            pinned=bool(pinned),
            favorite=bool(favorite),
            color_label=color_label.strip() or "default",
            created_at=stamp,
            updated_at=stamp,
        )
        self.data.notes.append(note)
        self.data.next_note_id += 1
        self.facade._autosave()
        return note

    def update_note(
        self,
        note_id: int,
        title: str,
        content: str,
        tags: List[str],
        pinned: bool,
        favorite: bool,
        color_label: str,
    ) -> Note:
        index = self._note_index(note_id)
        note = self.data.notes[index]

        note.title = validate_required(title, "Title")
        note.content = validate_required(content, "Content")
        note.tags = normalize_tags(tags)
        note.pinned = bool(pinned)
        note.favorite = bool(favorite)
        note.color_label = color_label.strip() or "default"
        note.updated_at = now_iso()

        self.facade._autosave()
        return note

    def toggle_note_pinned(self, note_id: int) -> Note:
        note = self.get_note(note_id)
        note.pinned = not note.pinned
        note.updated_at = now_iso()
        self.facade._autosave()
        return note

    def toggle_note_favorite(self, note_id: int) -> Note:
        note = self.get_note(note_id)
        note.favorite = not note.favorite
        note.updated_at = now_iso()
        self.facade._autosave()
        return note

    def delete_note(self, note_id: int) -> None:
        index = self._note_index(note_id)
        del self.data.notes[index]
        self.facade._autosave()

    def add_note_legacy(self, text: str, tags: Optional[List[str]] = None) -> Note:
        cleaned = validate_required(text, "Text")
        title = cleaned.splitlines()[0][:40]
        return self.add_note(title=title, content=cleaned, tags=tags)

    def edit_note_legacy(self, note_id: int, text: Optional[str] = None, tags: Optional[List[str]] = None) -> Note:
        note = self.get_note(note_id)
        return self.update_note(
            note_id=note_id,
            title=note.title,
            content=text if text is not None else note.content,
            tags=tags if tags is not None else note.tags,
            pinned=note.pinned,
            favorite=note.favorite,
            color_label=note.color_label,
        )

    def search_notes(self, query: Optional[str] = None, tag: Optional[str] = None) -> List[Note]:
        return self.list_notes(query=query or "", tag=tag or "")

    def sort_notes_by_tag(self, tag: str) -> List[Note]:
        tag_l = tag.strip().lower()
        with_tag = [note for note in self.data.notes if tag_l in note.tags]
        without_tag = [note for note in self.data.notes if tag_l not in note.tags]
        with_tag.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)
        without_tag.sort(key=lambda item: self._safe_dt(item.updated_at), reverse=True)
        return with_tag + without_tag
