import csv
import tempfile
import unittest
from pathlib import Path

from annotation_csv_converter import convert, parse_annotation_xml


SAMPLE_XML = Path("examples/sample_annotations.xml")


class AnnotationCsvConverterTests(unittest.TestCase):
    def test_parse_sample_xml(self) -> None:
        images, boxes = parse_annotation_xml(SAMPLE_XML)

        self.assertEqual(len(images), 1)
        self.assertEqual(len(boxes), 3)
        self.assertEqual(images[0]["image_name"], "sample_image_001.jpg")
        self.assertEqual(boxes[0]["label"], "OBJECT")
        self.assertEqual(boxes[0]["box_width"], 63.48)
        self.assertEqual(boxes[0]["attr_confidence"], "High")

    def test_convert_writes_expected_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            images_path, boxes_path, image_count, box_count = convert(
                SAMPLE_XML,
                Path(temp_dir),
            )

            self.assertEqual(image_count, 1)
            self.assertEqual(box_count, 3)
            self.assertTrue(images_path.exists())
            self.assertTrue(boxes_path.exists())

            with boxes_path.open(newline="", encoding="utf-8") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(rows[0]["item_id"], "sample_image_001")
        self.assertEqual(rows[0]["attr_category"], "type_a")


if __name__ == "__main__":
    unittest.main()
