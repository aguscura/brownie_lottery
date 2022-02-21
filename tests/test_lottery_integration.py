# THE INTEGRATION TEST WILL RUN IN THE REAL BLOCKCHAIN (TESTNET)

import pytest
from brownie import network
from scripts.useful_scripts import local_environments, get_account, fund_with_link
from scripts.deploy import deploy_lottery
import time

def test_can_pick_winner():
    if network.show_active() in local_environments:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from":account})
    
    #In rinkeby, is us entering 2 times to the lottery.
    lottery.enter({"from":account, "value":(lottery.getEntranceFee()+1000)})
    lottery.enter({"from":account, "value":(lottery.getEntranceFee()+1000)})
    #Funding with link to request randomness
    fund_with_link(lottery)
    #Ending Lottery
    lottery.endLottery({"from":account})

    #We are connected to rinkeby so don't need to simulate the randomness request.
    #We'll wait 1 minute until the chainlink node responds.
    time.sleep(60)

    assert lottery.recentWinner() == account.address()
    assert lottery.balance() == 0

    #IMPORTANT TIP
    # add "-s" at the end to see whatever brownie is printing. 