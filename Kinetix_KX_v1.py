import streamlit as st
from web3 import Web3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
PUBLIC_KEY = Web3.to_checksum_address(os.getenv("PUBLIC_KEY"))

# Setup Web3
infura_url = "https://sepolia.infura.io/v3/e0fcce634506410b87fc31064eed915a"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Load contract ABI
with open('abi.json') as f:
    abi = json.load(f)

contract_address = Web3.to_checksum_address("0xEDC2F9dCdeE3BBdd7bDbEad04c3E0cEdf165b39b")
contract = web3.eth.contract(address=contract_address, abi=abi)

# Streamlit UI
st.set_page_config(page_title="Kinetix dApp", layout="centered")
st.title("🚀 Kinetix Token dApp")

wallet_address = st.text_input("Enter your wallet address")

if wallet_address:
    try:
        wallet_address = Web3.to_checksum_address(wallet_address)
    except Exception as e:
        st.error("Invalid wallet address format.")
    else:
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

        st.subheader("🛠️ Write Functions")

        # Buy Function
        eth_value = st.text_input("Amount of ETH to send (in wei)", "10000000000000000")  # 0.01 ETH
        if st.button("Buy"):
            try:
                nonce = web3.eth.get_transaction_count(PUBLIC_KEY)
                txn = contract.functions.buy().build_transaction({
                    'from': PUBLIC_KEY,
                    'value': int(eth_value),
                    'gas': 200000,
                    'gasPrice': web3.to_wei('50', 'gwei'),
                    'nonce': nonce
                })
                signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                st.success(f"Buy transaction sent! TX Hash: {tx_hash.hex()}")
            except Exception as e:
                st.error(str(e))

        # Manual Sell Function
        if st.button("Manual Sell"):
            try:
                nonce = web3.eth.get_transaction_count(PUBLIC_KEY)
                txn = contract.functions.manualSell().build_transaction({
                    'from': PUBLIC_KEY,
                    'gas': 200000,
                    'gasPrice': web3.to_wei('50', 'gwei'),
                    'nonce': nonce
                })
                signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                st.success(f"Manual sell transaction sent! TX Hash: {tx_hash.hex()}")
            except Exception as e:
                st.error(str(e))

        # Withdraw Function
        position_id = st.text_input("Position ID to withdraw", "0")
        if st.button("Withdraw"):
            try:
                nonce = web3.eth.get_transaction_count(PUBLIC_KEY)
                txn = contract.functions.withdraw(int(position_id)).build_transaction({
                    'from': PUBLIC_KEY,
                    'gas': 200000,
                    'gasPrice': web3.to_wei('50', 'gwei'),
                    'nonce': nonce
                })
                signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                st.success(f"Withdraw transaction sent! TX Hash: {tx_hash.hex()}")
            except Exception as e:
                st.error(str(e))

        # CheckUpkeep and PerformUpkeep
        st.write("📡 Chainlink Automation")
        calldata = st.text_input("Calldata (hex)", "0x")
        
        if st.button("Check Upkeep"):
            try:
                upkeep_needed, _ = contract.functions.checkUpkeep(calldata).call()
                st.success(f"Upkeep Needed: {upkeep_needed}")
            except Exception as e:
                st.error(str(e))

        if st.button("Perform Upkeep"):
            try:
                nonce = web3.eth.get_transaction_count(PUBLIC_KEY)
                txn = contract.functions.performUpkeep(calldata).build_transaction({
                    'from': PUBLIC_KEY,
                    'gas': 250000,
                    'gasPrice': web3.to_wei('50', 'gwei'),
                    'nonce': nonce
                })
                signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
                tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                st.success(f"Perform upkeep transaction sent! TX Hash: {tx_hash.hex()}")
            except Exception as e:
                st.error(str(e))
