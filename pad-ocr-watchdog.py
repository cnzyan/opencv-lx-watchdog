from Crypto.Cipher import AES
from pyautogui import *
from PIL import Image
from PIL import ImageGrab
from PIL import ImageTk, ImageSequence
import numpy
import time
import requests
import schedule
import smtplib
import loguru
import hashlib
import os
import base64
import configparser
import chardet
import tkinter as tk
import pygetwindow
import pyautogui
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

requests.packages.urllib3.disable_warnings()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" #允许 Intel AI OpenMP 库的重复加载
# .venv\Scripts\Activate.ps1
# pip install -r requirements.txt
# pyinstaller -F pad-ocr-watchdog.py

# 在新线程中运行函数


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

# 调用播放音频报警函数


@new_thread
def play_music(file_path):
    play_method = "pygame"
    if play_method == "ffplay":
        import os
        cmd_line = "ffplay.exe -nodisp -autoexit " + file_path
        # print(cmd_line)
        os.system(cmd_line)
    elif play_method == "pygame":
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue
    elif play_method == "winsound":
        import winsound
        # winsound.PlaySound(file_path, winsound.SND_FILENAME)
        winsound.PlaySound("filename", winsound.SND_ASYNC | winsound.SND_ALIAS)
    else:
        import backup.playsound as playsound
        playsound.playsound(file_path, False)
        print('Alert Sound Playing...')

# 在文本框中插入文本


def textPad_insert(text):
    global textPad
    textPad.insert("end", text+"\n")
    textPad.see("end")

# 播放音频报警


def run_play_music():
    global alert_mp3_file, alert_permit, daemon_permit
    if os.path.exists(alert_mp3_file) == False:
        alert_mp3_file = "alert.mp3"
    if alert_permit == True:
        play_music(alert_mp3_file)
    else:
        if daemon_permit == True:
            print("Alert Permitted is False, Skip Play Music")
        else:
            pass

# 切换音频报警状态/是否允许播放音频报警


def set_alert_permit(tag="none"):
    global alert_permit, textPad
    if tag == "on":
        alert_permit = True
    elif tag == "off":
        alert_permit = False
    else:
        if alert_permit == True:
            alert_permit = False
        else:
            alert_permit = True
    if alert_permit == True:
        print("Alert MP3 Play Permitted")
        textPad_insert("Alert MP3 Play Permitted")
    else:
        print("Alert MP3 Play Not Permitted")
        textPad_insert("Alert MP3 Play Not Permitted")

# 切换监视状态


def set_daemon_permit(tag="none"):
    global daemon_permit, textPad
    if tag == "on":
        daemon_permit = True
    elif tag == "off":
        daemon_permit = False
    else:
        if daemon_permit == True:
            daemon_permit = False
        else:
            daemon_permit = True
    if daemon_permit == True:
        print("WatchDog Started At ", get_curtime())
        textPad_insert("WatchDog Started At "+get_curtime())
    else:
        print("WatchDog Stopped At ", get_curtime())
        textPad_insert("WatchDog Stopped At "+get_curtime())


'''
def get_curtime(time_format="%Y-%m-%d %H:%M:%S"):
    curTime = time.localtime()
    curTime = time.strftime(time_format, curTime)
    return curTime
'''

# 获取时间戳，offset为偏移天数


def get_curtime(time_format="%Y-%m-%d %H:%M:%S", offset=0):
    curTime = time.time() + offset * 24 * 60 * 60
    curTime = time.localtime(curTime)
    curTime = time.strftime(time_format, curTime)
    return curTime

# 组合邮件内容


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
    if email_method == "smtp":
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
        # print(maillist)
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
    else:
        return send_mail_http(Subject, content, tomail)

# AES ECB加密


def AES_ECB_ENCRYPT(plain_text, secretKey):
    if type(plain_text) != type(""):
        plain_text = str(plain_text)
    key = secretKey.encode()
    cipher = AES.new(key, AES.MODE_ECB)
    # 确保明文长度是16的倍数
    pad = 16 - len(plain_text.encode('utf-8')) % 16
    plain_text += chr(pad) * pad
    encrypted_text = cipher.encrypt(plain_text.encode())
    return base64.b64encode(encrypted_text).decode()

# AES ECB解密


def AES_ECB_DECRYPT(textBase64, secretKey):
    key = secretKey.encode()
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_text = cipher.decrypt(base64.b64decode(textBase64))
    return decrypted_text.decode()

# 发送邮件-通过HTTP中继服务器


@new_thread
def send_mail_http(Subject, content, tomail):
    secret_seed = server_secret  # 服务器密钥
    secret_today = hashlib.md5(
        (secret_seed + get_curtime("%Y%m%d")).encode()).hexdigest()
    content_b64 = base64.b64encode(content.encode()).decode()
    origin = {
        "subject": Subject,
        "content": content_b64,
        "tomail": tomail
    }
    origin = str(origin)
    http_transport_data = AES_ECB_ENCRYPT(origin, secret_today)
    postdata = {
        "secret": secret_today,
        "content": http_transport_data
    }
    try:
        resp = requests.post(url=server_url, data=postdata,
                             verify=False).content.decode('utf-8')
        loguru.logger.info("邮件发送成功"+resp)
        return True
    except Exception as e:
        loguru.logger.error("邮件发送失败"+str(e))
        return False

# 发送邮件


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


def ocr_get_txt_pos(path="", text=""):
    """
    获取文字与位置对应map
    :param path:图片路径，图片路径为空则默认获取当前屏幕截图
    :param text: 筛选需要查找的内容，匹配所有位置
    :return:list
    """

    result, img_path = ocr_img_text(path, saveimg=True)

    # print("图片识别结果保存：", img_path)
    textPad_insert("图片识别结果保存："+img_path)
    poslist = [detection[0][0] for line in result for detection in line]
    txtlist = [detection[1][0] for line in result for detection in line]

    # 用list存文字与位置信息
    find_txt_pos = []

    items = 0

    if text == "":
        find_txt_pos = result
    else:
        for i in range(len(poslist)):
            if txtlist[i] == text:
                find_txt_pos.append(poslist[i])
                items += 1

    print(find_txt_pos)
    return find_txt_pos

# 图像文字识别


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
        image = screenshot(w_title=window_title)
        image = numpy.array(image)
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
        filepath = 'screenshots'
        if not os.path.isdir(filepath):
            # 创建文件夹
            os.mkdir(filepath)
        im_show = Image.fromarray(im_show)
        im_show.save(filepath+"\\"+img_name)

    return result, img_name, image

# 截图


def screenshot(fullscreen="no", w_title="蓝信", saving=False):
    """
    截图
    :return:Image
    """
    def active_window(w_title):
        windows = pygetwindow.getWindowsWithTitle(w_title)
        if len(windows) == 0:
            print("Window Not Found.")
            return False
        else:
            window = pygetwindow.getWindowsWithTitle(w_title)[0]
            if window.isActive == False:
                try:
                    window.restore()  # 恢复窗口,如果窗口处于最小化状态，无法截图
                    window.activate()  # 激活窗口
                    return True
                except:
                    print("Window Active Failed, try again.")
                    return False
            else:
                return True
    filepath = 'screenshots'
    if not os.path.isdir(filepath):
        # 创建文件夹
        os.mkdir(filepath)

    if fullscreen == "no":
        # w_title="集团内部单位处置群"
        windows = pygetwindow.getWindowsWithTitle(w_title)
        print(len(windows))
        if len(windows) == 0:
            print("Window Not Found, will check words fullscreen.")
            textPad_insert("Window Not Found, will check words fullscreen.")
            fullscreen = "yes"
        else:
            try:
                window = pygetwindow.getWindowsWithTitle(w_title)[0]
                window_activate = True
                if window.isActive == False:
                    window_activate = False
                    for i in range(0, 3):
                        window_activate = active_window(w_title)
                        time.sleep(0.5)
                        if window_activate == True:
                            break
                if window_activate == False:
                    print("Window Active Failed.")
                    fullscreen = "yes"
                # 获取窗口的位置和大小
                x, y, width, height = window.left, window.top, window.width, window.height

                # 截取窗口的屏幕截图
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            except Exception as e:
                print("Window Screenshot Failed."+str(e))
                fullscreen = "yes"
            # 保存截图
            if saving == True:
                screenshot_filename = "window_screenshot" + \
                    get_curtime("%Y%m%d%H%M%S")+".png"
                screenshot.save(filepath+"\\"+screenshot_filename)
                print("Screenshot of the window saved as " +
                      filepath+"\\"+screenshot_filename)
            return screenshot
    else:
        pass
    if fullscreen != "no":
        im = ImageGrab.grab()
        # 保存截图
        if saving == True:
            screenshot_filename = "window_screenshot" + \
                get_curtime("%Y%m%d%H%M%S")+".png"
            im.save(filepath+"\\"+screenshot_filename)
            print("Screenshot fullscreen saved as " +
                  filepath+"\\"+screenshot_filename)
        return im

# 检查IP是否变化


@new_thread
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

# 发送IP变化邮件 TODO


def send_email_ipchg():
    """
    发送IP变化邮件
    :return:
    """
    if check_ip_change():
        content = "IP地址变化了，请查看详情：<a href='http://httpbin.org/ip'>http://httpbin.org/ip</a>"
        Subject = "IP地址变化"

# 清理消息存储


def clean_msg_store():
    global alert_msg
    alert_msg = []


# 检查屏幕内容
@new_thread
def check_screen():
    global alert_msg, alert_words, alert_mp3_file, wxmsg_touser, last_sent_seprate
    if send_snapshot == True:
        send_image = True
        send_image_file = False
        send_fulltext = False
    else:
        send_image = False
        send_image_file = False
        send_fulltext = False

    if daemon_permit == False:
        return
    # print(alert_msg)
    alert_found = False
    print("WatchDog Checking At ", get_curtime())
    textPad_insert("WatchDog Checking At "+get_curtime())
    ocr_resp, img_filename, image = ocr_img_text(
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
            if line == [] or line == "":
                continue
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
        textPad_insert("ALerT Word FOUND!!!ALLLERRRRRTTTTT")
        set_alert_permit("on")
        if word in alert_msg:
            print("Same Msg sent already, skip")
            textPad_insert("Same Msg sent already, skip")
            pass
        else:
            # requests.get(url="http://pi.tzxy.cn/pi/app/wxadminsiteerr.asp?content="+word, verify=False)
            alert_msg.append(word)
            contents = word
            if send_image == True:
                import io
                output = io.BytesIO()
                image = Image.fromarray(image)
                image.save(output, format='JPEG')
                image_data = output.getvalue()

                img_base64 = base64.b64encode(image_data).decode()
                img_md5 = hashlib.md5(img_base64.encode('utf-8')).hexdigest()
                if img_md5 not in img_md5_list:
                    img_md5_list.append(img_md5)
                else:
                    print("Same Image Sent Already, Skip")
                    textPad_insert("Same Image Sent Already, Skip")
                    return
                img_base64 = "data:image/jpeg;base64," + img_base64
                contents = contents + "<br><img src='"+img_base64+"'>"
            if send_image_file == True:
                img_filename = "ImgTextOCR-img-" + \
                    get_curtime("%Y%m%d%H%M%S") + ".jpg"
                image.save(img_filename)
                if conf_serial:
                    serial_send("file", img_filename)

            if send_fulltext == True:
                contents = contents + "<br>"+str(ocr_resp)

            if conf_wxmsg:
                wxmsg(wxmsg_touser, contents)
            if conf_email:
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
            if conf_serial:
                serial_send("email", contents)

            if send_seprate == True:
                if last_sent_seprate != contents:
                    send_sep(ocr_method, ocr_resp, contents)
                    last_sent_seprate = contents

# 根据联系人组分组发送消息


@new_thread
def send_sep(ocr, data, contents=""):
    global contacts
    group_sent = []
    to_email = ""
    to_wx = ""
    if ocr == "tesseract":
        for alert_word in alert_words:
            if alert_word in data:
                group = alert_groups[alert_word]
                if group in group_sent:
                    continue
                group_sent.append(group)
                if to_email == "":
                    to_email = contacts[group][0].strip()
                else:
                    to_email = to_email+","+contacts[group][0].strip()
                if to_wx == "":
                    to_wx = contacts[group][1].strip().replace(",", "|")
                else:
                    to_wx = to_wx+"|" + \
                        contacts[group][1].strip().replace(",", "|")

    elif ocr == "paddle" or ocr == "easyocr":
        for line in data:
            if line == [] or line == "":
                continue
            if ocr_method == "paddle":
                for word in line:
                    word = word[1][0]
                    for alert_word in alert_words:
                        if alert_word in word:
                            group = alert_groups[alert_word]
                            if group in group_sent:
                                continue
                            group_sent.append(group)
                            if to_email == "":
                                to_email = contacts[group][0].strip()
                            else:
                                to_email = to_email+"," + \
                                    contacts[group][0].strip()
                            if to_wx == "":
                                to_wx = contacts[group][1].strip().replace(
                                    ",", "|")
                            else:
                                to_wx = to_wx+"|" + \
                                    contacts[group][1].strip().replace(
                                        ",", "|")
            elif ocr_method == "easyocr":
                if easyocr_detail == 1:
                    word = line[1]
                else:
                    word = line
                for alert_word in alert_words:
                    if alert_word in word:
                        group = alert_groups[alert_word]
                        if group in group_sent:
                            continue
                        group_sent.append(group)
                        if to_email == "":
                            to_email = contacts[group][0].strip()
                        else:
                            to_email = to_email+","+contacts[group][0].strip()
                        if to_wx == "":
                            to_wx = contacts[group][1].strip().replace(
                                ",", "|")
                        else:
                            to_wx = to_wx+"|" + \
                                contacts[group][1].strip().replace(",", "|")
        pass
    else:
        pass

    if conf_email:
        print(to_email)
        if "@" in to_email:
            send_email("ALERTonScreen_s", contents, to_email, smtp_host,
                       smtp_port, mail_user, mail_pass, sender_email, smtptype)
        else:
            print("No Email Address Found")
    elif conf_wxmsg:
        if to_wx != "":
            wxmsg(to_wx, contents)
        else:
            print("No Wxmsg Address")
    elif conf_serial:

        content_b64 = base64.b64encode(contents.encode()).decode()
        trans_data = {
            "content": content_b64,
            "tomail": to_email
        }
        trans_data = str(trans_data)
        trans_data_b64 = base64.b64encode(trans_data.encode()).decode()
        serial_send("emb64", trans_data_b64)
    else:
        pass

# 发送微信消息


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

# 读取配置文件-关键词


def load_alert_words():
    global alert_words, alert_groups
    alert_words = []
    alert_groups = {}
    if os.path.exists("alert_words.txt") == False:
        with open("alert_words.txt", "w", encoding="utf-8") as f:
            print(
                "alert_words.txt not found, creating a new one,pls add alert words in it"
            )
            textPad_insert(
                "alert_words.txt not found, creating a new one,pls add alert words in it")
            f.write(
                "# 监视-关键词1|联系人组名1\n监视-关键词2|联系人组名1\n监视-关键词3|联系人组名2\n监视-关键词4|联系人组名2\n")
    with open("alert_words.txt", "r", encoding="utf-8") as f:
        words = f.readlines()
        # alert_words = [x.strip().split("|")[0] for x in words]
        for x in words:
            if x.strip() == "":
                continue
            if x.strip().startswith("#"):
                continue
            alert_words.append(x.strip().split("|")[0])
            alert_groups[x.strip().split("|")[0]] = x.strip().split("|")[1]
    print("监视关键字：", alert_words)
    return alert_words, alert_groups

# 读取配置文件-联系人


def load_contacts():
    data = {}
    if os.path.exists("contacts.txt") == False:
        with open("contacts.txt", "w", encoding="utf-8") as f:
            print(
                "contacts.txt not found, creating a new one,pls add email and wxmsg contacts in it"
            )
            f.write("# 联系人组名1|邮箱1,邮箱2|微信1,微信2\n# 联系人组名2|邮箱1,邮箱2|微信1,微信2\n")
    with open("contacts.txt", "r", encoding="utf-8") as f:
        contacts = f.readlines()
        for item in contacts:
            if item.strip() == "":
                continue
            if item.strip().startswith("#"):
                continue
            corpname = item.strip().split("|")[0]
            email_receivers = item.strip().split("|")[1]
            wxmsg_touser = item.strip().split("|")[2]
            data[corpname] = [email_receivers, wxmsg_touser]
        print("联系人分组：", data)
        return data


def check_uart_port():
    port_list = list(serial.tools.list_ports.comports())
    # print(port_list)
    if len(port_list) == 0:
        print('can not find uart port')
        return False
    else:
        for i in range(0, len(port_list)):
            print(port_list[i])
    return True


def open_uart(port, bps, timeout):  # 打开串口
    try:
        # 打开串口，并返回串口对象
        uart = serial.Serial(port, bps, timeout=timeout)
        return uart
    except Exception as result:
        try:
            time.sleep(1)
            uart = serial.Serial(port, bps, timeout=timeout)
            return uart
        except Exception as result:
            print("Can not open Serial Port,Pls Check Occupation.")
            print(result)
            loguru.logger.error(result)
            return False


def uart_send_data(uart, txbuf):  # 发送数据
    try:
        len = uart.write(txbuf.encode('utf-8'))  # 写数据
        return len
    except:
        time.sleep(1)
        try:
            len = uart.write(txbuf.encode('utf-8'))  # 写数据
            return len
        except Exception as result:
            print("Send Data Error.")
            print(result)
            loguru.logger.error(result)
            return 0

# 关闭串口


def close_uart(uart):  # 关闭串口
    uart.close()

# 按长度分割字符串


def split_string(s, n):
    return [s[i:i+n] for i in range(0, len(s), n)]

# 串口发送数据(写入队列)


def serial_send(type, temp_data):
    global serial_queue
    if type == "email":
        temp_data = base64.b64encode(temp_data.encode()).decode()
    serial_queue.put([type, temp_data])

# 串口守护线程(从队列中读取数据发送)


@new_thread
def serial_daemon():
    from queue import Queue
    global serial_queue
    serial_queue = Queue()
    while True:
        if serial_queue.empty() == False:
            serial_data = serial_queue.get()
            serial_send_device(serial_data[0], serial_data[1])
        time.sleep(0.1)

# 串口发送数据


def serial_send_device(type, temp_data):

    # 扫描端口
    # result = check_uart_port()
    result = True
    if (result == False):
        return

    # 打开串口
    port = serialdev.split(',')[0]
    bps = int(serialdev.split(',')[1])
    timeout = int(serialdev.split(',')[2])

    serial_opened = False
    while serial_opened == False:
        try:
            uart1 = open_uart(port, bps, timeout)
            serial_opened = True
        except Exception as e:
            loguru.logger.error("Serial Open Error."+str(e))
            time.sleep(1)

        # 定义YMODEM发送函数
    def send_ymodem(filename):
        def getc(size, timeout=1):
            return uart1.read(size)

        def putc(data, timeout=1):
            return uart1.write(data)
        modem = xmodem.XMODEM(getc, putc)
        with open(filename, "rb") as f:
            status = modem.send(f)
        return status

    for num in range(0, 3):
        # c for command, b for begin : send begin
        txbuf = '{"c":"b","iv":{}}'
        len = uart_send_data(uart1, txbuf)
        print("Serial send len: ", len, ";data:", txbuf)
        time.sleep(0.001)
    if type == "email" or type == "emb64":
        # 串口缓冲区最大长度为4096，所以分片发送，每片3300字节(base64编码后)
        temp_data_pieces = split_string(temp_data, 3300)
        max_len = 0
        for element in temp_data_pieces:
            max_len += 1

        # print(max_len)

        timestamp = hashlib.md5(
            (str(int(time.time()))+temp_data).encode()).hexdigest()
        index = 0
        for index in range(0, max_len):
            data_piece = str(temp_data_pieces[index])
            data_piece_hash = hashlib.md5(data_piece.encode()).hexdigest()
            txbuf = '{"c":"'+type+'","index":"'+str(
                index+1)+'","timestamp":"'+timestamp+'","num":"'+str(max_len)+'","data":"'+data_piece+'","hash":"'+data_piece_hash+'"}'
            try:
                len = uart_send_data(uart1, txbuf)
                print("Serial send len: ", len, ";data_hash:", data_piece_hash)
                loguru.logger.info("Serial send len: " +
                                   str(len)+";data_hash:"+data_piece_hash)
                time.sleep(0.001)
                pass
            except Exception as e:
                loguru.logger.error("Serial send error."+str(e))

    if type == "rt":
        for item in temp_data:
            txbuf = '{"c":"rtd","iv":{"t":"' + \
                str(item[0])+'","v":"'+str(item[1])+'\"}}'
            try:
                len = uart_send_data(uart1, txbuf)
                print("Serial send len: ", len, ";data:", txbuf)
                time.sleep(0.001)
                pass
            except Exception as e:
                # save_log('error', "Serial send error."+str(e))
                loguru.logger.error("Serial send error."+str(e))
    if type == "file":
        fn = (temp_data.replace("\\", "/").split("/"))[-1]
        txbuf = '{"c":"f","fn":"'+fn+'","fs":""}'
        try:
            len = uart_send_data(uart1, txbuf)
            print("Serial send len: ", len, ";data:", txbuf)
            time.sleep(0.001)

            # 发送文件
            status = send_ymodem(temp_data)
            if status:
                print(f"文件发送成功：{temp_data}")
            else:
                print(f"文件发送失败：{temp_data}")

            pass
        except Exception as e:
            # save_log('error', "Serial send error."+str(e))
            loguru.logger.error("Serial send error."+str(e))

        pass
    for num in range(0, 3):
        # c for command, e for end : send end
        txbuf = '{"c":"e","iv":{}}'
        len = uart_send_data(uart1, txbuf)
        print("Serial send len: ", len, ";data:", txbuf)
        time.sleep(0.001)
    pass

# 准备配置文件


def prepare_conf_file(configpath):  # 准备配置文件
    if os.path.isfile(configpath) == True:
        pass
    else:
        config.add_section("config")
        config.set("config", "alert_mp3_file", r"alert.mp3")
        config.set("config", "send_wxmsg", r"1")
        config.set("config", "send_email", r"1")
        config.set("config", "send_serial", r"1")
        config.set("config", "ocr_method", r"paddle")
        config.set("config", "easyocr_detail", r"0")
        config.set("config", "window_title", r"xxxx")
        config.set("config", "send_snapshot", r"1")
        config.set("config", "alert_words", r"alert_words.txt")
        config.set("config", "contacts", r"contacts.txt")
        config.set("config", "send_seprate", r"1")

        config.add_section("Email")
        config.set("Email", "email_method", r"")
        config.set("Email", "server_secret", r"")
        config.set("Email", "server_url", r"")
        config.set("Email", "smtp_host", r"smtp.qq.com")
        config.set("Email", "smtp_port", r"465")
        config.set("Email", "mail_user", r"xxx@qq.com")
        config.set("Email", "mail_pass", r"xxx")
        config.set("Email", "sender_email", r"xxx@qq.com")
        config.set("Email", "email_receivers", r"xxx@qq.com")
        config.set("Email", "smtptype", r"SSL")

        config.add_section("micromsg")
        config.set(
            "micromsg", "wxmsg_url_get", r"http://pi.111.cn/pi/app/wxadminsiteerr.asp"
        )
        config.set(
            "micromsg", "wxmsg_url_post", r"https://pi.111.cn/PI/app/overlimwx.php"
        )
        config.set("micromsg", "wxmsg_method", r"POST")
        config.set("micromsg", "secret_seed", r"111")
        config.set("micromsg", "wxmsg_touser", r"111|222|333")

        config.add_section("serial")
        config.set("serial", "serialdev_in", r"COM2,9600,1")
        config.set("serial", "serialdev_out", r"COM1,9600,1")
        # write to file
        config.write(open(configpath, "w"))
        pass
    pass

# 读取配置文件-配置项


def get_conf_from_file(config_path, config_section, conf_list):  # 读取配置文件
    conf_default = {
        "alert_mp3_file": "alert.mp3",
        "send_wxmsg": "1",
        "send_email": "1",
        "send_serial": "0",
        "ocr_method": "paddle",
        "easyocr_detail": "0",
        "window_title": "xxxx",
        "send_snapshot": "1",
        "alert_words": "alert_words.txt",
        "contacts": "contacts.txt",
        "send_seprate": "1",
        "wxmsg_url_get": "http://pi.111.cn/pi/app/wxadminsiteerr.asp",
        "wxmsg_url_post": "https://pi.111.cn/PI/app/overlimwx.php",
        "wxmsg_method": "POST",
        "secret_seed": "111",
        "wxmsg_touser": "111|222|333",
        "email_method": "",
        "server_secret": "",
        "server_url": "",
        "smtp_host": "smtp.qq.com",
        "smtp_port": "465",
        "mail_user": "111@qq.com",
        "mail_pass": "111",
        "sender_email": "111@qq.com",
        "smtptype": "SSL",
        "email_receivers": "111@qq.com",
        "serialdev_in": "COM2,9600,1",
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
    if len(conf_list) > 1:
        return tuple(conf_item_settings)
    else:
        return conf_item_settings[0]

# 定时器


@new_thread
def daemon_worker():
    global app_run
    while app_run == True:
        schedule.run_pending()
        time.sleep(1)

# 退出程序


def quit_program():
    import sys
    global app_run
    app_run = False
    root.destroy()  # 结束Tk事件循环
    try:
        sys.exit(0)
    except:
        pass
    try:
        os._exit(0)
    except:
        pass

# 闪屏


@new_thread
def splash_play():
    global splash

    def play_animation():
        # 打开GIF图像文件
        image = Image.open("reload.gif")

        # 获取图像的所有帧
        frames = []
        for frame in ImageSequence.Iterator(image):
            frames.append(ImageTk.PhotoImage(frame))

        # 创建一个标签显示GIF图像
        label = tk.Label(splash, image=frames[0])
        label.pack()

        # 播放动画
        def update_frame(frame_index):
            # 更新标签的图像
            label.configure(image=frames[frame_index])

            # 获取下一帧的索引
            next_frame_index = (frame_index + 1) % len(frames)

            # 在固定的时间间隔后调用更新函数
            splash.after(100, update_frame, next_frame_index)

        # 开始动画
        update_frame(0)

    def splash_stop():
        # splash.quit()
        try:
            splash.quit()
        except:
            pass

    # 创建一个Tkinter窗口
    splash = tk.Tk()
    screenWidth = splash.winfo_screenwidth()  # 获取显示区域的宽度
    screenHeight = splash.winfo_screenheight()  # 获取显示区域的高度
    width = 300  # 设定窗口宽度
    height = 200  # 设定窗口高度
    left = (screenWidth - width) / 2
    top = (screenHeight - height) / 2

    # 宽度x高度+x偏移+y偏移
    # 在设定宽度和高度的基础上指定窗口相对于屏幕左上角的偏移位置
    splash.geometry("%dx%d+%d+%d" % (width, height, left, top))
    splash.overrideredirect(1)  # 隐藏窗口边框
    splash.wm_attributes("-transparentcolor", "gray99")  # 设置透明背景色
    splash.wm_attributes("-topmost", 1)  # 置顶窗口
    splash.attributes("-alpha", 0.8)  # 设置透明度
    splash.after(4000, splash_stop)
    splash_labl = tk.Label(splash, text=(
        prog_window_title+"\n"), font=("黑体", 12))
    splash_labl.pack()
    # 在窗口中播放动画
    play_animation()
    splash_labl = tk.Label(splash, text="正在加载中，请稍后...", font=("黑体", 12))
    splash_labl.pack()
    # 运行Tkinter的事件循环
    splash.mainloop()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='桌面关键字监视器')
    parser.add_argument('--UseSerial', type=str, default='no',
                        required=False, help='是否启用串口发送功能')
    # required = False 只能用于可选参数。 对于可选参数，应该使用 - -，如果没有 - -，python 会将其视为位置参数。
    args = parser.parse_args()

    prog_window_title = '桌面关键字监视器'
    splash = ''
    splash_play()
    last_sent_seprate = ''
    alert_msg = []
    img_md5_list = []
    log_path = './logs'
    if not os.path.isdir(log_path):
        # 创建文件夹
        os.mkdir(log_path)
    sheduler = loguru.logger.add(log_path+"\\padocr-watchdog.log", rotation="1 day", retention="7 days", level="INFO", encoding="utf-8"
                                 )
    config = configparser.ConfigParser()  # 类实例化

    # 定义文件路径
    configpath = r".\setup.ini"
    prepare_conf_file(configpath)
    alert_mp3_file, conf_wxmsg, conf_email, ocr_method, easyocr_detail, window_title, conf_serial, send_snapshot, send_seprate = (
        get_conf_from_file(
            configpath,
            "config",
            [
                "alert_mp3_file",
                "send_wxmsg",
                "send_email",
                "ocr_method",
                "easyocr_detail",
                "window_title",
                "send_serial",
                "send_snapshot",
                "send_seprate",
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
    if conf_wxmsg == "1":  # 是否启用微信发送功能
        conf_wxmsg = True
    else:
        conf_wxmsg = False
    if conf_email == "1":  # 是否启用邮件发送功能
        conf_email = True
    else:
        conf_email = False
    if conf_serial == "1":  # 是否启用串口发送功能
        conf_serial = True
    else:
        conf_serial = False
    if args.UseSerial == "no":  # 是否启用串口发送功能
        conf_serial = False
    if send_snapshot == "1":  # 是否发送截图
        send_snapshot = True
    else:
        send_snapshot = False
    if send_seprate == "1":  # 是否分开发送
        send_seprate = True
    else:
        send_seprate = False
    if conf_email == True:
        (
            email_receivers,
            smtp_host,
            smtp_port,
            mail_user,
            mail_pass,
            sender_email,
            smtptype,
            email_method,
            server_secret,
            server_url,
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
                "email_method",
                "server_secret",
                "server_url",
            ],
        )
    if conf_wxmsg == True:
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
    if conf_serial == True:
        import serial
        import serial.tools.list_ports
        import xmodem
        serialdev = get_conf_from_file(
            configpath, 'serial', ['serialdev_in'])
    alert_words, alert_groups = load_alert_words()

    contacts = load_contacts()
    app_run = True
    alert_permit = False
    daemon_permit = False

    schedule.every(20).seconds.do(check_screen)  # 每10秒执行一次
    schedule.every(240).seconds.do(clean_msg_store)  # 每240秒执行一次
    schedule.every(120).seconds.do(load_alert_words)  # 每120秒执行一次
    schedule.every(120).seconds.do(load_contacts)  # 每120秒执行一次
    schedule.every(3).seconds.do(run_play_music)  # 每3秒执行一次

    serial_daemon()
    daemon_worker()

    try:
        splash.quit()
    except:
        pass
    root = tk.Tk()
    screenWidth = root.winfo_screenwidth()  # 获取显示区域的宽度
    screenHeight = root.winfo_screenheight()  # 获取显示区域的高度
    width = 500  # 设定窗口宽度
    height = 400  # 设定窗口高度
    left = (screenWidth - width-50)
    top = (screenHeight - height-150)

    # 宽度x高度+x偏移+y偏移
    # 在设定宽度和高度的基础上指定窗口相对于屏幕左上角的偏移位置
    root.geometry("%dx%d+%d+%d" % (width, height, left, top))
    # root.geometry('500x300')

    root.title(prog_window_title)
    root.protocol("WM_DELETE_WINDOW", quit_program)
    tk.Label(root, text="ProG By CrazYan 202408").pack()
    textPad = tk.Text(root, undo=True)
    textPad.pack(expand=tk.YES, fill=tk.BOTH)
    scroll = tk.Scrollbar(textPad)
    textPad.config(yscrollcommand=scroll.set)
    scroll.config(command=textPad.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    bt1 = tk.Button(root, text="启动监视!",
                    command=lambda: set_daemon_permit("on")).pack(side=tk.LEFT)
    bt2 = tk.Button(root, text="消音!", command=lambda: set_alert_permit(
        "off")).pack(side=tk.LEFT)
    bt3 = tk.Button(root, text="停止监视!", command=lambda: set_daemon_permit(
        "off")).pack(side=tk.LEFT)
    bt4 = tk.Button(root, text="退出程序!",
                    command=quit_program).pack(side=tk.LEFT)
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    root.mainloop()
