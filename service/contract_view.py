from MongoDao import mongo_instance
from contractUtils import ContractUtils
import tornado.ioloop
import tornado.web
import tornado.template
import tornado.httpserver

import json
import time
import traceback
import configparser

class adminViewHandler(tornado.web.RequestHandler):
    def get(self):
        user_address = self.get_argument('user_address', default='')
        if not mongo_instance.is_admin_valid(user_address):
            self.render("templates/errorView.html", msg="该用户无效")

        isValid = self.get_arguments('isValid')
        msg = self.get_arguments('msg')
        if (len(isValid) > 0 and len(msg) > 0):
            isValid = int(isValid[0])
            msg = msg[0]
        else:
            isValid = None
            msg = None
        # print(msg)
        # print(isValid)
        valid_admin = mongo_instance.get_admin_by_status("valid")
        invalid_admin = mongo_instance.get_admin_by_status("invalid")
        pending_admin = mongo_instance.get_admin_by_status("pending")
        self.render("templates/adminView.html", valid_admin=valid_admin, invalid_admin=invalid_admin,
                    pending_admin=pending_admin, profile=mongo_instance.admin_collection_show_profile,
                    isValid=isValid, msg=msg, user_address=user_address)

class transactionViewHandler(tornado.web.RequestHandler):
    def get(self):
        user_address = self.get_argument('user_address', default='')
        if not mongo_instance.is_admin_valid(user_address):
            self.render("templates/errorView.html", msg="该用户无效")

        transactions = mongo_instance.get_all_transaction()
        self.render("templates/transactionView.html", profile=mongo_instance.transaction_collection_show_profile, transactions=transactions, user_address=user_address)

class appViewHandler(tornado.web.RequestHandler):
    def get(self):
        user_address = self.get_argument('user_address', default='')
        isValid = self.get_arguments('isValid')
        is_admin = mongo_instance.is_admin_valid(user_address)
        msg = self.get_arguments('msg')
        if (len(isValid) > 0 and len(msg) > 0):
            isValid = int(isValid[0])
            msg = msg[0]
        else:
            isValid = None
            msg = None

        apps_status = mongo_instance.get_apps_status()
        self.render("templates/appView.html", apps_status=apps_status, profile=mongo_instance.app_collection_show_profile,
                    is_admin=is_admin,
                    isValid=isValid, msg=msg, user_address=user_address)


class addAdminHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            admin_address = self.get_argument('admin_address', default='')
            admin_private_key = self.get_argument('admin_private_key', default='')
            sender = self.get_argument('sender', default='')
            admin = mongo_instance.get_admin_by_address(sender)
            if admin == None:
                self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '增加admin失败,您没有权限', sender))
            if(contract_util.check_private_key(admin_address, admin_private_key)):
                if(not mongo_instance.is_admin_invalid(admin_address)):
                    self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '增加admin失败,admin已经存在', sender))
                else:
                    transaction_hash = contract_util.add_admin(admin['admin_private_key'], admin_address)
                    mongo_instance.create_or_update_admin(admin_address, admin_private_key,'pending')
                    # add transaction
                    msg = {"function": "add_admin",
                        "admin_address": admin_address,
                        "admin_private_key": admin_private_key,
                    }
                    mongo_instance.create_transaction(transaction_hash, sender, json.dumps(msg))
                    self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(1, '增加admin成功,transaction_hash:'+str(transaction_hash), sender))
            else:
                self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '增加admin失败,地址私钥不匹配', sender))
        except Exception as e:
            self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '增加admin失败{}'.format(e), sender))

class deleteAdminHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            admin_address = self.get_argument('admin_address', default='')
            sender = self.get_argument('sender', default='')
            admin = mongo_instance.get_admin_by_address(sender)
            if admin == None:
                self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '删除admin失败,您没有权限', sender))

            transaction_hash = contract_util.del_admin(admin['admin_private_key'], admin_address)
            msg = {"function": "delete_admin",
                "admin_address": admin_address,
            }
            mongo_instance.create_transaction(transaction_hash, sender, json.dumps(msg))
            self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(1, '删除admin成功,transaction_hash:'+str(transaction_hash), sender))
        except Exception as e:
            self.redirect("/adminView?isValid={}&msg={}&user_address={}".format(0, '删除admin失败{}'.format(e), sender))

class prohibitAppHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            app_name = self.get_argument('app_name', default='')
            sender = self.get_argument('sender', default='')
            admin = mongo_instance.get_admin_by_address(sender)
            if admin == None:
                self.redirect("/appView?isValid={}&msg={}&user_address={}".format(0, '取消认证失败,您没有权限', sender))

            transaction_hash = contract_util.prohibit_app(admin['admin_private_key'], app_name)

            # add transaction
            msg = {"function": "prohibit_app",
                "app_name": app_name,
            }

            mongo_instance.create_transaction(transaction_hash, sender, json.dumps(msg))
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(1, '取消认证成功,transaction_hash:'+str(transaction_hash), sender))

        except Exception as e:
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(0, '取消认证失败{}'.format(e), sender))

class authorizeAppHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            app_name = self.get_argument('app_name', default='')
            sender = self.get_argument('sender', default='')
            admin = mongo_instance.get_admin_by_address(sender)
            if admin == None:
                self.redirect("/appView?isValid={}&msg={}&user_address={}".format(0, '认证失败,您没有权限', sender))

            transaction_hash = contract_util.authorize_app(admin['admin_private_key'], app_name)

            # add transaction
            msg = {"function": "authorize_app",
                "app_name": app_name,
            }

            mongo_instance.create_transaction(transaction_hash, sender, json.dumps(msg))
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(1, '认证成功,transaction_hash:'+str(transaction_hash), sender))

        except Exception as e:
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(0, '认证失败{}'.format(e), sender))


class addAppHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            app_name = self.get_argument('app_name', default='')
            sender = self.get_argument('sender', default='')
            admin = mongo_instance.get_admin_by_address(sender)
            if admin == None:
                sender = config.get("base", "coinbase")
                admin = mongo_instance.get_admin_by_address(sender)

            transaction_hash = contract_util.authorize_app(admin['admin_private_key'], app_name)

            # add transaction
            msg = {"function": "add_app",
                "app_name": app_name,
            }

            mongo_instance.create_transaction(transaction_hash, sender, json.dumps(msg))
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(1, '添加app成功,transaction_hash:'+str(transaction_hash), sender))

        except Exception as e:
            self.redirect("/appView?isValid={}&msg={}&user_address={}".format(0, '添加app失败{}'.format(e), sender))


def router():
    return tornado.web.Application([
        # views
        (r"/adminView", adminViewHandler),
        (r"/transactionView", transactionViewHandler),
        (r"/appView", appViewHandler),

        # functions
        (r"/addAdmin", addAdminHandler),
        (r"/deleteAdmin", deleteAdminHandler),

        (r"/addApp", addAppHandler),
        (r"/prohibitApp", prohibitAppHandler),
        (r"/authorizeApp", authorizeAppHandler),
    ])

if __name__ == "__main__":
    # argument
    config = configparser.ConfigParser()
    config.read("config.ini")
    port = config.get("view", "port")

    # application
    print("http://localhost:{}/adminView?user_address={}".format(port, config.get('base', 'coinbase')))

    contract_util = ContractUtils("config.ini")
    app = router()
    app.listen(port)
    tornado.ioloop.IOLoop.current().start()
