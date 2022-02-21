from msilib.schema import ControlCondition
from tracemalloc import start
from brownie import network, config, accounts, MockV3Aggregator, Contract, VRFCoordinatorMock, LinkToken


#forked environments
forked_environments = ["mainnet-fork", "mainnet-fork-dev"]
#ganache-local is a network in "Ethereum" part where the contracts won't be deleted automaticaly.
local_environments = ["development", "ganache-local"]

def get_account(index=None, id=None):

    # if we pass an index
    if index:
        return accounts[index]
    
    #if we pass the brownie acount id (brownie accounts list)
    if id:
        return accounts.load(id)       

    if (network.show_active() in local_environments or network.show_active() in forked_environments):
        return accounts[0]
    
    return accounts.add(config["wallets"]["from_key"])


#Creating mapping // Contract name to Contract type.
contract_to_mock = {

    "eth_usd_rate" : MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken 
}

def get_contract(contract_name):

    """ This function will grab the contract addresses from the brownie config if defined.
    Otherwise it will deploy a mock version of that contract and return that mock contract.

    Args: contract_name (string)

    Returns: brownie.network.contract.ProjectContract: The most recently deployed version of 
             this contract.
    
    """
    contract_type = contract_to_mock[contract_name]

    # Do we need to deploy a mock? 

    if network.show_active() in local_environments:
        #MockV3Aggregator length. If 0, let's deploy the mock.
        if len(contract_type) <= 0:
            deploy_mocks()

        #MockV3Aggregator[-1]
        contract = contract_type[-1]
    
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        #Address & ABI
        # This below function allows us to get the contract from its ABI.
        contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
   
    return contract
 
decimals = 8
starting_price = 200000000000

def deploy_mocks(decimals=decimals, starting_price=starting_price):
    account = get_account()
    print("Deploying mocks...")
    #IMPORTANT - Here, "MockV3Aggregator" is a list with all the Mock contracts.
    #We add the parameters that constructor needs.
    MockV3Aggregator.deploy(decimals, starting_price, {"from":account})
    link_token = LinkToken.deploy({"from":account})
    VRFCoordinatorMock.deploy(link_token.address, {"from":account})

    print("Mocks deployed!")


#Acá contract address es la direccion del contrato al que le queremos mandar LINK.
def fund_with_link(contract_address, account=None, link_token=None, amount=1000000000000000000):
    
    # "if account" means that someone passes the argument. otherwise, use get_account().
    account = account if account else get_account()

    # 1 - using 'GET_CONTRACT()' function that we built to get the CONTRACT. 
    link_token = link_token if link_token else get_contract("link_token") 

    # 2 - using INTERFACES  to get the CONTRACT.
    #link_token_contract = interface.LinkTokenInterface(link_token.address)

    tx = link_token.transfer(contract_address, amount, {"from":account})
    tx.wait(1)

    print("Funded with LINK!")
    return tx
