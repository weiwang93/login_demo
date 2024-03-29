from web3 import Web3, HTTPProvider

from utils.MongoDao import mongo_instance
from utils.contractUtils import ContractUtils
from utils.logger import logger

import configparser
import time
import traceback

def app_status_updater():
    logger.info('start update app status')
    all_apps = contract_util.get_all_apps()
    authenticated_apps = contract_util.get_authenticated_apps()
    nonauthed_apps = set(all_apps).difference(set(authenticated_apps))
    mongo_instance.update_apps_status(all_apps, authenticated_apps, list(nonauthed_apps))
    logger.info('update app status finish')

def transaction_updater():
    try:
        logger.info('start update transaction status')
        transactions = mongo_instance.get_pending_transaction()
        for trans in transactions:
            logger.info("parse:" + str(trans))
            currentBlock = web3.eth.blockNumber
            receipt = web3.eth.getTransactionReceipt(trans['transaction_hash'])
            if receipt:
                # from pending to accepted
                if trans['status'] == "pending":
                    mongo_instance.update_transaction_status(trans['transaction_hash'], "acceptd")
                else:
                    deltaBlock = currentBlock - receipt['blockNumber']
                    # from accepted to confirmed
                    if deltaBlock >= config.getint("base", "confirm_num"):
                        # transaction success
                        if receipt['status'] == 1:
                            mongo_instance.update_transaction_status(trans['transaction_hash'], "success")
                        # transaction failed
                        else:
                            mongo_instance.update_transaction_status(trans['transaction_hash'], "failed")
            else:
                # from accepted to reverted, i.e. fail
                if trans['status'] != "pending":
                    mongo_instance.update_transaction_status(trans['transaction_hash'], "failed")
        logger.info('update transaction status finish')
    except Exception as e:
        logger.info('update transaction error:' + str(e))
        traceback.print_exc()

def admin_status_updater():
    logger.info('start update admin status')
    valid_admin = contract_util.get_all_admin()
    logger.info("valid_admin:" + str(valid_admin))
    mongo_instance.update_admin_status(valid_admin)
    logger.info('update admin status finish')

if __name__ == "__main__":
    # argument
    config = configparser.ConfigParser()
    config.read("config.ini")
    port = config.get("view", "port")
    web3 = Web3(HTTPProvider(config.get("contract", "rpc_url")))
    contract_util = ContractUtils("config.ini")


    while True:
        transaction_updater()
        app_status_updater()
        admin_status_updater()
        time.sleep(5)
