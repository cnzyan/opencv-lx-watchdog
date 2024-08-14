import serial
import xmodem
import time
import loguru
import os
import configparser
import chardet
import json
import threading
import smtplib
import schedule
import base64,hashlib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


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
        if type(mail) == str:
            mail = mail.strip()
            if maillist == "":
                maillist = maillist + mail
            else:
                maillist = maillist + "," + mail
        else:
            for mail1 in mail:
                mail1 = mail1.strip()
                if maillist == "":
                    maillist = maillist + mail1
                else:
                    maillist = maillist + "," + mail1
    # print(maillist)
    message["To"] = maillist
    message["Cc"] = ""
    message["Bcc"] = ""

    # 设置html格式参数
    content = str(content)
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
        loguru.logger.info("邮件发送成功")
        return True
    except Exception as e:
        loguru.logger.error("邮件发送失败" + str(e))
        return False


def send_wxmsg(wxmsg_content):  # 发送微信消息
    import requests
    import json
    pass


def addtwodimdict(thedict, key_a, key_b, val):
    if key_a in thedict:
        thedict[key_a].update({key_b: val})
    else:
        thedict.update({key_a: {key_b: val}})


def serial_send(type, temp_data):  # 串口发送数据

    # 扫描端口
    # result = check_uart_port()
    result = True
    if (result == False):
        return

    # 打开串口
    port = serialdev.split(',')[0]
    bps = int(serialdev.split(',')[1])
    timeout = int(serialdev.split(',')[2])
    result = open_uart(port, bps, timeout)
    if (result == False):
        return
    else:
        uart1 = result

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
        print("can not open uart")
        print(result)
        return False


def uart_send_data(uart, txbuf):  # 发送数据
    len = uart.write(txbuf.encode('utf-8'))  # 写数据
    return len


def uart_receive_data(uart):  # 接收数据
    global rt_data_recv_flag
    global report_email_waiting
    global recv_file
    # 定义YMODEM接收函数
    filepath = 'recv_files'
    if not os.path.isdir(filepath):
        # 创建文件夹
        os.mkdir(filepath)

    def recv_ymodem(filename):
        def getc(size, timeout=1):
            return uart.read(size) or None

        def putc(data, timeout=1):
            return uart.write(data)
        modem = xmodem.XMODEM(getc, putc)
        with open(filepath+'\\'+filename, "wb") as f:
            status = modem.recv(f)
        with open(filepath+'\\'+filename, 'rb') as f:
            file_content = f.read()

        # 倒序文件内容
        reversed_content = bytes(file_content[::-1])
        # print(reversed_content)
        reversed_realdata = bytearray()
        # 去除多余的 \b1A
        is_head = 1
        for byte in reversed_content:
            # print((byte))
            if str(byte) == '26' and is_head == 1:
                pass
            else:
                is_head = 0
                reversed_realdata.append(byte)
        reversed_realdata = bytes(reversed_realdata)
        realdata = reversed_realdata[::-1]
        # 打开输出文件，以二进制写模式打开
        with open(filepath+'\\'+filename, 'wb') as f:
            # 写入倒序后的内容到输出文件
            f.write(realdata)

        return status

    if uart.in_waiting:
        rxdata = uart.read(uart.in_waiting).decode("utf-8")   # 以字符串接收
        # rxdata = uart.read().hex()  # 以16进制(hex)接收
        # print(rxdata)  # 打印数据
        if 1 == 1:
            try:
                response = json.loads(rxdata)
                resp_cmd = response['c']
            except Exception as e:
                resp_cmd = "e"
                pass

            if resp_cmd == "b":
                rt_data_recv_flag = 'waiting'
                temp_rt_data = []
                pass
            if resp_cmd == "d":
                temp_rt_data.append([response['iv']['t'], response['iv']['v']])
            if resp_cmd == "e":
                rt_data_recv_flag = 'ok'
                pass
            if resp_cmd == "f":
                # 接收文件并保存
                status = recv_ymodem(response['fn'])
                report_email_waiting = 1
                recv_file = [response['fn']]
                if status:
                    print(f"文件接收成功：{response['fn']}")
                else:
                    print(f"文件接收失败：{response['fn']}")
            if resp_cmd == "email" or resp_cmd == "emb64":
                recv_data = response['data']    # 接收数据
                recv_hash = response['hash']    # 接收数据hash
                if hashlib.md5(recv_data.encode()).hexdigest() == recv_hash:
                    if resp_cmd == "email":
                        email_receivers_this=email_receivers
                    if resp_cmd == "emb64":
                        pass
                    if recv_data != "":
                        if recv_data in recv_msgs:
                            pass
                        else:
                            recv_msgs.append(recv_data)
                            if resp_cmd == "email":
                                email_content=recv_data
                            if resp_cmd == "emb64":
                                pass
                            if response['num'] == "1":
                                send_email(
                                    "ALERTonSerial",
                                    email_content,
                                    email_receivers_this,
                                    smtp_host,
                                    smtp_port,
                                    mail_user,
                                    mail_pass,
                                    sender_email,
                                    smtptype,
                                )
                            else:
                                report_email_waiting = 1
                                addtwodimdict(
                                    temp_recv_msg, response['timestamp'], 'num', response['num'])
                                if resp_cmd=="email":
                                    addtwodimdict(
                                        temp_recv_msg, response['timestamp'], 'type', 'email')
                                    addtwodimdict(
                                        temp_recv_msg, response['timestamp'], 'tomail', email_receivers_this)
                                if resp_cmd=="emb64":
                                    addtwodimdict(
                                        temp_recv_msg, response['timestamp'], 'type', 'emb64')
                                addtwodimdict(
                                    temp_recv_msg, response['timestamp'], response['index'], recv_data)

                                pass
                    loguru.logger.info("Hash校验成功"+response['timestamp']+":No."+response['index']+"of"+response['num'])
                else:
                    # hash校验失败
                    loguru.logger.error("Hash校验失败"+response['timestamp']+":No."+response['index']+"of"+response['num'])
                    pass

            if resp_cmd == "wxmsg":
                wxmsg_content = response['data']
                if wxmsg_content != "":
                    send_wxmsg(wxmsg_content)
                    pass

                pass
        try:
            pass
        except Exception as e:
            pass


def close_uart(uart):  # 关闭串口
    uart.close()


def prepare_conf_file(configpath):  # 准备配置文件
    if os.path.isfile(configpath) == True:
        pass
    else:
        config.add_section("config")
        config.set("config", "alert_mp3_file", r"alert.mp3")
        config.set("config", "send_wxmsg", r"1")
        config.set("config", "send_email", r"1")
        config.set("config", "send_serial", r"1")

        config.add_section("Email")
        config.set("Email", "smtp_host", r"smtp.qq.com")
        config.set("Email", "smtp_port", r"465")
        config.set("Email", "mail_user", r"cnzyan@qq.com")
        config.set("Email", "mail_pass", r"omxjtlivotdgbici")
        config.set("Email", "sender_email", r"cnzyan@qq.com")
        config.set("Email", "email_receivers", r"cnzyan@qq.com")
        config.set("Email", "smtptype", r"SSL")

        config.add_section("micromsg")
        config.set(
            "micromsg", "wxmsg_url_get", r"http://pi.tzxy.cn/pi/app/wxadminsiteerr.asp"
        )
        config.set(
            "micromsg", "wxmsg_url_post", r"https://pi.tzxy.cn/PI/app/overlimwx.php"
        )
        config.set("micromsg", "wxmsg_method", r"POST")
        config.set("micromsg", "secret_seed", r"crazyan")
        config.set("micromsg", "wxmsg_touser", r"crazyan|XinFeng|DingXin")

        config.add_section("serial")
        config.set("serial", "serialdev_out", r"COM1,9600,1")

        # write to file
        config.write(open(configpath, "w"))
        pass
    pass


def get_conf_from_file(config_path, config_section, conf_list):  # 读取配置文件
    conf_default = {
        "alert_mp3_file": "alert.mp3",
        "send_wxmsg": "1",
        "send_email": "1",
        "send_serial": "0",

        "wxmsg_url_get": "http://pi.tzxy.cn/pi/app/wxadminsiteerr.asp",
        "wxmsg_url_post": "https://pi.tzxy.cn/PI/app/overlimwx.php",
        "wxmsg_method": "POST",
        "secret_seed": "crazyan",
        "wxmsg_touser": "crazyan|XinFeng|DingXin",
        "smtp_host": "smtp.qq.com",
        "smtp_port": "465",
        "mail_user": "cnzyan@qq.com",
        "mail_pass": "omxjtlivotdgbici",
        "sender_email": "cnzyan@qq.com",
        "smtptype": "SSL",
        "email_receivers": "cnzyan@qq.com",

        "serialdev_out": "COM1,9600,1",
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


class myThread (threading.Thread):   # 继承父类threading.Thread
    def __init__(self, uart):
        threading.Thread.__init__(self)
        self.uart = uart

    def run(self):                   # 把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        while True:
            # print("thread_uart_receive")
            uart_receive_data(self.uart)  # 接收数据
            # time.sleep(0.01)


def serial_recv():  # 串口接收数据
    # 扫描端口
    result = check_uart_port()
    # result = True
    if (result == False):
        return

    # 打开串口
    port = serialdev.split(',')[0]
    bps = int(serialdev.split(',')[1])
    timeout = int(serialdev.split(',')[2])
    result = open_uart(port, bps, timeout)
    if (result == False):
        print("Serial Open Failed.Pls Check Occupation.")
        return
    else:
        uart1 = result

    # 创建一个线程用来接收串口数据
    thread_uart = myThread(uart1)
    thread_uart.start()

    pass


@new_thread
def s2e_worker():
    try:
        serial_recv_thread = threading.Thread(target=serial_recv)
        serial_recv_thread.start()
    except Exception as e:
        print("Error: unable to start thread, try again.")
        time.sleep(1)
        s2e_worker()
    pass


def clean_msg_store():
    global recv_msgs,temp_recv_msg,report_email_waiting
    if report_email_waiting == 0:
        recv_msgs = []
        temp_recv_msg={}


def email_daemon():
    global temp_recv_msg
    global report_email_waiting
    global recv_file
    global recv_msgs
    global temp_recv_msg
    if report_email_waiting == 1:
        try:
            for key in list(temp_recv_msg.keys()):
                if temp_recv_msg[key]['num'] == '1':
                    if temp_recv_msg[key]['type'] == 'email':
                        email_content_this=temp_recv_msg[key]['1']
                        email_content_this=base64.b64decode(email_content_this).decode()
                        email_receivers_this=temp_recv_msg[key]['tomail']
                    if temp_recv_msg[key]['type'] == 'emb64':
                        
                        email_data =base64.b64decode(temp_recv_msg[key]['1']).decode()
                        email_data = json.loads(email_data)
                        email_receivers_this = email_data['tomail']
                        email_content =base64.b64decode(email_data['content']).decode()
                    send_email(
                        "ALERTonSerial",
                        email_content_this,
                        email_receivers_this,
                        smtp_host,
                        smtp_port,
                        mail_user,
                        mail_pass,
                        sender_email,
                        smtptype,
                    )
                    report_email_waiting = 0
                    temp_recv_msg = {}
                else:
                    email_content = ''
                    content_complete = 0
                    max_num = int(temp_recv_msg[key]['num'])
                    for key2 in temp_recv_msg[key].keys():
                        if key2 not in ['num','type','tomail']:
                            if int(key2) == max_num:
                                content_complete = 1
                                pass
                    for key2 in (range(1, max_num+1)):
                        if key2 not in ['num','type','tomail']:
                            try:
                                email_content = email_content + \
                                    temp_recv_msg[key][str(key2)]
                            except Exception as e:
                                email_content=email_content+'MDAwMDAwMDA'*300
                                
                    if content_complete == 1:
                        if temp_recv_msg[key]['type'] == 'email':
                            email_content_this=email_content
                            email_content_this=base64.b64decode(email_content_this).decode()
                            email_receivers_this=temp_recv_msg[key]['tomail']
                        if temp_recv_msg[key]['type'] == 'emb64':
                            
                            email_data =base64.b64decode(email_content).decode()
                            email_data = json.loads(email_data)
                            email_receivers_this = email_data['tomail']
                            email_content_this =base64.b64decode(email_data['content']).decode()
                        try:
                            send_email(
                                "ALERTonSerial",
                                email_content_this,
                                email_receivers_this,
                                smtp_host,
                                smtp_port,
                                mail_user,
                                mail_pass,
                                sender_email,
                                smtptype,
                            )
                            temp_recv_msg.pop(key)
                        except Exception as e:
                            loguru.logger.error("Send email error."+str(e))
            
            if temp_recv_msg == {}:
                report_email_waiting = 0
        except Exception as e:
            loguru.logger.error("Send email error."+str(e))


if __name__ == "__main__":
    config = configparser.ConfigParser()  # 类实例化
    recv_msgs = []
    temp_recv_msg = {}
    report_email_waiting = 0
    log_path = './logs'
    if not os.path.isdir(log_path):
        # 创建文件夹
        os.mkdir(log_path)
    sheduler = loguru.logger.add(
        log_path+"\\padocr-seiral-out.log", rotation="1 day", retention="7 days", level="INFO", encoding="utf-8"
    )
    # 定义文件路径
    configpath = r".\setup.ini"
    prepare_conf_file(configpath)
    alert_mp3_file, conf_wxmsg, conf_email, conf_serial = (
        get_conf_from_file(
            configpath,
            "config",
            [
                "alert_mp3_file",
                "send_wxmsg",
                "send_email",
                "send_serial",
            ],
        )
    )
    if conf_wxmsg == "1":
        conf_wxmsg = True
    else:
        conf_wxmsg = False
    if conf_email == "1":
        conf_email = True
    else:
        conf_email = False
    if conf_serial == "1":
        conf_serial = True
    else:
        conf_serial = False
    if conf_email == True:
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
            configpath, 'serial', ['serialdev_out'])

    s2e_worker()
    schedule.every(5).seconds.do(email_daemon)  # 每5秒执行一次
    schedule.every(300).seconds.do(clean_msg_store)  # 每300秒执行一次
    while True:
        schedule.run_pending()
        time.sleep(1)
