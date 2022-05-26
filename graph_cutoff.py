import itertools

import click
import pandas as pd

import dot
import log as l

GAS_CUTOFF = 0.2
ADDRESS_DTYPE = "|U42"


@click.command()
@click.option(
    "--input",
    "-i",
    "input_path",
    required=True,
    type=click.File(),
    help="interactions file used as input",
)
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.File("w"),
    help="output file",
)
def main(input_path, output):
    l.log("loading dataset...")

    interactions = pd.read_csv(input_path)
    for key in ["from", "to"]:
        interactions[key] = interactions[key].astype(ADDRESS_DTYPE)

    l.log(f"reducing dataset of {len(interactions)} interactions...")

    # find receivers with highest gas usage such that selection covers GAS_CUTOFF of all gas used
    gas_users = interactions[["to", "gas"]].groupby("to").sum().sort_values("gas")
    gas_users_cum = gas_users["gas"].cumsum()
    high_gas_users_mask = gas_users_cum > GAS_CUTOFF * gas_users_cum.iloc[-1]
    high_gas_users = gas_users[high_gas_users_mask].index

    # filter interactions
    interactions = interactions[interactions["to"].isin(high_gas_users)]

    # aggregate transactions with same from and to
    interactions = (
        interactions[["from", "to", "gas"]].groupby(["from", "to"]).sum().reset_index()
    )

    l.log(f"computing edges from {len(interactions)} interactions...")

    groups = interactions[["to", "from"]].groupby("from")

    edges = {}
    nodes = {}
    for _, g in groups:
        for n1, n2 in itertools.combinations(g["to"], 2):
            nodes[n1] = {"width": (gas_users["gas"][n1] / 1000000) ** 0.5}
            nodes[n2] = {"width": (gas_users["gas"][n2] / 1000000) ** 0.5}
            edge = tuple(sorted([n1, n2]))
            if edge not in edges:
                edges[edge] = {"weight": 0}
            edges[edge]["weight"] += 1

    l.log(f"storing graph with {len(nodes)} nodes and {len(edges)} edges")

    dot.store_graph(nodes, edges, output)


if __name__ == "__main__":
    main()
