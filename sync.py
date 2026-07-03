#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path

import pandas as pd

DEFAULT_MAPPINGS = {
    "shopify": {
        "Title": "name",
        "Body (HTML)": "description",
        "Variant SKU": "sku",
        "Variant Price": "price",
        "Variant Inventory Qty": "stock",
        "Variant Weight": "weight",
        "Status": "status",
    },
    "woocommerce": {
        "Name": "name",
        "SKU": "sku",
        "Price": "price",
        "Stock": "stock",
        "Description": "description",
        "Categories": "category",
    },
}


def guess_column(df: pd.DataFrame, hints: list[str]) -> str | None:
    for hint in hints:
        for col in df.columns:
            if hint in col.lower().replace(" ", "_"):
                return col
    return None


def map_columns(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    result = {}
    for target, source_field in mapping.items():
        if source_field in df.columns:
            result[target] = df[source_field]
        else:
            # Try fuzzy match
            hints = [source_field, source_field.replace("_", " ")]
            guessed = guess_column(df, hints)
            if guessed:
                result[target] = df[guessed]
            else:
                result[target] = ""
    return pd.DataFrame(result)


def main():
    parser = argparse.ArgumentParser(description="Convert supplier data to store format")
    parser.add_argument("input", help="Supplier file (CSV/Excel)")
    parser.add_argument("--template", "-t", choices=["shopify", "woocommerce"], help="Built-in template")
    parser.add_argument("--mapping", "-m", help="Custom mapping JSON file")
    args = parser.parse_args()

    if not args.template and not args.mapping:
        sys.exit("Specify --template or --mapping")

    p = Path(args.input)
    if p.suffix in (".csv", ".tsv"):
        sep = "\t" if p.suffix == ".tsv" else ","
        df = pd.read_csv(p, sep=sep, dtype=str)
    elif p.suffix in (".xls", ".xlsx"):
        df = pd.read_excel(p, dtype=str)
    else:
        sys.exit("Unsupported format")

    if args.mapping:
        with open(args.mapping) as f:
            mapping = json.load(f)
    else:
        mapping = DEFAULT_MAPPINGS[args.template]

    out = map_columns(df, mapping)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / f"{p.stem}_for_store.csv"
    out.to_csv(out_path, index=False)
    print(f"{len(out)} rows mapped → {out_path}")


if __name__ == "__main__":
    main()
