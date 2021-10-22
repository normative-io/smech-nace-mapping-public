<!--
 Copyright 2022 Meta Mind AB
 
 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at
 
     http://www.apache.org/licenses/LICENSE-2.0
 
 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
-->

# SME Climate Hub NACE name mapping

There are multiple industry sector taxonomies in use by different systems in Normative and in Normative's partner organisations.

- Exiobase-derived data covers a subset of NACE codes.
- SME Climate Hub has their own industry sector list with names and codes. This is probably derived from NACE, but it's a fairly small subset and the names and codes may not match exactly. From a technical perspective it's best to treat it as an independent taxonomy.
- Business Carbon Calculator has an industry sector list with names and codes. This should be a subset of NACE, though some names have been changed to make them more easily understood by the BCC target audience. The codes should be 'real' NACE codes, and should also be a subset of the Exiobase covered sectors.
- Industry CO2 Insights uses the same names and codes as BCC (though it has its own copy).

This repository holds manually curated mappings between these code systems, and tools to generate JSON data used by the
Industry CO2 Insights and Business Carbon Calculator sites.

## Inputs

Manually curated data is in the `data` directory. The files are direct exports of
https://docs.google.com/spreadsheets/d/15oaJevwHlPPNSlTuWNv5UulVliLNs9v6W80EAC94dDg/edit?resourcekey=0-WsO0SaYjwmN35of6hQWVhQ#gid=670791350

- `data/smech_sectors.csv` is an export of the `Industry insight mapping` tab.
  Expected columns:

  - **A**: SMECH sector name -- Name of the industry sector in SME Climate Hub
  - **B**: SMECH sector code -- Code for the industry sector in SME Climate Hub (sent to Industry CO2 Insights as a URL query parameter)
  - **C**: NACE name -- Best available mapping to NACE (name, not code)
  - **D**: Exio2 sector code -- Best available sector from the Exiobase 2 data.
  - **E**: Exio3 sector code -- Best available sector from the Exiobase 3 data.
  - **F**: BCC sector code -- Best NACE code from the subset used in BCC & Industry CO2 Insights
    Columns beyond this are ignored. The actual column headers are ignored. This data is used just to produce the mapping from SMECH code (column B) to a NACE code that is included in the sectors supported in BCC & Industry CO2 Insights (column F).

- `data/bcc_sectors.csv` is an export of the `Mapping` tab.
  Expected columns:
  - **A**: ISIC -- NACE/ISIC code
  - **B**, **C**: ignored.
  - **D**: Exio3 name -- Name for this sector in Exiobase 3 data. Note there's a lot of duplicate here; this comes from duplication that is really present in the Exiobase-derived sector average data.
  - **E**: NACE name -- Name for this sector from NACE.
  - **F**: notes (ignored)
  - **G**: Use for BCC -- Marks entries that are to be included in the BCC & Industry CO2 Insights sector lists.
  - **H**: BCC sector name -- "Friendly" name; this is the display name for the sector on the BCC & Industry CO2 Insights sector sites.
    Columns beyond this are ignored. The actual column headers are ignored. This data is just used to produce the table of sectors.

## Prerequisites

Needs `python3`. If you want to automatically run Prettier on the output during generation then you will also need `prettier`, or (more likely) `npx`.

## Building the mapping

**Warning:** If you're writing the output directly to adjacent checkouts of the BCC and Benchmark frontends, then you will most likely want to ensure that those checkouts are each on an appropriate branch before running the generator.

Generate files with a command like the following (you will need to alter the exact paths depending on your system):

```bash
# Change these paths as necessary.
BCC_ROOT=$HOME/starter/normative-ngx-starter
BENCHMARK_ROOT=$HOME/benchmark/sme-public-profile-client
./generate.py \
  --prettier \
  --prettier_config_bcc="$BCC_ROOT"/.prettierrc \
  --prettier_config_benchmark="$BENCHMARK_ROOT"/.prettierrc \
  --output_bcc="$BCC_ROOT"/apps/starter/src/app/core/data/sectors.data.ts \
  --output_benchmark="$BENCHMARK_ROOT"/src/sector-constants/naces.ts
```

You can skip the `--ouptut...` arguments in which case output will be written to a "$PWD/dist" directory. You can also skip the `--prettier...` arguments in which case output will be written 'raw' without any reformatting. You will most likely want to run Prettier manually in this case.

## Contributing

This project is maintained by Normative but currently not actively seeking external contributions. If you however are interested in contributing to the project please [sign up here](https://docs.google.com/forms/d/e/1FAIpQLSe80c9nrHlAq6w2vUbeFSPVGG7IPqorKMkizhHJ98viwnT-OA/viewform?usp=sf_link) or come [join us](https://normative.io/jobs/).

Thank you to all the people from Google.org who were critical in making this project a reality!
- John Bartholomew ([@johnbartholomew](https://github.com/johnbartholomew))

## License
Copyright (c) Meta Mind AB. All rights reserved.

Licensed under the [Apache-2.0 license](/LICENSE)
