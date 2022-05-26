import csv
import json
import pathlib

import click

import log as l

COLUMN_NAMES = ["block_number", "tx_index", "from", "to", "gas"]


@click.command(
    help="""Extract account interactions from a set of blocks.

The input directory must contain JSON encoded blocks (one block per file), including transactions.
The output is a CSV file with columns "block_number", "tx_index", "from", "to" and "gas".

Note that only direct interactions between EOA and contract accounts are counted as the input data
contains no information about internal message calls.
"""
)
@click.option(
    "--input",
    "-i",
    "input_dir",
    required=True,
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    help="input directory containing blocks",
)
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(dir_okay=False, path_type=pathlib.Path),
    help="output file",
)
def main(input_dir, output):
    interactions = []
    num_blocks = len(list(input_dir.iterdir()))

    with l.Line() as line:
        for i, p in enumerate(input_dir.iterdir()):
            line.write(f"processing block {l.progress(i, num_blocks)}...")
            if not p.is_file():
                continue
            try:
                with open(p) as f:
                    block = json.load(f)
            except:
                print(f"error loading block at {p}")
                raise

            block_number = int(block["number"], 16)
            for j, tx in enumerate(block["transactions"]):
                if "to" not in tx or tx["to"] is None:
                    continue
                interaction = {
                    "block_number": block_number,
                    "tx_index": j,
                    "from": tx["from"],
                    "to": tx["to"],
                    "gas": int(tx["gas"], 16),
                }
                assert set(interaction.keys()) == set(COLUMN_NAMES)
                interactions.append(interaction)

        line.write(f"found {len(interactions)} interactions, exporting as csv...")

        with output.open("w", newline="") as f:
            writer = csv.DictWriter(f, COLUMN_NAMES)
            writer.writeheader()
            for interaction in interactions:
                writer.writerow(interaction)

        line.write(f"found {len(interactions)} interactions")


def load_blocks_lazy(d):
    for p in d.iterdir():
        if not p.is_file():
            continue
        try:
            with open(p) as f:
                block = json.load(f)
        except:
            print(f"error loading block at {p}")
            raise
        yield block


if __name__ == "__main__":
    main()
