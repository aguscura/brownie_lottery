// SPDX-License-Identifier: MIT

pragma solidity ^0.6.0; 

import "@chainlink/contracts/src/v0.6/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";

// is VRFConsumerBase to inherit functions from it.
contract Lottery is VRFConsumerBase, Ownable {

    address payable[] public Players; // The array is payable, public and called Players.
    uint256 public usdEntryFee;

    uint256 public fee;
    bytes32 public keyhash;
    address payable public recentWinner; //if we are going to send money, use payable address.
    uint256 public randomness;

    AggregatorV3Interface internal ethUsdRate; 


    // Creating type
    enum LOTTERY_STATE {
        OPEN, 
        CLOSED,
        CALCULATING_WINNER
    }
    // OPEN --> 0
    // CLOSED --> 1
    // CALCULATING WINNER --> 2

    // Creating variable of type LOTTERY_STATE
    LOTTERY_STATE public lottery_state;

    // Creating an Event for the Requested randomness
    event RequestedRandomness(bytes32 requestId);



    // After keyword 'public' we can add other constructors from inherited SmartContracts (in this case VRFConsumerBase contract)
    constructor(address rate_contract, 
                address _vrfCoordinator, 
                address _link,
                uint256 _fee,
                bytes32 _keyhash) 
                public VRFConsumerBase(_vrfCoordinator, _link) {
        usdEntryFee = 50 * (10**18); // In wei.
        ethUsdRate = AggregatorV3Interface(rate_contract);
        lottery_state = LOTTERY_STATE.CLOSED; // Is the same if we use '= 1'. Because 1 means closed.
        fee = _fee;
        keyhash = _keyhash;
    }

    function enter() public payable {
        // 50USD minimum.
        require(lottery_state == LOTTERY_STATE.OPEN);
        require(msg.value >= getEntranceFee(), "Not enough ETH!");
        Players.push(msg.sender);

    }


    function getEntranceFee() public view returns (uint256) {
    
        (, int256 rate,,,) = ethUsdRate.latestRoundData(); // INT
        // Everything in wei. As the function returns already with 8 decimals we add 10 more.
        uint256 adjustedPrice = uint256(rate) * 10**10; // UINT  

        //ENTRY ETH PRICE 
        // 5O USD / ETH_USD_RATE

        // IMPORTANT - We should use SafeMath just to be safe. But in latest solidity version we don't need it
        // We add the 10*18 manually to have the final result in Wei as Solidity does not support floats.
        uint256 costToEnterinWei = uint256(usdEntryFee*10**18)/ uint256(adjustedPrice);
        return costToEnterinWei; 

    }


    function startLottery() public onlyOwner {

        require(lottery_state == LOTTERY_STATE.CLOSED, "Can't start a new lottery yet!");
        lottery_state = LOTTERY_STATE.OPEN;

    }


    function endLottery() public onlyOwner {

        require(lottery_state == LOTTERY_STATE.OPEN, "Haven't opened a lottery yet!");

        lottery_state = LOTTERY_STATE.CALCULATING_WINNER;

        // requestRandomness returns a variable called requestId of type bytes32.
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
        
    }

    // override keyword allows us to replace everything inside the original function.
    // fulfillRandomness is made for that. For using it here and replace the original function that is void.
    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override {

        require( lottery_state == LOTTERY_STATE.CALCULATING_WINNER, "You aren't there yet!");
        require(_randomness > 0, "random not found");

        uint256 indexOfWinner = _randomness % Players.length;
        recentWinner = Players[indexOfWinner];

        // We transfer the entire balance of this address to the winner.
        recentWinner.transfer(address(this).balance);

        //Reset
        Players = new address payable[](0);

        //Change lottery state
        lottery_state = LOTTERY_STATE.CLOSED;
        randomness = _randomness;



    }

}