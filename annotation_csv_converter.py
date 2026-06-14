#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Any


DEFAULT_XML_PATH = Path("examples/sample_annotations.xml")
DEFAULT_OUTPUT_DIR = Path("output")


IMAGE_BASE_COLUMNS = [
    "image_id",
    "image_name",
    "item_id",
    "image_width",
    "image_height",
    "number_of_boxes",
]


BOX_BASE_COLUMNS = [
    "item_id",
    "image_name",
    "box_id",
    "label",
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "box_width",
    "box_height",
]


Row = dict[str, Any]


def normalise_text(value: str | None) -> str:
    """Return a stripped string, or an empty string for missing values."""
    if value is None:
        return ""
    return value.strip()


def normalise_key(value: str | None) -> str:
    """Normalise names into stable CSV column suffixes."""
    value = normalise_text(value).lower()
    for old, new in [(" ", "_"), ("-", "_"), (".", "_"), ("/", "_")]:
        value = value.replace(old, new)
    return "".join(char for char in value if char.isalnum() or char == "_")


def prefixed_attribute_column(name: str) -> str:
    """Build a CSV column name for an annotation attribute."""
    return f"attr_{normalise_key(name)}"


def derive_item_id(image_name: str) -> str:
    """Derive a neutral item ID from the image filename."""
    return Path(image_name).stem


def parse_float(value: str | None) -> float:
    """Parse a coordinate value, defaulting missing values to 0.0."""
    value = normalise_text(value)
    if not value:
        return 0.0
    return float(value)


def extract_attributes(element: ET.Element) -> dict[str, str]:
    """Extract child attributes from an XML element."""
    attributes = {}

    for attr in element.findall("attribute"):
        name = normalise_text(attr.attrib.get("name"))
        if name:
            attributes[prefixed_attribute_column(name)] = normalise_text(attr.text)

    return attributes


def extract_image_attributes(image_element: ET.Element) -> dict[str, str]:
    """Extract direct image attributes and image-level tag attributes."""
    attributes = extract_attributes(image_element)

    for tag in image_element.findall("tag"):
        tag_label = normalise_text(tag.attrib.get("label"))
        if tag_label:
            attributes.setdefault("tag_label", tag_label)
        attributes.update(extract_attributes(tag))

    return attributes


def parse_annotation_xml(
    xml_path: Path,
) -> tuple[list[Row], list[Row]]:
    """Parse annotation XML into image rows and box rows."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    if root.tag != "annotations":
        raise ValueError(f"Expected root element 'annotations', found '{root.tag}'.")

    images = []
    boxes = []

    for image_element in root.findall("image"):
        image_id = normalise_text(image_element.attrib.get("id"))
        image_name = normalise_text(image_element.attrib.get("name"))
        image_width = normalise_text(image_element.attrib.get("width"))
        image_height = normalise_text(image_element.attrib.get("height"))
        item_id = derive_item_id(image_name)
        image_boxes = []

        for box_index, box_element in enumerate(image_element.findall("box"), start=1):
            x_min = parse_float(box_element.attrib.get("xtl"))
            y_min = parse_float(box_element.attrib.get("ytl"))
            x_max = parse_float(box_element.attrib.get("xbr"))
            y_max = parse_float(box_element.attrib.get("ybr"))

            box_row = {
                "item_id": item_id,
                "image_name": image_name,
                "box_id": box_index,
                "label": normalise_text(box_element.attrib.get("label")),
                "x_min": round(x_min, 2),
                "y_min": round(y_min, 2),
                "x_max": round(x_max, 2),
                "y_max": round(y_max, 2),
                "box_width": round(x_max - x_min, 2),
                "box_height": round(y_max - y_min, 2),
                **extract_attributes(box_element),
            }

            image_boxes.append(box_row)
            boxes.append(box_row)

        images.append(
            {
                "image_id": image_id,
                "image_name": image_name,
                "item_id": item_id,
                "image_width": image_width,
                "image_height": image_height,
                "number_of_boxes": len(image_boxes),
                **extract_image_attributes(image_element),
            }
        )

    return images, boxes


def collect_columns(base_columns: list[str], rows: list[Row]) -> list[str]:
    """Return base columns followed by sorted dynamic columns."""
    dynamic_columns = sorted({
        column for row in rows for column in row if column not in base_columns
    })
    return [*base_columns, *dynamic_columns]


def write_csv(path: Path, rows: list[Row], columns: list[str]) -> None:
    """Write rows to a CSV file using a stable column order."""
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def convert(xml_path: Path, output_dir: Path) -> tuple[Path, Path, int, int]:
    """Convert annotation XML into images and boxes CSV files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    images, boxes = parse_annotation_xml(xml_path)

    images_csv_path = output_dir / "images.csv"
    boxes_csv_path = output_dir / "boxes.csv"

    write_csv(images_csv_path, images, collect_columns(IMAGE_BASE_COLUMNS, images))
    write_csv(boxes_csv_path, boxes, collect_columns(BOX_BASE_COLUMNS, boxes))

    return images_csv_path, boxes_csv_path, len(images), len(boxes)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert annotation XML to images.csv and boxes.csv."
    )
    parser.add_argument(
        "xml_path",
        nargs="?",
        type=Path,
        default=DEFAULT_XML_PATH,
        help=f"Path to annotation XML file. Default: {DEFAULT_XML_PATH}",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output folder for images.csv and boxes.csv.",
    )

    args = parser.parse_args()
    if not args.xml_path.exists():
        parser.error(f"XML file does not exist: {args.xml_path}")

    images_csv_path, boxes_csv_path, image_count, box_count = convert(
        args.xml_path,
        args.out,
    )

    print("Conversion complete.")
    print(f"Images written to: {images_csv_path}")
    print(f"Boxes written to: {boxes_csv_path}")
    print(f"Number of images: {image_count}")
    print(f"Number of boxes: {box_count}")


if __name__ == "__main__":
    main()
