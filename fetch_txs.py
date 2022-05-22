import click
import csv
import datetime
import dateparser
import json
import os
import re
import requests
import log as l

BLOCK_INTERVAL = 13

units = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
    "w": 60 * 60 * 24 * 4,
}


@click.command()
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(file_okay=False),
    help="output directory",
)
@click.option("--start", "-s", "start_string", default="now", help="start time")
@click.option(
    "--range", "-r", "time_range_string", default="1d", help="time span to scrape"
)
@click.option("--rpc-url", "-r", envvar="ETH_RPC_URL", help="Ethereum JSON RPC URL")
@click.pass_context
def main(ctx, output, start_string, time_range_string, rpc_url):
    """Fetch the hashes of all transactions in a range of blocks."""
    if not os.path.exists(output):
        ctx.fail("output directory does not exist")

    start_time = dateparser.parse(start_string)
    if start_time is None:
        ctx.fail(f"could not parse start time {start}")
    time_range = parse_range(time_range_string)
    if time_range is None:
        ctx.fail(f"could not parse time range {time_range_string}")

    l.log("find start and end blocks...")
    start_block = fetch_block_at_time(start_time.timestamp(), rpc_url)
    if start_block is None:
        ctx.fail(f"could not find block for start time {start_time}")
    start_block_number = int(start_block["number"], 16)
    if isinstance(time_range, datetime.timedelta):
        end_time = start_time + time_range
        end_block = fetch_block_at_time(end_time.timestamp(), rpc_url)
        if end_block is None:
            ctx.fail(f"could not find block for end time {end_time}")
        end_block_number = int(end_block["number"], 16)
    elif isinstance(time_range, int):
        end_block_number = start_block_number + time_range
    else:
        assert False

    prefetched = get_prefetched_blocks(output)

    num = end_block_number - start_block_number
    l.log(f"fetching {num} blocks from #{start_block_number} to #{end_block_number}...")

    with l.ProgressPrinter(num) as p:
        for n in range(start_block_number, end_block_number):
            if n in prefetched:
                continue
            p.update(n - start_block_number)
            block = fetch_block(n, rpc_url=rpc_url)
            file_path = os.path.join(output, f"{n}.json")
            with open(file_path, "w") as f:
                json.dump(block, f)
        p.update(num)

    l.log("done")


def parse_range(s):
    m = re.match(r"^\s*(\d+)\s*([a-z]*)\s*$", s.lower())
    if m is None:
        return None
    magnitude_string, unit = m.groups()
    magnitude = float(magnitude_string)

    # if unit is b (for blocks) or missing, return magnitude as integer
    if unit == "" or unit == "b":
        if not float.is_integer(magnitude):
            return None
        return int(magnitude)

    # otherwise, return it as timedelta
    if unit not in units:
        return None
    seconds = magnitude * units[unit]
    return datetime.timedelta(seconds=seconds)


def get_prefetched_blocks(d):
    prefetched = set()
    regex = re.compile(r"^(\d+).json$")
    for p in os.listdir(d):
        m = regex.match(p)
        if m is None:
            continue
        (block_number,) = m.groups()
        prefetched.add(int(block_number))
    return prefetched


def fetch_block(n, rpc_url):
    r = request(rpc_url, "eth_getBlockByNumber", [hex(n), True])
    return r["result"]


def fetch_current_block(rpc_url):
    r = request(rpc_url, "eth_blockNumber")
    n = int(r["result"], 16)
    return n


def fetch_block_at_time(t, rpc_url):
    """Fetch the latest block with timestamp >= t."""
    # Start by setting b1 to the latest block. If b1 is not later than t, return b1. Otherwise
    # find a b0 earlier than t. Then, perform a binary search ensuring b0.t <= t < b1.t until
    # b0.n + 1 == b1.n and return b0.
    b1 = request(rpc_url, "eth_getBlockByNumber", ["latest", False])["result"]
    b1_n = int(b1["number"], 16)
    b1_t = int(b1["timestamp"], 16)

    if b1_t <= t:
        return b1

    b0_n = int(b1_n - (b1_t - t) / BLOCK_INTERVAL * 1.3)
    while True:
        b0 = fetch_block(b0_n, rpc_url)
        b0_t = int(b0["timestamp"], 16)
        if b0_t <= t:
            break
        if b0_n == 0:
            return None
        b0_n -= int((b0_t - 1) / BLOCK_INTERVAL * 1.3 + 1)
        b0_n = max(0, b0_n)

    while b1_n - b0_n > 1:
        if b0_t == b1_t:
            b_n = (b0_n + b1_n) // 2
        else:
            # if t is 30% on the way between b0_t and b1_t in terms of timestamps, pick next block
            # number guess as 30% between b0_n and b1_n
            dt_0t = t - b0_t
            dt_01 = b1_t - b0_t
            db_01 = b1_n - b0_n
            db_0t = int(db_01 * dt_0t / dt_01)
            b_n = b0_n + db_0t
            b_n = max(b_n, b0_n + 1)
            b_n = min(b_n, b1_n - 1)

        b = fetch_block(b_n, rpc_url)
        b_t = int(b["timestamp"], 16)
        if b_t < t:
            b0 = b
            b0_n = b_n
            b0_t = b_t
        else:
            b1 = b
            b1_n = b_n
            b1_t = b_t

    return b0


def request(rpc_url, method, params=None):
    return requests.post(
        rpc_url,
        json={"jsonrpc_url": "2.0", "method": method, "params": params or [], "id": 0},
    ).json()


if __name__ == "__main__":
    main()
