#!/usr/bin/python3
# Copyright 2022 Meta Mind AB
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import csv
import datetime
import json
import os
import re
import string
import subprocess

# Also see README.md for the columns we expect.
SMECH_SECTORS_COLUMNS = (
    "smech_name",
    "smech_code",
    "nace_name",
    "exio2_code",
    "exio3_code",
    "bcc_code",
)

BCC_SECTORS_COLUMNS = (
    "nace_code",
    "ignore1",
    "ignore2",
    "exio3_name",
    "nace_name",
    "notes",
    "use_for_bcc",
    "bcc_name",
)

BENCHMARK_OUT_NAME = "naces.ts"
BENCHMARK_OUT_TEMPLATE = string.Template(
    """\
// GENERATED FILE. DO NOT EDIT BY HAND.
//
// Generated at $generation_timestamp.
// See repository smech-nace-mapping

export interface NaceInfo {
  name: string;
  nace: string;
}

export const SECTOR_LIST: NaceInfo[] = $sector_list;

export type SMECHNaceInfo = { [key: string]: string };

export const SMECH_NACE_MAPPING: SMECHNaceInfo = $smech_mapping;
"""
)

BCC_SECTORS_OUT_NAME = "sectors.data.ts"
BCC_SECTORS_OUT_TEMPLATE = string.Template(
    """\
// GENERATED FILE. DO NOT EDIT BY HAND.
//
// Generated at $generation_timestamp.
// See repository smech-nace-mapping

import { Sector } from './data.model';

export const SECTORS: Sector[] = $bcc_sector_array;
"""
)

RX_DIGITS = re.compile("^[0-9]+$")


def expect_just_digits(value, fieldname, rownum):
    if not RX_DIGITS.match(value):
        raise ValueError(f"{fieldname} is expected to be just digits, but got {repr(value)} on row {rownum}")


def expect_non_digits(value, fieldname, rownum):
    if RX_DIGITS.match(value):
        raise ValueError(f"{fieldname} is expected to have text not just digits, but got {repr(value)} on row {rownum}")


def load_smech_to_bcc(file):
    reader = csv.DictReader(file, fieldnames=SMECH_SECTORS_COLUMNS, restkey="extra", dialect="excel")
    next(reader)  # Skip the first row (the column headings from the file).
    out = {}
    for row_idx, row in enumerate(reader, start=2):
        smech_code = row["smech_code"].strip()
        bcc_code = row["bcc_code"].strip()
        if bcc_code == "":
            print(f"WARNING: Skipping mapping for SMECH code {smech_code} ({row['smech_name']}) - no BCC code")
            continue
        expect_just_digits(smech_code, "smech_code", row_idx)
        expect_just_digits(bcc_code, "bcc_code", row_idx)
        print(f"mapping code {smech_code} ({row['smech_name']}) to {bcc_code}")
        if smech_code in out and out[smech_code] != bcc_code:
            raise ValueError(f"smech_code {smech_code} has multiple mappings (duplicate on row {row_idx})")
        out[smech_code] = bcc_code
    return out


def load_bcc_sectors(file):
    reader = csv.DictReader(file, fieldnames=BCC_SECTORS_COLUMNS, restkey="extra", dialect="excel")
    next(reader)  # Skip the first row (the column headings from the file).
    out = {}
    for row_idx, row in enumerate(reader, start=2):
        nace_code = row["nace_code"].strip()
        bcc_name = row["bcc_name"].strip()
        use_for_bcc = row["use_for_bcc"].strip().lower() in ("x", "y", "yes")
        if not use_for_bcc:
            continue
        expect_just_digits(nace_code, "nace_code", row_idx)
        expect_non_digits(bcc_name, "bcc_name", row_idx)
        if nace_code in out:
            raise ValueError(
                f"nace_code is expected to be unique but got a duplicate of {repr(nace_code)} on row {row_idx}. Mistake?"
            )
        out[nace_code] = bcc_name
    return out


def prettier_format_code(code, code_path, cmd, config_path=None):
    args = cmd.split()
    if config_path is not None:
        args.extend(["--config", config_path])
    args.extend(["--stdin-filepath", code_path])
    prettier = subprocess.run(args, shell=False, input=code, capture_output=True, text=True, encoding="utf-8")
    prettier.check_returncode()
    return prettier.stdout


def main():
    aparser = argparse.ArgumentParser(description="Generate sector mappings and lists")
    aparser.add_argument(
        "--prettier", action=argparse.BooleanOptionalAction, help="If set, run Prettier on the output."
    )
    aparser.add_argument("--prettier_cmd", default="npx prettier", help="Command to run Prettier.")
    aparser.add_argument("--prettier_config", help="Location of a Prettier config file.")
    aparser.add_argument("--prettier_config_bcc", help="Location of a Prettier config file.")
    aparser.add_argument("--prettier_config_benchmark", help="Location of a Prettier config file.")
    aparser.add_argument("--output_bcc", help=f"Output path to write the generated {BCC_SECTORS_OUT_NAME} file")
    aparser.add_argument("--output_benchmark", help=f"Output path to write the generated {BENCHMARK_OUT_NAME} file")
    args = aparser.parse_args()

    with open("data/smech_sectors.csv", encoding="utf-8") as f:
        smech_to_bcc = load_smech_to_bcc(f)
    with open("data/bcc_sectors.csv", encoding="utf-8") as f:
        bcc_sectors = load_bcc_sectors(f)

    # Verify that every SMECH code maps to a BCC code
    for k, v in smech_to_bcc.items():
        if v not in bcc_sectors:
            raise ValueError(f"SMECH code {k} maps to NACE {v} which is not in the BCC sector list")

    generation_timestamp = datetime.datetime.now().isoformat()

    sector_list = sorted(({"name": v, "nace": k} for k, v in bcc_sectors.items()), key=lambda x: x["name"])

    dump_args = {
        "ensure_ascii": True,
        "indent": None,
    }

    # Build some JSON!
    benchmark_code = BENCHMARK_OUT_TEMPLATE.substitute(
        sector_list=json.dumps(sector_list, **dump_args),
        smech_mapping=json.dumps(smech_to_bcc, sort_keys=True, **dump_args),
        generation_timestamp=generation_timestamp,
    )

    bcc_sectors_code = BCC_SECTORS_OUT_TEMPLATE.substitute(
        bcc_sector_array=json.dumps(sector_list + [{"name": "Not listed", "nace": ""}], **dump_args),
        generation_timestamp=generation_timestamp,
    )

    if args.prettier:
        benchmark_code = prettier_format_code(
            benchmark_code,
            "naces.ts",
            args.prettier_cmd,
            config_path=(args.prettier_config_benchmark or args.prettier_config),
        )
        bcc_sectors_code = prettier_format_code(
            bcc_sectors_code,
            "sectors.data.ts",
            args.prettier_cmd,
            config_path=(args.prettier_config_bcc or args.prettier_config),
        )

    # Write it out.
    output_benchmark = args.output_benchmark or os.path.join("dist", BENCHMARK_OUT_NAME)
    output_bcc_sectors = args.output_bcc or os.path.join("dist", BCC_SECTORS_OUT_NAME)
    if not args.output_bcc or not args.output_benchmark:
        os.makedirs("dist", exist_ok=True)
    with open(output_benchmark, "w", encoding="utf-8") as f:
        f.write(benchmark_code)
    with open(output_bcc_sectors, "w", encoding="utf-8") as f:
        f.write(bcc_sectors_code)


if __name__ == "__main__":
    main()
