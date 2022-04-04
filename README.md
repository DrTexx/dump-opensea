# Dump-OpenSea
<pre>
 ██████████   █████  █████ ██████   ██████ ███████████                     
░░███░░░░███ ░░███  ░░███ ░░██████ ██████ ░░███░░░░░███                    
 ░███   ░░███ ░███   ░███  ░███░█████░███  ░███    ░███                    
 ░███    ░███ ░███   ░███  ░███░░███ ░███  ░██████████                     
 ░███    ░███ ░███   ░███  ░███ ░░░  ░███  ░███░░░░░░                      
 ░███    ███  ░███   ░███  ░███      ░███  ░███                            
 ██████████   ░░████████   █████     █████ █████                           
░░░░░░░░░░     ░░░░░░░░   ░░░░░     ░░░░░ ░░░░░                            
                                                                           
                                                                           
                                                                           
    ███████                                   █████████                    
  ███░░░░░███                                ███░░░░░███                   
 ███     ░░███ ████████   ██████  ████████  ░███    ░░░   ██████   ██████  
░███      ░███░░███░░███ ███░░███░░███░░███ ░░█████████  ███░░███ ░░░░░███ 
░███      ░███ ░███ ░███░███████  ░███ ░███  ░░░░░░░░███░███████   ███████ 
░░███     ███  ░███ ░███░███░░░   ░███ ░███  ███    ░███░███░░░   ███░░███ 
 ░░░███████░   ░███████ ░░██████  ████ █████░░█████████ ░░██████ ░░████████
   ░░░░░░░     ░███░░░   ░░░░░░  ░░░░ ░░░░░  ░░░░░░░░░   ░░░░░░   ░░░░░░░░ 
               ░███                                                        
               █████                                                       
              ░░░░░                      - BROUGHT TO YOU BY DOS PUNKS DAO
                                         - REIMAGINED BY DENVERS.ETH                            
</pre>

# Basic Information

> **Dump OpenSea** (aka DOS) is a tool for taking snapshots of NFT collections.

## What is a snapshot?

A snapshot is a **recording all of the current `owners`/`holders` of a collection** and **the `quantity held` by each owner**.

## Only OpenSea Collections?

Despite the name, DOS can snapshot non-OpenSea collections.

**For non-OpenSea collection snapshots, make sure to select the `1 - Token ID JSON` option** or use the `-t/--token-id-json` flag.

## Other Marketplaces?

Support for other marketplaces is planned for the future, follow [@DrTexx](https://twitter.com/DrTexx/) or watch this repository for updates.

## How

See [Usage](#Usage).

## Why

Snapshots are particularly useful for **distributing suprise rewards to owners/holders**, such as [airdrops](https://cointelegraph.com/news/early-ethereum-name-service-ens-adopters-rewarded-with-a-hefty-five-figure-airdrop).

## Who

DOS is useful for anyone who

- Works on an NFT project
- Performs on-chain analysis/research
- Wants to use a pretty CLI
- Wishes to learn about Web3 APIs

# Installation

## Linux (Typical)

```bash
git clone https://github.com/DrTexx/dump-opensea.git  # STEP 1
cd dump-opensea                                       # STEP 2
pip install -r requirements.txt -U                    # STEP 3
```

# Usage

If any required flags are missing you can fill them in once the script starts

| Parameter               | Required | Description                             | Where To Find                                                                                  |
| ----------------------- | -------- | --------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `-c/--contract`         | **yes**  | Contract address of Collection          | Use Etherscan to check contract address for an NFT transaction                                 |
| `-k/--apikey`           | **yes**  | Moralis API Key                         | Get from [Moralis Admin](https://admin.moralis.io/register) *(FREE)*                           |
| `-s/--slug`             | no       | OpenSea collection slug                 | End of URL on OpenSea collection page (e.g. `https://opensea.io/collection/`***`dos-punks`***) |
| `-j/--token-id-json`    | no       | Filepath to Token ID JSON               | Type the filepath to your Token ID JSON file                                                   |
| `-e/--exception-traces` | no       | Enable exception stacktraces (advanced) | -                                                                                              |
| `-h/--help`             | no       | Display help text                       | -                                                                                              |
| `-f/--filter`           | no       | Filter owners by minimum tokens held    | -                                                                                              |  |
| `-o/--opensea-api-key`  | no       | OpenSea API Key                         | Get from [OpenSea API Key Request Page](https://docs.opensea.io/reference/request-an-api-key)  |

## Usage Examples

### Running with User Input

```bash
python dump-opensea.py
```
- Fill the inputs with your data
- Unsure where to get something? Check [Usage](#Usage) above.

## Running with Flags

- Type ```python dump-opensea.py -h``` to get the available flags

### OpenSea Example

```bash
python dump-opensea.py -c 0x495f947276749Ce646f68AC8c248420045cb7b5e -k <MORALIS_API_KEY> -s bofanimals -o <OPENSEA_API_KEY>
```

### Import JSON Example

```bash
python dump-opensea.py -c 0x495f947276749Ce646f68AC8c248420045cb7b5e -k <MORALIS_API_KEY> -t bofanimals_token_ids.json
```

# Results

- JSON file will be written inside the `./snapshots` directory.

```jsonc
{
  "<wallet_address_1>": "<number_of_tokens_held_1>",
  "<wallet_address_2>": "<number_of_tokens_held_2>",
  "<wallet_address_3>": "<number_of_tokens_held_3>",
  // etc...
}
```
  - Wallet Address: Number of tokens

# Credits

Created by [GBE](https://github.com/gbe3hunna/) for the [DOS PUNKS DAO](https://github.com/DOSPunksDAO) to thank [@maxcapacity](https://twitter.com/maxcapacity) and [@greencrosslive](https://twitter.com/greencrosslive) for all their effort in buidling such a strong #DOSLIFE.

Developed by DOS Punks DAO for the NFT Community.   

Reimagined by [denvers.eth](https://github.com/drtexx) 🌱

This software is distributed under the 🅭🅯🄏🄎 Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)
