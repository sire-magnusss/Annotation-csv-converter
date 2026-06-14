# Generic Annotation CSV Converter

Convert a CVAT XML annotation export into two general-purpose CSV files:

- `images.csv`: one row per image
- `boxes.csv`: one row per bounding box

The converter uses only the Python standard library. No third-party packages are required.

## Quick Start

```bash
python3 annotation_csv_converter.py
```

By default, this reads `examples/sample_annotations.xml` and writes CSV files to `output/`.

To convert your own CVAT XML export:

```bash
python3 annotation_csv_converter.py path/to/annotations.xml --out output
```

## CSV Schema

`images.csv` contains:

- `image_id`
- `image_name`
- `item_id`
- `image_width`
- `image_height`
- `number_of_boxes`
- any image-level annotation attributes

`boxes.csv` contains:

- `item_id`
- `image_name`
- `box_id`
- `label`
- bounding box coordinates and dimensions
- any box-level annotation attributes

Annotation attributes are inferred from the XML and written as `attr_` columns, for example `attr_confidence`.

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Repository Hygiene

The sample data is synthetic and safe to publish. Generated files such as `output/`, CSV exports, Python caches, local virtual environments, and `.env` files are ignored by Git.
