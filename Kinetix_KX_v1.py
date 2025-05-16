import streamlit as st
from web3 import Web3
import json

st.set_page_config(page_title="Kinetix DApp", layout="wide")

# Connect to Ethereum node
infura_url = "https://sepolia.infura.io/v3/e0fcce634506410b87fc31064eed915a"
web3 = Web3(Web3.HTTPProvider(infura_url))

st.title("⚡ Kinetix Token DApp")
st.markdown("---")

# Load ABI
with open("abi.json") as f:
    abi = json.load(f)

# Contract setup
contract_address = Web3.to_checksum_address("0xEDC2F9dCdeE3BBdd7bDbEad04c3E0cEdf165b39b")
contract = web3.eth.contract(address=contract_address, abi=abi)

# User wallet
wallet_address = st.text_input("Enter your wallet address", placeholder="0x...", key="wallet")
if wallet_address:
    wallet_address = Web3.to_checksum_address(wallet_address)
    st.success(f"Wallet connected: {wallet_address}")

# Show ETH price
if st.button("Get Current ETH Price"):
    price = contract.functions.getEthPrice().call()
    st.info(f"Current ETH Price (from Oracle): ${price / 1e8:.2f}")

# Buy position
st.markdown("## Buy Position")
eth_amount = st.number_input("ETH to Buy", min_value=0.0001, step=0.0001, format="%.4f")
if st.button("Buy"):
    if not wallet_address:
        st.error("Connect wallet first.")
    else:
        try:
            tx = contract.functions.buy().build_transaction({
                "from": wallet_address,
                "value": web3.to_wei(eth_amount, 'ether'),
                "nonce": web3.eth.get_transaction_count(wallet_address),
                "gas": 250000,
                "gasPrice": web3.to_wei('10', 'gwei')
            })
            st.code(tx)
            st.success("Transaction built. Sign it in your wallet (e.g. MetaMask).")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# View positions
st.markdown("## My Positions")
if st.button("View My Positions"):
    try:
        positions = contract.functions.getMyPositions().call({'from': wallet_address})
        for i, pos in enumerate(positions):
            st.write(f"🔹 Position #{i}")
            st.write(f"Entry Price: {pos[0]/1e8:.2f} USD")
            st.write(f"Amount: {web3.from_wei(pos[1], 'ether')} ETH")
            st.write(f"Sold: {'✅' if pos[2] else '❌'}")
            st.markdown("---")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Withdraw
st.markdown("## Withdraw Position")
pos_id = st.number_input("Position ID to Withdraw", min_value=0, step=1)
if st.button("Withdraw"):
    try:
        tx = contract.functions.withdraw(pos_id).build_transaction({
            "from": wallet_address,
            "nonce": web3.eth.get_transaction_count(wallet_address),
            "gas": 150000,
            "gasPrice": web3.to_wei('10', 'gwei')
        })
        st.code(tx)
        st.success("Withdraw transaction built. Sign it to continue.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Upkeep check
st.markdown("## Chainlink Automation")
if st.button("Check Upkeep"):
    try:
        upkeep, data = contract.functions.checkUpkeep(b'').call({'from': wallet_address})
        st.write(f"Upkeep Needed: {'✅' if upkeep else '❌'}")
        st.write(f"Perform Data: {data.hex()}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

if st.button("Perform Upkeep"):
    try:
        tx = contract.functions.performUpkeep(b'').build_transaction({
            "from": wallet_address,
            "nonce": web3.eth.get_transaction_count(wallet_address),
            "gas": 200000,
            "gasPrice": web3.to_wei('10', 'gwei')
        })
        st.code(tx)
        st.success("Perform Upkeep transaction built. Sign it in your wallet.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

