from PIL import Image
from PIL import ImageGrab
import numpy as np
import time
import requests
import schedule
import smtplib
import loguru
import hashlib
import os
import configparser
import chardet
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

requests.packages.urllib3.disable_warnings()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# .venv\Scripts\Activate.ps1
# pip install -r requirements.txt
# pyinstaller -F "pad-ocr-watchdog copy.py"


def new_thread(func):
    import threading
    from functools import wraps

    @wraps(func)
    def inner(*args, **kwargs):
        # print(f'函数的名字：{func.__name__}')
        # print(f'函数的位置参数：{args}')
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return inner


@new_thread
def play_music(file_path):
    import os

    cmd_line = "ffplay.exe -nodisp -autoexit " + file_path
    print(cmd_line)
    os.system(cmd_line)


def get_curtime(time_format="%Y-%m-%d %H:%M:%S"):
    curTime = time.localtime()
    curTime = time.strftime(time_format, curTime)
    return curTime


@new_thread
def send_email(
    Subject,
    content,
    tomail,
    smtp_host,
    smtp_port,
    mail_user,
    mail_pass,
    sender_email,
    smtptype,
):  # 发送邮件-准备邮件内容
    # 设置登录及服务器信息
    # 设置email信息
    # 添加一个MIMEmultipart类，处理正文及附件
    message = MIMEMultipart()
    message["From"] = sender_email
    maillist = ""
    temp = []
    if type(tomail) == str:
        temp.append(tomail)
    else:
        temp = tomail
    for mail in temp:
        if maillist == "":
            maillist = maillist + mail
        else:
            maillist = maillist + "," + mail
    print(maillist)
    message["To"] = maillist
    message["Cc"] = ""
    message["Bcc"] = ""

    # 设置html格式参数
    part1 = MIMEText(content, "html", "utf-8")
    # 添加一个附件
    message["Subject"] = Subject
    message.attach(part1)

    # message.attach(picture)
    return send_mail(message, smtp_host, smtp_port, mail_user, mail_pass, smtptype)


@new_thread
def send_mail(
    message, smtp_host, smtp_port, user=None, passwd=None, security=None
):  # 发送邮件
    """
    Sends a message to a smtp server
    """
    try:
        if security == "SSL":
            s = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            s = smtplib.SMTP(smtp_host, smtp_port)
        # s.set_debuglevel(10)
        s.ehlo()

        if security == "TLS":
            s.starttls()
            s.ehlo()

        if user:
            s.login(user, passwd)

        to_addr_list = []

        if message["To"]:
            to_addr_list.append(message["To"])
        if message["Cc"]:
            to_addr_list.append(message["Cc"])
        if message["Bcc"]:
            to_addr_list.append(message["Bcc"])

        to_addr_list = ",".join(to_addr_list).split(",")

        s.sendmail(message["From"], to_addr_list, message.as_string())
        s.close()
        # save_log("INFO", "邮件发送成功")
        loguru.logger.info("邮件发送成功")
        return True
    except Exception as e:
        # save_log("ERROR", "邮件发送失败"+str(e))
        loguru.logger.error("邮件发送失败" + str(e))
        return False


def ocr_img_text(
    path="", saveimg=False, printResult=False, conf_detail=1, engine="paddle"
):
    """
    图像文字识别
    :param path:图片路径
    :param saveimg:是否把结果保存成图片
    :param printResult:是否打印出识别结果
    :return:result,img_name
    """
    image = path

    # 图片路径为空就默认获取屏幕截图
    if image == "":
        image = screenshot()
        image = np.array(image)
    else:
        # 不为空就打开
        image = Image.open(image).convert("RGB")

    # need to run only once to download and load model into memory
    if engine == "paddle":
        ocr = paddleocr.PaddleOCR(
            use_angle_cls=True, lang="ch", show_log=False)

        result = ocr.ocr(image, cls=True)
        if printResult is True:
            for line in result:
                for word in line:
                    print(word)
    elif engine == "easyocr":
        # need to run only once to download and load model into memory
        # need to run only once to load model into memory
        # ocr = easyocr.Reader(['ch_sim', 'en'], gpu=False)  # need to run only once to load model into memory
        ocr = easyocr.Reader(["ch_sim", "en"])
        result = ocr.readtext(image, detail=conf_detail)
        if printResult is True:
            for line in result:
                if conf_detail == 1:
                    for word in line:
                        print(word)
                else:
                    print(line)
    else:
        result = pytesseract.image_to_string(image, lang="chi_sim+eng")

    # 识别出来的文字保存为图片
    img_name = "ImgTextOCR-img-" + get_curtime("%Y%m%d%H%M%S") + ".jpg"
    if saveimg is True:
        if engine == "paddle":
            boxes = [
                detection[0] for line in result for detection in line
            ]  # Nested loop added
            txts = [
                detection[1][0] for line in result for detection in line
            ]  # Nested loop added
            scores = [
                detection[1][1] for line in result for detection in line
            ]  # Nested loop added
            im_show = paddleocr.draw_ocr(image, boxes, txts, scores)
        elif engine == "easyocr":
            im_show = image
            for detection in result:
                # print(detection)
                top_left = tuple([int(val) for val in detection[0][0]])
                bottom_right = tuple([int(val) for val in detection[0][2]])
                im_show = cv2.rectangle(
                    im_show, top_left, bottom_right, (0, 255, 0), 2)
                im_show = cv2.putText(
                    im_show,
                    detection[1],
                    (top_left[0], top_left[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (36, 255, 12),
                    2,
                )
        else:
            im_show = image
        im_show = Image.fromarray(im_show)
        im_show.save(img_name)

    return result, img_name


def screenshot():
    """
    截图
    :return:Image
    """
    im = ImageGrab.grab()
    return im


def check_ip_change():
    """
    检查IP是否变化
    :return:bool
    """
    try:
        ip = requests.get("http://httpbin.org/ip").json()
        ip = ip["origin"]
        with open("ip.txt", "r") as f:
            old_ip = f.read()
        if ip != old_ip:
            with open("ip.txt", "w") as f:
                f.write(ip)
            return True
        else:
            return False
    except Exception as e:
        loguru.logger.error("检查IP变化失败" + str(e))
        return False


def send_email_ipchg():
    """
    发送IP变化邮件
    :return:
    """
    if check_ip_change():
        content = "IP地址变化了，请查看详情：<a href='http://httpbin.org/ip'>http://httpbin.org/ip</a>"
        Subject = "IP地址变化"


def clean_msg_store():
    global alert_msg
    alert_msg = []


@new_thread
def check_screen():
    global alert_msg, alert_words, alert_mp3_file, wxmsg_touser
    # print(alert_msg)
    alert_found = False
    print("WatchDog Checking At ", get_curtime())
    ocr_resp, img = ocr_img_text(
        saveimg=False, printResult=False, conf_detail=easyocr_detail, engine=ocr_method
    )
    if ocr_method == "tesseract":
        for line in ocr_resp.split("\n"):
            # print(line)
            for alert_word in alert_words:
                if alert_word in line:
                    alert_found = True
                    break
            if alert_found == True:
                word = line
                break
    else:
        for line in ocr_resp:
            if ocr_method == "paddle":
                for word in line:
                    word = word[1][0]
                    for alert_word in alert_words:
                        if alert_word in word:
                            alert_found = True
                            break
                    if alert_found == True:
                        break
            elif ocr_method == "easyocr":
                if easyocr_detail == 1:
                    word = line[1]
                else:
                    word = line
                for alert_word in alert_words:
                    if alert_word in word:
                        alert_found = True
                        break
            if alert_found == True:
                break
    if alert_found == True:
        word = word.strip()
        print("ALerT Word FOUND!!!ALLLERRRRRTTTTT", word)
        if word in alert_msg:
            print("Same Msg sent already, skip")
            pass
        else:
            # requests.get(url="http://pi.tzxy.cn/pi/app/wxadminsiteerr.asp?content="+word, verify=False)
            if conf_wxmsg:
                wxmsg(wxmsg_touser, word)
            if conf_email:
                contents = word
                send_email(
                    "ALERTonScreen",
                    contents,
                    email_receivers,
                    smtp_host,
                    smtp_port,
                    mail_user,
                    mail_pass,
                    sender_email,
                    smtptype,
                )
            alert_msg.append(word)
        play_music(alert_mp3_file)


@new_thread
def wxmsg(touser, content):
    global secret_seed, wxmsg_url, wxmsg_method
    wechatdata = "touser=" + touser
    wechatdata = wechatdata + "&cont=[" + content + "]hvv-lx-msg"

    secret = hashlib.md5(
        (secret_seed + get_curtime("%Y%m%d")).encode()).hexdigest()
    wechatdata = wechatdata + "&sec_msg_ret=" + secret
    try:
        if wxmsg_method == "GET":
            requests.get(url=wxmsg_url + "?" + wechatdata, verify=False)
        else:
            requests.post(url=wxmsg_url, data=wechatdata, verify=False)
        loguru.logger.info("微信消息发送成功")
    except Exception as e:
        loguru.logger.error("微信消息发送失败" + str(e))
    pass


def load_alert_words():
    global alert_words
    if os.path.exists("alert_words.txt") == False:
        with open("alert_words.txt", "w", encoding="utf-8") as f:
            print(
                "alert_words.txt not found, creating a new one,pls add alert words in it"
            )
            f.write("监视-关键词1\n监视-关键词2\n监视-关键词3\n")
    with open("alert_words.txt", "r", encoding="utf-8") as f:
        alert_words = f.readlines()
        alert_words = [x.strip() for x in alert_words]
    # print(alert_words)
    return alert_words


def prepare_conf_file(configpath):  # 准备配置文件
    if os.path.isfile(configpath) == True:
        pass
    else:
        config.add_section("config")
        config.set("config", "alert_mp3_file", r"alert.mp3")
        config.set("config", "send_wxmsg", r"1")
        config.set("config", "send_email", r"1")
        config.set("config", "ocr_method", r"paddle")
        config.set("config", "easyocr_detail", r"0")

        config.add_section("Email")
        config.set("Email", "smtp_host", r"smtp.qq.com")
        config.set("Email", "smtp_port", r"465")
        config.set("Email", "mail_user", r"")
        config.set("Email", "mail_pass", r"")
        config.set("Email", "sender_email", r"")
        config.set("Email", "toemail", r"")
        config.set("Email", "smtptype", r"SSL")

        config.add_section("micromsg")
        config.set(
            "micromsg", "wxmsg_url_get", r"http://pi.123.cn/pi/app/wxadminsiteerr.asp"
        )
        config.set(
            "micromsg", "wxmsg_url_post", r"https://pi.123.cn/PI/app/overlimwx.php"
        )
        config.set("micromsg", "wxmsg_method", r"POST")
        config.set("micromsg", "secret_seed", r"")
        config.set("micromsg", "wxmsg_touser", r"333|222|111")

        # write to file
        config.write(open(configpath, "w"))
        pass
    pass


def get_conf_from_file(config_path, config_section, conf_list):  # 读取配置文件
    conf_default = {
        "alert_mp3_file": "alert.mp3",
        "send_wxmsg": "1",
        "send_email": "1",
        "ocr_method": "paddle",
        "easyocr_detail": "0",
        "wxmsg_url_get": "http://pi.123.cn/pi/app/wxadminsiteerr.asp",
        "wxmsg_url_post": "https://pi.123.cn/PI/app/overlimwx.php",
        "wxmsg_method": "POST",
        "secret_seed": "111",
        "wxmsg_touser": "333|222|111",
        "smtp_host": "",
        "smtp_port": "465",
        "mail_user": "",
        "mail_pass": "",
        "sender_email": "",
        "smtptype": "SSL",
        "email_receivers": "",
    }
    with open(config_path, "rb") as f:
        result = chardet.detect(f.read())
        encoding = result["encoding"]
    config.read(config_path, encoding=encoding)
    conf_item_settings = []
    for conf_item in conf_list:
        try:
            conf_item_setting = config[config_section][conf_item]

            # 获取 列表类型的配置项
            if conf_item == "piserver" or conf_item == "email_receivers":
                item_nodes = conf_item_setting.split(",")
                conf_item_setting = []
                for item_node in item_nodes:
                    conf_item_setting.append(item_node)
                # print(conf_item_setting)
        except Exception as e:
            conf_item_setting = conf_default[conf_item]

        print(str(conf_item) + ":" + str(conf_item_setting))
        conf_item_settings.append(conf_item_setting)
        pass
    return tuple(conf_item_settings)


if __name__ == "__main__":
    alert_msg = []

    config = configparser.ConfigParser()  # 类实例化

    # 定义文件路径
    configpath = r".\setup.ini"
    prepare_conf_file(configpath)
    alert_mp3_file, conf_wxmsg, conf_email, ocr_method, easyocr_detail = (
        get_conf_from_file(
            configpath,
            "config",
            [
                "alert_mp3_file",
                "send_wxmsg",
                "send_email",
                "ocr_method",
                "easyocr_detail",
            ],
        )
    )
    if ocr_method == "paddle":
        import paddleocr
    elif ocr_method == "easyocr":
        import easyocr
        import cv2
    elif ocr_method == "tesseract":
        import pytesseract
    easyocr_detail = int(easyocr_detail)
    if conf_wxmsg == "1":
        conf_wxmsg = True
    else:
        conf_wxmsg = False
    if conf_email == "1":
        conf_email = True
    else:
        conf_email = False
    (
        email_receivers,
        smtp_host,
        smtp_port,
        mail_user,
        mail_pass,
        sender_email,
        smtptype,
    ) = get_conf_from_file(
        configpath,
        "Email",
        [
            "email_receivers",
            "smtp_host",
            "smtp_port",
            "mail_user",
            "mail_pass",
            "sender_email",
            "smtptype",
        ],
    )

    wxmsg_url_get, wxmsg_url_post, wxmsg_method, secret_seed, wxmsg_touser = (
        get_conf_from_file(
            configpath,
            "micromsg",
            [
                "wxmsg_url_get",
                "wxmsg_url_post",
                "wxmsg_method",
                "secret_seed",
                "wxmsg_touser",
            ],
        )
    )

    if wxmsg_method == "GET":
        wxmsg_url = wxmsg_url_get
    else:
        wxmsg_url = wxmsg_url_post

    print("WatchDog Started At ", get_curtime())
    sheduler = loguru.logger.add(
        "padocr-watchdog.log", rotation="1 day", retention="7 days", level="INFO"
    )
    alert_words = load_alert_words()
    check_screen()
    schedule.every(20).seconds.do(check_screen)  # 每10秒执行一次
    schedule.every(120).seconds.do(clean_msg_store)  # 每120秒执行一次
    schedule.every(120).seconds.do(load_alert_words)  # 每120秒执行一次
    while True:
        schedule.run_pending()
        time.sleep(3)
