from pymongo import MongoClient
import pymongo
from datetime import datetime
import time
import traceback
import configparser

class MongoDao():
    def __init__(self):
        config = configparser.ConfigParser()
        config.read("config.ini")
        self._conn_ = MongoClient('{}:{}'.format(
            config.get('mongo', 'mongo_host'),
            config.get('mongo', 'mongo_port'),
        ),
            username=config.get('mongo', 'mongo_user'),
            password=config.get('mongo', 'mongo_pass'),
            authSource=config.get('mongo', 'mongo_db'),
            authMechanism='SCRAM-SHA-1'
        )

        self.mongodb = self._conn_.get_database(config.get('mongo', 'mongo_db'))
        # collection names
        # create index for collections

        ################################
        ########admin_collection########
        ################################
        # admin_address
        # admin_private_key
        # status:pending valid invalid
        # update_time: yyyy-mm-dd hh:mm:ss
        self.admin_collection = self.mongodb.get_collection("admin_collection")
        if (self.admin_collection.count() == 0):
            self.admin_collection.create_index([("admin_address", pymongo.DESCENDING)],
                                          unique=True)
            self.admin_collection.create_index([("status", pymongo.DESCENDING)])
        self.admin_collection_show_profile = ['admin_address', 'status', 'update_time']

        ################################
        #####transaction_collection#####
        ################################
        # transaction_hash
        # sender
        # status: pending, acceptd, success, failed
        # function_data
        # sender
        # created_time
        self.transaction_collection = self.mongodb.get_collection("transaction_collection")
        if(self.transaction_collection.count() == 0):
            self.transaction_collection.create_index([("transaction_hash", pymongo.DESCENDING)],
                                          unique=True)
            self.admin_collection.create_index([("sender", pymongo.DESCENDING)])
            self.admin_collection.create_index([("status", pymongo.DESCENDING)])
        self.transaction_collection_show_profile = ['transaction_hash', 'sender', 'status', 'msg', 'update_time']


        ################################
        ########app_collection##########
        ################################
        # all_apps:list
        # authenticated_apps: list
        # nonauthed_apps:list
        # update_time
        self.app_collection = self.mongodb.get_collection("app_collection")
        self.app_collection_show_profile = ['app_name', 'status', 'update_time']

        # add owner
        self.create_or_update_admin(config.get('base', 'coinbase'), config.get('base', 'private_key'), 'valid')

    def get_time(self):
        now = int(time.time())
        time_struct = time.localtime(now)
        strTime = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
        return strTime

    # **********************
    # functions
    # **********************

    # **********************
    # admin related
    # **********************
    def get_admin_by_status(self, status):
        return self.admin_collection.find({"status":status})

    def get_admin_by_address(self, address):
        return self.admin_collection.find_one({"admin_address":address})

    def is_admin_invalid(self, admin_address):
        if(self.admin_collection.find({"admin_address":admin_address, "status":"invalid"}).count() == 0):
            return False
        return True

    def is_admin_valid(self, admin_address):
        if(self.admin_collection.find({"admin_address":admin_address, "status":"valid"}).count() == 0):
            return False
        return True

    def create_or_update_admin(self, admin_address, admin_private_key, status):
        if(self.admin_collection.find({"admin_address":admin_address}).count() == 0):
            admin = {"admin_address": admin_address,
                    "admin_private_key": admin_private_key,
                    "status": status,
                    "update_time": self.get_time()}
            self.admin_collection.insert(admin)
        else:
            self.admin_collection.update_one(filter={"admin_address": admin_address},
                                    update={"$set": {"status": status, "update_time":self.get_time()}})

    # **********************
    # transaction related
    # **********************
    def create_transaction(self, transaction_hash, sender, msg):
        try:
            transaction = {
                'transaction_hash':transaction_hash,
                'sender': sender,
                'msg': msg,
                'status': 'pending',
                "update_time": self.get_time()
            }
            self.transaction_collection.insert(transaction)
            return True
        except Exception as e:
            traceback.print_exc()
            return False

    def get_all_transaction(self):
        return self.transaction_collection.find()

    def get_pending_transaction(self):
        return self.transaction_collection.find({"status": {"$in": ["pending", "acceptd"]}})

    def update_transaction_status(self, hash, status):
        self.transaction_collection.update_one(filter={'transaction_hash': hash},
                                        update={"$set": {"status": status, "update_time":self.get_time()}})


    # **********************
    # app related
    # **********************
    def get_apps_status(self):
        return self.app_collection.find_one()

    def update_apps_status(self, all_apps, authenticated_apps, nonauthed_apps):
        status = {
            "all_apps": all_apps,
            "authenticated_apps": authenticated_apps,
            "nonauthed_apps": nonauthed_apps,
            "update_time": self.get_time()
        }
        self.app_collection.update_one(filter={},
                                    update={"$set": status})


mongo_instance = MongoDao()