import streamlit as st
from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Set up Web3
infura_url = f"https://sepolia.infura.io/v3/{os.getenv('INFURA_PROJECT_ID')}"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Load contract ABI and address
with open('abi.json') as f:
    abi = json.load(f)

contract_address = Web3.to_checksum_address(os.getenv("CONTRACT_ADDRESS"))
contract = web3.eth.contract(address=contract_address, abi=abi)

st.set_page_config(page_title="Kinetix dApp", layout="centered")
st.title("🚀 Kinetix Token dApp")

wallet_address = st.text_input("Enter your wallet address")

if wallet_address:
    st.subheader("🔍 Query Functions")
    
    if st.button("Get ETH Price"):
        try:
            eth_price = contract.functions.getEthPrice().call()
            st.success(f"ETH Price: {eth_price}")
        except Exception as e:
            st.error(str(e))

    if st.button("Get Sell Target Price"):
        try:
            target_price = contract.functions.getSellTargetPrice(wallet_address).call()
            st.success(f"Sell Target Price: {target_price}")
        except Exception as e:
            st.error(str(e))

    if st.button("Get My Positions"):
        try:
            positions = contract.functions.getMyPositions().call({'from': wallet_address})
            st.json(positions)
        except Exception as e:
            st.error(str(e))

    if st.button("Get Position Count"):
        try:
            count = contract.functions.getPositionCount(wallet_address).call()
            st.success(f"Total Positions: {count}")
        except Exception as e:
            st.error(str(e))

    st.subheader("🛠️ Write Functions (Simulated)")
    st.warning("The following functions require transaction signing and are shown for display only.")

    st.code("buy() - Send ETH with the transaction")
    st.code("manualSell() - Manually sell all open positions")
    st.code("withdraw(positionId) - Withdraw ETH after selling a position")
    st.code("checkUpkeep(bytes calldata) and performUpkeep(bytes calldata) - Used by Chainlink Automation")
