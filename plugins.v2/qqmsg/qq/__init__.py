import json
from typing import Optional, Union, List, Tuple, Any, Dict

from app.core.context import MediaInfo, Context
from app.core.config import settings
from app.log import logger
from app.modules import _ModuleBase, _MessageBase
from app.plugins.qqmsg.qq.qq import QQ
from app.schemas import MessageChannel, CommingMessage, Notification
from app.schemas.types import ModuleType


class QQModule(_ModuleBase, _MessageBase[QQ]):
    qq: QQ = None

    def init_module(self, url, num) -> None:
        self.qq = QQ(url=url,num=num)
    
    @staticmethod
    def get_name() -> str:
        return "QQ"

    @staticmethod
    def get_type() -> ModuleType:
        """
        获取模块类型
        """
        return ModuleType.Notification

    @staticmethod
    def get_subtype() -> MessageChannel:
        """
        获取模块子类型
        """
        return MessageChannel.Telegram

    @staticmethod
    def get_priority() -> int:
        """
        获取模块优先级，数字越小优先级越高，只有同一接口下优先级才生效
        """
        return 0

    def stop(self):
        self.qq.stop()

    def test(self) -> Tuple[bool, str]:
        """
        测试模块连接性
        """
        state = self.qq.get_state()
        if state:
            return True, ""
        return False, "QQ未就续，请检查参数设置和网络连接"
  
    def init_setting(self) -> Tuple[str, Union[str, bool]]:
        return "MESSAGER", "telegram"

    def message_parser(self, source: str, body: Any, form: Any,
                       args: Any) -> Optional[CommingMessage]:
        """
        解析消息内容，返回字典，注意以下约定值：
        userid: 用户ID
        username: 用户名
        text: 内容
        :param body: 请求体
        :param form: 表单
        :param args: 参数
        :return: 渠道、消息体
        """
        """
            {
                'is_qq': ,
                'message': {
                    'message_id': ,
                    'user_id': ,
                    'user_name': ,  
                    'date': ,
                    'text': ''
                }
            }
        """
        # 获取服务配置
        client_config = self.get_config(source)
        # if not client_config:
        #     return None
        # 校验token
        token = args.get("token")
        if not token or token != settings.API_TOKEN:
            return None
        try:
            message: dict = json.loads(body).get('message')
            is_qq: dict = json.loads(body).get('is_qq')
        except Exception as err:
            logger.debug(f"解析QQ消息失败：{str(err)}")
            return None
        if not is_qq:
            return None
        
        if message:
            text = message.get("text")
            user_id = message.get("user_id")
            # 获取用户名
            user_name = message.get("username")
            if text:
                logger.info(f"收到QQ消息：userid={user_id}, username={user_name}, text={text}")
                return CommingMessage(channel=MessageChannel.Telegram,
                                      userid=user_id, username=user_name, text=text)
        return None

    def post_message(self, message: Notification) -> None:
        """
        发送消息
        :param message: 消息体
        :return: 成功或失败
        """
        self.qq.send_msg(title=message.title, text=message.text,
                               image=message.image, userid=message.userid)

    def post_medias_message(self, message: Notification, medias: List[MediaInfo]) -> Optional[bool]:
        """
        发送媒体信息选择列表
        :param message: 消息体
        :param medias: 媒体列表
        :return: 成功或失败
        """
        return self.qq.send_meidas_msg(title=message.title, medias=medias,
                                             userid=message.userid)

    def post_torrents_message(self, message: Notification, torrents: List[Context]) -> Optional[bool]:
        """
        发送种子信息选择列表
        :param message: 消息体
        :param torrents: 种子列表
        :return: 成功或失败
        """
        return self.qq.send_torrents_msg(title=message.title, torrents=torrents, userid=message.userid)

    def register_commands(self, commands: Dict[str, dict]):
        """
        注册命令，实现这个函数接收系统可用的命令菜单
        :param commands: 命令字典
        """
        # self.qq.register_commands(commands)
        pass
