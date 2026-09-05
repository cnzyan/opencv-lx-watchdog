from Crypto.Cipher import AES
import gc
import keyboard
from PIL import Image, ImageGrab, ImageTk, ImageSequence
import numpy
import time
import requests
import urllib
import schedule
import smtplib
import loguru
import hashlib
import os

os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_use_onednn"] = "0"
import sys
import re
import base64
import configparser
import chardet
import tkinter as tk
from tkinter import ttk
import pygetwindow
import pyautogui
import pystray
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from functools import wraps
import queue
from collections import deque

# DPI感知由pyscreeze内部自动处理，不需要手动设置
requests.packages.urllib3.disable_warnings()
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"  # 允许 Intel AI OpenMP 库的重复加载
# .venv\Scripts\Activate.ps1
# pip install -r requirements.txt
# pyinstaller -F pad-ocr-watchdog.py
VERSION_TEXT = "ProG By CrazYan 202408/upd202608"
CONTACT_FILE = "conf_contacts.txt"
ALERT_WORDS_FILE = "conf_alert_words.txt"
MSG_GROUP_FILE = "conf_msg_groups.txt"
LOGS_DIR = "logs"
DEPARTMENT_MAPPING = {
    "山东": "shandong",
    "滕州": "tengzhou",
    "十里泉": "shiliquan",
    "淄博": "zibo",
    "潍坊": "weifang",
    "邹县": "zouxian",
    "新能源": "xinnengyuan",
    "莱州": "laizhou",
    "青岛": "qingdao",
    "莱城": "laicheng",
    "章丘": "zhangqiu",
    "龙口": "longkou",
}


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


def set_volume(val=50):
    val = int(float(val))
    # 设置音量
    global conf_volume, volume_label
    if val > 100:
        val = 100
    elif val < 0:
        val = 0
    # 获取滑块当前值并更新变量和标签
    if abs(val - conf_volume) < 5:
        # print("Volume Not Changed, Current Value is ", conf_volume, "%")
        # textPad_insert("Volume Not Changed, Current Value is "+str(conf_volume)+"%")
        return
    conf_volume = val
    val = str(val)
    if len(val) == 1:
        val = "  " + val
    elif len(val) == 2:
        val = " " + val
    volume_label.config(text=f"{val}%")
    print("Set Volume To ", val, "%")
    textPad_insert("Set Volume To " + str(val) + "%")


def set_daemon_interval(val=20):
    # 设置监视间隔
    global daemon_interval, textPad
    global bt3_1, bt3_2, bt3_3, bt3_4
    if bt3_1 != None:
        # 重置按钮颜色
        bt3_1.config(bg="SystemButtonFace")
    if bt3_2 != None:
        # 重置按钮颜色
        bt3_2.config(bg="SystemButtonFace")
    if bt3_3 != None:
        # 重置按钮颜色
        bt3_3.config(bg="SystemButtonFace")
    if bt3_4 != None:
        # 重置按钮颜色
        bt3_4.config(bg="SystemButtonFace")
    if val == 5:
        bt3_1.config(bg="green")
    elif val == 10:
        bt3_2.config(bg="green")
    elif val == 15:
        bt3_3.config(bg="green")
    elif val == 20:
        bt3_4.config(bg="green")
    if val < 1:
        val = 1
    elif val > 60:
        val = 60
    daemon_interval = val
    print("Set Daemon Interval To ", daemon_interval, " seconds")
    textPad_insert("Set Daemon Interval To " + str(daemon_interval) + " seconds")


@new_thread
def play_music(file_path):
    global conf_volume
    # 调用播放音频报警函数
    play_method = "pygame"
    if play_method == "ffplay":
        import os

        cmd_line = "ffplay.exe -nodisp -autoexit " + file_path
        # print(cmd_line)
        os.system(cmd_line)
    elif play_method == "pygame":
        import pygame

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.set_volume(conf_volume / 100)
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
    elif play_method == "winsound":
        import winsound

        # winsound.PlaySound(file_path, winsound.SND_FILENAME)
        winsound.PlaySound("filename", winsound.SND_ASYNC | winsound.SND_ALIAS)
    else:
        import backup.playsound as playsound

        playsound.playsound(file_path, False)
        print("Alert Sound Playing...")


def textPad_insert(text):
    global textPad, root
    if textPad == None:
        print("TextPad is None, Cannot Insert Text")
        return
    if threading.current_thread() is not threading.main_thread():
        root.after(0, lambda t=text: _do_textPad_insert(t))
    else:
        _do_textPad_insert(text)


def _do_textPad_insert(text):
    global textPad
    textPad.insert("end", text + "\n")
    textPad.see("end")


def textPad_clear():
    # 清空文本框
    global textPad
    if textPad == None:
        print("TextPad is None, Cannot  Clear")
        return
    textPad.delete("1.0", "end")
    print("TextPad Cleared")
    textPad_insert("TextPad Cleared")


def textPad_save():
    # 保存文本框内容到文件
    global textPad
    if textPad == None:
        print("TextPad is None, Cannot Save")
        return "TextPad is None, Cannot Save"
    try:
        filename = f"logs/textPad_content{get_curtime('%Y%m%d%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            content = textPad.get("1.0", "end")
            f.write(content)
        print("TextPad Content Saved")
        textPad_insert("TextPad Content Saved")
        return filename
    except Exception as e:
        print("Error Saving TextPad Content: ", str(e))
        textPad_insert("Error Saving TextPad Content: " + str(e))
        return "Error Saving TextPad Content: " + str(e)


def textPad_save_and_clear():
    # 保存文本框内容到文件并清空文本框
    global textPad
    if textPad == None:
        print("TextPad is None, Cannot Save and Clear")
        return
    line_count = int(len(textPad.get("1.0", "end").splitlines()))
    print("TextPad Line Count: ", line_count)
    if line_count < 1000:
        # print("TextPad is Empty, No Need to Save")
        # textPad_insert("TextPad is Empty, No Need to Save")
        return
    try:
        filename = textPad_save()
        for i in range(0, 3):
            time.sleep(0.5)
            textPad_insert(".")
        textPad_clear()
        textPad_insert("TextPad Content Saved to " + filename)
    except Exception as e:
        print("Error Saving TextPad Content: ", str(e))
        textPad_insert("Error Saving TextPad Content: " + str(e))


_valid_audio_file = None


def run_play_music():
    # 播放音频报警
    global alert_mp3_file, alert_permit, daemon_permit, _valid_audio_file
    if _valid_audio_file is None:
        if "resources/audio" not in alert_mp3_file:
            alert_mp3_file = "./resources/audio/" + alert_mp3_file
        if os.path.exists(alert_mp3_file) == False:
            alert_mp3_file = "./resources/audio/alert.mp3"
        _valid_audio_file = alert_mp3_file
    if alert_permit == True:
        play_music(_valid_audio_file)
    else:
        if daemon_permit == True:
            print(".", end="")
            # print("Alert Permitted is False, Skip Play Music")
        else:
            pass


def play_test_sound():
    """试音函数，不受 alert_permit 限制"""
    global alert_mp3_file
    file_path = alert_mp3_file
    if "resources/audio" not in file_path:
        file_path = "./resources/audio/" + file_path
    if os.path.exists(file_path) == False:
        file_path = "./resources/audio/alert.mp3"
    play_music(file_path)


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
        # 每次启动都清空文本框
        textPad_save_and_clear()

        print("WatchDog Started At ", get_curtime())
        textPad_insert("WatchDog Started At " + get_curtime())
    else:
        print("WatchDog Stopped At ", get_curtime())
        textPad_insert("WatchDog Stopped At " + get_curtime())


"""
def get_curtime(time_format="%Y-%m-%d %H:%M:%S"):
    curTime = time.localtime()
    curTime = time.strftime(time_format, curTime)
    return curTime
"""


def get_curtime(time_format="%Y-%m-%d %H:%M:%S", offset=0):
    # 获取时间戳，offset为偏移天数
    curTime = time.time() + offset * 24 * 60 * 60
    curTime = time.localtime(curTime)
    curTime = time.strftime(time_format, curTime)
    return curTime


def put_email_queue(message, smtp_host, smtp_port, mail_user, mail_pass, smtptype):
    """
    创建一个邮件队列
    """
    delay = 0
    email_queue.put(
        (message, smtp_host, smtp_port, mail_user, mail_pass, smtptype, delay)
    )


@new_thread
def process_email_queue(email_queue):
    loguru.logger.info("邮件队列处理线程已启动")
    while True:
        try:
            msg, host, port, user, passwd, security, delay = email_queue.get(timeout=1)
        except queue.Empty:
            continue
        re_put = False
        if delay == 0:
            if send_mail(msg, host, port, user, passwd, security):
                pass
            else:
                delay = 60
                loguru.logger.error("邮件发送失败，延迟60秒重试")
                re_put = True
            time.sleep(0.1)
        else:
            time.sleep(1)
            delay -= 1
            if delay <= 0:
                delay = 0
            loguru.logger.info("邮件发送延迟，等待" + str(delay) + "秒")
            re_put = True
        if re_put:
            email_queue.put((msg, host, port, user, passwd, security, delay))


# 组合邮件内容


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
    loguru.logger.info("准备发送邮件到 " + str(tomail))
    if email_method == "smtp":
        message = MIMEMultipart()
        message["From"] = sender_email
        temp = []
        if type(tomail) == str:
            temp.append(tomail)
        else:
            temp = tomail
        maillist = ",".join(temp)
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
        return put_email_queue(
            message, smtp_host, smtp_port, mail_user, mail_pass, smtptype
        )

    else:
        return send_mail_http(Subject, content, tomail)


# AES ECB加密


def AES_ECB_ENCRYPT(plain_text, secretKey):
    if type(plain_text) != type(""):
        plain_text = str(plain_text)
    key = secretKey.encode()
    cipher = AES.new(key, AES.MODE_ECB)
    # 确保明文长度是16的倍数
    pad = 16 - len(plain_text.encode("utf-8")) % 16
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


def send_mail_http(Subject, content, tomail):
    secret_seed = server_secret  # 服务器密钥
    secret_today = hashlib.md5(
        (secret_seed + get_curtime("%Y%m%d")).encode()
    ).hexdigest()
    content_b64 = base64.b64encode(content.encode()).decode()
    origin = {"subject": Subject, "content": content_b64, "tomail": tomail}
    origin = str(origin)
    http_transport_data = AES_ECB_ENCRYPT(origin, secret_today)
    postdata = {"secret": secret_today, "content": http_transport_data}
    try:
        resp = requests.post(
            url=server_url, data=postdata, verify=False
        ).content.decode("utf-8")
        loguru.logger.info("邮件发送成功 to " + tomail + ":" + resp)
        return True
    except Exception as e:
        loguru.logger.error("邮件发送失败" + str(e))
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
    """
    获取文字与位置对应map
    :param path:图片路径，图片路径为空则默认获取当前屏幕截图
    :param text: 筛选需要查找的内容，匹配所有位置
    :return:list
    """

    result, img_path, image, fs = ocr_img_text(path, saveimg=True)

    print("图片识别结果保存：", img_path)

    # 把结果列表的两个值分别再存为两个list
    poslist = [
        detection[0][0] for line in result for detection in line
    ]  # 取top一个点的位置
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
    if isinstance(image, str) and image == "":
        image, fullscreen = screenshot(w_title=window_title)
        image = numpy.array(image)

    elif isinstance(image, str):
        # 不为空就打开
        image = Image.open(image).convert("RGB")
        image = numpy.array(image)
    elif isinstance(image, numpy.ndarray):
        # 已经是numpy数组，直接使用
        fullscreen = "no"
    else:
        image = numpy.array(image)
    if engine == "paddle":
        global _paddle_ocr_instance
        if "_paddle_ocr_instance" not in globals() or _paddle_ocr_instance is None:
            _paddle_ocr_instance = paddleocr.PaddleOCR(
                use_textline_orientation=True, lang="ch", enable_mkldnn=False
            )
        # PaddleOCR 3.x 使用 predict()，返回 OCRResult 迭代器
        ocr_results = list(_paddle_ocr_instance.predict(image))
        if ocr_results:
            r = ocr_results[0]
            # 将 3.x OCRResult 转为 2.x 兼容格式: [[[box, (text, score)], ...]]
            compat_result = []
            line_list = []
            for i in range(len(r["rec_texts"])):
                box = (
                    r["dt_polys"][i]
                    if i < len(r["dt_polys"])
                    else [[0, 0], [0, 0], [0, 0], [0, 0]]
                )
                text = r["rec_texts"][i]
                score = r["rec_scores"][i] if i < len(r["rec_scores"]) else 0.0
                line_list.append([box, (text, score)])
            if line_list:
                compat_result.append(line_list)
            result = compat_result
        else:
            result = [[]]
        if printResult is True:
            for line in result:
                for word in line:
                    print(word)
    elif engine == "easyocr":
        global _easyocr_reader_instance
        if (
            "_easyocr_reader_instance" not in globals()
            or _easyocr_reader_instance is None
        ):
            _easyocr_reader_instance = easyocr.Reader(["ch_sim", "en"])
        result = _easyocr_reader_instance.readtext(image, detail=conf_detail)
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
                image, lang="chi_sim+eng", output_type=pytesseract.Output.DICT
            )

            if printResult is True:
                print(result)
        else:
            result = pytesseract.image_to_string(image, lang="chi_sim+eng")
    if debug:
        with open(
            "ocr_result_" + engine + "_" + get_curtime("%H%M%S") + ".txt",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(str(result))

    # 识别出来的文字保存为图片
    img_name = "ImgTextOCR-img-" + get_curtime("%Y%m%d%H%M%S") + ".jpg"
    if saveimg is True:
        if engine == "paddle":
            # paddleocr 3.x移除了draw_ocr，改为手动绘制
            im_show = image.copy()
            for line in result:
                for detection in line:
                    # detection: [box_points, (text, score)]
                    box = detection[0]  # [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
                    text = detection[1][0]
                    # 绘制矩形框
                    pts = numpy.array(box, dtype=numpy.int32).reshape((-1, 1, 2))
                    im_show = cv2.polylines(im_show, [pts], True, (0, 255, 0), 2)
                    # 绘制文字
                    top_left = (int(box[0][0]), int(box[0][1]) - 10)
                    im_show = cv2.putText(
                        im_show,
                        text,
                        top_left,
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2,
                    )
        elif engine == "easyocr":
            im_show = image.copy()
            for detection in result:
                # print(detection)
                top_left = tuple([int(val) for val in detection[0][0]])
                bottom_right = tuple([int(val) for val in detection[0][2]])
                im_show = cv2.rectangle(im_show, top_left, bottom_right, (0, 255, 0), 2)
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
            im_show = image.copy()
        filepath = "screenshots"
        im_show = Image.fromarray(im_show)
        im_show.save(filepath + "\\" + img_name)

    return result, img_name, image, fullscreen


def _gc_collect():
    gc.collect()


def _log_memory(tag=""):
    import psutil

    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    msg = f"[Memory{f' {tag}' if tag else ''}] RSS: {mem_mb:.1f} MB"
    print(msg)
    textPad_insert(msg)


# 截图


def screenshot(fullscreen="no", w_title="蓝信", saving=False):
    global w_left, w_top
    """
    截图
    :return:Image
    """
    fullscreen = "no"

    def active_window(w_title):
        windows = pygetwindow.getWindowsWithTitle(w_title)
        if len(windows) == 0:
            print("Window Not Found.")
            return False
        else:
            window = windows[0]
            if window.isActive == False:
                try:
                    if window.isMaximized == False:
                        window.restore()  # 非最大化时才恢复窗口（避免全屏变窗口化）
                    window.activate()  # 激活窗口
                    return True
                except Exception:
                    print("Window Active Failed, try again.")
                    return False
            else:
                return True

    filepath = "screenshots"

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
                window = windows[0]
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
                x, y, width, height = (
                    window.left,
                    window.top,
                    window.width,
                    window.height,
                )
                w_left, w_top = window.left, window.top
                # 截取窗口的屏幕截图
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            except Exception as e:
                print("Window Screenshot Failed." + str(e))
                fullscreen = "yes"
            # 保存截图
            if saving == True:
                screenshot_filename = (
                    "window_screenshot" + get_curtime("%Y%m%d%H%M%S") + ".png"
                )
                screenshot.save(filepath + "\\" + screenshot_filename)
                print(
                    "Screenshot of the window saved as "
                    + filepath
                    + "\\"
                    + screenshot_filename
                )
            return screenshot, fullscreen
    else:
        pass
    if fullscreen != "no":
        im = ImageGrab.grab()
        # 保存截图
        if saving == True:
            screenshot_filename = (
                "window_screenshot" + get_curtime("%Y%m%d%H%M%S") + ".png"
            )
            im.save(filepath + "\\" + screenshot_filename)
            print(
                "Screenshot fullscreen saved as "
                + filepath
                + "\\"
                + screenshot_filename
            )
        return im, fullscreen


def check_ip_change():
    """
    检查IP是否变化
    :return:bool
    """
    try:
        ip = requests.get("http://httpbin.org/ip").json()
        ip = ip["origin"]
        try:
            with open("ip.txt", "r") as f:
                old_ip = f.read()
        except FileNotFoundError:
            old_ip = ""
        if ip != old_ip:
            with open("ip.txt", "w") as f:
                f.write(ip)
            return True, ip
        else:
            return False, ip  # 返回False表示IP未变化
    except Exception as e:
        loguru.logger.error("检查IP变化失败" + str(e))
        return False, "检查IP变化失败"  # 返回False表示IP未变化


@new_thread
def send_email_ipchg():
    """
    发送IP变化邮件
    :return:
    """
    ip_Changed, ip = check_ip_change()
    if ip_Changed:
        content = "IP地址变化了，新的IP地址是：" + ip + "<br>请注意检查网络连接。"
        Subject = "IP地址变化"
        send_email(
            Subject=Subject,
            content=content,
            tomail=email_receivers,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            mail_user=mail_user,
            mail_pass=mail_pass,
            sender_email=sender_email,
            smtptype=email_method,
        )


def clean_msg_store():  # 清理消息存储
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
    detect_list = [
        "条新消息",
        "条新",
        "条新消",
        "条",
        "新消息",
        "新消",
        "新",
        "消息",
        "消",
        "息",
    ]
    unread_detected = False
    if ocr_method == "tesseract":
        all_text = "".join(ocr_resp["text"])
        if ocr_detail == 1:

            for chr in text_to_detect:
                if chr not in all_text:
                    return False

            for word in ocr_resp["text"]:
                if word in detect_list:
                    pos_index = get_index_of_list(ocr_resp["text"], word)
                    if word != text_to_detect:
                        for index in pos_index:
                            if index != -1:
                                if ocr_resp["text"][index + 1] in detect_list:
                                    print("Unread Msg Found!!!")
                                    textPad_insert("Unread Msg Found!!!")
                                    unread_detected = True
                    else:
                        print("Unread Msg Found!!!")
                        textPad_insert("Unread Msg Found!!!")
                        unread_detected = True
                    break
            if unread_detected == True:
                pos = [
                    ocr_resp["left"][index],
                    ocr_resp["top"][index],
                    ocr_resp["width"][index],
                    ocr_resp["height"][index],
                ]
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
                        pos = [
                            word[0][0][0],
                            word[0][0][1],
                            word[0][2][0] - word[0][0][0],
                            word[0][2][1] - word[0][0][1],
                        ]

            elif ocr_method == "easyocr":
                if ocr_detail == 1:
                    if text_to_detect in line[1]:
                        unread_detected = True
                        pos = [
                            line[0][0][0],
                            line[0][0][1],
                            line[0][2][0] - line[0][0][0],
                            line[0][2][1] - line[0][0][1],
                        ]
            else:
                return False

            if unread_detected == True:
                return pos
            else:
                continue
        pass


def click_unread_msg(pos):
    pos_x = pos[0] + pos[2] / 2 + w_left
    pos_y = pos[1] + pos[3] / 2 + w_top
    pyautogui.click(pos_x, pos_y, button="left")
    textPad_insert("Mouse Click At " + str(pos_x) + "," + str(pos_y))
    # pyautogui.click(100, 150, button='left')
    # pyautogui.click('屏幕区块.png')
    pass


_SPLIT_PATTERN = re.compile(r"[a-zA-Z0-9_]+|\S")


def split_string(s):
    return _SPLIT_PATTERN.findall(s)


# 检查屏幕内容


def click_in_window(x, y, key="left"):
    """点击当前活动窗口内的相对坐标位置 (包括标题栏)"""
    # 获取当前活动窗口
    active_win = pyautogui.getActiveWindow()

    if active_win is None:
        print("未检测到活动窗口！")
        return

    print(
        f"活动窗口信息: {active_win.title} | 大小: {active_win.size} | 位置: {active_win.topleft}"
    )

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
    try:
        # print(auto_reply_text)
        global alert_msg, alert_words, alert_mp3_file, wxmsg_touser, last_sent_seprate
        image_saved = False
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
        textPad_insert("WatchDog Checking At " + get_curtime())
        if debug:
            _log_memory("check_start")

        # e行PC模式下，使用三张定位图片裁剪有效检测区域（排除标题栏、侧边栏和工具栏）
        crop_region = None
        if conf_app_name == "e行PC":
            dpi_scale = get_dpi_scale()
            print(f"当前系统DPI缩放倍率: {dpi_scale:.2f}x (DPI: {int(dpi_scale * 96)})")
            textPad_insert(f"当前系统DPI缩放倍率: {dpi_scale:.2f}x")
            try:
                # 定位左侧边缘图：取其最右下坐标作为裁剪左边界
                try:
                    left_path = get_resource_path_dpi(
                        "./resources/image/left_edge_hdex_pc.png"
                    )
                    print(f"使用定位图片: {left_path}")
                    left_loc = pyautogui.locateOnScreen(
                        left_path,
                        confidence=0.7,
                        region=(w_left, w_top, 200, 800),  # 仅在窗口左侧区域搜索
                    )
                except pyautogui.ImageNotFoundException:
                    left_loc = None
                # 定位右上边缘图：取其最左下坐标作为裁剪右边界
                try:
                    right_loc = pyautogui.locateOnScreen(
                        get_resource_path_dpi(
                            "./resources/image/rightup_edge_hdex_pc.png"
                        ),
                        confidence=0.7,
                        region=(w_left + 500, w_top, 400, 600),  # 仅在窗口右侧区域搜索
                    )
                except pyautogui.ImageNotFoundException:
                    right_loc = None
                # 定位工具栏图（在聊天下方）：取其最上坐标作为裁剪下边界
                try:
                    toolbar_loc = pyautogui.locateOnScreen(
                        get_resource_path_dpi("./resources/image/toolbar_hdex_pc.png"),
                        confidence=0.7,
                        region=(w_left, w_top, 800, 200),  # 仅在窗口顶部区域搜索
                    )
                except pyautogui.ImageNotFoundException:
                    toolbar_loc = None
                # 分别处理每个定位结果：找到的图片约束对应边界，未找到的不做限制
                # 左边界：找到左侧边缘图则取其最右下x，否则取0
                if left_loc:
                    crop_left = left_loc.left + left_loc.width
                else:
                    crop_left = 0
                    print("未找到left_edge_hdex_pc.png，左边界不裁剪")
                # 右边界：找到右上边缘图则取其最左下x，否则取图像右边界（后续由图像宽度决定）
                if right_loc:
                    crop_right = right_loc.left
                else:
                    crop_right = None  # 标记为未找到，后续用图像宽度
                    print("未找到rightup_edge_hdex_pc.png，右边界不裁剪")
                # 下边界：找到工具栏图则取其最上y，否则取图像下边界
                if toolbar_loc:
                    crop_bottom = toolbar_loc.top
                else:
                    crop_bottom = None  # 标记为未找到，后续用图像高度
                    print("未找到toolbar_hdex_pc.png，下边界不裁剪")

                if left_loc or right_loc or toolbar_loc:
                    # 至少有一个定位成功时，构建裁剪区域（缺失的边界先用占位值，后续在裁剪时根据图像尺寸修正）
                    # 临时占位：宽和高先用大值，裁剪时会根据图像大小截断
                    tmp_crop_right = crop_right if crop_right is not None else 99999
                    tmp_crop_bottom = crop_bottom if crop_bottom is not None else 99999
                    crop_region = (
                        crop_left - w_left,
                        0,  # 上边界从0开始（窗口顶部）
                        tmp_crop_right - crop_left,
                        tmp_crop_bottom - w_top,
                    )
                    print(f"e行PC裁剪区域: {crop_region}")
                    textPad_insert(f"e行PC裁剪区域: {crop_region}")
                else:
                    # 所有图片均未找到时，使用基于图像尺寸的估算裁剪区域
                    # 此处image尚未获取，在OCR后根据实际图像尺寸计算
                    print("e行PC定位图片均未找到，将在OCR后使用估算裁剪区域")
                    crop_region = "estimated"
            except Exception as e:
                print(f"e行PC区域定位失败: {e}，使用全窗口检测")
                textPad_insert(f"e行PC区域定位失败: {e}，使用全窗口检测")
                crop_region = None

        ocr_resp, img_filename, image, fullscreen = ocr_img_text(
            saveimg=False, printResult=False, conf_detail=ocr_detail, engine=ocr_method
        )

        # e行PC模式：若定位图片未找到，使用图像实际尺寸估算裁剪区域
        if conf_app_name == "e行PC" and crop_region == "estimated":
            try:
                img_h, img_w = image.shape[:2]
                crop_region = (
                    300,  # crop_x: 避开左侧边栏（约300px）
                    0,  # crop_y: 从顶部开始
                    img_w - 350,  # crop_w: 宽度减去左右边距
                    img_h - 150,  # crop_h: 高度减去底部工具栏
                )
                print(
                    f"e行PC使用估算裁剪区域(基于图像尺寸{img_w}x{img_h}): {crop_region}"
                )
                textPad_insert(f"e行PC使用估算裁剪区域: {crop_region}")
            except Exception as e:
                print(f"e行PC估算裁剪区域失败: {e}，使用全窗口检测")
                textPad_insert(f"e行PC估算裁剪区域失败: {e}，使用全窗口检测")
                crop_region = None
        if (
            conf_app_name == "e行PC"
            and crop_region is not None
            and crop_region != "estimated"
        ):
            try:
                crop_x, crop_y, crop_w, crop_h = crop_region
                if crop_y + crop_h > image.shape[0]:
                    crop_h = image.shape[0] - crop_y
                if crop_x + crop_w > image.shape[1]:
                    crop_w = image.shape[1] - crop_x
                if crop_w > 0 and crop_h > 0:
                    cropped_image = image[
                        crop_y : crop_y + crop_h, crop_x : crop_x + crop_w
                    ].copy()
                    del image
                    ocr_resp, img_filename, image, fullscreen = ocr_img_text(
                        path=cropped_image,
                        saveimg=False,
                        printResult=False,
                        conf_detail=ocr_detail,
                        engine=ocr_method,
                    )
                    del cropped_image
                    print(f"裁剪后OCR完成，裁剪区域: {crop_region}")
                    textPad_insert(f"裁剪后OCR完成，裁剪区域: {crop_region}")
            except Exception as e:
                print(f"裁剪后OCR失败: {e}")
                textPad_insert(f"裁剪后OCR失败: {e}")
        if ocr_method == "tesseract":
            if ocr_detail == 1:
                ocr_resp_tes = "".join(t for t in ocr_resp["text"] if t)

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
                                        if ocr_resp["text"][index + 1] in detect_list:
                                            # 找到关键词坐标
                                            pos_detected = True
                                            pos_to_mid = [
                                                (
                                                    ocr_resp["left"][index]
                                                    + ocr_resp["left"][index + 1]
                                                )
                                                / 2,
                                                (
                                                    ocr_resp["top"][index]
                                                    + ocr_resp["top"][index + 1]
                                                )
                                                / 2,
                                            ]
                            else:
                                pos_detected = True
                                index = pos_index[0]
                                pos_to_mid = [
                                    ocr_resp["left"][index]
                                    + ocr_resp["width"][index] / 2,
                                    ocr_resp["top"][index]
                                    + ocr_resp["height"][index] / 2,
                                ]
                            if pos_detected:
                                # 检查是否有特征像素
                                pixel_char_count = 0
                                roi = image[
                                    int(ocr_resp["top"][index]) : int(
                                        ocr_resp["top"][index]
                                        + ocr_resp["height"][index]
                                    ),
                                    int(ocr_resp["left"][index]) : int(
                                        ocr_resp["left"][index]
                                        + ocr_resp["width"][index]
                                    ),
                                ]
                                """
                                for row in roi:
                                    for pixel in row:
                                        # 现在pixel是一个一维数组（三个元素）
                                        if (pixel > 80).any():
                                            continue
                                        else:
                                            pixel_char_count += 1

                                            if pixel_char_count > 20:
                                                print("Alert Word Found: ", word, " at position: ",
                                                    pos_to_mid, " with dark pixel: ", pixel)
                                                textPad_insert(
                                                    "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                                                alert_found = True
                                                break
                                """
                                # HDe行 接收 e8e8e9 发送 c9e7ff
                                # 蓝信 接收FFFFFF 发送 6392ed
                                # 判断每个像素是否所有通道都<=80
                                # 得到二维布尔数组，每个元素表示该像素是否所有通道<=80
                                if (
                                    conf_app_name == "蓝信"
                                ):  # 蓝信接收到的文字为黑色，判断黑色像素数量
                                    char_pixels = (roi <= 80).all(axis=2)
                                    char_num = 20
                                elif (
                                    conf_app_name == "e行PC"
                                ):  # HDe行接收到的文字为背景为灰白色 (#E4E4E5)，判断灰白像素数量
                                    char_pixels = (roi >= 228).all(axis=2)
                                    char_num = 60
                                else:  # 其他应用(e行安卓)接收到的文字为背景为白色，判断白像素数量
                                    char_pixels = (roi >= 250).all(axis=2)
                                    char_num = 60
                                pixel_char_count = char_pixels.sum()
                                if pixel_char_count > char_num:
                                    alert_found = True
                                    print(
                                        "Alert Word Found: ",
                                        word,
                                        " at position: ",
                                        pos_to_mid,
                                        " with dark pixel count: ",
                                        pixel_char_count,
                                    )
                                    textPad_insert(
                                        "Alert Word Found: "
                                        + word
                                        + " at position: "
                                        + str(pos_to_mid)
                                    )
                        """
                        alert_found = True
                        break
                        """
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
                                if image_saved == False:
                                    try:
                                        image_save = Image.fromarray(image)
                                        image_save = compress_image(
                                            image_save,
                                            target_width=1280,
                                            target_height=800,
                                            quality=85,
                                        )
                                        image_save.save(
                                            "screenshots\\" + img_filename,
                                            format="JPEG",
                                        )
                                        image_saved = True
                                        print(
                                            "Keyword found,Image saved:" + img_filename
                                        )
                                        textPad_insert(
                                            "Keyword found,Image saved:" + img_filename
                                        )
                                    except Exception as e:
                                        print("Image Compress Failed." + str(e))
                                        textPad_insert(
                                            "Image Compress Failed." + str(e)
                                        )

                                # print("Alert Word Found: ", word)
                                pos_to_mid = [
                                    (words[0][0][0] + words[0][1][0]) / 2,
                                    (words[0][0][1] + words[0][2][1]) / 2,
                                ]
                                # e行PC模式：如果裁剪区域有效，检查关键字坐标是否在裁剪区域内，排除侧边栏等无关区域
                                if conf_app_name == "e行PC" and crop_region is not None:
                                    crop_x, crop_y, crop_w, crop_h = crop_region
                                    if not (
                                        crop_x <= pos_to_mid[0] <= crop_x + crop_w
                                        and crop_y <= pos_to_mid[1] <= crop_y + crop_h
                                    ):
                                        print(
                                            f"关键字 '{word}' 在裁剪区域外，已跳过 (pos={pos_to_mid}, crop=({crop_x},{crop_y},{crop_w},{crop_h}))"
                                        )
                                        textPad_insert(
                                            f"关键字 '{word}' 在裁剪区域外，已跳过"
                                        )
                                        continue
                                # 检查是否有特征像素
                                square = [
                                    words[0][0][0],
                                    words[0][0][1],
                                    words[0][2][0] - words[0][0][0],
                                    words[0][2][1] - words[0][0][1],
                                ]
                                # print("Square: ", square)
                                # print(image)
                                pixel_char_count = 0
                                roi = image[
                                    int(square[1]) : int(square[1] + square[3]),
                                    int(square[0]) : int(square[0] + square[2]),
                                ]
                                """
                                for row in roi:
                                    for pixel in row:
                                        # 现在pixel是一个一维数组（三个元素）
                                        if (pixel > 80).any():
                                            continue
                                        else:
                                            pixel_char_count += 1

                                            if pixel_char_count > 20:
                                                print("Alert Word Found: ", word, " at position: ",
                                                    pos_to_mid, " with dark pixel: ", pixel)
                                                textPad_insert(
                                                    "Alert Word Found: "+word+" at position: "+str(pos_to_mid))
                                                alert_found = True
                                                break
                                """
                                # HDe行pc 接收 e8e8e9 发送 c9e7ff
                                # HDe行android 接收 ffffff 发送 c9e7ff
                                # 蓝信 接收FFFFFF 发送 6392ed
                                # 判断每个像素是否所有通道都<=80
                                # 得到二维布尔数组，每个元素表示该像素是否所有通道<=80
                                if (
                                    conf_app_name == "蓝信"
                                ):  # 蓝信接收到的文字为黑色，判断黑色像素数量
                                    char_pixels = (roi <= 80).all(axis=2)
                                    char_num = 20
                                elif (
                                    conf_app_name == "e行PC"
                                ):  # HDe行接收到的文字为背景为灰白色 (#E4E4E5)，判断灰白像素数量

                                    char_pixels = (roi >= 228).all(axis=2)
                                    char_num = 60
                                else:  # 其他应用(e行安卓)接收到的文字为背景为白色，判断白像素数量
                                    char_pixels = (roi >= 250).all(axis=2)
                                    char_num = 60
                                pixel_char_count = char_pixels.sum()
                                if debug:
                                    textPad_insert(
                                        "Conf App Name: "
                                        + conf_app_name
                                        + " , pixel_char_count:"
                                        + str(pixel_char_count)
                                    )
                                if pixel_char_count > char_num:
                                    alert_found = True
                                    print(
                                        "Alert Word Found: ",
                                        word,
                                        " at position: ",
                                        pos_to_mid,
                                        " with dark pixel count: ",
                                        pixel_char_count,
                                    )
                                    textPad_insert(
                                        "Alert Word Found: "
                                        + word
                                        + " at position: "
                                        + str(pos_to_mid)
                                    )
                                """
                                print("Alert Word Found: ", word, " at position: ", pos_to_mid)
                                alert_found = True
                                break
                                """
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
            if conf_app_name == "蓝信":  # 蓝信
                pos = check_unread_msg(image, ocr_resp)
                if pos != False and pos != None:
                    try:
                        click_unread_msg(pos)
                    except Exception as e:
                        print("Mouse Click Error." + str(e))
                        textPad_insert("Mouse Click Error." + str(e))
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
                    print("position x y to click: ", pos_to_mid)
                    # '''
                    if conf_app_name == "蓝信":  # 蓝信
                        y_offset = 50
                    elif conf_app_name == "e行PC":  # HDe行
                        y_offset = 120

                    if fullscreen == "yes":
                        if conf_app_name == "蓝信":
                            pyautogui.click(
                                # 右键点击关键字文本
                                pos_to_mid[0],
                                pos_to_mid[1],
                                button="right",
                            )
                            time.sleep(1)
                            pyautogui.click(
                                # 左键点击菜单项
                                pos_to_mid[0] + 50,
                                pos_to_mid[1] + y_offset,
                                button="left",
                            )
                        elif (
                            conf_app_name == "e行PC"
                        ):  # e行PC，类似e行安卓，长按弹出菜单
                            pyautogui.click(
                                pos_to_mid[0], pos_to_mid[1], button="right"
                            )
                            time.sleep(1)
                            quota_image = get_resource_path_dpi(
                                "./resources/image/quota_hdex_pc.png"
                            )
                            try:
                                location_q = pyautogui.locateOnScreen(
                                    quota_image, confidence=0.7
                                )
                            except pyautogui.ImageNotFoundException:
                                location_q = None
                            if location_q:
                                print("图片位置:", location_q)
                                pyautogui.click(
                                    location_q[0] + 20,
                                    location_q[1] + 25,
                                    button="left",
                                )
                            else:
                                print("未找到quota_hdex_pc.png")
                                textPad_insert("未找到quota_hdex_pc.png")
                        else:  # e行安卓，长按弹出菜单
                            # 移动鼠标到指定位置
                            pyautogui.moveTo(pos_to_mid[0], pos_to_mid[1] + 30)
                            textPad_insert(
                                "移动鼠标到指定位置:"
                                + str(pos_to_mid[0])
                                + ","
                                + str(pos_to_mid[1] + 30)
                            )
                            # 按下鼠标左键
                            pyautogui.mouseDown(button="left")

                            # 等待一段时间，模拟长按效果
                            time.sleep(2.5)  # 例如，长按2秒

                            # 释放鼠标左键
                            pyautogui.mouseUp(button="left")

                            time.sleep(1)
                            quota_image = get_resource_path_dpi(
                                "./resources/image/quota_hdex_android.png"
                            )
                            try:
                                location_q = pyautogui.locateOnScreen(
                                    quota_image, confidence=0.8
                                )  # 查找按钮图标
                            except pyautogui.ImageNotFoundException:
                                location_q = None
                            if location_q:
                                print("图片位置:", location_q)
                                pyautogui.click(
                                    # 点击输入框
                                    location_q[0] + 20,
                                    location_q[1] + 25,
                                    button="left",
                                )
                    else:  # fullscreen == "no" 只对蓝信/e行PC有效
                        # 在当前活动窗口内点击
                        if conf_app_name == "蓝信":
                            click_in_window(pos_to_mid[0], pos_to_mid[1], "right")
                            time.sleep(1)
                            # 点击当前活动窗口内的相对坐标位置
                            click_in_window(
                                pos_to_mid[0] + 50, pos_to_mid[1] + y_offset, "left"
                            )
                        elif (
                            conf_app_name == "e行PC"
                        ):  # e行PC，右键弹出菜单后通过图片定位点击输入框
                            click_in_window(pos_to_mid[0], pos_to_mid[1], "right")
                            time.sleep(1)
                            quota_image = get_resource_path_dpi(
                                "./resources/image/quota_hdex_pc.png"
                            )
                            try:
                                location_q = pyautogui.locateOnScreen(
                                    quota_image, confidence=0.8
                                )
                            except pyautogui.ImageNotFoundException:
                                location_q = None
                            if location_q:
                                print("图片位置:", location_q)
                                pyautogui.click(
                                    location_q[0] + 20,
                                    location_q[1] + 25,
                                    button="left",
                                )
                            else:
                                print("未找到quota_hdex_pc.png")
                                textPad_insert("未找到quota_hdex_pc.png")
                        else:  # e行安卓
                            active_win = pyautogui.getActiveWindow()

                            if active_win is None:
                                print("未检测到活动窗口！")
                                return

                            print(
                                f"活动窗口信息: {active_win.title} | 大小: {active_win.size} | 位置: {active_win.topleft}"
                            )

                            # 计算绝对坐标 (窗口位置 + 相对位置)
                            absolute_x = active_win.left + pos_to_mid[0]
                            absolute_y = active_win.top + pos_to_mid[1]
                            pyautogui.moveTo(absolute_x, absolute_y)
                            textPad_insert(
                                "移动鼠标到指定位置:"
                                + str(absolute_x)
                                + ","
                                + str(absolute_y)
                            )

                            # 按下鼠标左键
                            pyautogui.mouseDown(button="left")

                            # 等待一段时间，模拟长按效果
                            time.sleep(2.5)  # 例如，长按2秒

                            # 释放鼠标左键
                            pyautogui.mouseUp(button="left")

                            time.sleep(1)
                            quota_image = get_resource_path_dpi(
                                "./resources/image/quota_hdex_android.png"
                            )
                            try:
                                location_q = pyautogui.locateOnScreen(
                                    quota_image, confidence=0.8
                                )  # 查找按钮图标
                            except pyautogui.ImageNotFoundException:
                                location_q = None
                            if location_q:
                                print("图片位置:", location_q)
                                pyautogui.click(
                                    # 点击输入框
                                    location_q[0],
                                    location_q[1],
                                    button="left",
                                )
                    # '''
                    time.sleep(0.5)
                    # '''
                    # 点击输入框，不是必须 ====start
                    try:
                        # 查找图片位置
                        if conf_app_name == "蓝信":  # 蓝信
                            toolbar_image = get_resource_path_dpi(
                                "./resources/image/toolbar_lx.png"
                            )
                            x_offset = 0
                            y_offset = 80
                        elif conf_app_name == "e行PC":  # HDe行
                            toolbar_image = get_resource_path_dpi(
                                "./resources/image/toolbar_hdex_pc.png"
                            )
                            x_offset = 0
                            y_offset = 80
                        else:  # e行安卓
                            toolbar_image = get_resource_path_dpi(
                                "./resources/image/toolbar_hdex_android.png"
                            )
                            x_offset = 100
                            y_offset = 20
                        location = pyautogui.locateOnScreen(
                            toolbar_image, confidence=0.8
                        )  # 查找按钮图标
                        if location:
                            print("图片位置:", location)
                            pyautogui.click(
                                # 点击输入框
                                location[0] + x_offset,
                                location[1] + y_offset,
                                button="left",
                            )
                            if conf_app_name == "蓝信":  # 蓝信
                                pass
                            elif conf_app_name == "e行PC":  # HDe行
                                # 因引文在文本框上部，靠近toolbar，按下向下键，避免选中引文
                                keyboard.press_and_release("down")
                            else:  # e行安卓
                                pass
                        else:
                            print("未找到图片")
                    except pyautogui.ImageNotFoundException:
                        print("未找到图片")
                    # 点击输入框，不是必须 ====end
                    time.sleep(0.5)
                    keyboard.write(auto_reply_text)  # 输入自动回复内容

                    wait_time_random = False  # 是否等待随机时间
                    if wait_time_random == True:
                        wait_time = random.randint(0, 10) + 0.5  # 生成随机数
                    else:
                        wait_time = 0.5
                    textPad_insert("Wait Time: " + str(wait_time))
                    time.sleep(wait_time)  # 等待发送按钮出现
                    if (
                        conf_app_name == "蓝信" or conf_app_name == "e行PC"
                    ):  # 蓝信/e行PC
                        pyautogui.press("enter")
                    else:  # e行安卓
                        send_button_image = get_resource_path_dpi(
                            "./resources/image/send_button_hdex_android.png"
                        )
                        try:
                            location = pyautogui.locateOnScreen(
                                send_button_image, confidence=0.7
                            )  # 查找按钮图标
                            if location:
                                print("图片位置:", location)
                                pyautogui.click(
                                    # 点击输入框
                                    location[0] + 30,
                                    location[1] + 20,
                                    button="left",
                                )
                        except pyautogui.ImageNotFoundException:
                            print("未找到图片")
                            textPad_insert(
                                "未找到发送按钮图片，可能是屏幕分辨率不匹配，请检查资源图片。"
                            )
                    time.sleep(0.5)
                if send_image == True:
                    import io

                    output = io.BytesIO()
                    image = Image.fromarray(image)
                    image = compress_image(
                        image, target_width=1280, target_height=800, quality=85
                    )
                    image.save(output, format="JPEG")
                    image_data = output.getvalue()

                    img_base64 = base64.b64encode(image_data).decode()
                    img_md5 = hashlib.md5(img_base64.encode("utf-8")).hexdigest()
                    if img_md5 not in img_md5_set:
                        img_md5_set.add(img_md5)
                        img_md5_list.append(img_md5)
                        if len(img_md5_list) > 500:
                            for _ in range(300):
                                img_md5_set.discard(img_md5_list.popleft())
                    else:
                        print("Same Image Sent Already, Skip")
                        textPad_insert("Same Image Sent Already, Skip")
                        return
                    img_base64 = "data:image/jpeg;base64," + img_base64
                    contents = contents + "<br><img src='" + img_base64 + "'>"
                if send_image_file == True:
                    img_filename = (
                        "ImgTextOCR-img-" + get_curtime("%Y%m%d%H%M%S") + ".jpg"
                    )
                    image.save(img_filename)
                    if conf_serial:
                        serial_send("file", img_filename)

                if send_fulltext == True:  # 发送全文识别结果
                    contents = contents + "<br>" + str(ocr_resp)

                if send_seprate == True:  # 根据联系人组分组发送消息
                    if last_sent_seprate != contents:
                        send_sep(ocr_method, ocr_resp, contents, True)
                        last_sent_seprate = contents
                else:  # 不分组发送消息
                    if conf_wxmsg:
                        if micromsg_method == "local":
                            message = {"content": contents, "touser": wxmsg_touser}

                            message_queue.put(message)
                        elif micromsg_method == "server":
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
        # e行PC模式：自动回复和消息发送完成后，再检查新消息滚动按钮并点击滚动到最新消息
        if conf_app_name == "e行PC":
            try:
                newmsg_loc = pyautogui.locateOnScreen(
                    get_resource_path_dpi("./resources/image/newmsg_hdex_pc.png"),
                    confidence=0.7,
                )
                if newmsg_loc is not None:
                    print("e行PC新消息滚动按钮已定位，点击滚动到最新消息")
                    textPad_insert("e行PC新消息滚动按钮已定位，点击滚动")
                    pyautogui.click(
                        newmsg_loc.left + newmsg_loc.width // 2,
                        newmsg_loc.top + newmsg_loc.height // 2,
                        button="left",
                    )
            except Exception as e:
                print(f"e行PC新消息滚动按钮检测失败: {e}")
                textPad_insert(f"e行PC新消息滚动按钮检测失败: {e}")
    except Exception as e:
        print("Error in WatchDog: " + str(e))
        textPad_insert("Error in WatchDog: " + str(e))
        loguru.logger.exception("Error in WatchDog")
        try:
            global _paddle_ocr_instance
            _paddle_ocr_instance = None
        except Exception:
            pass
        _gc_collect()
        if conf_email:
            send_email(
                "ALERTonScreen Error",
                "Error in WatchDog: " + str(e),
                email_receivers,
                smtp_host,
                smtp_port,
                mail_user,
                mail_pass,
                sender_email,
                smtptype,
            )
    finally:
        try:
            del image
        except Exception:
            pass
        _gc_collect()
        if debug:
            _log_memory("check_end")


@new_thread
def send_sep(ocr, data, contents="", send_to_default=True):  # 根据联系人组分组发送消息
    global contacts, msg_group
    group_sent = []
    to_email, to_wx = "", ""
    if send_to_default:
        # 使用配置文件中的接收邮箱和微信用户
        if conf_email:
            if (
                email_receivers == []
                or email_receivers == None
                or email_receivers == [""]
                or email_receivers == ""
            ):
                to_email = ""
            else:
                # 默认发送到配置文件中的接收邮箱
                for email in email_receivers:
                    if email != "":
                        if to_email == "":
                            to_email = email.strip()
                        else:
                            to_email = to_email + "," + email.strip()
        if conf_wxmsg:
            to_wx = wxmsg_touser
    else:
        pass  # 不使用配置文件中的接收邮箱和微信用户

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
                    to_email = to_email + "," + contacts[group][0].strip()
                if to_wx == "":
                    to_wx = contacts[group][1].strip().replace(",", "|")
                else:
                    to_wx = to_wx + "|" + contacts[group][1].strip().replace(",", "|")

    elif ocr == "paddle" or ocr == "easyocr":
        for line in data:
            if line == [] or line == "":
                continue
            if ocr_method == "paddle":
                for word in line:
                    word = word[1][0]
                    # add 20250627
                    # 细分关键字分组发送 / IP识别
                    # TODO
                    for key in msg_group:
                        for k in msg_group[key]:
                            if k in word:
                                group = key
                                if group in group_sent:
                                    continue
                                group_sent.append(group)
                                try:
                                    if to_email == "":
                                        to_email = contacts[group][0].strip()
                                    else:
                                        to_email = (
                                            to_email + "," + contacts[group][0].strip()
                                        )
                                    if to_wx == "":
                                        to_wx = (
                                            contacts[group][1].strip().replace(",", "|")
                                        )
                                    else:
                                        to_wx = (
                                            to_wx
                                            + "|"
                                            + contacts[group][1]
                                            .strip()
                                            .replace(",", "|")
                                        )
                                except Exception as e:
                                    print("Error in contacts: " + str(e))
                                    textPad_insert("Error in contacts: " + str(e))
                                    continue
                    # 关键词分别发送对应联系人
                    for alert_word in alert_words:
                        if alert_word in word:
                            group = alert_groups[alert_word]
                            if group in group_sent:
                                continue
                            group_sent.append(group)
                            try:
                                if to_email == "":
                                    to_email = contacts[group][0].strip()
                                else:
                                    to_email = (
                                        to_email + "," + contacts[group][0].strip()
                                    )
                                if to_wx == "":
                                    to_wx = contacts[group][1].strip().replace(",", "|")
                                else:
                                    to_wx = (
                                        to_wx
                                        + "|"
                                        + contacts[group][1].strip().replace(",", "|")
                                    )
                            except Exception as e:
                                print("Error in contacts: " + str(e))
                                textPad_insert("Error in contacts: " + str(e))
                                continue
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
                        try:
                            if to_email == "":
                                to_email = contacts[group][0].strip()
                            else:
                                to_email = to_email + "," + contacts[group][0].strip()
                            if to_wx == "":
                                to_wx = contacts[group][1].strip().replace(",", "|")
                            else:
                                to_wx = (
                                    to_wx
                                    + "|"
                                    + contacts[group][1].strip().replace(",", "|")
                                )
                        except Exception as e:
                            print("Error in contacts: " + str(e))
                            textPad_insert("Error in contacts: " + str(e))
                            continue
        pass
    else:
        pass

    if conf_email:
        print(to_email)
        if "@" in to_email:
            send_email(
                "ALERTonScreen_s",
                contents,
                to_email,
                smtp_host,
                smtp_port,
                mail_user,
                mail_pass,
                sender_email,
                smtptype,
            )
        else:
            print("No Email Address Found")
    if conf_wxmsg:

        if to_wx != "":
            if micromsg_method == "local":
                message = {"content": contents, "touser": to_wx}

                message_queue.put(message)
            elif micromsg_method == "server":
                wxmsg(to_wx, contents)
        else:
            print("No Wxmsg Address")
    if conf_serial:

        content_b64 = base64.b64encode(contents.encode()).decode()
        trans_data = {"content": content_b64, "tomail": to_email}
        trans_data = str(trans_data)
        trans_data_b64 = base64.b64encode(trans_data.encode()).decode()
        serial_send("emb64", trans_data_b64)


class AccessTokenManager:
    """管理企业微信Access Token"""

    def __init__(self, corp_id, corp_secret):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.token = None
        self.expire_time = 0
        self.refresh_token()

    def get_token(self):
        """获取有效的access_token"""
        if not self.token or time.time() > self.expire_time:
            self.refresh_token()
        return self.token

    def refresh_token(self):
        """刷新access_token"""
        access_token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
        try:
            response = requests.get(access_token_url, timeout=10)
            result = response.json()
            if result.get("errcode") == 0:
                self.token = result["access_token"]
                self.expire_time = time.time() + result["expires_in"] - 300
                loguru.logger.info("Access token refreshed")
            else:
                loguru.logger.error(f"刷新access_token失败: {result}")
                raise Exception(f"刷新access_token失败: {result}")
        except Exception as e:
            loguru.logger.exception("刷新access_token时出错")
            raise


class DepartmentValidator:
    """验证部门ID有效性"""

    def __init__(self, token_manager):
        self.token_manager = token_manager
        self.valid_departments = set()
        self.refresh_departments()

    def refresh_departments(self):
        """获取并缓存有效的部门ID"""
        try:
            access_token = self.token_manager.get_token()
            url = f"https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token={access_token}"
            response = requests.get(url, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                self.valid_departments = {
                    str(dept["id"]) for dept in result.get("department", [])
                }
                loguru.logger.info(
                    f"已获取有效部门ID: {len(self.valid_departments)} 个"
                )
            else:
                loguru.logger.error(f"获取部门列表失败: {result}")
        except Exception as e:
            loguru.logger.exception("刷新部门列表时出错")

    def is_valid_department(self, dept_id):
        """检查部门ID是否有效"""
        if not self.valid_departments:
            self.refresh_departments()
        return dept_id in self.valid_departments

    def filter_valid_departments(self, dept_ids):
        """从列表或字符串中筛选有效部门ID"""
        if isinstance(dept_ids, str):
            dept_ids = dept_ids.split("|")

        valid_ids = [
            dept_id for dept_id in dept_ids if self.is_valid_department(dept_id)
        ]
        return "|".join(valid_ids)


class MessageSender(threading.Thread):
    """消息发送线程"""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.token_manager = AccessTokenManager(
            config["CORP_ID"], config["CORP_SECRET"]
        )
        self.department_validator = DepartmentValidator(self.token_manager)
        self.agent_id = config["AGENT_ID"]

    def run(self):
        loguru.logger.info("消息发送线程已启动")
        while not exit_flag.is_set():
            try:
                message = message_queue.get(timeout=5)

                success = self.send_message(message)

                if not success:
                    time.sleep(30)
                    message_queue.put(message)
                    loguru.logger.warning(
                        f"消息发送失败，已重新入队: {message['reqid']}"
                    )
                else:
                    self.record_message(message)

                message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                loguru.logger.exception("发送线程出错")
                time.sleep(10)

    def send_message(self, message, touser="", toparty=""):
        """发送消息到企业微信"""
        try:
            access_token = self.token_manager.get_token()
            send_msg_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
            params = {"access_token": access_token}
            toparty = message["toparty"] if message["toparty"] else toparty
            touser = message["touser"] if message["touser"] else touser

            payload = {
                "touser": touser,
                "toparty": toparty,
                "msgtype": "text",
                "agentid": self.agent_id,
                "text": {"content": message["content"]},
                "safe": 0,
            }

            response = requests.post(
                send_msg_url, params=params, json=payload, timeout=10
            )
            result = response.json()

            if result.get("errcode") == 0:
                loguru.logger.info(f"消息发送成功: {message['reqid']}")
                return True
            elif result.get("errcode") in [40014, 42001]:
                loguru.logger.warning("Token已过期，尝试刷新...")
                self.token_manager.refresh_token()
                return False
            else:
                loguru.logger.error(f"消息发送失败: {result}")
                return False
        except Exception as e:
            loguru.logger.exception(f"发送消息时出错: {message['reqid']}")
            return False

    def record_message(self, message):
        """记录已发送消息的日志"""
        filepath = os.path.join(LOGS_DIR, f"{message['reqid']}.txt")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(message["content"])
        except Exception as e:
            loguru.logger.exception(f"记录日志失败: {message['reqid']}")

    def get_valid_toparty(self, touser):
        """获取有效的接收部门ID"""
        # 获取责任部门ID
        party_id = DEPARTMENT_MAPPING.get(touser, "12")

        # 合并默认部门ID并过滤无效ID
        all_parties = f"{party_id}|{self.valid_default_departments}"
        return self.department_validator.filter_valid_departments(all_parties)


@new_thread
def wxmsg(touser, content):
    # 发送微信消息 over http 中继服务器
    global secret_seed, wxmsg_url, wxmsg_method
    wechatdata = "touser=" + touser
    content = urllib.parse.quote(content, encoding="utf-8")
    wechatdata = wechatdata + "&cont=[" + content + "]hvv-lx-msg"

    secret = hashlib.md5((secret_seed + get_curtime("%Y%m%d")).encode()).hexdigest()
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
                f"{ALERT_WORDS_FILE} not found, creating a new one,pls add alert words in it"
            )
            f.write(
                "# 监视-关键词1|联系人组名1\n监视-关键词2|联系人组名1\n监视-关键词3|联系人组名2\n监视-关键词4|联系人组名2\n"
            )
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
            f.write(
                "# 联系人组名1|邮箱1,邮箱2|微信1,微信2\n# 联系人组名2|邮箱1,邮箱2|微信1,微信2\n"
            )
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
                msg_group[group_name].append(
                    ip_start.split(".")[0] + "." + ip_start.split(".")[1] + "."
                )
            elif net_mask == "8":
                msg_group[group_name].append(ip_start.split(".")[0] + ".")
            elif int(net_mask) > 16 and int(net_mask) < 25:
                for i in range(0, 2 ** (24 - int(net_mask))):
                    msg_group[group_name].append(
                        ip_start.split(".")[0]
                        + "."
                        + ip_start.split(".")[1]
                        + "."
                        + str(int(ip_start.split(".")[2]) + i)
                        + "."
                    )
            else:
                msg_group[group_name].append(ip_start)

        print("关键字分组：", msg_group)
        return msg_group


def check_uart_port():
    port_list = list(serial.tools.list_ports.comports())
    # print(port_list)
    if len(port_list) == 0:
        print("can not find uart port")
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
        len = uart.write(txbuf.encode("utf-8"))  # 写数据
        return len
    except:
        time.sleep(1)
        try:
            len = uart.write(txbuf.encode("utf-8"))  # 写数据
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
    return [s[i : i + n] for i in range(0, len(s), n)]


# 串口发送数据(写入队列)


def serial_send(type, temp_data):
    global serial_queue
    if type == "email":
        temp_data = base64.b64encode(temp_data.encode()).decode()
    serial_queue.put([type, temp_data])


# 串口守护线程(从队列中读取数据发送)


@new_thread
def serial_daemon():
    global serial_queue
    serial_queue = queue.Queue()
    while True:
        # 使用阻塞获取替代轮询，减少CPU占用
        serial_data = serial_queue.get()
        serial_send_device(serial_data[0], serial_data[1])


# 串口发送数据


def serial_send_device(type, temp_data):
    global serial_opened
    # 扫描端口
    # result = check_uart_port()
    result = True
    if result == False:
        return

    # 打开串口
    port = serialdev.split(",")[0]
    bps = int(serialdev.split(",")[1])
    timeout = int(serialdev.split(",")[2])

    max_retries = 3
    retry_count = 0
    while serial_opened == False:
        try:
            uart1 = open_uart(port, bps, timeout)
            if uart1 is False:
                raise Exception("open_uart returned False")
            serial_opened = True
        except Exception as e:
            retry_count += 1
            loguru.logger.error(
                f"Serial Open Error (尝试 {retry_count}/{max_retries}): {e}"
            )
            if retry_count >= max_retries:
                loguru.logger.error(
                    f"串口 {port} 打开失败已达最大重试次数，放弃本次发送"
                )
                print(f"串口 {port} 打开失败，已放弃发送")
                textPad_insert(f"串口 {port} 打开失败，已放弃发送")
                return
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
            (str(int(time.time())) + temp_data).encode()
        ).hexdigest()
        index = 0
        for index in range(0, max_len):
            data_piece = str(temp_data_pieces[index])
            data_piece_hash = hashlib.md5(data_piece.encode()).hexdigest()
            txbuf = (
                '{"c":"'
                + type
                + '","index":"'
                + str(index + 1)
                + '","timestamp":"'
                + timestamp
                + '","num":"'
                + str(max_len)
                + '","data":"'
                + data_piece
                + '","hash":"'
                + data_piece_hash
                + '"}'
            )
            try:
                len = uart_send_data(uart1, txbuf)
                print("Serial send len: ", len, ";data_hash:", data_piece_hash)
                loguru.logger.info(
                    "Serial send len: " + str(len) + ";data_hash:" + data_piece_hash
                )
                time.sleep(0.001)
                pass
            except Exception as e:
                loguru.logger.error("Serial send error." + str(e))

    if type == "rt":
        for item in temp_data:
            txbuf = (
                '{"c":"rtd","iv":{"t":"'
                + str(item[0])
                + '","v":"'
                + str(item[1])
                + '"}}'
            )
            try:
                len = uart_send_data(uart1, txbuf)
                print("Serial send len: ", len, ";data:", txbuf)
                time.sleep(0.001)
                pass
            except Exception as e:
                # save_log('error', "Serial send error."+str(e))
                loguru.logger.error("Serial send error." + str(e))
    if type == "file":
        fn = (temp_data.replace("\\", "/").split("/"))[-1]
        txbuf = '{"c":"f","fn":"' + fn + '","fs":""}'
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
            loguru.logger.error("Serial send error." + str(e))

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
        config.set("config", "alert_words", r"conf_alert_words.txt")
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
        config.set("micromsg", "method", r"local")
        config.set("micromsg", "CORP_ID", r"YOUR_CORP_ID")
        config.set("micromsg", "CORP_SECRET", r"YOUR_CORP_SECRET")
        config.set("micromsg", "AGENT_ID", r"YOUR_AGENT_ID")
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


_encoding_cache = {}


def get_file_encoding(filepath):
    if filepath not in _encoding_cache:
        with open(filepath, "rb") as f:
            _encoding_cache[filepath] = chardet.detect(f.read())["encoding"]
    return _encoding_cache[filepath]


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
        "alert_words": "conf_alert_words.txt",
        "contacts": "conf_contacts.txt",
        "send_seprate_group": r"conf_msg_group.txt",
        "send_seprate": "1",
        "auto_reply": "1",
        "auto_reply_text": "收到，立即处置",
        "daemon_interval": "5",
        "micromsg_method": "local",
        "CORP_ID": "YOUR_CORP_ID",
        "CORP_SECRET": "YOUR_CORP_SECRET",
        "AGENT_ID": "YOUR_AGENT_ID",
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
    encoding = get_file_encoding(config_path)
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


def schedule_load(interval):
    # 定时加载配置文件
    schedule.every(interval).seconds.do(check_screen)  # 每10秒执行一次，检查屏幕
    schedule.every(60 * 20).seconds.do(clean_msg_store)  # 每20分执行一次，清除消息存储
    schedule.every(120).seconds.do(load_alert_words)  # 每120秒执行一次，加载关键词
    schedule.every(120).seconds.do(load_contacts)  # 每120秒执行一次，加载联系人
    schedule.every(3).seconds.do(run_play_music)  # 每3秒执行一次，播放报警音
    schedule.every(60 * 30).seconds.do(
        send_email_ipchg
    )  # 每30分执行一次，检查IP变化并发送邮件
    schedule.every(60 * 60).seconds.do(
        textPad_save_and_clear
    )  # 每60分执行一次，保存并清除文本编辑器内容


@new_thread
def daemon_worker():
    # 定时器
    global app_run, daemon_interval, exit_flag

    running_interval = 0
    while True:
        if exit_flag.is_set() == True:
            break

        if running_interval != daemon_interval:
            schedule.clear()
            running_interval = daemon_interval
            if running_interval < 1:
                running_interval = 1
            print("Daemon interval changed to: ", running_interval)
            # 重新加载定时任务
            schedule_load(running_interval)
        while (
            app_run == True
            and exit_flag.is_set() == False
            and running_interval == daemon_interval
        ):
            # print("Daemon running...")
            # 执行定时任务
            schedule.run_pending()
            idle = schedule.idle_seconds()
            time.sleep(max(1, idle) if idle is not None else 1)


def quit_program():
    global icon, app_run

    # 确保只执行一次退出操作
    if not hasattr(quit_program, "called"):
        quit_program.called = True
    else:
        return

    exit_flag.set()  # 设置全局事件，通知线程退出
    app_run = False  # 停止主循环

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
                f.write(item + "\n")
    except:
        pass

    # 尝试显示控制台
    try:
        if w_console:
            w_console.show()  # 显示控制台
            w_console.restore()  # 恢复窗口
    except:
        pass

    # 关闭tkinter主窗口
    try:
        if "root" in globals() and root is not None:
            # 先销毁所有Tkinter变量
            for name, var in list(root.__dict__.items()):
                if isinstance(var, (tk.Variable, tk.Widget)):
                    try:
                        var.destroy()
                    except Exception:
                        pass
            # 然后销毁主窗口
            if root.winfo_exists():
                root.quit()  # 先停止主循环
                root.destroy()  # 再销毁窗口
    except Exception:
        pass

    try:
        os._exit(0)
    except:
        pass
    try:
        sys.exit(0)
    except:
        pass


def splash_play():
    global splash
    splash = tk.Toplevel(root)

    # 窗口设置
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    width, height = 300, 200
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.overrideredirect(1)
    splash.wm_attributes("-topmost", 1)
    splash.attributes("-alpha", 0.8)
    splash.configure(bg="gray99")  # 设置窗口背景色

    # 使用Canvas而不是Label来显示，提供更多控制
    canvas = tk.Canvas(
        splash, bg="gray99", highlightthickness=0, width=width, height=height
    )
    canvas.pack(fill="both", expand=True)

    # 标题文本
    title_label = tk.Label(
        canvas, text=f"{prog_window_title}\n", font=("黑体", 12), bg="gray99"
    )
    canvas.create_window((width / 2, 30), window=title_label)

    # 创建动画容器（重要：使用Label代替Canvas创建图像）
    img_container = tk.Label(canvas, bg="gray99", bd=0)
    canvas.create_window((width / 2, height / 2), window=img_container)

    # 使用GIFLoader类加载GIF动画
    class GIFLoader:
        def __init__(self, label, gif_path):
            self.label = label
            self.gif_path = gif_path
            self.frames = []
            self.idx = 0
            self.load_gif()
            self.play()

        def load_gif(self):
            try:
                from PIL import Image, ImageTk, ImageSequence

                with open(self.gif_path, "rb") as f:
                    gif = Image.open(f)
                    # 获取GIF的循环次数（非必需，但有助于精确控制）
                    loop_count = 0
                    for item in gif.info:
                        if item == "loop":
                            loop_count = gif.info[item]
                    # 提取所有帧
                    for frame in ImageSequence.Iterator(gif):
                        frame = frame.resize((80, 80), Image.LANCZOS)
                        self.frames.append(ImageTk.PhotoImage(frame))
            except Exception as e:
                # 加载失败时使用单帧图像
                print(f"GIF加载出错: {e}")
                img = ImageTk.PhotoImage(
                    Image.open(
                        get_resource_path("./resources/image/reload.gif")
                    ).resize((80, 80), Image.LANCZOS)
                )
                self.frames = [img]

        def play(self):
            if not splash.winfo_exists() or not self.frames:
                return

            self.label.config(image=self.frames[self.idx])
            self.idx = (self.idx + 1) % len(self.frames)
            splash.after(100, self.play)  # 根据GIF帧率调整播放速度

    # 使用修正后的方法加载动画
    gif_loader = GIFLoader(img_container, "./resources/image/reload.gif")

    # 保存对动画对象的引用
    img_container.gif_loader = gif_loader

    # 底部文本
    bottom_label = tk.Label(
        canvas, text="正在加载中，请稍后...", font=("黑体", 12), bg="gray99"
    )
    canvas.create_window((width / 2, height - 30), window=bottom_label)

    # 4秒后自动关闭
    def safe_destroy():
        if splash and splash.winfo_exists():
            try:
                splash.destroy()
            except:
                pass

    splash.after(4000, safe_destroy)
    splash.lift()
    splash.update_idletasks()


# ...（程序其余部分保持不变）...


def get_resource_path(relative_path):
    if relative_path.startswith("./"):
        relative_path = relative_path[2:]
    relative_path = relative_path.replace("/", "\\")
    base_dir = ""
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.abspath(".")
    return os.path.join(base_dir, relative_path)


# 获取当前系统DPI缩放比例
_cached_dpi_scale = None


def get_dpi_scale():
    """获取当前系统DPI缩放比例，如1.0、1.25、1.5、2.0等"""
    global _cached_dpi_scale
    if _cached_dpi_scale is not None:
        return _cached_dpi_scale
    try:
        windll = ctypes.windll
        user32 = windll.user32
        hdc = user32.GetDC(0)
        dpi = windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        user32.ReleaseDC(0, hdc)
        _cached_dpi_scale = dpi / 96.0
    except Exception:
        _cached_dpi_scale = 1.0
    return _cached_dpi_scale


# 获取与当前DPI匹配的资源图片路径
_dpi_path_cache = {}


def get_resource_path_dpi(relative_path):
    """
    根据当前DPI缩放比例自动选择最匹配的资源图片。
    图片命名规则: {basename}@{scale}x.{ext}，如 toolbar_hdex_pc@1.5x.png
    找不到匹配的缩放版本时回退到基准图片（get_resource_path的结果）。
    """
    if relative_path in _dpi_path_cache:
        return _dpi_path_cache[relative_path]

    base_path = get_resource_path(relative_path)

    # 只对 resources/image 下的图片进行DPI适配
    if "resources\\image" not in base_path and "resources/image" not in relative_path:
        _dpi_path_cache[relative_path] = base_path
        return base_path

    scale = get_dpi_scale()

    # 定义需要尝试的缩放比例（从最接近到最远）
    scale_candidates = [1.0, 1.25, 1.5, 2.0, 1.75, 3.0, 2.5, 1.33]

    # 找到最接近当前缩放的可用图片
    dir_name = os.path.dirname(base_path)
    basename = os.path.basename(base_path)
    name, ext = os.path.splitext(basename)

    # 如果当前系统缩放接近1.0，直接使用基准图片，避免错用其他缩放版本
    if abs(scale - 1.0) < 0.05:
        _dpi_path_cache[relative_path] = base_path
        return base_path

    # 按与当前scale的差距排序（从小到大）
    sorted_candidates = sorted(scale_candidates, key=lambda s: abs(s - scale))

    for s in sorted_candidates:
        if s == 1.0:
            # 1.0x 就是基准图片本身，跳过不需查找
            continue
        # 只使用与当前缩放比例接近（差距不超过25%）的缩放版本
        if abs(s - scale) > 0.25:
            continue
        # 格式化缩放比例，如 1.25 -> "1.25x", 2.0 -> "2x"（去掉末尾的.0）
        scale_str = f"{s:.2f}".rstrip("0").rstrip(".") + "x"
        scaled_name = f"{name}@{scale_str}{ext}"
        scaled_path = os.path.join(dir_name, scaled_name)
        if os.path.exists(scaled_path):
            # 如果缩放比例与当前系统DPI完全匹配，直接使用
            _dpi_path_cache[relative_path] = scaled_path
            return scaled_path

    # 没有找到任何缩放版本的图片，回退到基准图片
    _dpi_path_cache[relative_path] = base_path
    return base_path


@new_thread
def systray(icon):
    while 1 == 1:
        if root == None:
            time.sleep(1)
            continue
        else:
            break
    icon.run()


def sw_console():
    global settings_window, sw_show
    # 确保主窗口存在
    if "root" in globals() and root is not None:
        if not hasattr(tk, "_default_root") or not tk._default_root:
            return
        if (
            settings_window == None
            or not tk._default_root
            or not settings_window.winfo_exists()
        ):
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
    global settings_window, sw_show, textPad, volume_label, conf_volume, scaler_volume, bt3_1, bt3_2, bt3_3, bt3_4
    # 确保主窗口存在
    if not hasattr(tk, "_default_root") or not tk._default_root:
        return None
    # 如果窗口已经存在，则直接显示
    if settings_window and settings_window.winfo_exists():
        settings_window.deiconify()
        settings_window.focus_force()
        sw_show = True
        return settings_window
    # 确保 scaler_volume 已初始化
    if not hasattr(scaler_volume, "get"):
        scaler_volume = tk.IntVar(value=conf_volume)
    # 创建新窗口
    settings_window = tk.Toplevel(root)
    settings_window.title("程序设置")
    settings_window.geometry("300x200")
    # 修改4: 窗口关闭时隐藏而非销毁
    settings_window.protocol("WM_DELETE_WINDOW", lambda: sw_console())

    settings_window.iconbitmap(
        get_resource_path("./resources/image/reload.gif")
    )  # 设置窗口图标
    screenWidth = settings_window.winfo_screenwidth()  # 获取显示区域的宽度
    screenHeight = settings_window.winfo_screenheight()  # 获取显示区域的高度
    width = 550  # 设定窗口宽度
    height = 500  # 设定窗口高度
    left = screenWidth - width - 50
    top = screenHeight - height - 150

    # 宽度x高度+x偏移+y偏移
    settings_window.geometry("%dx%d+%d+%d" % (width, height, left, top))

    settings_window.title(prog_window_title)
    # settings_window.protocol("WM_DELETE_WINDOW", quit_program)
    view_frame = tk.Frame(settings_window, bg="#f0f0f0")
    view_frame.pack(pady=5, fill=tk.BOTH, expand=True)

    tk.Label(view_frame, text=VERSION_TEXT).pack()
    textPad = tk.Text(view_frame, undo=True)
    textPad.pack(expand=tk.YES, fill=tk.BOTH)
    scroll = tk.Scrollbar(textPad)
    textPad.config(yscrollcommand=scroll.set)
    scroll.config(command=textPad.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    button_frame = tk.Frame(settings_window, bg="#f0f0f0")
    button_frame.pack(fill=tk.X, pady=5)

    label2 = tk.Label(button_frame, text="音量:").pack(side=tk.LEFT)
    """
    bt2_1 = tk.Button(button_frame, text="小", command=lambda: set_volume(0.2)).pack(side=tk.LEFT)
    bt2_2 = tk.Button(button_frame, text="中", command=lambda: set_volume(0.5)).pack(side=tk.LEFT)
    bt2_3 = tk.Button(button_frame, text="大", command=lambda: set_volume(1)).pack(side=tk.LEFT)
    """
    # 创建滑块组件
    slider = ttk.Scale(
        button_frame,
        from_=0,  # 最小值
        to=100,  # 最大值
        orient=tk.HORIZONTAL,  # 水平方向
        length=100,  # 滑块长度
        command=set_volume,  # 值变化时的回调函数
        variable=scaler_volume,  # 绑定到变量
    )
    slider.pack(side=tk.LEFT, padx=5)
    set_volume(50)  # 设置初始音量为50%
    # 显示当前值的标签
    volume_label = ttk.Label(button_frame, text=f"{int(scaler_volume.get())}%")
    volume_label.pack(side=tk.LEFT, padx=5)
    bt2 = tk.Button(button_frame, text="试", command=play_test_sound).pack(
        side=tk.LEFT, padx=5
    )
    label3 = tk.Label(button_frame, text="监视间隔:").pack(side=tk.LEFT, padx=10)
    bt3_1 = tk.Button(button_frame, text="5", command=lambda: set_daemon_interval(5))
    bt3_1.pack(side=tk.LEFT, padx=2)  # 必须分行pack 否则会返回None导致无法调用按钮对象
    bt3_2 = tk.Button(button_frame, text="10", command=lambda: set_daemon_interval(10))
    bt3_2.pack(side=tk.LEFT, padx=2)  # 必须分行pack 否则会返回None导致无法调用按钮对象
    bt3_3 = tk.Button(button_frame, text="15", command=lambda: set_daemon_interval(15))
    bt3_3.pack(side=tk.LEFT, padx=2)  # 必须分行pack 否则会返回None导致无法调用按钮对象
    bt3_4 = tk.Button(button_frame, text="20", command=lambda: set_daemon_interval(20))
    bt3_4.pack(side=tk.LEFT, padx=2)  # 必须分行pack 否则会返回None导致无法调用按钮对象
    set_daemon_interval(daemon_interval)  # 设置初始监视间隔
    button_frame2 = tk.Frame(settings_window, bg="#f0f0f0")
    button_frame2.pack(fill=tk.X, pady=5)
    label4 = tk.Label(button_frame2, text="控制:").pack(side=tk.LEFT)
    bt1 = tk.Button(
        button_frame2, text="启动监视!", command=lambda: set_daemon_permit("on")
    ).pack(side=tk.LEFT)
    bt2 = tk.Button(
        button_frame2, text="消音!", command=lambda: set_alert_permit("off")
    ).pack(side=tk.LEFT)
    bt3 = tk.Button(
        button_frame2, text="停止监视!", command=lambda: set_daemon_permit("off")
    ).pack(side=tk.LEFT)
    label4 = tk.Label(button_frame2, text=" ").pack(side=tk.LEFT)
    bt4 = tk.Button(button_frame2, text="退出程序!", command=quit_program).pack(
        side=tk.LEFT
    )

    settings_window.attributes("-topmost", True)
    settings_window.after_idle(settings_window.attributes, "-topmost", False)
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
    prog_window_title = "桌面关键字监视器"
    root = None  # 初始化tkinter主窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    splash = ""
    splash_play()
    # 读取配置文件-关键词分组
    msg_group = load_msg_groups()

    # 全局事件，用于通知线程退出
    exit_flag = threading.Event()
    # 事件队列
    ui_queue = queue.Queue()

    icon, textPad = "", ""
    try:
        w_title = "Screen OCR Watchdog"  # 控制台窗口标题 通过 title 命令在bat文件中设置
        w_console = pygetwindow.getWindowsWithTitle(w_title)[0]
        w_console.minimize()  # 最小化窗口
        w_console.hide()  # 隐藏窗口
    except:
        pass
    import argparse

    parser = argparse.ArgumentParser(description="桌面关键字监视器")
    parser.add_argument(
        "--UseSerial",
        type=str,
        default="no",
        required=False,
        help="是否启用串口发送功能",
    )
    # required = False 只能用于可选参数。 对于可选参数，应该使用 - -，如果没有 - -，python 会将其视为位置参数。
    args = parser.parse_args()

    last_sent_seprate = ""
    alert_msg = []
    img_md5_list = deque()
    img_md5_set = set()
    if os.path.exists("img_md5_list.txt") == True:
        with open("img_md5_list.txt", "r", encoding="utf-8") as f:
            for line in f.readlines():
                md5 = line.strip()
                if md5 and md5 not in img_md5_set:
                    img_md5_set.add(md5)
                    img_md5_list.append(md5)
    w_left, w_top = 0, 0
    debug = False
    log_path = "./logs"
    os.makedirs(log_path, exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)
    sheduler = loguru.logger.add(
        log_path + "\\padocr-watchdog.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        encoding="utf-8",
    )
    config = configparser.ConfigParser()  # 类实例化

    # 定义文件路径
    configpath = r".\setup.ini"
    prepare_conf_file(configpath)
    (
        daemon_interval,
        alert_mp3_file,
        conf_wxmsg,
        conf_email,
        ocr_method,
        ocr_detail,
        conf_app_name,
        window_title,
        conf_serial,
        send_snapshot,
        send_seprate,
        auto_reply,
        auto_reply_text,
    ) = get_conf_from_file(
        configpath,
        "config",
        [
            "daemon_interval",
            "alert_mp3_file",
            "send_wxmsg",
            "send_email",
            "ocr_method",
            "ocr_detail",
            "app_name",
            "window_title",
            "send_serial",
            "send_snapshot",
            "send_seprate",
            "auto_reply",
            "auto_reply_text",
        ],
    )
    if conf_app_name == "e行pc" or conf_app_name == "e行PC":
        window_title = "华电e行"
        conf_app_name = "e行PC"  # 统一为标准格式
    daemon_interval = int(daemon_interval)
    print("daemon_interval:", daemon_interval)
    alert_mp3_file = alert_mp3_file.strip()

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
        # 如果配置为0，检查命令行参数是否覆盖
        if args.UseSerial == "yes":
            conf_serial = True
        else:
            conf_serial = False
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
        email_queue = queue.Queue()
        process_email_queue(email_queue)
    if conf_wxmsg == True:
        (
            micromsg_method,
            corp_id,
            corp_secret,
            agent_id,
            wxmsg_url_get,
            wxmsg_url_post,
            wxmsg_method,
            secret_seed,
            wxmsg_touser,
        ) = get_conf_from_file(
            configpath,
            "micromsg",
            [
                "method",
                "CORP_ID",
                "CORP_SECRET",
                "AGENT_ID",
                "wxmsg_url_get",
                "wxmsg_url_post",
                "wxmsg_method",
                "secret_seed",
                "wxmsg_touser",
            ],
        )
        if micromsg_method == "local":
            message_queue = queue.Queue()
            wxlocal_config = {
                "CORP_ID": corp_id,
                "CORP_SECRET": corp_secret,
                "AGENT_ID": agent_id,
            }
            sender_thread = MessageSender(wxlocal_config)
            sender_thread.daemon = True
            sender_thread.start()
        elif micromsg_method == "server":
            pass
        else:
            loguru.logger.error(
                "micromsg_method must be 'local' or 'server',please check your config file."
            )
        if wxmsg_method == "GET":
            wxmsg_url = wxmsg_url_get
        else:
            wxmsg_url = wxmsg_url_post
    if conf_serial == True:
        import serial
        import serial.tools.list_ports
        import xmodem

        serialdev = get_conf_from_file(configpath, "serial", ["serialdev_in"])

        serial_opened = False

    alert_words, alert_groups = load_alert_words()

    contacts = load_contacts()
    app_run = True
    alert_permit = False
    daemon_permit = False

    serial_daemon()
    daemon_worker()

    menu_options = pystray.Menu(
        pystray.MenuItem("启动监视!", lambda: set_daemon_permit("on")),
        pystray.MenuItem("停止监视!", lambda: set_daemon_permit("off")),
        pystray.MenuItem("消音!", lambda: set_alert_permit("off")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("控制台", sw_console),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", quit_program),
    )
    icon = pystray.Icon(
        name="桌面关键字监视器",
        icon=Image.open(get_resource_path("./resources/image/reload.gif")),
        menu=menu_options,
        on_quit=quit_program,
    )

    systray(icon)
    """创建隐藏的tkinter主窗口"""

    try:
        splash.destroy()
    except:
        pass
    conf_volume = 50  # 初始化音量变量
    scaler_volume = None  # 初始化音量滑块变量
    volume_label = None  # 初始化音量标签
    bt3_1 = None  # 初始化按钮变量
    bt3_2 = None  # 初始化按钮变量
    bt3_3 = None  # 初始化按钮变量
    bt3_4 = None  # 初始化按钮变量
    # 修改1: 定义全局状态变量
    settings_window = None  # 确保settings_window是全局变量
    sw_show = False  # False表示隐藏，True表示显示
    # 延迟启动设置窗口，确保主循环已启动
    root.after(100, sw_console)
    root.protocol("WM_DELETE_WINDOW", sw_console)  # 确保关闭窗口时调用sw_console

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
    if icon and hasattr(icon, "stop"):
        icon.stop()
