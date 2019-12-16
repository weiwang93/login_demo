import os
import sys
import time
import json
import logging
import datetime
import configparser

from web3 import Web3, IPCProvider, HTTPProvider

def wait_for_receipt(w3, tx_hash, poll_interval):
    while True:
        try:
            tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
            if tx_receipt:
                return tx_receipt
            time.sleep(poll_interval)
        except Exception as e:
            time.sleep(poll_interval)

def main():
    config = configparser.ConfigParser()
    config.read("deploy_contract.ini")

    rpc_uri = "https://ropsten.infura.io/v3/dd535079894e4e2c97b71b2029b83c6c"

    web3 = Web3(HTTPProvider(rpc_uri))

    contract_ = web3.eth.contract(
        abi=json.loads(config.get("contract", "abi")),
        bytecode=config.get("contract", "bin")
    )

    privateKey = config.get("base", "private_key")
    acct = web3.eth.account.privateKeyToAccount(privateKey)

    construct_txn = contract_.constructor().buildTransaction({
        'from': acct.address,
        'nonce': web3.eth.getTransactionCount(acct.address)})

    signed = acct.signTransaction(construct_txn)
    web3.eth.sendRawTransaction(signed.rawTransaction)
    tx_hash = signed['hash'].hex()
    print("tx_hash:"+str(tx_hash))
    receipt = wait_for_receipt(web3, tx_hash, 1)
    contract_address = receipt['contractAddress']
    print(contract_address)

if __name__ == "__main__":
    main()
