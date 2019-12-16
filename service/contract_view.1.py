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

        transactions = mongo_instance.get_transaction()
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

class taskViewHandler(tornado.web.RequestHandler):
    def get(self):
        filters = Filter.getFilterNames()
        filters = [{'name':x[0], 'alias': x[1]} for x in filters.items()]

        isValid = self.get_arguments('isValid')
        msg = self.get_arguments('msg')
        if(len(isValid) > 0 and len(msg) > 0):
            isValid = int(isValid[0])
            msg = msg[0]
        else:
            isValid = None
            msg = None

        kafkaTaskProfiles = mongoDao.getTaskProfileList_byTaskSourceType(taskSourceType = 'kafka')
        fileTaskProfiles = mongoDao.getTaskProfileList_byTaskSourceType(taskSourceType='file')
        # file task 预计推送数量/已推送数量
        for fileTaskProfile in fileTaskProfiles:
            if 'all_task_num' in fileTaskProfiles:
                all_task_num = fileTaskProfile['all_task_num']
            else:
                all_task_num = mongoDao.getTaskNumByName(fileTaskProfile['taskName'])
                fileTaskProfile['all_task_num'] = all_task_num

            pushed_task_num = mongoDao.getPushedTaskNumByName(fileTaskProfile['taskName'])
            fileTaskProfile['pushed_task_num'] = pushed_task_num
            mongoDao.putTaskProfile(fileTaskProfile)

        # kfka task num待更新
        for fileTaskProfile in kafkaTaskProfiles:
            fileTaskProfile['all_task_num'] = -1
            fileTaskProfile['pushed_task_num'] = -1

        self.render("templates/taskView.html", filters=filters, isValid=isValid, msg=msg,
                    kafkaTaskProfiles=kafkaTaskProfiles, fileTaskProfiles=fileTaskProfiles,
                    taskProfileKeys=TaskProfile.show_keys)

class fileBasedViewHandler(tornado.web.RequestHandler):
    def get(self):
        taskId = self.get_argument("taskId")
        task = mongoDao.getTaskPushedById(taskId)

        self.render("templates/fileBasedView.html", title=task['title'], content=task['content'])

class deleteTaskProfileHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            taskName = self.get_argument("taskName")
            taskSourceType = self.get_argument("taskSourceType")
            # 删除对应的taskprofile
            mongoDao.deleteTaskProfileByName(taskName)

            # 删除未推送的任务
            mongoDao.deleteUnpushedTasksByName(taskName)
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(1, '删除任务成功'))
        except Exception as e:
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, '删除任务失败 {}'.format(e)))

class updateTaskProfileStatusHandler(tornado.web.RequestHandler):
    # update taskprofile status
    def post(self):
        try:
            taskName = self.get_argument("taskName")
            status = int(self.get_argument("status"))
            mongoDao.updateTaskProfileByName(taskName, "status", status)
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(1, '更新状态成功'))

        except Exception as e:
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, '更新状态失败 {}'.format(e)))

class addTaskProfileHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            taskProfile = TaskProfile()
            for key in taskProfile.keys:
                if(key == 'status'):
                    taskProfile.dict[key] = 0
                elif key == 'customize-selector':
                    value = self.get_argument(key, default='')
                    try:
                        if value == '':
                            taskProfile.dict[key] = {}
                            continue

                        cust_selector_map = {}
                        tmp_filter = json.loads(value)
                        # 全部封装为list形式
                        for k, v in tmp_filter.items():
                            # 判断为列表
                            if isinstance(v, list):
                                cust_selector_map[k] = v
                            else:
                                cust_selector_map[k] = [v]
                        taskProfile.dict[key] = cust_selector_map
                    except Exception as e:
                        self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, '增加任务失败 {}'.format(
                            'json 解析失败')))
                        traceback.print_exc()
                        return

                else:
                    value = self.get_arguments(key)
                    isValid, msg = taskProfile.updateValue(key, value)
                    if(not isValid):
                        self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, msg))
                        return
        except Exception as e:
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, '增加任务失败 {}'.format(e)))
            traceback.print_exc()

        try:
            # add filebased news list
            if taskProfile.dict['taskSourceType'] == 'file':
                newsListFile = self.request.files['fileTaskNewsList'][0]['body']
                lines = newsListFile.splitlines()

                for row in lines:
                    news = json.loads(row.decode('utf-8'))
                    news['id'] = mpNews.getNewsUniqId_FromJson(news)
                    task2MongoWorker.insertFileTask(news, taskProfile.dict)

                validCnt = mongoDao.getTaskNumByName(taskProfile.dict['taskName'])
                taskProfile.dict['all_task_num'] = validCnt
                logger.info('putFileBaseNews {} count {}'.format(taskProfile.dict['taskName'], validCnt))

            # 添加taskprofile
            mongoDao.insertTaskProfile(taskProfile.dumpToJson())
            # 复审后台添加相应类型
            if mongoDao.getReviewTaskProfile(taskProfile.dict['taskType']) == None:
                mongoDao.putReviewTaskkProfile(taskProfile.dict['taskType'], taskProfile.dict['taskSourceType'],
                                               taskProfile.dict['taskDesc'])

            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(1, '增加任务类型成功'))
        except Exception as e:
            self.redirect("/mcu/mcu_annotation/taskView?isValid={}&msg={}".format(0, '增加任务失败 {}'.format(e)))
            traceback.print_exc()

class addReviewTaskProfileHandler(tornado.web.RequestHandler):
    def post(self):
        try:
            taskType = self.get_arguments('taskType')
            taskDesc = self.get_arguments('taskDesc')
            taskSourceType = self.get_arguments('taskSourceType')
            if not mongoDao.getReviewTaskProfile(taskType[0]):
                mongoDao.putReviewTaskkProfile(taskType[0], taskSourceType[0], taskDesc[0])
                self.redirect("/mcu/mcu_annotation/reviewView?isValid={}&msg={}".format(1, '增加任务类型成功'))
            else:
                self.redirect("/mcu/mcu_annotation/reviewView?isValid={}&msg={}".format(0, '增加任务失败, 任务类型已存在'))
        except Exception as e:
            self.redirect("/mcu/mcu_annotation/reviewView?isValid={}&msg={}".format(0, '增加任务失败 {}'.format(e)))

def router():
    return tornado.web.Application([
        # views
        (r"/adminView", adminViewHandler),
        (r"/transactionView", transactionViewHandler),
        (r"/appView", appViewHandler),

        # functions
        (r"/addAdmin", addAdminHandler),
        (r"/deleteAdmin", deleteAdminHandler),

        (r"/mcu/mcu_annotation/fileBasedView", fileBasedViewHandler),

        # functions
        (r"/mcu/mcu_annotation/taskView/addTaskProfile", addTaskProfileHandler),
        (r"/mcu/mcu_annotation/taskView/deleteTaskProfile", deleteTaskProfileHandler),
        (r"/mcu/mcu_annotation/taskView/updateTaskProfileStatus", updateTaskProfileStatusHandler),

        (r"/mcu/mcu_annotation/reviewView/addReviewTaskProfile", addReviewTaskProfileHandler),
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
