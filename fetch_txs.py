import click
import csv
import os
import requests


@click.command()
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(dir_okay=False),
    help="output path",
)
@click.option("--start", "-s", default=-1, help="start block number (inclusive)")
@click.option("--num", "-n", default=1, help="number of blocks to scrape")
@click.option("--rpc-url", "-r", envvar="ETH_RPC_URL", help="Ethereum JSON RPC URL")
@click.pass_context
def main(ctx, output, start, num, rpc_url):
    """Fetch the hashes of all transactions in a range of blocks."""
    if os.path.exists(output):
        ctx.fail("output file already exists")

    current_block = fetch_current_block(rpc_url=rpc_url)
    if start < 0:
        start = current_block + start
    end = min(start + num, current_block)

    lines = []
    for n in range(start, end):
        tx_hashes = fetch_tx_hashes(n, rpc_url=rpc_url)
        new_lines = [[n, i, "0x" + h.hex()] for i, h in enumerate(tx_hashes)]
        lines += new_lines

    with open(output, "w") as f:
        writer = csv.writer(f)
        for line in lines:
            writer.writerow(line)


def fetch_tx_hashes(n, rpc_url):
    r = request(rpc_url, "eth_getBlockByNumber", [hex(n), False])
    tx_hashes_hex = r["result"]["transactions"]
    tx_hashes_bytes = [bytes.fromhex(h[2:]) for h in tx_hashes_hex]
    return tx_hashes_bytes


def fetch_current_block(rpc_url):
    r = request(rpc_url, "eth_blockNumber")
    n = int(r["result"], 16)
    return n


def request(rpc_url, method, params=None):
    return requests.post(
        rpc_url,
        json={"jsonrpc_url": "2.0", "method": method, "params": params or [], "id": 0},
    ).json()


if __name__ == "__main__":
    main()
