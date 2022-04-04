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
             {Fore.WHITE}Reimagined by: {Fore.LIGHTRED_EX}DENVERS.ETH{Fore.WHITE} - Error context, support for JSON imports, parser rearchitecture, refactoring,
                                          ... support for OpenSea API keys.
    """
    )


# Styling helper
def styleArgVal(yellowText):
    return Fore.YELLOW + str(yellowText) + Fore.WHITE


# Input prompt with styling
def inputStyled(argumentName):
    print(f"{Fore.YELLOW}[] {argumentName}: {Style.RESET_ALL}", end="")
    return input().strip()


def _keys_to_string(_dict) -> str:
    """Return a comma-separated list of keys for a given object.

    Should work with anything that can be used as a dict key (e.g. string, number, etc.)"""
    return ",".join([str(key) for key in _dict.keys()])


# TODO: improve docstring
# TODO: move to own script/library
def chooseFromDict(
    _dict,
    message_prompt,
    value_prompt_attr,
    message_invalid=f"{Fore.RED}\nSorry, that's not a valid choice. Please try again.\n{Style.RESET_ALL}",
    display_options=True,
    convert_ints=True,
    retry=False,
):
    """Prompt user to select an option from a given dictionaries.

    Returns the value of the corrosponding key choice.

    - value_prompt_attr: an attribute each value in the dictionary has which is
        - Used as context for the value when displaying choices
    """
    # Collect options based on dict keys
    options = {i: a for (i, a) in enumerate(_dict)}

    # Generate prompt message
    prompt = f"{message_prompt} [{_keys_to_string(options)}]"

    while True:
        # Display options to user
        if display_options:
            for (i, a) in options.items():
                option_context = getattr(_dict[i], value_prompt_attr)
                print(f" {i}: {option_context}")
            print()

        # Prompt for choice
        sourceChoice = inputStyled(prompt)

        # Convert integers if applicable
        if convert_ints:
            if sourceChoice.isdigit():
                sourceChoice = int(sourceChoice)

        # If choice is valid, return corrosponding dict value
        if sourceChoice in options.keys():
            return options[sourceChoice]
        else:
            print(message_invalid)
            if not retry:
                raise ValueError("Invalid choice")


# Init with flags
def flagInit():
    global userWasPrompted
    # Parse Flags
    parser = argparse.ArgumentParser()
    requiredParameters = parser.add_argument_group("required")
    tokenIdSource = parser.add_argument_group(
        "sources"
    ).add_mutually_exclusive_group()
    advancedParameters = parser.add_argument_group("advanced")
    openseaParameters = parser.add_argument_group("opensea")
    actions = [
        # Required arguments
        requiredParameters.add_argument(
            "-c", "--contract", help="Contract Address", default="==PROMPT=="
        ),
        requiredParameters.add_argument(
            "-k", "--apikey", help="API Key (Moralis)", default="==PROMPT=="
        ),
        # Required mutex arguments
        tokenIdSource.add_argument("-s", "--slug", help="Slug Name (OpenSea)"),
        tokenIdSource.add_argument(
            "-t", "--token-id-json", help="Token ID JSON"
        ),
        # Optional arguments
        parser.add_argument(
            "-f",
            "--filter",
            help="Filter Owners (Minimum Tokens Held)",
            type=int,
        ),
        advancedParameters.add_argument(
            "-e",
            "--exception-traces",
            help="Show error stacktraces",
            action="store_true",
        ),
        # OpenSea specific
        openseaParameters.add_argument(
            "-o", "--opensea-api-key", help="API Key (OpenSea)"
        ),
    ]

    try:
        args = parser.parse_args()

        # Prompts begin

        # Create dictionary of dest-indexed actions
        destActions = {
            action.dest: action
            for action in actions
            if hasattr(action, "dest")
        }

        # Ensure source for token IDs provided
        if not (args.slug or args.token_id_json):
            # Prompt user to select a source
            sourceAction = chooseFromDict(
                tokenIdSource._group_actions,
                "Which token_id source would you like to use?",
                "help",
                )

            # Set source-specific argument to be prompted
            setattr(args, sourceAction.dest, "==PROMPT-STRICT==")

            statusMsg("SELECTED TOKEN ID SOURCE.")

            # Note that user was prompted
            userWasPrompted = True

        # Ensure OpenSea args are set (if necessary)
        if args.slug:
            if not args.opensea_api_key:
                setattr(
                    args,
                    destActions["opensea_api_key"].dest,
                    "==PROMPT-STRICT==",
                )

        # Prompt user for values for all arguments set to "==PROMPT=="
        for a in actions:
            strict = getattr(args, a.dest) is "==PROMPT-STRICT=="
            if getattr(args, a.dest) in ("==PROMPT==", "==PROMPT-STRICT=="):
                values = inputStyled(a.help)
                setattr(args, a.dest, values)
                userWasPrompted = True
                # If prompt-strict, raise an error if the provided value is falsy
                if strict:
                    if bool(getattr(args, a.dest)) is False:
                        raise Exception(f"{a.dest} mustn't be falsy")
    except KeyboardInterrupt:
        raise Exception("Quitting...")
    except Exception as err:
        raise Exception(f"An error occuring during parsing: {err}")

    # Get flags
    (
        contract,
        apiKey,
        slug,
        tokenIdJson,
        tokenFilter,
        excepTraces,
        openseaApiKey,
    ) = vars(args).values()

    # Enable exception traces
    if excepTraces is True:
        global exception_traces
        exception_traces = True

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
        statusMsg("ALL REQUIRED PARAMETERS COLLECTED.")

    # TODO: add any missing flags
    print(
        f"[] Slug: {styleArgVal(slug)}\n"
        + f"[] Token ID JSON: {styleArgVal(tokenIdJson)}\n"
        + f"[] Contract Address: {styleArgVal(contract)}\n"
        + f"[] API Key (Moralis): {styleArgVal(apiKey)}\n"
        + f"[] API Key (OpenSea): {styleArgVal(openseaApiKey)}\n"
        + f"[] Filter: {styleArgVal(tokenFilter)}",
    )

    # TODO: add any missing flags
    return slug, tokenIdJson, contract, apiKey, tokenFilter, openseaApiKey


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

    # TODO: add typehints to funcsig
    def get_opensea_collection_stats(collection_slug, opensea_api_key):
        """Get stats on an OpenSea collection with the collection's slug."""
        headers = {}
        if opensea_api_key is not None:
            headers["X-API-Key"] = opensea_api_key

        response = requests.get(
            f"https://api.opensea.io/api/v1/collection/{collection_slug}",
            headers=headers,
        )
        if not response.ok:
            raise RuntimeError(
                f"Failed to get OpenSea collection stats: {response.status_code} ({response.reason})"
            )

        return response.json()["collection"]["stats"]


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
            # TODO: Add debug flag that re-enables error printing in this section
            except RuntimeError as err:
                # print(err)
                # print("might be getting throttled, trying again in 1.5 seconds...")
                time.sleep(1.5)
            except KeyboardInterrupt:
                # print("Cancelled by user...")
                raise KeyboardInterrupt
            except requests.exceptions.ReadTimeout:
                continue
                # print(
                #     f"{Fore.YELLOW}Timed-out waiting for server response...{Style.RESET_ALL}"
                # )
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
def getOwners(contract, tokenIds, tokenFilter, apiKey):
    # showCheckingHolders()

                with progressBar(len(tokenIds), bar="filling") as bar:
                    _getOwners(tokenIds, contract, apiKey, bar)

                try:
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
    # TODO: Add timestamp to snapshot file
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


class CollectTokenIds:
    def from_opensea(slug, contract, opensea_api_key):
        # Get size of collection
        collection_stats = API.get_opensea_collection_stats(
            slug, opensea_api_key
        )
        # NOTE: Supersedes totalMinted argument
        collection_size = collection_stats["total_supply"]

        # Figure out how many requests we need to make
        assets_per_request = 50
        requests_left = math.ceil(collection_size / assets_per_request)
        collected = 0
        token_ids = []

        with progressBar(requests_left, bar="filling") as bar:
            for r in range(requests_left):
                # Calculate request's offset
                offset = r * assets_per_request

                # Collect OpenSea collection assets
                response = API.get_opensea_collection_assets(
                    slug, offset, opensea_api_key
                )
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

                # Extract token_ids from response, append to total collection
                token_ids.extend(
                    [asset["token_id"] for asset in responseJson["assets"]]
                )

                # Increment collected counter
                collected += assets_per_request
                if collected > collection_size:
                    collected = collection_size

                # Announce progress
                # print(f"Request #{r} - {collected} assets collected")
                bar()

        return token_ids

    def from_json(tokenIdJson):
        with open(tokenIdJson) as f:
            return json.load(f)["tokenIds"]


def statusMsg(msg):
    """Prints status message with common formatting."""
    print(f"\n{Fore.YELLOW}{Back.BLACK} {msg} {Style.RESET_ALL}\n")


# Main handle
def main():
    coloramaInit()
    showHeader()
    try:
        # Gather arguments
        (
            slug,
            tokenIdJson,
            contract,
            apiKey,
            tokenFilter,
            openseaApiKey,
        ) = flagInit()

        statusMsg("COLLECTING TOKEN IDS.")

        # Gather token_ids
        if slug:
            tokenIds = CollectTokenIds.from_opensea(
                slug, contract, openseaApiKey
            )
        elif tokenIdJson:
            tokenIds = CollectTokenIds.from_json(tokenIdJson)
        else:
            raise Exception(
                "No valid token_ids sources to selected! - Please open a GitHub issue if you see this"
            )

        statusMsg("COLLECTING OWNERS.")

        # Get owners
        getOwners(contract, tokenIds, tokenFilter, apiKey)

        statusMsg("EXPORTING RESULTS.")

        # Export results
        exportJSON(slug)

    except Exception as err:
        fatalError(err)


# Start
main()
