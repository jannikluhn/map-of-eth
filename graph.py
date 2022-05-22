import click
import collections
import itertools
import json
import pathlib
import random
import networkx as nx
import log as l


EDGE_PROBABILITY = 1
PRUNE_WEIGHT = 1


@click.command()
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
    # graph = create_contract_graph(blocks)
    # nx.drawing.nx_pydot.write_dot(graph, output)
    nodes, edges = create_contract_graph(blocks)
    dump_graph(nodes, edges, output)
    # nx.drawing.nx_pydot.write_dot(graph, output)

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
                if int(tx["gas"], 16) == 21000 or tx["input"] == "0x":
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
    node_set = set()
    with l.Line() as line:
        for i, (_, contracts) in enumerate(interactions.items()):
            line.write(f"num edges: {len(edge_dict)}")
            for n1, n2 in itertools.combinations(contracts, 2):
                if not random.random() < EDGE_PROBABILITY:
                    continue
                node_set.add(n1)
                node_set.add(n2)
                edge = tuple(sorted([n1, n2]))
                if edge not in edge_dict:
                    edge_dict[edge] = (edge[0], edge[1], {"weight": 0})
                edge_dict[edge][2]["weight"] += 1
        edges_per_node = len(edge_dict) / len(node_set)
        line.write(f"created {len(edge_dict)} edges ({edges_per_node:.1f} per node)")

    # l.log("pruning light edges...")
    # edges_to_prune = []
    # with l.Line() as line:
    #     num_edges_unpruned = len(edge_dict)
    #     for i, (edge, (_, _, attrs)) in enumerate(edge_dict.items()):
    #         line.write(f"searching edges ({l.progress(i, len(edge_dict))})")
    #         if attrs["weight"] <= 1:
    #             edges_to_prune.append(edge)
    #     for i, edge in enumerate(edges_to_prune):
    #         line.write(f"pruning edges ({l.progress(i, len(edges_to_prune))})")
    #         edge_dict.pop(edge)
    #     line.write(f"pruned {len(edges_to_prune)} of {num_edges_unpruned} edges")

    l.log("created graph")
    return node_set, edge_dict

    # l.log("creating graph...")
    # g = nx.Graph()
    # g.add_nodes_from(node_set, label="", shape="circle")
    # g.add_edges_from(edge_dict.values())

    # return g


def dump_graph(nodes, edges, path):
    l.log("dumping graph")
    with path.open() as f:
        f.write("strict graph {\n")
        for n in nodes:
            f.write(f'"{n}" [label="", shape=circle];\n')
        for n1, n2, attrs in edges.values():
            attr_str = ", ".join([f'{k}="{v}"' for k, v in attrs.items()])
            f.write(f'"{n1}" -- "{n2}"  [{attr_str}];\n')
        f.write("}")


def create_call_graph(blocks):
    node_set = set()
    edge_dict = collections.defaultdict(int)

    l.log("creating edges from blocks...")
    with l.ProgressPrinter(len(blocks)) as p:
        for i, block in enumerate(blocks):
            p.update(i)
            for tx in block["transactions"]:
                # ignore contract creations which don't have "to"
                if "to" not in tx:
                    continue

                n1 = tx["from"]
                n2 = tx["to"]
                edge = tuple(sorted([n1, n2]))

                node_set.add(n1)
                node_set.add(n2)
                edge_dict[edge] += 1

        p.update(len(blocks))

    edges = []
    for (n1, n2), w in edge_dict.items():
        edges.append((n1, n2, {"weight": w}))

    l.log("creating graph...")
    g = nx.Graph()
    g.add_nodes_from(node_set, label="", shape="circle")
    g.add_edges_from(edges)

    # remove nodes with only one neighbor
    # nodes_to_remove = set()
    # for node in g.nodes:
    #     if len(g[node]) <= 1:
    #         nodes_to_remove.add(node)
    # g.remove_nodes_from(nodes_to_remove)

    return g


if __name__ == "__main__":
    main()
