import click
import csv
import json
import os
import requests


@click.command()
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(file_okay=False),
    help="output directory",
)
@click.option("--start", "-s", default=-1, help="start block number (inclusive)")
@click.option("--num", "-n", default=1, help="number of blocks to scrape")
@click.option("--rpc-url", "-r", envvar="ETH_RPC_URL", help="Ethereum JSON RPC URL")
@click.pass_context
def main(ctx, output, start, num, rpc_url):
    """Fetch the hashes of all transactions in a range of blocks."""
    if not os.path.exists(output):
        ctx.fail("output directory does not exist")

    current_block = fetch_current_block(rpc_url=rpc_url)
    if start < 0:
        start = current_block + start
    end = min(start + num, current_block)

    print(f"fetching {num} blocks from #{start} to #{end}...")

    with ProgressPrinter(num) as p:
        for n in range(start, end):
            p.update(n - start)
            block = fetch_block(n, rpc_url=rpc_url)
            file_path = os.path.join(output, f"{n}.json")
            with open(file_path, "w") as f:
                json.dump(block, f)
        p.update(num)

    print("done")


def fetch_block(n, rpc_url):
    r = request(rpc_url, "eth_getBlockByNumber", [hex(n), True])
    return r["result"]


def fetch_current_block(rpc_url):
    r = request(rpc_url, "eth_blockNumber")
    n = int(r["result"], 16)
    return n


def request(rpc_url, method, params=None):
    return requests.post(
        rpc_url,
        json={"jsonrpc_url": "2.0", "method": method, "params": params or [], "id": 0},
    ).json()


class ProgressPrinter:
    def __init__(self, n):
        self.n = n

    def update(self, i):
        s = f"{i / self.n * 100:.1f}% ({i} of {self.n})"
        print("\r" + s + "\033[K", end="")

    def print(self, s):
        print("\n" + s)

    def __enter__(self):
        return self

    def __exit__(self, _1, _2, _3):
        print("", end="\n")


if __name__ == "__main__":
    main()
