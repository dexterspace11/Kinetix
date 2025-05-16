import streamlit as st
from web3 import Web3
import json

st.set_page_config(page_title="Kinetix dApp", layout="centered")

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/e0fcce634506410b87fc31064eed915a"))

# Load contract
contract_address = "0xEDC2F9dCdeE3BBdd7bDbEad04c3E0cEdf165b39b"
with open("KinetixABI.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=contract_address, abi=abi)

# Login
st.title("🔗 Kinetix dApp")
st.subheader("Login")
private_key = st.text_input("Enter your private key", type="password")
account = w3.eth.account.from_key(private_key) if private_key else None
if account:
    st.success(f"Logged in as {account.address}")

    # ETH Price
    if st.button("Get ETH Price"):
        eth_price = contract.functions.getEthPrice().call()
        st.write(f"📈 ETH Price: {Web3.from_wei(eth_price, 'ether')} USD")

    # Buy
    st.subheader("Buy ETH with Kinetix")
    eth_to_send = st.number_input("ETH to Buy", min_value=0.001, value=0.01)
    if st.button("Buy"):
        tx = contract.functions.buy().build_transaction({
            "from": account.address,
            "value": Web3.to_wei(eth_to_send, "ether"),
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        st.success(f"Buy transaction sent: {tx_hash.hex()}")

    # Manual Sell
    if st.button("Manual Sell"):
        tx = contract.functions.manualSell().build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        st.success(f"Sell transaction sent: {tx_hash.hex()}")

    # Get My Positions
    if st.button("View My Positions"):
        positions = contract.functions.getMyPositions().call({'from': account.address})
        for idx, pos in enumerate(positions):
            st.write(f"Position {idx}: EntryPrice={pos[0]}, Amount={Web3.from_wei(pos[1], 'ether')} ETH, Sold={pos[2]}")

    # Get Sell Target Price
    if st.button("Get Sell Target Price"):
        price = contract.functions.getSellTargetPrice(account.address).call()
        st.write(f"📊 Sell Target Price: {Web3.from_wei(price, 'ether')} USD")

    # Token Balance
    if st.button("Check Kinetix Token Balance"):
        balance = contract.functions.balanceOf(account.address).call()
        st.write(f"💰 Token Balance: {Web3.from_wei(balance, 'ether')} KX")

    # Withdraw
    position_id = st.number_input("Position ID to withdraw", min_value=0, step=1)
    if st.button("Withdraw"):
        tx = contract.functions.withdraw(position_id).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        st.success(f"Withdraw transaction sent: {tx_hash.hex()}")