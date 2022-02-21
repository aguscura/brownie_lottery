from brownie import Lottery, config, network
from scripts.useful_scripts import get_account, get_contract, fund_with_link
import time

def deploy_lottery(): 
    account = get_account()
    lottery = Lottery.deploy(
                        get_contract("eth_usd_rate").address,
                        get_contract("vrf_coordinator").address,
                        get_contract("link_token").address,
                        config["networks"][network.show_active()]["fee"],
                        config["networks"][network.show_active()]["keyhash"],
                        {"from": account},
                        publish_source= config["networks"][network.show_active()].get("verify", False)                        
                        )

    print("Lottery Deployed!!")
    return lottery

# IMPORTANT - We need to wait for the LAST transaction. In this case startLottery.
def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from":account})
    starting_tx.wait(1)
    print("The lottery has started!")      

def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFee() + 100000000
    tx = lottery.enter({"from":account, "value":value})
    tx.wait(1)
    print("You entered the lottery!")  

def end_lottery():
    account = get_account()
    lottery = Lottery[-1]

    #fund the contract with LINK to request randomness to chainlink first
    tx1 = fund_with_link(lottery.address)
    tx1.wait(1)

    #then, end the lottery. 
    ending_tx = lottery.endLottery({"from":account})
    ending_tx.wait(1)
    print("Calculating Winner..")

    """llamamos a end_lottery, pero tenemos que esperar que chainlink busque un numero random.
        una vez que lo tiene, va a llamar a fulfillrandomness y recien ahi vamos a tener al ganador.
        para eso ponemos un sleep porque damos por hecho que en 60 seg va a estar todo ok.    
    """
    time.sleep(180)
    print(f"{lottery.recentWinner()} is the new winner!!")
       

def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
