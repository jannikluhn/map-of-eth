# Map of ETH

This project is an experiment aiming to visualize the relationship between smart contracts on
Ethereum as a force-directed graph. The nodes in the graph are contracts. Nodes are connected by
an edge if they are called by the same EOA.

## Usage

1. Install in a virtualenv `python -m pip -r requirements.txt`.
2. Fetch the input data with `python fetch_blocks.py -o <blocks_dir> -s 2022-05-18 -r 1d -u <json_rpc_url>`
   (this will take some time, use a smaller range to speed it up).
3. Extract account interactions with `python interactions.py -i <blocks_dir> -o <interactions_file.csv>`.
4. Create the graph with `python graph_cutoff.py -i <interactions_file.csv> -o <graph_file.dot>`.

`graph_prob.py` implements a similar algorithm but with different pruning method. Check the
`--help` of the commands for details.

The resulting graph can be explored and visualized with tools such as [Gephi](https://gephi.org/). Try
"Fruchterman Reingold" with default parameters as layout algorithm. (unfortunately, it doesn't take
edge weights into account).

## Example

![graph](/example/graph.png)

Input data is one day of transactions (1130101 transactions in 5971 blocks from 14795323 to
14801293 on May 18th, 2022).
