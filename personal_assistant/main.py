from __future__ import annotations

import argparse
import cmd
import difflib
import shlex
import sys
import traceback
from pathlib import Path
from typing import Callable, List, Optional

from personal_assistant.app.exceptions import PersonalAssistantError
from personal_assistant.app.models import Contact, Note
from personal_assistant.app.services import PersonalAssistantService


class AssistantCLI(cmd.Cmd):
    intro = "Personal Assistant CLI\nType 'help' to see commands. Use quotes for values with spaces."
    prompt = "assistant> "

    def __init__(self, service: PersonalAssistantService, debug_mode: bool = False) -> None:
        super().__init__()
        self.service = service
        self.debug_mode = debug_mode
        self.identchars += "-"
        self.commands = sorted(
            [
                "add-contact",
                "list-contacts",
                "search-contacts",
                "edit-contact",
                "delete-contact",
                "birthdays",
                "add-note",
                "list-notes",
                "search-notes",
                "edit-note",
                "delete-note",
                "sort-notes",
                "export-json",
                "import-json",
                "backup",
                "data-path",
                "help",
                "exit",
                "quit",
            ]
        )

    def parseline(self, line: str):  # type: ignore[override]
        cmd_name, arg, original = super().parseline(line)
        if cmd_name:
            cmd_name = cmd_name.replace("-", "_")
        return cmd_name, arg, original

    def default(self, line: str) -> None:
        token = line.strip().split(" ", 1)[0]
        hint = difflib.get_close_matches(token, self.commands, n=1, cutoff=0.5)
        if hint:
            print(f"Unknown command: {token}. Did you mean '{hint[0]}'?")
        else:
            print(f"Unknown command: {token}. Type 'help' for available commands.")

    @staticmethod
    def _split(arg: str) -> List[str]:
        return shlex.split(arg)

    def _execute_cli(self, parser: argparse.ArgumentParser, arg: str, callback: Callable[[argparse.Namespace], None]) -> None:
        try:
            try:
                args = parser.parse_args(self._split(arg))
            except SystemExit as exc:
                raise ValueError("Invalid command arguments.") from exc
            callback(args)
        except PersonalAssistantError as exc:
            print(f"Error: {exc}")
        except Exception as exc:
            print(f"Error: {exc}")
            if self.debug_mode:
                traceback.print_exc()

    @staticmethod
    def _parse_bool(raw: Optional[str]) -> Optional[bool]:
        if raw is None:
            return None
        if raw.lower() in {"on", "true", "1", "yes"}:
            return True
        if raw.lower() in {"off", "false", "0", "no"}:
            return False
        raise ValueError("Use on/off for this flag.")

    @staticmethod
    def _format_contact(contact: Contact) -> str:
        return (
            f"ID: {contact.id} | First name: {contact.first_name or '-'} | "
            f"Last name: {contact.last_name or '-'} | "
            f"Phone: {contact.formatted_phone or '-'} | Email: {contact.email or '-'} | "
            f"Country: {contact.country or '-'} | Birthday: {contact.birthday or '-'} | "
            f"Favorite: {'yes' if contact.favorite else 'no'}"
        )

    @staticmethod
    def _format_note(note: Note) -> str:
        return (
            f"ID: {note.id} | Title: {note.title} | "
            f"Tags: {', '.join(note.tags) if note.tags else '-'} | "
            f"Pinned: {'yes' if note.pinned else 'no'} | Favorite: {'yes' if note.favorite else 'no'}\n"
            f"Content: {note.content}"
        )

    def do_data_path(self, arg: str) -> None:
        """Show active data.json path."""
        print(self.service.get_data_path())

    def do_add_contact(self, arg: str) -> None:
        """add-contact [--first-name "John"] [--name "John"] [--last-name "Doe"] [--country "Ireland"] [--phone-number "+353 871234567"] [--phone "+353 871234567"] [--email x@y.com] [--address "..."] [--birthday DD/MM/YYYY] [--comment "..."] [--favorite]"""
        parser = argparse.ArgumentParser(prog="add-contact", add_help=False)
        parser.add_argument("--first-name")
        parser.add_argument("--name")  # legacy alias
        parser.add_argument("--nickname", default="", help=argparse.SUPPRESS)  # legacy ignored
        parser.add_argument("--last-name", default="")
        parser.add_argument("--country", default="")
        parser.add_argument("--country-code", help=argparse.SUPPRESS)  # legacy alias for phone prefix
        parser.add_argument("--phone-number")
        parser.add_argument("--phone", action="append", default=[])
        parser.add_argument("--email")
        parser.add_argument("--address")
        parser.add_argument("--birthday")
        parser.add_argument("--comment")
        parser.add_argument("--favorite", action="store_true")

        def _handler(args):
            first_name = (args.first_name or args.name or "").strip()
            if not first_name:
                raise ValueError("Provide --first-name (or legacy --name).")
            contact = self.service.add_contact(
                first_name=first_name,
                last_name=args.last_name,
                country=args.country,
                country_phone_code=args.country_code or "",
                phone_number=args.phone_number or "",
                phones=args.phone,
                email=args.email,
                address=args.address,
                birthday=args.birthday,
                comment=args.comment or "",
                favorite=args.favorite,
            )
            print(f"Added contact: {self._format_contact(contact)}")

        self._execute_cli(parser, arg, _handler)

    def do_list_contacts(self, arg: str) -> None:
        """list-contacts [--query "john"] [--filter all|favorites|with_birthday|without_birthday] [--sort name|birthday|created|updated]"""
        parser = argparse.ArgumentParser(prog="list-contacts", add_help=False)
        parser.add_argument("--query", default="")
        parser.add_argument("--filter", default="all")
        parser.add_argument("--sort", default="name")

        def _handler(args):
            contacts = self.service.list_contacts(query=args.query, filter_by=args.filter, sort_by=args.sort)
            if not contacts:
                print("No contacts found.")
                return
            for idx, contact in enumerate(contacts, start=1):
                print(f"{idx}. {self._format_contact(contact)}")

        self._execute_cli(parser, arg, _handler)

    def do_search_contacts(self, arg: str) -> None:
        """search-contacts --query john"""
        parser = argparse.ArgumentParser(prog="search-contacts", add_help=False)
        parser.add_argument("--query", required=True)

        def _handler(args):
            contacts = self.service.search_contacts(args.query)
            if not contacts:
                print("No contacts matched.")
                return
            for idx, contact in enumerate(contacts, start=1):
                print(f"{idx}. {self._format_contact(contact)}")

        self._execute_cli(parser, arg, _handler)

    def do_edit_contact(self, arg: str) -> None:
        """edit-contact --name "John" [--new-name "..."] [--add-phone "..."] [--remove-phone "..."] [--set-email "..."] [--clear-email] [--set-address "..."] [--clear-address] [--set-birthday DD/MM/YYYY] [--clear-birthday] [--set-comment "..."] [--clear-comment] [--favorite on|off]"""
        parser = argparse.ArgumentParser(prog="edit-contact", add_help=False)
        parser.add_argument("--name", required=True)
        parser.add_argument("--new-name")
        parser.add_argument("--add-phone", action="append", default=[])
        parser.add_argument("--remove-phone", action="append", default=[])
        parser.add_argument("--set-email")
        parser.add_argument("--clear-email", action="store_true")
        parser.add_argument("--set-address")
        parser.add_argument("--clear-address", action="store_true")
        parser.add_argument("--set-birthday")
        parser.add_argument("--clear-birthday", action="store_true")
        parser.add_argument("--set-comment")
        parser.add_argument("--clear-comment", action="store_true")
        parser.add_argument("--favorite")

        def _handler(args):
            updated = self.service.edit_contact_by_name(
                name=args.name,
                new_name=args.new_name,
                add_phones=args.add_phone,
                remove_phones=args.remove_phone,
                set_email=args.set_email,
                clear_email=args.clear_email,
                set_address=args.set_address,
                clear_address=args.clear_address,
                set_birthday=args.set_birthday,
                clear_birthday=args.clear_birthday,
                set_comment=args.set_comment,
                clear_comment=args.clear_comment,
                favorite=self._parse_bool(args.favorite),
            )
            print(f"Updated contact: {self._format_contact(updated)}")

        self._execute_cli(parser, arg, _handler)

    def do_delete_contact(self, arg: str) -> None:
        """delete-contact --name John"""
        parser = argparse.ArgumentParser(prog="delete-contact", add_help=False)
        parser.add_argument("--name", required=True)

        def _handler(args):
            self.service.delete_contact_by_name(args.name)
            print("Contact deleted.")

        self._execute_cli(parser, arg, _handler)

    def do_birthdays(self, arg: str) -> None:
        """birthdays --days 14"""
        parser = argparse.ArgumentParser(prog="birthdays", add_help=False)
        parser.add_argument("--days", type=int, required=True)

        def _handler(args):
            rows = self.service.upcoming_birthdays(args.days)
            if not rows:
                print("No upcoming birthdays in this period.")
                return
            for idx, row in enumerate(rows, start=1):
                contact = row["contact"]
                print(f"{idx}. {self.service.get_contact_display_name(contact)} -> {row['next_birthday']} ({row['days_left']} days)")

        self._execute_cli(parser, arg, _handler)

    def do_add_note(self, arg: str) -> None:
        """add-note [--title "..."] [--content "..."] [--text "..."] [--tag work] [--pinned] [--favorite] [--color-label blue]"""
        parser = argparse.ArgumentParser(prog="add-note", add_help=False)
        parser.add_argument("--title")
        parser.add_argument("--content")
        parser.add_argument("--text")
        parser.add_argument("--tag", action="append", default=[])
        parser.add_argument("--pinned", action="store_true")
        parser.add_argument("--favorite", action="store_true")
        parser.add_argument("--color-label", default="default")

        def _handler(args):
            if args.text and not args.title and not args.content:
                note = self.service.add_note_legacy(args.text, tags=args.tag)
            else:
                title = args.title or (args.content or args.text or "").splitlines()[0][:40]
                content = args.content or args.text or ""
                note = self.service.add_note(
                    title=title,
                    content=content,
                    tags=args.tag,
                    pinned=args.pinned,
                    favorite=args.favorite,
                    color_label=args.color_label,
                )
            print(f"Added note: {self._format_note(note)}")

        self._execute_cli(parser, arg, _handler)

    def do_list_notes(self, arg: str) -> None:
        """list-notes [--query "..."] [--tag "..."] [--filter all|pinned|favorites] [--sort updated|created|title]"""
        parser = argparse.ArgumentParser(prog="list-notes", add_help=False)
        parser.add_argument("--query", default="")
        parser.add_argument("--tag", default="")
        parser.add_argument("--filter", default="all")
        parser.add_argument("--sort", default="updated")

        def _handler(args):
            notes = self.service.list_notes(query=args.query, tag=args.tag, filter_by=args.filter, sort_by=args.sort)
            if not notes:
                print("No notes found.")
                return
            for note in notes:
                print(self._format_note(note))
                print("-" * 60)

        self._execute_cli(parser, arg, _handler)

    def do_search_notes(self, arg: str) -> None:
        """search-notes [--query "..."] [--tag "..."]"""
        parser = argparse.ArgumentParser(prog="search-notes", add_help=False)
        parser.add_argument("--query")
        parser.add_argument("--tag")

        def _handler(args):
            if not args.query and not args.tag:
                raise ValueError("Provide at least --query or --tag.")
            notes = self.service.search_notes(query=args.query, tag=args.tag)
            if not notes:
                print("No notes matched.")
                return
            for note in notes:
                print(self._format_note(note))
                print("-" * 60)

        self._execute_cli(parser, arg, _handler)

    def do_edit_note(self, arg: str) -> None:
        """edit-note --id 1 [--title "..."] [--content "..."] [--text "..."] [--tag "..."] [--pinned on|off] [--favorite on|off] [--color-label blue]"""
        parser = argparse.ArgumentParser(prog="edit-note", add_help=False)
        parser.add_argument("--id", type=int, required=True)
        parser.add_argument("--title")
        parser.add_argument("--content")
        parser.add_argument("--text")
        parser.add_argument("--tag", action="append")
        parser.add_argument("--pinned")
        parser.add_argument("--favorite")
        parser.add_argument("--color-label")

        def _handler(args):
            note = self.service.get_note(args.id)
            if args.text is not None and args.content is None:
                args.content = args.text
            updated = self.service.update_note(
                note_id=args.id,
                title=args.title if args.title is not None else note.title,
                content=args.content if args.content is not None else note.content,
                tags=args.tag if args.tag is not None else note.tags,
                pinned=note.pinned if args.pinned is None else self._parse_bool(args.pinned) or False,
                favorite=note.favorite if args.favorite is None else self._parse_bool(args.favorite) or False,
                color_label=args.color_label if args.color_label is not None else note.color_label,
            )
            print(f"Updated note: {self._format_note(updated)}")

        self._execute_cli(parser, arg, _handler)

    def do_delete_note(self, arg: str) -> None:
        """delete-note --id 1"""
        parser = argparse.ArgumentParser(prog="delete-note", add_help=False)
        parser.add_argument("--id", type=int, required=True)

        def _handler(args):
            self.service.delete_note(args.id)
            print("Note deleted.")

        self._execute_cli(parser, arg, _handler)

    def do_sort_notes(self, arg: str) -> None:
        """sort-notes --tag work"""
        parser = argparse.ArgumentParser(prog="sort-notes", add_help=False)
        parser.add_argument("--tag", required=True)

        def _handler(args):
            notes = self.service.sort_notes_by_tag(args.tag)
            if not notes:
                print("No notes found.")
                return
            for note in notes:
                print(self._format_note(note))
                print("-" * 60)

        self._execute_cli(parser, arg, _handler)

    def do_export_json(self, arg: str) -> None:
        """export-json --path C:\\temp\\export.json"""
        parser = argparse.ArgumentParser(prog="export-json", add_help=False)
        parser.add_argument("--path", required=True)

        def _handler(args):
            self.service.export_json(Path(args.path))
            print("Export completed.")

        self._execute_cli(parser, arg, _handler)

    def do_import_json(self, arg: str) -> None:
        """import-json --path C:\\temp\\data.json"""
        parser = argparse.ArgumentParser(prog="import-json", add_help=False)
        parser.add_argument("--path", required=True)

        def _handler(args):
            self.service.import_json(Path(args.path))
            print("Import completed.")

        self._execute_cli(parser, arg, _handler)

    def do_backup(self, arg: str) -> None:
        """Create backup file in backups folder."""
        try:
            path = self.service.create_backup()
            print(f"Backup created: {path}")
        except Exception as exc:
            print(f"Error: {exc}")

    def do_exit(self, arg: str) -> bool:
        """Exit program."""
        print("Bye.")
        return True

    def do_quit(self, arg: str) -> bool:
        """Exit program."""
        return self.do_exit(arg)

    def emptyline(self) -> None:
        pass


def main() -> None:
    debug_mode = "--debug" in sys.argv
    service = PersonalAssistantService()
    AssistantCLI(service, debug_mode=debug_mode).cmdloop()


if __name__ == "__main__":
    main()
