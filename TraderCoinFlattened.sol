// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

// Interface for Chainlink's AggregatorV3
interface AggregatorV3Interface {
    function latestRoundData()
        external
        view
        returns (
            uint80,
            int256,
            uint256,
            uint256,
            uint80
        );
}

// Interface for Chainlink Automation
interface AutomationCompatibleInterface {
    function checkUpkeep(bytes calldata checkData) external returns (bool upkeepNeeded, bytes memory performData);
    function performUpkeep(bytes calldata performData) external;
}

// Minimal ERC20 Implementation
contract ERC20 {
    string public name;
    string public symbol;
    uint8 public decimals = 18;
    uint256 public totalSupply;
    mapping(address => uint256) public balanceOf;
    event Transfer(address indexed from, address indexed to, uint256 value);

    constructor(string memory _name, string memory _symbol) {
        name = _name;
        symbol = _symbol;
    }

    function _mint(address account, uint256 amount) internal {
        totalSupply += amount;
        balanceOf[account] += amount;
        emit Transfer(address(0), account, amount);
    }

    function _burn(address account, uint256 amount) internal {
        require(balanceOf[account] >= amount, "Burn amount exceeds balance");
        balanceOf[account] -= amount;
        totalSupply -= amount;
        emit Transfer(account, address(0), amount);
    }
}

// Ownable Contract
contract Ownable {
    address public owner;
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    constructor(address _owner) {
        owner = _owner;
        emit OwnershipTransferred(address(0), _owner);
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Caller is not the owner");
        _;
    }
}

// TraderCoin Contract
contract TraderCoin is ERC20, Ownable, AutomationCompatibleInterface {
    AggregatorV3Interface public priceFeed;

    struct Position {
        uint256 entryPrice;
        uint256 amount; // in wei
        bool sold;
    }

    mapping(address => Position[]) public userPositions;
    address[] public usersWithPositions;

    // --- Events ---
    event Bought(address indexed user, uint256 indexed positionId, uint256 entryPrice, uint256 amount);
    event Sold(address indexed user, uint256 totalAmount, uint256 sellPrice);
    event Withdrawn(address indexed user, uint256 indexed positionId, uint256 amount);
    event UpkeepCheckLog(
        address indexed user,
        uint256 avgEntryPrice,
        uint256 currentPrice,
        uint256 targetPrice,
        bool eligible,
        uint256 gasLeft
    );

    constructor(address _priceFeed) ERC20("TraderCoin", "TRC") Ownable(msg.sender) {
        priceFeed = AggregatorV3Interface(_priceFeed);
    }

    function getEthPrice() public view returns (uint256) {
        (, int256 price, , , ) = priceFeed.latestRoundData();
        require(price > 0, "Invalid price");
        return uint256(price);
    }

    function buy() external payable {
        require(msg.value > 0, "Send ETH to buy");
        uint256 entryPrice = getEthPrice();

        if (userPositions[msg.sender].length == 0) {
            usersWithPositions.push(msg.sender);
        }

        userPositions[msg.sender].push(Position({
            entryPrice: entryPrice,
            amount: msg.value,
            sold: false
        }));

        emit Bought(msg.sender, userPositions[msg.sender].length - 1, entryPrice, msg.value);
        _mint(msg.sender, msg.value);
    }

    function getSellTargetPrice(address user) public view returns (uint256) {
        Position[] memory positions = userPositions[user];

        uint256 totalEntryPrice = 0;
        uint256 totalAmount = 0;

        for (uint256 i = 0; i < positions.length; i++) {
            if (!positions[i].sold && positions[i].amount > 0) {
                totalEntryPrice += positions[i].entryPrice * positions[i].amount;
                totalAmount += positions[i].amount;
            }
        }

        if (totalAmount == 0) {
            return 0;
        }

        uint256 avgEntryPrice = totalEntryPrice / totalAmount;
        uint256 targetPrice = (avgEntryPrice * 10005) / 10000; // 0.05% gain
        return targetPrice;
    }

    function checkUpkeep(bytes calldata) external view override returns (bool upkeepNeeded, bytes memory performData) {
        upkeepNeeded = false;

        for (uint256 u = 0; u < usersWithPositions.length; u++) {
            address user = usersWithPositions[u];
            Position[] memory positions = userPositions[user];

            uint256 totalEntryPrice = 0;
            uint256 totalAmount = 0;

            for (uint256 i = 0; i < positions.length; i++) {
                if (!positions[i].sold && positions[i].amount > 0) {
                    totalEntryPrice += positions[i].entryPrice * positions[i].amount;
                    totalAmount += positions[i].amount;
                }
            }

            if (totalAmount > 0) {
                uint256 avgEntryPrice = totalEntryPrice / totalAmount;
                uint256 currentPrice = getEthPrice();
                uint256 targetPrice = (avgEntryPrice * 10005) / 10000; // 0.05% gain

                if (currentPrice >= targetPrice) {
                    upkeepNeeded = true;
                    performData = abi.encode(user);
                    return (true, performData);
                }
            }
        }
    }

    function performUpkeep(bytes calldata performData) external override {
        address user = abi.decode(performData, (address));
        Position[] storage positions = userPositions[user];

        uint256 totalEntryPrice = 0;
        uint256 totalAmount = 0;

        for (uint256 i = 0; i < positions.length; i++) {
            if (!positions[i].sold && positions[i].amount > 0) {
                totalEntryPrice += positions[i].entryPrice * positions[i].amount;
                totalAmount += positions[i].amount;
            }
        }

        require(totalAmount > 0, "No open positions");

        uint256 avgEntryPrice = totalEntryPrice / totalAmount;
        uint256 currentPrice = getEthPrice();
        uint256 targetPrice = (avgEntryPrice * 10005) / 10000;

        emit UpkeepCheckLog(user, avgEntryPrice, currentPrice, targetPrice, currentPrice >= targetPrice, gasleft());

        require(currentPrice >= targetPrice, "Target not met");

        for (uint256 i = 0; i < positions.length; i++) {
            if (!positions[i].sold && positions[i].amount > 0) {
                positions[i].sold = true;
            }
        }

        emit Sold(user, totalAmount, currentPrice);
    }

    function withdraw(uint256 positionId) external {
        Position storage pos = userPositions[msg.sender][positionId];
        require(pos.sold, "Position not sold yet");

        uint256 amount = pos.amount;
        pos.amount = 0;

        payable(msg.sender).transfer(amount);
        emit Withdrawn(msg.sender, positionId, amount);

        _burn(msg.sender, amount);
    }

    function manualSell() external {
        Position[] storage positions = userPositions[msg.sender];

        uint256 totalAmount = 0;
        for (uint256 i = 0; i < positions.length; i++) {
            if (!positions[i].sold && positions[i].amount > 0) {
                totalAmount += positions[i].amount;
                positions[i].sold = true;
            }
        }

        require(totalAmount > 0, "Nothing to sell");

        uint256 currentPrice = getEthPrice();
        emit Sold(msg.sender, totalAmount, currentPrice);
    }

    function getMyPositions() external view returns (Position[] memory) {
        return userPositions[msg.sender];
    }

    function getPositionCount(address user) external view returns (uint256) {
        return userPositions[user].length;
    }

    receive() external payable {}
}
