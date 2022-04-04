# Import necessary libraries
import requests, argparse, json, sys, time, traceback
import math
from colorama import Fore, Back, Style, init as coloramaInit
from alive_progress import alive_bar as progressBar
from pathlib import Path

# Set constants
MORALIS_READ_TIMEOUT = 2
MORALIS_PAUSE_BETWEEN_REQUESTS = 0.7

# Initialize main vars
offset = 0
num = 0
totalOwned = 0
totalNfts = 0
owners = {}
filteredOwners = {}
userWasPrompted = False
exception_traces = False

# Header
def showHeader():
    print(
        f"""{Fore.LIGHTBLUE_EX}
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

                {Fore.WHITE}Created by: {Fore.LIGHTRED_EX}GBE#0001{Fore.WHITE} for DOS PUNKS DAO
                {Fore.WHITE}Updated by: {Fore.LIGHTRED_EX}DENVERS.ETH{Fore.WHITE} - Error context, support for JSON imports, alternative user input handling, refactoring
    """
    )


# Styling helper
def styleArgVal(yellowText):
    return Fore.YELLOW + str(yellowText) + Fore.WHITE


# Input prompt with styling
def inputStyled(argumentName):
    print(f"{Fore.YELLOW}[] {argumentName}: {Style.RESET_ALL}", end="")
    return input().strip()


# Init with flags
def flagInit():
    global userWasPrompted
    # Parse Flags
    parser = argparse.ArgumentParser()
    tokenIdSource = parser.add_mutually_exclusive_group()
    advancedParameters = parser.add_argument_group("advanced")
    actions = [
        tokenIdSource.add_argument("-s", "--slug", help="Slug Name (OpenSea)"),
        tokenIdSource.add_argument(
            "-t", "--token-id-json", help="Token ID JSON"
        ),
        parser.add_argument(
            "-c", "--contract", help="Contract Address", default="==PROMPT=="
        ),
        parser.add_argument(
            "-m", "--minted", help="Total Minted", default="==PROMPT=="
        ),
        parser.add_argument(
            "-k", "--apikey", help="API Key", default="==PROMPT=="
        ),
        parser.add_argument(
            "-f",
            "--filter",
            help="Filter by Tokens (2 If you want to filter by holders with 2 or more tokens)",
            type=int,
        ),
        advancedParameters.add_argument(
            "-e",
            "--exception-traces",
            help="Show error stacktraces",
            action="store_true",
        ),
    ]

    try:
        args = parser.parse_args()

        # Prompts begin

        # Ensure information for token ID source
        if not (args.slug or args.token_id_json):
            # NOTE: unsure if _group_actions are scoped to this specific mutex group or parser itself
            for i, a in enumerate(tokenIdSource._group_actions):
                print(f"{i} - {a.help}")
            tokenIdSource = int(
                inputStyled(
                    "Which token_id source would you like to use? [0,1]"
                )
            )
            # HACK: using indices of actions here is prone to break if arg order changes
            slugAction = actions[0]
            jsonAction = actions[1]
            if tokenIdSource == 0:
                values = inputStyled(slugAction.help)
                setattr(args, slugAction.dest, values)
            elif tokenIdSource == 1:
                values = inputStyled(jsonAction.help)
                setattr(args, jsonAction.dest, values)
            else:
                raise ValueError("Invalid selection")

            userWasPrompted = True
        for a in actions:
            if getattr(args, a.dest) == "==PROMPT==":
                values = inputStyled(a.help)
                setattr(args, a.dest, values)
                userWasPrompted = True
    except Exception as err:
        raise Exception(f"An error occuring during parsing: {err}")

    # Get flags
    (
        slug,
        tokenIdJson,
        contract,
        totalMinted,
        apiKey,
        tokenFilter,
        excepTraces,
    ) = vars(args).values()

    # Enable exception traces
    if excepTraces is True:
        global exception_traces
        exception_traces = True

    # Ensure totalMinted is an int
    # (argparse 'type' kwarg not used instead because it breaks ==PROMPT== functionality)
    try:
        totalMinted = int(totalMinted)
    except ValueError as err:
        raise ValueError("Total Minted must be an integer (whole number)")

    # Check either slug or tokenIdJson are set
    if not (slug or tokenIdJson):
        raise argparse.ArgumentError(
            None, "Must provide either Slug name or Token ID JSON"
        )

    # Check tokenIdJson is a valid filepath
    if tokenIdJson is not None:
        tidjPath = Path(tokenIdJson)
        if tidjPath.is_file() is False:
            raise FileNotFoundError(
                f"Failed to find token ID JSON file specified: {tidjPath}"
            )

    if userWasPrompted is True:
        print(
            f"\n{Fore.YELLOW}{Back.BLACK} ALL REQUIRED PARAMETERS COLLECTED. {Style.RESET_ALL}\n"
        )

    print(
        f"[] Slug: {styleArgVal(slug)}\n"
        + f"[] Token ID JSON: {styleArgVal(tokenIdJson)}\n"
        + f"[] Contract Address: {styleArgVal(contract)}\n"
        + f"[] Total Minted: {styleArgVal(totalMinted)}\n"
        + f"[] API Key: {styleArgVal(apiKey)}\n"
        + f"[] Filter: {styleArgVal(tokenFilter)}\n"
    )
    return slug, tokenIdJson, contract, totalMinted, apiKey, tokenFilter


# Fatal Error --> Exit
def fatalError(excep):
    global exception_traces
    if exception_traces:
        print(traceback.format_exc())
    print(
        f"\n{Fore.BLACK}{Back.YELLOW} ⚠︎ FATAL ERROR ⚠︎ {Style.RESET_ALL}"
        + f"{Fore.YELLOW}{Back.BLACK} {excep} {Style.RESET_ALL}"
    )
    print(f"\n{Fore.RED}An error has occurred. Please try again.\n")
    sys.exit()


class API:
    # TODO: add typehints to funcsig
    def get_asset_metadata(contract_address, token_id, moralis_api_key):
        """Retrieve asset metadata from Moralis API."""
        return requests.get(
            f"https://deep-index.moralis.io/api/v2/nft/{contract_address}/{token_id}/owners?chain=eth&format=decimal",
            headers={"X-API-Key": moralis_api_key},
            timeout=MORALIS_READ_TIMEOUT,
        )

    # TODO: add typehints to funcsig
    def get_opensea_collection_assets(
        collection_slug, offset, opensea_api_key=None
    ):
        """Retrieve assets from an OpenSea collection using OpenSea API.

        Response contains an array of token IDs that can be used with other APIs.
        """
        headers = {}
        if opensea_api_key is not None:
            headers["X-API-Key"] = opensea_api_key

        return requests.get(
            f"https://api.opensea.io/api/v1/assets?order_direction=desc&offset={offset}&limit=50&collection={collection_slug}",
            headers=headers,
        )


def _getOwners(tokenIds, contract, apiKey, bar):
    for tokenId in tokenIds:
        global totalNfts, totalOwned, owners, num
        totalNfts += 1
        while True:
            try:
                time.sleep(MORALIS_PAUSE_BETWEEN_REQUESTS)
                response = API.get_asset_metadata(contract, tokenId, apiKey)
                if response.ok is not True:
                    _msgBase = f"Failed to get asset metadata from Moralis: {response.status_code} ({response.reason})"
                    if response.status_code == 401:
                        raise RuntimeError(
                            f"{_msgBase}: {Fore.YELLOW}Double-check your Moralis API key is valid{Style.RESET_ALL}"
                        )
                    if response.status_code == 429:
                        raise RuntimeError(
                            f"{_msgBase}: {Fore.YELLOW}Getting rate-limited{Style.RESET_ALL}"
                        )
                    raise RuntimeError(_msgBase)

                web3response = response.json()
                if not "total" in web3response:
                    raise RuntimeError("total is missing!")
                break
            except RuntimeError as err:
                print(err)
                print(
                    "might be getting throttled, trying again in 1.5 seconds..."
                )
                time.sleep(1.5)
            except KeyboardInterrupt:
                print("Cancelled by user...")
                raise KeyboardInterrupt
            except requests.exceptions.ReadTimeout:
                print(
                    f"{Fore.YELLOW}Timed-out waiting for server response...{Style.RESET_ALL}"
                )
            except Exception as err:
                print(response.status_code, response.reason, type(err))
                print("Unexpected error, trying again in 1 second...")
                print(f"Error: ${err}")
                time.sleep(1)

        totalOwned += web3response["total"]
        for r in web3response["result"]:
            if r["owner_of"] in owners:
                owners[r["owner_of"]] += 1
            else:
                owners[r["owner_of"]] = 1
        num += 1
        bar()


# Retrieving owners from API's
def getOwners(slug, tokenIdJson, contract, pagination, tokenFilter, apiKey):
    # Iterate trough the pagination
    print(
        f"""\n{Fore.YELLOW}
        +------------------------------------------------------------+
        |              CHECKING HOLDERS. PLEASE WAIT...              |
        +------------------------------------------------------------+{Fore.WHITE}\n"""
    )
    try:
        # if slug is specified, ignore it (argparse should've already performed conflict check)
        if tokenIdJson:
            # JSON IMPORT METHOD
            with open(tokenIdJson) as f:
                dict_root = json.load(f)
                tokenIds = dict_root["tokenIds"]
                with progressBar(len(tokenIds), bar="filling") as bar:
                    _getOwners(tokenIds, contract, apiKey, bar)
        else:
            # SLUG BASED METHOD

            # FIXME: pagniation broken (probably easiest to just refactor)
            raise NotImplementedError(
                "Sourcing token IDs from OpenSea collection slug is temporarily disabled"
            )

            # TODO: Requires testing by another person with an OpenSea API key
            for i in range(0, int(pagination)):
                offset = i * 50

                # TODO: Add support for OpenSea API keys
                # FIXME: TEMP
                # opensea_api_key = ""

                # Fetch OpenSea collection assets
                response = API.get_opensea_collection_assets(slug, offset, "")
                if response.ok is not True:
                    raise RuntimeError(
                        f"Failed to collect assets from OpenSea API: {response.status_code} ({response.reason})"
                    )

                # Parse OpenSea response
                try:
                    # NOTE: .assets[n].owner.address is always 0x000...0 (guess: related to frozen/non-frozen metadata?)
                    responseJson = response.json()
                except Exception as err:
                    raise RuntimeError(
                        f"Failed to parse OpenSea response: {err}"
                    )

                # Extract token_ids from response
                tokenIds = [
                    asset["token_id"] for asset in responseJson["assets"]
                ]

                with progressBar(int(pagination), bar="filling") as bar:
                    _getOwners(tokenIds, contract, apiKey, bar)

        if tokenFilter not in (None, 0):
            print(
                f"\n\n{Fore.WHITE}[+] Filtered by holders with: {Fore.GREEN}{tokenFilter} or + Tokens{Fore.WHITE}"
            )
            for _o in owners:
                if int(owners[_o]) >= int(tokenFilter):
                    filteredOwners[_o] = owners[_o]
            owners = filteredOwners
    except Exception as err:
        fatalError(err)


# Export to JSON
def exportJSON(slug):
    global totalNfts, totalOwned, owners
    outputFile = open(f"./snapshots/{slug}-owners.json", "w")
    json.dump(owners, outputFile)
    time.sleep(1.5)
    print(
        f"""\n{Fore.YELLOW}
        +------------------------------------------------------------+
        |                  SNAPSHOT HAS BEEN TAKEN                   |
        +------------------------------------------------------------+\n
        {Fore.GREEN}     [+] Total NFTS: {Fore.WHITE}{totalNfts}{Fore.YELLOW}
        {Fore.GREEN}     [+] Total Owned: {Fore.WHITE}{totalOwned}{Fore.YELLOW}
        {Fore.GREEN}     [+] Total Owners: {Fore.WHITE}{len(owners)}{Fore.YELLOW}
        {Fore.GREEN}     [+] Exported File: {Fore.WHITE}./snapshots/{slug}-owners.json{Fore.YELLOW}\n\n"""
    )


# Main handle
def main():
    coloramaInit()
    showHeader()
    try:
        (
            slug,
            tokenIdJson,
            contract,
            totalMinted,
            apiKey,
            tokenFilter,
        ) = flagInit()  # Init with flags
    except Exception as err:
        fatalError(err)

    pagination = int(math.ceil((int(totalMinted)) / 50))  # Get pagination
    getOwners(
        slug, tokenIdJson, contract, pagination, tokenFilter, apiKey
    )  # Main method
    exportJSON(slug)  # Export results


# Start
main()
