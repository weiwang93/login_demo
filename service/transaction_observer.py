from MongoDao import mongo_instance
import configparser
from contractUtils import ContractUtils
from web3 import Web3, HTTPProvider

def app_status_updater(contract_util):
    all_apps = contract_util.get_all_apps()
    authenticated_apps = contract_util.get_authenticated_apps()
    nonauthed_apps = set(all_apps).difference(set(authenticated_apps))
    # all_apps = [11, 22]
    # authenticated_apps = [22]
    # nonauthed_apps = [11]
    mongo_instance.update_apps_status(all_apps, authenticated_apps, nonauthed_apps)

def transaction_updater():
    transactions = mongo_instance.get_pending_transaction()
    for trans in transactions:
        print(trans)
        currentBlock = web3.eth.blockNumber
        receipt = web3.eth.getTransactionReceipt(trans.transaction_hash)
        if receipt:
            # from pending to accepted
            if trans.status == "pending":
                mongo_instance.update_transaction_status(trans['transaction_hash'], "acceptd")
            else:
                deltaBlock = currentBlock - receipt['blockNumber']
                # from accepted to confirmed
                if deltaBlock >= config.getint("base", "confirm_num"):
                    mongo_instance.update_transaction_status(trans['transaction_hash'], "success")
        else:
            # from accepted to reverted, i.e. fail
            if trans.status != "pending":
                mongo_instance.update_transaction_status(trans['transaction_hash'], "failed")

if __name__ == "__main__":
    # argument
    config = configparser.ConfigParser()
    config.read("config.ini")
    port = config.get("view", "port")
    web3 = Web3(HTTPProvider(config.get("contract", "rpc_url")))
    contract_util = ContractUtils("config.ini")
    transaction_updater()

    # while True:
        # app_status_updater(contract_util)
