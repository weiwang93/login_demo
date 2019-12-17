import json
import configparser

from web3 import Web3, HTTPProvider

class ContractUtils():
    def __init__(self, config_path):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self.web3 = Web3(HTTPProvider(config.get("contract", "rpc_url")))
        self.contract = self.web3.eth.contract(
            address=config.get("contract", "address"),
            abi=json.loads(config.get("contract", "abi"))
        )

    def check_private_key(self, address, private_key):
        try:
            acct = self.web3.eth.account.privateKeyToAccount(private_key)
            if(acct.address != address):
                return False
            return True
        except Exception as e:
            return False

    def add_admin(self, sender_private_key, new_admin):
        acct = self.web3.eth.account.privateKeyToAccount(sender_private_key)
        construct_txn = self.contract.functions.addAdmin(new_admin).buildTransaction({
            'from': acct.address,
            'gas': 500000,
            'gasPrice': 2000000000,
            'nonce': self.web3.eth.getTransactionCount(acct.address)
        })
        signed = acct.signTransaction(construct_txn)
        tx_hash = signed['hash'].hex()
        # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash

    def del_admin(self, privateKey, admin_address):
        acct = self.web3.eth.account.privateKeyToAccount(privateKey)
        construct_txn = self.contract.functions.deleteAdmin(admin_address).buildTransaction({
            'from': acct.address,
            'gas': 500000,
            'gasPrice': 2000000000,
            'nonce': self.web3.eth.getTransactionCount(acct.address)
        })
        signed = acct.signTransaction(construct_txn)
        tx_hash = signed['hash'].hex()
        # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash

    def get_all_admin(self):
        return self.contract.functions.getAllAdmin().call()

    def add_app(self, privateKey, app_name):
        acct = self.web3.eth.account.privateKeyToAccount(privateKey)
        construct_txn = self.contract.functions.addApp(app_name).buildTransaction({
            'from': acct.address,
            'gas': 500000,
            'gasPrice': 2000000000,
            'nonce': self.web3.eth.getTransactionCount(acct.address)
        })
        signed = acct.signTransaction(construct_txn)
        tx_hash = signed['hash'].hex()
        # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash

    def authorize_app(self, privateKey, app_name):
        acct = self.web3.eth.account.privateKeyToAccount(privateKey)
        construct_txn = self.contract.functions.authorizeApp(app_name).buildTransaction({
            'from': acct.address,
            'gas': 500000,
            'gasPrice': 2000000000,
            'nonce': self.web3.eth.getTransactionCount(acct.address)
        })
        signed = acct.signTransaction(construct_txn)
        tx_hash = signed['hash'].hex()
        # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash

    def prohibit_app(self, privateKey, app_name):
        acct = self.web3.eth.account.privateKeyToAccount(privateKey)
        construct_txn = self.contract.functions.prohibitApp(app_name).buildTransaction({
            'from': acct.address,
            'gas': 500000,
            'gasPrice': 2000000000,
            'nonce': self.web3.eth.getTransactionCount(acct.address)
        })
        signed = acct.signTransaction(construct_txn)
        tx_hash = signed['hash'].hex()
        # tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)
        self.web3.eth.sendRawTransaction(signed.rawTransaction)
        return tx_hash

    def get_app_stratus(self, app_name):
        return self.contract.functions.getAppStatus(app_name).call()

    def get_all_apps(self):
        return self.contract.functions.getAllApp().call()

    def get_authenticated_apps(self):
        return self.contract.functions.getAuthenticatedApp().call()


# contract_instance = ContractUtils('config.ini')
# print(contract_instance.get_all_admin())
# print(contract_instance.check_private_key('0xA4438a2d06E9eC4A3f4Dba8bb77A4Ec9680b5096', '603C6161347D1A071A2EE7C1430EFB67A0734F821722FF0D6FFF8CA7553E076'))
