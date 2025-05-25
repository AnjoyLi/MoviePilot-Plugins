import re,json
import threading
from pathlib import Path
from threading import Event
from typing import Optional, List, Dict
from urllib.parse import urlencode

from app.core.config import settings
from app.core.context import MediaInfo, Context
from app.core.metainfo import MetaInfo
from app.log import logger
from app.utils.common import retry
from app.utils.http import RequestUtils
from app.utils.singleton import Singleton
from app.utils.string import StringUtils

# apihelper.proxy = settings.PROXY


class QQ(metaclass=Singleton):
    _ds_url = None
    _qq_number = None
    _event = Event()

    def __init__(self, num, url: str = None):
        """
        初始化参数
        """
        self._ds_url = url
        self._qq_number = num

    def get_state(self) -> bool:
        """
        获取状态
        """
        return self._ds_url is not None
    
    @retry(Exception, logger=logger)
    def __send_request(self, userid: str = None, image="", caption="",title= "") -> bool:
        headers = {'content-type': 'application/json'}
        message_url = self._ds_url
        req_json = {
            "user_id": self._qq_number,
        }
        
        data = {
            "user": userid,
            "title": title,
            "image": image,
            "text": caption
        }
        if ret := RequestUtils(headers=headers).post(message_url,
                                                     data=json.dumps({**req_json, **data}, ensure_ascii=False).encode('utf-8')):
            logger.info(f"发送消息结果：[{ret.status_code}]")

        return True if ret and ret.status_code == 200 else False
    
    def send_msg(self, title: str, text: Optional[str] = None, image: Optional[str] = None,
                 userid: Optional[str] = None, link: Optional[str] = None) -> Optional[bool]:
        """
        发送QQ消息
        :param title: 消息标题
        :param text: 消息内容
        :param image: 消息图片地址
        :param userid: 用户ID，如有则只发消息给该用户
        :param link: 跳转链接
        :userid: 发送消息的目标用户ID，为空则发给管理员
        """
        if not title and not text:
            logger.warn("标题和内容不能同时为空")
            return False

        try:
            if text:
                caption = f"*{title}*\n{text}"
            else:
                caption = f"*{title}*"

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            if userid:
                chat_id = userid
            else:
                chat_id = self._qq_number

            return self.__send_request(userid=chat_id, image=image, caption=caption,title=title)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False

    def send_meidas_msg(self, medias: List[MediaInfo], userid: Optional[str] = None,
                        title: Optional[str] = None, link: Optional[str] = None) -> Optional[bool]:
        """
        发送媒体列表消息
        """
        try:
            index, image, caption = 1, "", "*%s*" % title
            for media in medias:
                if not image:
                    image = media.get_message_image()
                if media.vote_average:
                    caption = "%s\n%s. [%s](%s)\n_%s，%s_" % (caption,
                                                             index,
                                                             media.title_year,
                                                             media.detail_link,
                                                             f"类型：{media.type.value}",
                                                             f"评分：{media.vote_average}")
                else:
                    caption = "%s\n%s. [%s](%s)\n_%s_" % (caption,
                                                          index,
                                                          media.title_year,
                                                          media.detail_link,
                                                          f"类型：{media.type.value}")
                index += 1

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            if userid:
                chat_id = userid
            else:
                chat_id = self._qq_number
            return self.__send_request(userid=chat_id, image=image, caption=caption,title=title)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False

    def send_torrents_msg(self, torrents: List[Context],
                          userid: Optional[str] = None, title: Optional[str] = None, link: Optional[str] = None) -> Optional[bool]:
        """
        发送列表消息
        """
        if not torrents:
            return False

        try:
            index, caption = 1, "*%s*" % title
            mediainfo = torrents[0].media_info
            for context in torrents:
                torrent = context.torrent_info
                site_name = torrent.site_name
                meta = MetaInfo(torrent.title, torrent.description)
                link = torrent.page_url
                title = f"{meta.season_episode} " \
                        f"{meta.resource_term} " \
                        f"{meta.video_term} " \
                        f"{meta.release_group}"
                title = re.sub(r"\s+", " ", title).strip()
                free = torrent.volume_factor
                seeder = f"{torrent.seeders}↑"
                caption = f"{caption}\n{index}.【{site_name}】[{title}]({link}) " \
                          f"{StringUtils.str_filesize(torrent.size)} {free} {seeder}"
                index += 1

            if link:
                caption = f"{caption}\n[查看详情]({link})"

            if userid:
                chat_id = userid
            else:
                chat_id = self._qq_number

            return self.__send_request(userid=chat_id, caption=caption,
                                       image=mediainfo.get_message_image(),title=title)

        except Exception as msg_e:
            logger.error(f"发送消息失败：{msg_e}")
            return False


    def stop(self):
        """
        停止qq消息接收服务
        """
        pass
