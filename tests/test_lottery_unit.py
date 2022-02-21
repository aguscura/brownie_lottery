#TESTING ALL FUNCTIONS IN THE SMART CONTRACT.
from threading import local
from scripts.useful_scripts import get_account, get_contract, local_environments, get_account, fund_with_link, get_contract
from brownie import network, exceptions
from scripts.deploy import deploy_lottery
from web3 import Web3
import pytest

def test_get_entrance_fee():
    if network.show_active() not in local_environments:
        pytest.skip()
    #arrange 
    lottery = deploy_lottery()
    #act
    entrance_fee = lottery.getEntranceFee()
    expected_entrance_fee = Web3.toWei(0.025,"ether") #Initial rate is 2000 USD/ETH (we set that)
    #assert
    assert expected_entrance_fee==entrance_fee
    
    
def test_cant_enter_unless_started ():
    #arrange
    if network.show_active() not in local_environments:
        pytest.skip()
    lottery = deploy_lottery()
    
    #act/assert

    # Option 1 - checking the lottery is closed (lottery_state=1)
    assert(lottery.lottery_state() == 1)
    
    # Option 2 - with pytest. the player can't enter because lottery has not started yet (exception VME)
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": (lottery.getEntranceFee()+10000000)})

def test_can_enter_if_started():
    #arrange
    if network.show_active() not in local_environments:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()

    #act 1
    lottery.startLottery({"from": account})

    #assert1
    #checking the lottery is openned (lottery_state=0)
    assert(lottery.lottery_state()==0)

    #act2
    lottery.enter({"from":account, "value": lottery.getEntranceFee()+1000000})

    #assert2
    #checking if the player that has entered is in the Players array.
    assert(lottery.Players(0) == account)

#ALL TEST FUNCTIONS MUST START WITH TEST WORD.
def test_can_end_lottery():
    #arrange
    if network.show_active() not in local_environments:
        pytest.skip()

    lottery = deploy_lottery()
    account = get_account()

    lottery.startLottery({"from":account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from":account})    
    
    assert(lottery.lottery_state() == 2)

def test_can_pick_winner_correctly():
    #arrange
    if network.show_active() not in local_environments:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()

    lottery.startLottery({"from":account})
    lottery.enter({"from":account, "value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=1), "value":lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=2), "value":lottery.getEntranceFee()})

    #Here we fund the contract with some link to request the random number
    fund_with_link(lottery)

    #We'll listen an event. MUCH MORE GAS EFFICIENT. Instead of a storage variable.
    #The events are stored in the blockchain but are not accessible by any smart contract.
    #Like the "Print lines" of the blockchain.
    #Events when: 1) Upgrae our SmartContract 2) To hear when mapping changes. 3) Testing.
    transaction = lottery.endLottery({"from":account})
    request_id = transaction.events["RequestedRandomness"]["requestId"]

    #Simulating VRF Coordinator action (giving back the random number)
    STATIC_RANDOM = 777
    get_contract("vrf_coordinator").callBackWithRandomness(request_id, STATIC_RANDOM, lottery.address, {"from": account})

    # 777 % 3 = 0 (winner: our "account")
    starting_balance_winner = account.balance()
    contract_balance = lottery.balance()

    #Checking winner
    assert lottery.recentWinner() == account
    #Contract balance restarts to 0
    assert lottery.balance() == 0
    #Account balance at the end sould have the prize.
    assert account.balance() == starting_balance_winner + contract_balance




