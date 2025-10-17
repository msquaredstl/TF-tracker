from unittest import TestCase

from app.importers.import_csv import split_characters


class SplitCharactersTests(TestCase):
    def test_handles_commas_and_semicolons(self) -> None:
        values = "Optimus Prime |primary; Bumblebee, Megatron"
        self.assertEqual(
            split_characters(values),
            ["Optimus Prime |primary", "Bumblebee", "Megatron"],
        )

    def test_trims_primary_marker_whitespace(self) -> None:
        values = "Arcee | primary, Ultra Magnus | Primary ; Rodimus |   PRIMARY"
        self.assertEqual(
            split_characters(values),
            ["Arcee |primary", "Ultra Magnus |Primary", "Rodimus |PRIMARY"],
        )
