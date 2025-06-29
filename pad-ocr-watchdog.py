from Crypto.Cipher import AES
from pyautogui import *
import keyboard
from PIL import Image
from PIL import ImageGrab
from PIL import ImageTk, ImageSequence
import numpy
import time
import requests
import urllib
import schedule
import smtplib
import loguru
import hashlib
import os
import sys
import re
import base64
import configparser
import chardet
import tkinter as tk
import pygetwindow
import pyautogui
import pystray
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from functools import wraps
import queue
# to fix OSError: [WinError 127] 找不到指定的程序。 Error loading "C:\Users\cnzya\AppData\Roaming\Python\Python313\site-packages\torch\lib\shm.dll" or one of its dependencies.
# import torch
# fix end
requests.packages.urllib3.disable_warnings()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # 允许 Intel AI OpenMP 库的重复加载
# .venv\Scripts\Activate.ps1
# pip install -r requirements.txt
# pyinstaller -F pad-ocr-watchdog.py
VERSION_TEXT = "ProG By CrazYan 202408/upd202506"
CONTACT_FILE = "conf_contacts.txt"
ALERT_WORDS_FILE = "conf_alert_words.txt"
MSG_GROUP_FILE = "conf_msg_groups.txt"


def new_thread1(func):
    # 在新线程中运行函数
    @wraps(func)
    def inner(*args, **kwargs):
        # print(f'函数的名字：{func.__name__}')
        # print(f'函数的位置参数：{args}')
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return inner


def new_thread(fn):
    def wrapper(*args, **kwargs):
        t = threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon = True  # 设置为守护线程
        t.start()
        return t
    return wrapper


@new_thread
def play_music(file_path):
    # 调用播放音频报警函数
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


def textPad_insert(text):
    # 在文本框中插入文本
    global textPad
    textPad.insert("end", text+"\n")
    textPad.see("end")


def run_play_music():
    # 播放音频报警
    global alert_mp3_file, alert_permit, daemon_permit
    if os.path.exists(alert_mp3_file) == False:
        alert_mp3_file = "alert.mp3"
    if alert_permit == True:
        play_music(alert_mp3_file)
    else:
        if daemon_permit == True:
            print(".", end="")
            # print("Alert Permitted is False, Skip Play Music")
        else:
            pass


def set_alert_permit(tag="none"):
    # 切换音频报警状态/是否允许播放音频报警
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


def set_daemon_permit(tag="none"):
    # 切换监视状态
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


def get_curtime(time_format="%Y-%m-%d %H:%M:%S", offset=0):
    # 获取时间戳，offset为偏移天数
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
        loguru.logger.info("邮件发送成功 to "+tomail+':'+resp)
        return True
    except Exception as e:
        loguru.logger.error("邮件发送失败"+str(e))
        return False

# 发送邮件


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
    '''
    获取文字与位置对应map
    :param path:图片路径，图片路径为空则默认获取当前屏幕截图
    :param text: 筛选需要查找的内容，匹配所有位置
    :return:list
    '''

    result, img_path, image, fs = ocr_img_text(path, saveimg=True)

    print("图片识别结果保存：", img_path)

    # 把结果列表的两个值分别再存为两个list
    poslist = [detection[0][0]
               for line in result for detection in line]  # 取top一个点的位置
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
        image, fullscreen = screenshot(w_title=window_title)

    else:
        # 不为空就打开
        image = Image.open(image).convert("RGB")
    image = numpy.array(image)
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
    else:  # tesseract
        if conf_detail == 1:
            result = pytesseract.image_to_data(
                image, lang="chi_sim+eng", output_type=pytesseract.Output.DICT)

            if printResult is True:
                print(result)
        else:
            result = pytesseract.image_to_string(image, lang="chi_sim+eng")
    if debug:
        with open("ocr_result_"+engine+"_"+get_curtime("%H%M%S")+".txt", "w", encoding="utf-8") as f:
            f.write(str(result))

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

    return result, img_name, image, fullscreen

# 截图


def screenshot(fullscreen="no", w_title="蓝信", saving=False):
    global w_left, w_top
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
                            # w_left=window.left
                            # w_top=window.top
                            break
                if window_activate == False:
                    print("Window Active Failed.")
                    fullscreen = "yes"
                # 获取窗口的位置和大小
                x, y, width, height = window.left, window.top, window.width, window.height
                w_left, w_top = window.left, window.top
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
            return screenshot, fullscreen
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
        return im, fullscreen

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


def get_index_of_list(list, element):  # 获取列表中元素的索引
    try:
        index = [i for i, x in enumerate(list) if x == element]
    except ValueError:
        index = [-1]
    return index


def check_unread_msg(image, ocr_resp):

    # print(alert_msg)
    text_to_detect = "条新消息"
    detect_list = ["条新消息", "条新", "条新消", "条", "新消息", "新消", "新", "消息", "消", "息"]
    unread_detected = False
    if ocr_method == "tesseract":
        all_text = ''
        for word in ocr_resp['text']:
            all_text = all_text+word
        if ocr_detail == 1:

            for chr in text_to_detect:
                if chr not in all_text:
                    return False

            for word in ocr_resp['text']:
                if word in detect_list:
                    pos_index = get_index_of_list(ocr_resp['text'], word)
                    if word != text_to_detect:
                        for index in pos_index:
                            if index != -1:
                                if ocr_resp['text'][index+1] in detect_list:
                                    print("Unread Msg Found!!!")
                                    textPad_insert("Unread Msg Found!!!")
                                    unread_detected = True
                    else:
                        print("Unread Msg Found!!!")
                        textPad_insert("Unread Msg Found!!!")
                        unread_detected = True
                    break
            if unread_detected == True:
                pos = [ocr_resp['left'][index], ocr_resp['top'][index],
                       ocr_resp['width'][index], ocr_resp['height'][index]]
                return pos
            else:
                return False
    if ocr_method == "paddle" or ocr_method == "easyocr":
        for line in ocr_resp:
            if line == [] or line == "":
                continue
            if ocr_method == "paddle":
                for word in line:
                    if text_to_detect in word[1][0]:
                        unread_detected = True
                        pos = [word[0][0][0], word[0][0][1], word[0][2]
                               [0]-word[0][0][0], word[0][2][1]-word[0][0][1]]

            elif ocr_method == "easyocr":
                if ocr_detail == 1:
                    if text_to_detect in line[1]:
                        unread_detected = True
                        pos = [line[0][0][0], line[0][0][1], line[0][2]
                               [0]-line[0][0][0], line[0][2][1]-line[0][0][1]]
            else:
                return False

            if unread_detected == True:
                return pos
            else:
                continue
        pass


def click_unread_msg(pos):
    pos_x = pos[0]+pos[2]/2 + w_left
    pos_y = pos[1]+pos[3]/2 + w_top
    pyautogui.click(pos_x, pos_y, button='left')
    textPad_insert("Mouse Click At "+str(pos_x)+","+str(pos_y))
    # pyautogui.click(100, 150, button='left')
    # pyautogui.click('屏幕区块.png')
    pass


def split_string(s):
    # 匹配连续的字母/数字/下划线 (词) 或单个非空白字符 (字)
    # [a-zA-Z0-9_]+ : 连续英文字母、数字、下划线
    # | : 或
    # \S : 单个非空白字符 (包括中文、标点等)
    return re.findall(r'[a-zA-Z0-9_]+|\S', s)
# 检查屏幕内容


def click_in_window(x, y, key="left"):
    """点击当前活动窗口内的相对坐标位置 (包括标题栏)"""
    # 获取当前活动窗口
    active_win = pyautogui.getActiveWindow()

    if active_win is None:
        print("未检测到活动窗口！")
        return

    print(
        f"活动窗口信息: {active_win.title} | 大小: {active_win.size} | 位置: {active_win.topleft}")

    # 计算绝对坐标 (窗口位置 + 相对位置)
    absolute_x = active_win.left + x
    absolute_y = active_win.top + y

    print(f"转换后的屏幕坐标: ({absolute_x}, {absolute_y})", key)

    # 移动并点击
    pyautogui.click(absolute_x, absolute_y, button=key)  # 使用指定的鼠标按键进行点击
    print(f"已点击窗口位置 ({x}, {y})")
    
def compress_image(img, target_width=1280, target_height=800, quality=85):
    """
    压缩图像分辨率到目标尺寸以内（保持宽高比）
    
    参数:
        input_path (str): 输入图像路径
        output_path (str): 输出图像路径
        target_width (int): 目标最大宽度（默认1280）
        target_height (int): 目标最大高度（默认800）
        quality (int): 输出图像质量（仅对JPEG有效，1-100，默认85）
    """
    # 获取原始尺寸
    original_width, original_height = img.size
    if original_width <= target_width and original_height <= target_height:
        # 如果原始图像已经小于目标尺寸，则不需要缩放
        return img
    else:
        # 计算宽度和高度方向的缩放比例（取较小值以保持比例）
        width_ratio = target_width / original_width
        height_ratio = target_height / original_height
        scale_ratio = min(width_ratio, height_ratio)
        
        # 计算新尺寸（整数）
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        
        # 调整图像大小（使用高质量插值）
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 保存图像（根据格式调整参数，JPEG使用quality，PNG可忽略）
        return resized_img

def check_screen():
    # print(auto_reply_text)
    global alert_msg, alert_words, alert_mp3_file, wxmsg_touser, last_sent_seprate
    pos_to_mid = [0, 0]
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
    ocr_resp, img_filename, image, fullscreen = ocr_img_text(
        saveimg=False, printResult=False, conf_detail=ocr_detail, engine=ocr_method
    )
    if ocr_method == "tesseract":
        if ocr_detail == 1:
            ocr_temp = ''
            for i in range(len(ocr_resp["text"])):
                if ocr_resp["text"][i] != "":  # 去除空行
                    ocr_temp = ocr_temp+ocr_resp["text"][i]
            ocr_resp_tes = ocr_temp

        else:
            ocr_resp_tes = ocr_resp
        print(ocr_resp)
        for line in ocr_resp_tes.split("\n"):
            # print(line)
            for alert_word in alert_words:
                if alert_word in line:
                    detect_list = split_string(alert_word)
                    for word in detect_list:
                        pos_index = get_index_of_list(ocr_resp["text"], word)
                        if word != alert_word:
                            for index in pos_index:
                                if index != -1:
                                    if ocr_resp['text'][index+1] in detect_list:
                                        # 找到关键词坐标
                                        pos_detected = True
                                        pos_to_mid = [
                                            (ocr_resp["left"][index] +
                                             ocr_resp["left"][index+1])/2,
                                            (ocr_resp["top"][index] +
                                             ocr_resp["top"][index+1])/2
                                        ]
                        else:
                            pos_detected = True
                            index = pos_index[0]
                            pos_to_mid = [ocr_resp["left"][index] + ocr_resp["width"][index]/2,
                                          ocr_resp["top"][index] + ocr_resp["height"][index]/2]
                        if pos_detected:
                            # 检查是否有深色像素
                            pixel_dark_count = 0
                            roi = image[int(ocr_resp["top"][index]):int(ocr_resp["top"][index]+ocr_resp["height"][index]), int(
                                ocr_resp["left"][index]):int(ocr_resp["left"][index]+ocr_resp["width"][index])]
                            '''
                            for row in roi:
                                for pixel in row:
                                    # 现在pixel是一个一维数组（三个元素）
                                    if (pixel > 80).any():
                                        continue
                                    else:
                                        pixel_dark_count += 1

                                        if pixel_dark_count > 20:
                                            print("Alert Word Found: ", word, " at position: ",
                                                pos_to_mid, " with dark pixel: ", pixel)
                                            textPad_insert(
                                                "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                                            alert_found = True
                                            break
                            '''
                            # 判断每个像素是否所有通道都<=80
                            # 得到二维布尔数组，每个元素表示该像素是否所有通道<=80
                            dark_pixels = (roi <= 80).all(axis=2)
                            pixel_dark_count = dark_pixels.sum()
                            if pixel_dark_count > 20:
                                alert_found = True
                                print("Alert Word Found: ", word, " at position: ",
                                      pos_to_mid, " with dark pixel count: ", pixel_dark_count)
                                textPad_insert(
                                    "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                    '''
                    alert_found = True
                    break
                    '''
                if alert_found == True:
                    if word in alert_msg:
                        alert_found = False
                        print("Same Msg sent already, skip")
                        continue
                    else:
                        word = line
                        break
            if alert_found == True:
                break
    else:
        for line in ocr_resp:
            if line == [] or line == "" or line == None:
                continue
            if ocr_method == "paddle":
                for words in line:
                    word = words[1][0]
                    word = word.replace(" ", "")  # 去除空格
                    for alert_word in alert_words:
                        if alert_word in word:
                            # print("Alert Word Found: ", word)
                            pos_to_mid = [
                                (words[0][0][0]+words[0][1][0])/2, (words[0][0][1]+words[0][2][1])/2]
                            # 检查是否有深色像素
                            square = [words[0][0][0], words[0][0][1], words[0][2]
                                      [0]-words[0][0][0], words[0][2][1]-words[0][0][1]]
                            # print("Square: ", square)
                            # print(image)
                            pixel_dark_count = 0
                            roi = image[int(square[1]):int(
                                square[1]+square[3]), int(square[0]):int(square[0]+square[2])]
                            '''
                            for row in roi:
                                for pixel in row:
                                    # 现在pixel是一个一维数组（三个元素）
                                    if (pixel > 80).any():
                                        continue
                                    else:
                                        pixel_dark_count += 1

                                        if pixel_dark_count > 20:
                                            print("Alert Word Found: ", word, " at position: ",
                                                pos_to_mid, " with dark pixel: ", pixel)
                                            textPad_insert(
                                                "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                                            alert_found = True
                                            break
                            '''
                            # 判断每个像素是否所有通道都<=80
                            # 得到二维布尔数组，每个元素表示该像素是否所有通道<=80
                            dark_pixels = (roi <= 80).all(axis=2)
                            pixel_dark_count = dark_pixels.sum()
                            if pixel_dark_count > 20:
                                alert_found = True
                                print("Alert Word Found: ", word, " at position: ",
                                      pos_to_mid, " with dark pixel count: ", pixel_dark_count)
                                textPad_insert(
                                    "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                            '''
                            print("Alert Word Found: ", word, " at position: ", pos_to_mid)
                            alert_found = True
                            break
                            '''
                        if alert_found == True:
                            if word in alert_msg:
                                alert_found = False
                                print("Same Msg sent already, skip")
                                continue
                            else:
                                break
                    if alert_found == True:

                        break
            elif ocr_method == "easyocr":
                if ocr_detail == 1:
                    word = line[1]
                else:
                    word = line
                for alert_word in alert_words:
                    if alert_word in word:
                        alert_found = True
                        break
            if alert_found == True:
                if word in alert_msg:
                    continue
                break
    if ocr_detail == 1 or ocr_method == "paddle":
        # 检查未读消息
        pos = None
        pos = check_unread_msg(image, ocr_resp)
        if pos != False and pos != None:
            try:
                click_unread_msg(pos)
            except Exception as e:
                print("Mouse Click Error."+str(e))
                textPad_insert("Mouse Click Error."+str(e))
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
            if auto_reply == True and pos_to_mid != [0, 0]:
                print('position x y to click: ', pos_to_mid)
                # '''
                if fullscreen == "yes":
                    pyautogui.click(
                        pos_to_mid[0], pos_to_mid[1], button="right")  # 右键点击

                    time.sleep(1)
                    pyautogui.click(
                        # 左键点击
                        pos_to_mid[0]+50, pos_to_mid[1]+50, button="left")
                else:
                    # 点击当前活动窗口内的相对坐标位置
                    click_in_window(pos_to_mid[0], pos_to_mid[1], "right")
                    time.sleep(1)
                    # 点击当前活动窗口内的相对坐标位置
                    click_in_window(pos_to_mid[0]+50, pos_to_mid[1]+50, "left")
                # '''
                time.sleep(0.5)
                # '''
                try:
                    # 查找图片位置
                    location = pyautogui.locateOnScreen(
                        'toolbar.png', confidence=0.8)  # 查找按钮图标
                    if location:
                        print('图片位置:', location)
                        pyautogui.click(
                            # 点击输入框
                            location[0], location[1]+80, button="left")

                    else:
                        print('未找到图片')
                except pyautogui.ImageNotFoundException:
                    print('未找到图片')
                time.sleep(0.5)
                keyboard.write(auto_reply_text)  # 输入自动回复内容
                pyautogui.press('enter')
                time.sleep(0.5)
            if send_image == True:
                import io
                output = io.BytesIO()
                image = Image.fromarray(image)
                image=compress_image(image, target_width=1280, target_height=800, quality=85)
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
            if conf_serial and send_seprate == False:
                serial_send("email", contents)

            if send_seprate == True:  # 根据联系人组分组发送消息
                if last_sent_seprate != contents:
                    send_sep(ocr_method, ocr_resp, contents)
                    last_sent_seprate = contents

# 根据联系人组分组发送消息


@new_thread
def send_sep(ocr, data, contents=""):
    global contacts, msg_group
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
                    # add 20250627
                    # 细分关键字分组发送
                    # TODO
                    for key in msg_group:
                        for k in msg_group[key]:
                            if k in word:
                                group = key
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
                    # 关键词分别发送对应联系人
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
                if ocr_detail == 1:
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
    if conf_wxmsg:
        if to_wx != "":
            wxmsg(to_wx, contents)
        else:
            print("No Wxmsg Address")
    if conf_serial:

        content_b64 = base64.b64encode(contents.encode()).decode()
        trans_data = {
            "content": content_b64,
            "tomail": to_email
        }
        trans_data = str(trans_data)
        trans_data_b64 = base64.b64encode(trans_data.encode()).decode()
        serial_send("emb64", trans_data_b64)


# 发送微信消息


@new_thread
def wxmsg(touser, content):
    global secret_seed, wxmsg_url, wxmsg_method
    wechatdata = "touser=" + touser
    content = urllib.parse.quote(content, encoding='utf-8')
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
    # 读取配置文件-关键词
    global alert_words, alert_groups
    alert_words = []
    alert_groups = {}
    if os.path.exists(ALERT_WORDS_FILE) == False:
        with open(ALERT_WORDS_FILE, "w", encoding="utf-8") as f:
            print(
                f"{ALERT_WORDS_FILE} not found, creating a new one,pls add alert words in it"
            )
            textPad_insert(
                f"{ALERT_WORDS_FILE} not found, creating a new one,pls add alert words in it")
            f.write(
                "# 监视-关键词1|联系人组名1\n监视-关键词2|联系人组名1\n监视-关键词3|联系人组名2\n监视-关键词4|联系人组名2\n")
    with open(ALERT_WORDS_FILE, "r", encoding="utf-8") as f:
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


def load_contacts():
    # 读取配置文件-联系人
    data = {}
    if os.path.exists(CONTACT_FILE) == False:
        with open(CONTACT_FILE, "w", encoding="utf-8") as f:
            print(
                f"{CONTACT_FILE} not found, creating a new one,pls add email and wxmsg contacts in it"
            )
            f.write("# 联系人组名1|邮箱1,邮箱2|微信1,微信2\n# 联系人组名2|邮箱1,邮箱2|微信1,微信2\n")
    with open(CONTACT_FILE, "r", encoding="utf-8") as f:
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


def load_msg_groups():
    # 读取配置文件-消息分组
    global msg_group
    msg_group = {}
    if os.path.exists(MSG_GROUP_FILE) == False:
        with open(MSG_GROUP_FILE, "w", encoding="utf-8") as f:
            print(
                f"{MSG_GROUP_FILE} not found, creating a new one,pls add keywords and groups in it"
            )
            f.write("# 关键字|分组\n")
    with open(MSG_GROUP_FILE, "r", encoding="utf-8") as f:
        contacts = f.readlines()
        for item in contacts:
            if item.strip() == "":
                continue
            if item.strip().startswith("#"):
                continue
            keyword = item.strip().split(",")[0]
            group_name = item.strip().split(",")[1]
            ip_start = keyword.split("/")[0]
            # print(keyword)
            net_mask = keyword.split("/")[1]
            if group_name not in msg_group:
                msg_group[group_name] = []
            if net_mask == "":
                net_mask = "32"
            if net_mask == "32":
                if ip_start not in msg_group[group_name]:
                    msg_group[group_name].append(ip_start)
            elif net_mask == "16":
                msg_group[group_name].append(ip_start.split(
                    ".")[0]+"."+ip_start.split(".")[1]+".")
            elif net_mask == "8":
                msg_group[group_name].append(ip_start.split(".")[0]+".")
            elif int(net_mask) > 16 and int(net_mask) < 25:
                for i in range(0, 2**(24-int(net_mask))):
                    msg_group[group_name].append(ip_start.split(
                        ".")[0]+"."+ip_start.split(".")[1]+"."+str(int(ip_start.split(".")[2])+i)+".")
            else:
                msg_group[group_name].append(ip_start)

        print("关键字分组：", msg_group)
        return msg_group


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
    global serial_opened
    # 扫描端口
    # result = check_uart_port()
    result = True
    if (result == False):
        return

    # 打开串口
    port = serialdev.split(',')[0]
    bps = int(serialdev.split(',')[1])
    timeout = int(serialdev.split(',')[2])

    
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
    close_uart(uart1)
    serial_opened = False
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
        config.set("config", "ocr_detail", r"0")
        config.set("config", "window_title", r"xxxx")
        config.set("config", "send_snapshot", r"1")
        config.set("config", "alert_words", r"alert_words.txt")
        config.set("config", "contacts", r"conf_contacts.txt")
        config.set("config", "send_seprate", r"1")
        config.set("config", "send_seprate_group", r"conf_msg_group.txt")
        # config.set("config", "daemon_permit", r"1")
        config.set("config", "daemon_interval", r"5")
        config.set("config", "auto_reply", r"1")
        config.set("config", "auto_reply_text", r"5")

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
        "ocr_detail": "0",
        "window_title": "xxxx",
        "send_snapshot": "1",
        "alert_words": "alert_words.txt",
        "contacts": "conf_contacts.txt",
        "send_seprate_group": r"conf_msg_group.txt",
        "send_seprate": "1",
        "auto_reply": "1",
        "auto_reply_text": "收到，立即处置",
        "daemon_interval": "5",
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


def quit_program():
    global icon, app_run

    # 确保只执行一次退出操作
    if not hasattr(quit_program, "called"):
        quit_program.called = True
    else:
        return

    exit_flag.set()  # 设置全局事件，通知线程退出
    app_run = False   # 停止主循环

    # 先停止托盘图标
    if icon is not None:
        try:
            icon.stop()
        except:
            pass
        icon = None

    # 保存数据
    try:
        with open("img_md5_list.txt", "w", encoding="utf-8") as f:
            for item in img_md5_list:
                f.write(item+"\n")
    except:
        pass

    # 尝试显示控制台
    try:
        w_console.show()  # 显示控制台
        w_console.restore()  # 恢复窗口
    except:
        pass

    # 关闭tkinter主窗口
    try:
        if root and root.winfo_exists():
            root.destroy()
    except:
        pass

    try:
        os._exit(0)
    except:
        pass
    try:
        sys.exit(0)
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


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


@new_thread
def systray(icon):
    icon.run()


def sw_console():
    global settings_window, sw_show

    if not settings_window or not tk._default_root or not settings_window.winfo_exists():
        # 窗口不存在则创建
        settings_window = open_settings()
        sw_show = True  # 创建后显示
    else:
        if sw_show:
            # 当前显示则隐藏
            settings_window.withdraw()
            sw_show = False
        else:
            # 当前隐藏则显示
            settings_window.deiconify()
            settings_window.focus_force()
            sw_show = True
# 修改3: 让open_settings返回创建的窗口


def open_settings():
    """显示设置窗口"""
    global settings_window, sw_show, textPad

    # 如果窗口已经存在，则直接显示
    if settings_window and settings_window.winfo_exists():
        settings_window.deiconify()
        settings_window.focus_force()
        sw_show = True
        return settings_window

    # 创建新窗口
    settings_window = tk.Toplevel(root)
    settings_window.title("程序设置")
    settings_window.geometry("300x200")
    # 修改4: 窗口关闭时隐藏而非销毁
    settings_window.protocol("WM_DELETE_WINDOW", lambda: sw_console())

    settings_window.iconbitmap(get_resource_path("reload.gif"))  # 设置窗口图标
    screenWidth = settings_window.winfo_screenwidth()  # 获取显示区域的宽度
    screenHeight = settings_window.winfo_screenheight()  # 获取显示区域的高度
    width = 500  # 设定窗口宽度
    height = 400  # 设定窗口高度
    left = (screenWidth - width-50)
    top = (screenHeight - height-150)

    # 宽度x高度+x偏移+y偏移
    settings_window.geometry("%dx%d+%d+%d" % (width, height, left, top))

    settings_window.title(prog_window_title)
    # settings_window.protocol("WM_DELETE_WINDOW", quit_program)
    tk.Label(settings_window, text=VERSION_TEXT).pack()
    textPad = tk.Text(settings_window, undo=True)
    textPad.pack(expand=tk.YES, fill=tk.BOTH)
    scroll = tk.Scrollbar(textPad)
    textPad.config(yscrollcommand=scroll.set)
    scroll.config(command=textPad.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    bt1 = tk.Button(settings_window, text="启动监视!",
                    command=lambda: set_daemon_permit("on")).pack(side=tk.LEFT)
    bt2 = tk.Button(settings_window, text="消音!", command=lambda: set_alert_permit(
        "off")).pack(side=tk.LEFT)
    bt3 = tk.Button(settings_window, text="停止监视!", command=lambda: set_daemon_permit(
        "off")).pack(side=tk.LEFT)
    bt4 = tk.Button(settings_window, text="退出程序!",
                    command=quit_program).pack(side=tk.LEFT)

    settings_window.attributes('-topmost', True)
    settings_window.after_idle(settings_window.attributes, '-topmost', False)
    sw_show = True  # 新创建窗口时设为显示状态

    return settings_window  # 返回创建的窗口


def process_queue():
    """处理来自其他线程的UI请求"""
    try:
        while not ui_queue.empty():
            command, data = ui_queue.get_nowait()

            if command == "show_message":
                tk.messagebox.showinfo("信息", "这是一个使用pystray和tkinter的示例程序")

            elif command == "exit_app":
                exit_flag.set()
                root.quit()  # 退出主事件循环

            # 修改6: 直接调用sw_console而不是open_settings
            elif command == "open_settings":
                sw_console()

    except queue.Empty:
        pass

    # 每100ms检查一次队列
    root.after(100, process_queue)


if __name__ == "__main__":
    # 读取配置文件-关键词分组
    msg_group = load_msg_groups()

    # 全局事件，用于通知线程退出
    exit_flag = threading.Event()
    # 事件队列
    ui_queue = queue.Queue()

    icon, textPad = '', ''
    try:
        w_title = "Screen OCR Watchdog"  # 控制台窗口标题 通过 title 命令在bat文件中设置
        w_console = pygetwindow.getWindowsWithTitle(w_title)[0]
        w_console.minimize()  # 最小化窗口
        w_console.hide()  # 隐藏窗口
    except:
        pass
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
    if os.path.exists("img_md5_list.txt") == True:
        with open("img_md5_list.txt", "r", encoding="utf-8") as f:
            for line in f.readlines():
                img_md5_list.append(line.strip())
    w_left, w_top = 0, 0
    debug = False
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
    alert_mp3_file, conf_wxmsg, conf_email, ocr_method, ocr_detail, window_title, conf_serial, send_snapshot, send_seprate, auto_reply, auto_reply_text = (
        get_conf_from_file(
            configpath,
            "config",
            [
                "alert_mp3_file",
                "send_wxmsg",
                "send_email",
                "ocr_method",
                "ocr_detail",
                "window_title",
                "send_serial",
                "send_snapshot",
                "send_seprate",
                "auto_reply",
                "auto_reply_text",
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

    ocr_detail = int(ocr_detail)
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
        else:
            conf_serial = True
    if send_snapshot == "1":  # 是否发送截图
        send_snapshot = True
    else:
        send_snapshot = False
    if send_seprate == "1":  # 是否分开发送
        send_seprate = True
    else:
        send_seprate = False
    if auto_reply == "1":  # 是否自动回复
        auto_reply = True
    else:
        auto_reply = False
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
        
        serial_opened = False
        
    alert_words, alert_groups = load_alert_words()

    contacts = load_contacts()
    app_run = True
    alert_permit = False
    daemon_permit = False

    schedule.every(20).seconds.do(check_screen)  # 每10秒执行一次，检查屏幕
    schedule.every(60*20).seconds.do(clean_msg_store)  # 每20分执行一次，清除消息存储
    schedule.every(120).seconds.do(load_alert_words)  # 每120秒执行一次，加载关键词
    schedule.every(120).seconds.do(load_contacts)  # 每120秒执行一次，加载联系人
    schedule.every(3).seconds.do(run_play_music)  # 每3秒执行一次，播放报警音

    serial_daemon()
    daemon_worker()

    try:
        splash.quit()
    except:
        pass

    menu_options = pystray.Menu(
        pystray.MenuItem("启动监视!", lambda: set_daemon_permit("on")),
        pystray.MenuItem("停止监视!", lambda: set_daemon_permit("off")),
        pystray.MenuItem("消音!", lambda: set_alert_permit("off")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("控制台", sw_console),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", quit_program)
    )
    icon = pystray.Icon(name="桌面关键字监视器", icon=Image.open(
        get_resource_path("./reload.gif")), menu=menu_options, on_quit=quit_program)

    systray(icon)
    """创建隐藏的tkinter主窗口"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口

    # 修改1: 定义全局状态变量
    settings_window = None
    sw_show = False  # False表示隐藏，True表示显示
    sw_console()  # 确保设置窗口在主循环结束后仍然可用
    sw_console()  # 确保设置窗口在主循环结束后仍然可用

    # 启动队列处理
    root.after(100, process_queue)

    # 启动tkinter主事件循环
    root.mainloop()

    # tkinter事件循环退出后，设置退出标志
    exit_flag.set()

    # 等待退出标志
    while not exit_flag.is_set():
        time.sleep(0.1)

    # 显式停止托盘图标
    if icon and hasattr(icon, 'stop'):
        icon.stop()
