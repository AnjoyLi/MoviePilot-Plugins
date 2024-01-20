from urllib.parse import urlencode

from app.plugins import _PluginBase
from app.core.module import ModuleManager
from app.helper.module import ModuleHelper
from app.core.event import eventmanager, Event
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils
from typing import Any, List, Dict, Tuple
from app.log import logger

import json

class QqMsg(_PluginBase):
    # 插件名称
    plugin_name = "QQ消息通知"
    # 插件描述
    plugin_desc = "支持使用QQ发送消息通知、交互。"
    # 插件图标
    plugin_icon = "https://qzonestyle.gtimg.cn/qzone/qzact/act/external/tiqq/logo.png"
    # 主题色
    plugin_color = "#fdfffd"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "anjoyli"
    # 作者主页
    author_url = "https://github.com/anjoyli"
    # 插件配置项ID前缀
    plugin_config_prefix = "qqmsg_"
    # 加载顺序
    plugin_order = 28
    # 可使用的用户级别
    auth_level = 1

    modulemanager: ModuleManager = None
    # 私有属性
    _enabled = False
    _token = None
    _msgtypes = []
    _send_type = None
    # qq对应的api
    _send_msg_url = ""
    # qq号
    _qq_number = None
    # 发送一次测试消息
    _testonce = False

    def init_plugin(self, config: dict = None):
        logger.info(f"初始化插件 {self.plugin_name}")
        if config:
            self._enabled = config.get("enabled")
            self._send_type = config.get("send_type")
            self._send_msg_url = config.get("msg_url")
            self._qq_number = config.get("qq_number")
            self._token = config.get("token")
            self._testonce = config.get("testonce")
            self._msgtypes = config.get("msgtypes") or []
        
        if not self._send_msg_url or not self._qq_number:
            self._enabled = False
        
        # send_fastapi_msg默认开启交互
        if self._send_type == 'send_fastapi_msg':
            if self.modulemanager:
                if self.modulemanager.get_modules('message_parser') == []:
                    self.register_module()
            else:
                self.modulemanager = ModuleManager()
                self.register_module()
        
        if self._testonce and self._enabled:
            logger.info(f"发送qq测试消息")
            self.send_msg_to_qq(title="测试消息", text="内容", user="tester")
            self._testonce = False

            self.update_config({
                "testonce": False,
                "enabled": self._enabled,
                "send_type": self._send_type,
                "msg_url": self._send_msg_url,
                "qq_number": self._qq_number,
                "token": self._token,
                "msgtypes": self._msgtypes or []
            })

    def register_module(self):
        modules = ModuleHelper.load(
            "app.plugins.qqmsg",
            filter_func=lambda _, obj: hasattr(obj, 'init_module') and hasattr(obj, 'init_setting')
        )
        for module in modules:
            module_id = module.__name__
            self.modulemanager._modules[module_id] = module
            # 生成实例
            _module = module()
            # 初始化模块
            _module.init_module(url=f"{self._send_msg_url}/send_fastapi_msg",num=self._qq_number)
            self.modulemanager._running_modules[module_id] = _module
            logger.info(f"Moudle Loaded：{module_id}")


    def get_state(self) -> bool:
        return self._enabled and (True if self._token else False)

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        # 编历 NotificationType 枚举，生成消息类型选项
        MsgTypeOptions = []
        for item in NotificationType:
            MsgTypeOptions.append({
                "title": item.value,
                "value": item.name
            })
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'testonce',
                                            'label': '测试消息发送',
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 8
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'msg_url',
                                            'label': '消息发送地址',
                                            'placeholder': 'http://{ip}:{port}',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 4
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'send_type',
                                            'label': '消息发送方式',
                                            'items': [
                                                {'title': 'Http正向私聊', 'value': 'send_private_msg'},
                                                {'title': 'Http正向群聊', 'value': 'send_group_msg'},
                                                {'title': 'bot内fastapi', 'value': 'send_fastapi_msg'},
                                            ]
                                        }
                                    }
                                ]
                            },
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'qq_number',
                                            'label': '私聊账号/群号',
                                            'placeholder': 'qq号/群号',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'token',
                                            'label': 'QQ令牌',
                                            'placeholder': 'http access_token',
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'model': 'msgtypes',
                                            'label': '消息类型',
                                            'items': MsgTypeOptions
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '消息交互只适用send_fastapi_msg方式,使用说明https://homev6.anjoy.top/wordpress/2023/12/25/moviepilot/'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            'token': '',
            'msgtypes': []
        }

    def get_page(self) -> List[dict]:
        pass


    @eventmanager.register(EventType.NoticeMessage)
    def send(self, event: Event):
        """
        消息发送事件
        """
        if not self.get_state():
            return

        if not event.event_data:
            return

        msg_body = event.event_data
        # 渠道
        # channel = msg_body.get("channel")
        # if channel:
        #     return
        if self.modulemanager:
            return
        # 类型
        msg_type: NotificationType = msg_body.get("type")
        # 标题
        title = msg_body.get("title")
        # 文本
        text = msg_body.get("text")
        # 图片
        image = msg_body.get("image")

        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return

        if (msg_type and self._msgtypes
                and msg_type.name not in self._msgtypes):
            logger.info(f"消息类型 {msg_type.value} 未开启消息发送")
            return

        try:
            state, res = self.send_msg_to_qq(title=title,
                                        text=text,
                                        image=""if image == None else image,
                                        user="Anjoy")
        except Exception as msg_e:
            logger.error(f"QQ消息发送失败，{str(msg_e)}")

    
    def send_msg_to_qq(self, title, text="", image="", user=""):
        headers = {'content-type': 'application/x-www-form-urlencoded'}
        message_url = self._send_msg_url
        req_json = {
            "user_id": self._qq_number,
        }
        
        content = "%s\n%s" % (title, text.replace("\n\n", "\n")) if text else title
        data = {
            "user": user,
            "title": title,
            "image": image,
            "text": content
        }

        if self._token:
            headers['Authorization'] = f"Bearer {self._token}"

        if self._send_type == "send_private_msg" or self._send_type == "send_group_msg":
            return self.__post_request(f"{message_url}/{self._send_type}", headers, {**req_json, **{'message': f'''#{title}\n{content}'''}})
        elif self._send_type == "send_fastapi_msg":
            headers['content-type'] = 'application/json'
            return self.__post_fastapi_request(f"{message_url}/send_fastapi_msg", headers, {**req_json, **data})
  

    def __post_request(self, message_url, headers, req_json):
        """
        向qq发送请求
        """
        try:
            res = RequestUtils(headers=headers).post(message_url,
                                                     data=urlencode(req_json))
            if res and res.status_code == 200:
                ret_json = res.json()
                if ret_json.get('retcode') == 0:
                    return True, ret_json.get('status')
                else:
                    return False, ret_json.get('status')
            elif res is not None:
                return False, f"错误码：{res.status_code}，错误原因：{res.reason}"
            else:
                return False, "未获取到返回信息"
        except Exception as err:
            return False, str(err)

    def __post_fastapi_request(self, message_url, headers, req_json):
        """
        向qq发送请求
        """
        try:
            res = RequestUtils(headers=headers).post(message_url,
                                                     data=json.dumps(req_json, ensure_ascii=False).encode('utf-8'))
            if res and res.status_code == 200:
                ret_json = res.json()
                if ret_json.get('status') == 0:
                    return True, ret_json.get('msg')
                else:
                    return False, ret_json.get('msg')
            elif res is not None:
                return False, f"错误码：{res.status_code}，错误原因：{res.reason}"
            else:
                return False, "未获取到返回信息"
        except Exception as err:
            return False, str(err)
    

    def stop_service(self):
        """
        退出插件
        """
        pass