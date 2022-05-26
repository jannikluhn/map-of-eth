import collections
import itertools
import json
import pathlib
import random

import click
import networkx as nx

import dot
import log as l


EDGE_PROBABILITY = 0.3
DEFAULT_NODE_ATTRS = {
    "label": "",
    "shape": "circle",
}


@click.command(
    help="""Create a contract graph.

The input directory must contain JSON encoded blocks (one block per file) with fully populated
transaction fields. The resulting graph is written to the output file (or stdout by default) in
DOT format for further processing.

The graph is constructed as follows: Each node represents one contract. Nodes are connected by an
edge if there is at least one EOA account that interacted with both contracts in the input data.
The edge is weighted by the number of accounts with these pairwise interactions.

To reduce the data size, pairwise interactions are only counted with a probability of 30%."""
)
@click.option(
    "--input",
    "-i",
    "input_dir",
    required=True,
    type=click.Path(file_okay=False, path_type=pathlib.Path),
    help="input directory containing blocks",
)
@click.option("--output", "-o", default="-", type=click.File("w"), help="output file")
def main(input_dir, output):
    blocks = load_blocks_lazy(input_dir)
    nodes, edges = create_contract_graph(blocks)
    dot.store_graph(nodes, edges, output)

    l.log("done")


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


def create_contract_graph(blocks):
    l.log("counting contract interactions...")
    interactions = collections.defaultdict(set)
    num_interactions = 0
    contracts = set()
    with l.Line() as line:
        for i, block in enumerate(blocks):
            line.write(f"processing block {i}...")
            for tx in block["transactions"]:
                if "to" not in tx or tx["to"] is None:
                    continue  # ignore contract creations
                gas_used = int(tx["gas"], 16)
                if gas_used == 21000 or tx["input"] == "0x":
                    continue  # ignore non-contract calls
                sender = tx["from"]
                receiver = tx["to"]

                contracts.add(receiver)
                if sender not in interactions or receiver not in interactions[sender]:
                    num_interactions += 1
                interactions[sender].add(receiver)
        line.write(
            f"found {num_interactions} interactions with {len(contracts)} contracts"
        )

    l.log("creating edges...")
    edge_dict = {}
    node_dict = {}
    with l.Line() as line:
        for i, (_, contracts) in enumerate(interactions.items()):
            line.write(f"num edges: {len(edge_dict)}")
            for n1, n2 in itertools.combinations(contracts, 2):
                if not random.random() < EDGE_PROBABILITY:
                    continue
                node_dict[n1] = {}
                node_dict[n2] = {}
                edge = tuple(sorted([n1, n2]))
                if edge not in edge_dict:
                    edge_dict[edge] = {"weight": 0}
                edge_dict[edge]["weight"] += 1
        edges_per_node = len(edge_dict) / len(node_dict)
        line.write(f"created {len(edge_dict)} edges ({edges_per_node:.1f} per node)")

    l.log("created graph")
    return node_dict, edge_dict


if __name__ == "__main__":
    main()
