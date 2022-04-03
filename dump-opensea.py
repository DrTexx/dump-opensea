# Import necessary libraries
import requests, argparse, json, sys, time
import math
from colorama import Fore, Back, Style, init as coloramaInit
from alive_progress import alive_bar as progressBar

# Initialize main vars
offset = 0
num = 0
totalOwned = 0
totalNfts = 0
owners = {}
filteredOwners = {}

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
    # Parse Flags
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--slug", help="Slug Name")
    parser.add_argument("-c", "--contract", help="Contract Address")
    parser.add_argument("-m", "--minted", help="Total Minted")
    parser.add_argument("-k", "--apikey", help="API Key")
    parser.add_argument(
        "-f",
        "--filter",
        help="Filter by Tokens (2 If you want to filter by holders with 2 or more tokens)",
    )
    args = parser.parse_args()

    # Check if flags exists
    slug = args.slug
    contract = args.contract
    totalMinted = int(args.minted)
    apiKey = args.apikey
    tokenFilter = args.filter
    print(
        f"[] Slug: {styleArgVal(slug)}\n"
        + f"[] Contract Address: {styleArgVal(contract)}\n"
        + f"[] Total Minted: {styleArgVal(totalMinted)}\n"
        + f"[] API Key: {styleArgVal(apiKey)}\n"
        + f"[] Filter: {styleArgVal(tokenFilter)}\n"
    )
    return slug, contract, totalMinted, apiKey, tokenFilter


# Init with user input
def inputInit():
    slug = inputStyled("Project Slug")
    contract = inputStyled("Contract Address")
    totalMinted = inputStyled("Collection Total Tokens")
    apiKey = inputStyled("Moralis API Key")
    tokenResponse = inputStyled("Filter owners ? (Y/N)").lower()
    if tokenResponse == "y":
        tokenFilter = inputStyled("Minimum number of tokens holding")
    else:
        tokenFilter = None
    return slug, contract, totalMinted, apiKey, tokenFilter


# Fatal Error --> Exit
def fatalError(excep):
    print(
        f"\n{Fore.BLACK}{Back.YELLOW} ⚠︎ FATAL ERROR ⚠︎ {Style.RESET_ALL}"
        + f"{Fore.YELLOW}{Back.BLACK} {excep} {Style.RESET_ALL}"
    )
    print(f"\n{Fore.RED}An error has occurred. Please try again.\n")
    sys.exit()


# Retrieving owners from API's
def getOwners(slug, contract, pagination, tokenFilter, apiKey):
    # Iterate trough the pagination
    print(
        f"""\n{Fore.YELLOW}
        +------------------------------------------------------------+
        |              CHECKING HOLDERS. PLEASE WAIT...              |
        +------------------------------------------------------------+{Fore.WHITE}\n"""
    )
    try:
        with progressBar(int(pagination), bar="filling") as bar:
            for i in range(0, int(pagination)):
                offset = i * 50
                response = requests.get(
                    f"https://api.opensea.io/api/v1/assets?order_direction=desc&offset={offset}&limit=50&collection={slug}"
                )
                if response.ok is not True:
                    raise RuntimeError(
                        f"Failed to collect assets from OpenSea API: {response.status_code} ({response.reason})"
                    )
                responseJson = response.json()
                for asset in responseJson["assets"]:
                    global totalNfts, totalOwned, owners, num
                    totalNfts += 1
                    try:
                        web3response = requests.get(
                            f"https://deep-index.moralis.io/api/v2/nft/{contract}/{asset['token_id']}/owners?chain=eth&format=decimal",
                            headers={"X-API-Key": apiKey},
                        ).json()
                    except:
                        web3response = requests.get(
                            f"https://deep-index.moralis.io/api/v2/nft/{contract}/{asset['token_id']}/owners?chain=eth&format=decimal",
                            headers={"X-API-Key": apiKey},
                        ).json()
                    totalOwned += web3response["total"]
                    for r in web3response["result"]:
                        if r["owner_of"] in owners:
                            owners[r["owner_of"]] += 1
                        else:
                            owners[r["owner_of"]] = 1
                    num += 1
                bar()
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
            contract,
            totalMinted,
            apiKey,
            tokenFilter,
        ) = flagInit()  # Init with flags
    except:
        (
            slug,
            contract,
            totalMinted,
            apiKey,
            tokenFilter,
        ) = inputInit()  # Init with user input
    pagination = int(math.ceil((int(totalMinted)) / 50))  # Get pagination
    getOwners(slug, contract, pagination, tokenFilter, apiKey)  # Main method
    exportJSON(slug)  # Export results


# Start
main()
