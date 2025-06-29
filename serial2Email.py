import serial
import serial.tools.list_ports
import xmodem
import time
import loguru
import os
import configparser
import chardet
import json
import threading
import smtplib
# import schedule
import base64
import hashlib
import signal
from queue import Queue
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import defaultdict
# 全局变量初始化
keep_running = True
thread_list = []
global_uart = None
stop_event = threading.Event()
recv_msgs = []
temp_recv_msg = {}

completed_emails = {}
last_clean_time = time.time()
report_email_waiting = 0
recv_file = []
rt_data_recv_flag = 'idle'
emr = 0

# 全局缓冲区管理
data_buffers = defaultdict(str)  # 按时间戳组织的缓冲区
fragment_buffer = ""             # 分段数据缓冲区
partial_json_buffer = ""         # 部分JSON缓冲区

# 在全局变量部分添加
pending_emails = {}
email_daemon_active = threading.Event()
email_send_lock = threading.Lock()


def new_thread(func):
    from functools import wraps
    import threading

    @wraps(func)
    def inner(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        thread_list.append(thread)
    return inner


def extract_json_objects(text):
    """从文本中提取完整的JSON对象"""
    objects = []
    stack = 0
    start_index = 0
    in_string = False

    for i, char in enumerate(text):
        # 处理字符串中的转义字符
        if in_string:
            if char == '\\':
                i += 1  # 跳过下一个字符
            elif char == '"':
                in_string = False
            continue

        # 正常处理字符
        if char == '"':
            in_string = True
        elif char == '{':
            if stack == 0:
                start_index = i
            stack += 1
        elif char == '}':
            if stack > 0:
                stack -= 1
                if stack == 0:
                    # 尝试提取完整对象
                    try:
                        json_str = text[start_index:i+1]
                        obj = json.loads(json_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        # 即使结构上完整但内容无效
                        pass

    # 返回完整对象和剩余文本
    last_index = start_index if stack > 0 else len(text)
    return objects, text[last_index:]


def uart_receive_data(uart):
    """改进的串口数据处理 - 处理分段传输"""
    global fragment_buffer, partial_json_buffer, data_buffers

    try:
        # 检查串口状态
        if uart is None or not uart.is_open or not uart.in_waiting:
            return

        # 读取所有可用数据
        new_data = uart.read(uart.in_waiting).decode("utf-8", errors='replace')
        if not new_data:
            return

        # 添加到片段缓冲区
        fragment_buffer += new_data
        loguru.logger.debug(f"累积数据: {len(fragment_buffer)}字符")

        # 尝试提取所有可能的JSON对象
        json_objects, fragment_buffer = extract_json_objects(fragment_buffer)

        # 处理每个提取到的JSON对象
        for obj in json_objects:
            resp_cmd = obj.get('c', 'unknown')
            timestamp = obj.get('timestamp', 'default')
            loguru.logger.info(f"解析到命令: {resp_cmd} (ID: {timestamp})")

            # 处理邮件命令
            if resp_cmd in ["email", "emb64"]:
                process_email_command(obj, resp_cmd)
            else:
                # 处理其他命令
                if resp_cmd == "e":
                    loguru.logger.info(f"命令接收: {resp_cmd}")
                    fragment_buffer = ""
                pass
        # 处理未完成的JSON (长度超过阈值)
        if len(fragment_buffer) > 400000000:  # 设置最大缓冲区大小
            loguru.logger.warning(f"长时间未完成JSON: {fragment_buffer[:50]}...")
            fragment_buffer = ""  # 防止无限增长

    except (OSError, serial.serialutil.SerialException) as e:
        loguru.logger.error(f"串口读取错误: {str(e)}")
        handle_serial_error()
    except Exception as e:
        loguru.logger.exception(f"数据处理异常: {str(e)}")
        fragment_buffer = ""  # 重置缓冲区以防错误


def process_email_command(response, cmd_type):
    """处理邮件命令 - 修复触发逻辑"""
    global pending_emails, email_receivers, report_email_waiting

    # 提取关键字段
    recv_data = response.get('data', '')
    recv_hash = response.get('hash', '')
    timestamp = response.get('timestamp', str(time.time()))
    index = response.get('index', '1')
    total_parts = response.get('num', '1')

    # 验证完整性
    if not recv_data or not recv_hash:
        loguru.logger.warning("邮件命令缺失必要字段")
        return

    # 计算并验证哈希
    computed_hash = hashlib.md5(recv_data.encode()).hexdigest()
    if computed_hash != recv_hash:
        loguru.logger.error(f"Hash校验失败 {timestamp}: {index}/{total_parts}")
        recv_data = 'MDAwMDAwMDA'*300
        # return

    loguru.logger.info(f"Hash校验成功 {timestamp}: {index}/{total_parts}")

    # 邮件内容处理
    with email_send_lock:
        # 确保初始化时间戳条目
        if timestamp not in pending_emails:
            pending_emails[timestamp] = {
                'parts': {},
                'type': cmd_type,
                'receivers': email_receivers,
                'timestamp': time.time(),
                'total_parts': int(total_parts)
            }

        # 存储当前部分
        pending_emails[timestamp]['parts'][index] = recv_data
        loguru.logger.info(f"存储邮件部分 {timestamp}: {index}/{total_parts}")

        if int(index) == 1:
            loguru.logger.info(
                f"邮件接收开始 {timestamp} ({len(pending_emails[timestamp]['parts'])}/{total_parts})")
        if int(index) == int(total_parts):
            loguru.logger.info(
                f"邮件接收结束 {timestamp} ({len(pending_emails[timestamp]['parts'])}/{total_parts})")
            # 检查是否完整
            if len(pending_emails[timestamp]['parts']) == int(total_parts):
                report_email_waiting = 1
                loguru.logger.info(f"邮件接收完成 {timestamp}")
                # 直接触发处理而不等待守护进程
                process_completed_email(timestamp)
            else:
                loguru.logger.warning(
                    f"邮件 {timestamp} 部分接收不完整 ({len(pending_emails[timestamp]['parts'])}/{total_parts})")
                for i in range(1, int(total_parts) + 1):
                    if i not in pending_emails[timestamp]['parts'] and str(i) not in pending_emails[timestamp]['parts']:
                        loguru.logger.warning(f"缺失部分: {i} (总计: {total_parts})")
                        # 填充缺失部分
                        pending_emails[timestamp]['parts'][index] = 'MDAwMDAwMDA'*300


@new_thread
def process_completed_email(timestamp):
    """处理完整的邮件并立即发送"""
    global pending_emails

    if timestamp not in pending_emails:
        loguru.logger.error(f"ID {timestamp} 不在待处理邮件中")
        return

    email_data = pending_emails[timestamp]

    # 组合所有部分
    # sorted_indices = sorted(email_data['parts'].keys(),key=lambda x: int(x['index']))
    combined_data = ''.join(email_data['parts'][idx]
                            for idx in email_data['parts'])

    # 处理不同类型邮件
    if email_data['type'] == "email" or email_data['type'] == "emb64":
        try:
            # Base64解码
            decoded_data = base64.b64decode(combined_data).decode()
            decoded_data = decoded_data.strip().replace('\'', '"')  # 替换单引号为双引号,避免 JSON 解析错误
            try:
                # 尝试解析为JSON
                email_info = json.loads(decoded_data)
                email_content = email_info.get('content', '')
                email_content = base64.b64decode(email_content).decode()
                receivers = email_info.get('tomail', email_data['receivers'])
                loguru.logger.info("使用JSON解析的邮件数据")
            except json.JSONDecodeError:
                # 直接使用解码文本
                email_content = decoded_data
                receivers = email_data['receivers']
                loguru.logger.info("使用直接文本邮件数据")
        except Exception as e:
            loguru.logger.error(f"Base64解码失败: {str(e)}")
            del pending_emails[timestamp]
            return

    # 发送邮件
    if email_content and receivers:
        loguru.logger.info(f"准备发送邮件: {timestamp}")
        try:
            send_done = send_email(
                "ALERTonSerial",
                email_content,
                receivers,
                smtp_host,
                smtp_port,
                mail_user,
                mail_pass,
                sender_email,
                smtptype,
            )
            loguru.logger.info(f"邮件发送成功: {timestamp}")
            # 记录已完成的邮件
            completed_emails[timestamp] = {
                'content': email_content,
                'receivers': receivers,
                'timestamp': time.time()
            }
        except Exception as e:
            loguru.logger.error(f"发送邮件时发生异常: {str(e)}")

    # 清理已处理的邮件
    else:
        loguru.logger.warning(f"邮件内容或收件人为空: {timestamp}")
    del pending_emails[timestamp]


def signal_handler(sig, frame):
    """处理Ctrl+C信号"""
    global keep_running
    loguru.logger.info("接收到退出信号，开始优雅退出...")
    keep_running = False
    stop_event.set()

    # 关闭串口资源
    if global_uart and global_uart.is_open:
        try:
            global_uart.close()
            loguru.logger.info("串口已关闭")
        except Exception as e:
            loguru.logger.error(f"关闭串口时出错: {str(e)}")

    # 等待所有线程结束
    for t in thread_list:
        if t.is_alive():
            t.join(timeout=2.0)

    loguru.logger.info("程序已退出")
    os._exit(0)


def put_email_queue(message,
                    smtp_host,
                    smtp_port,
                    mail_user,
                    mail_pass,
                    smtptype):
    """
    创建一个邮件队列
    """
    delay = 0
    email_queue.put((message,
                    smtp_host,
                    smtp_port,
                    mail_user,
                    mail_pass,
                    smtptype, delay))


@new_thread
def process_email_queue(email_queue):
    loguru.logger.info("邮件队列处理线程已启动")
    while keep_running and not stop_event.is_set():
        if email_queue.empty():
            # loguru.logger.info("邮件队列为空，等待新任务")
            time.sleep(1)
            continue
        message, smtp_host, smtp_port, mail_user, mail_pass, smtptype, delay = email_queue.get()
        re_put = False
        if delay == 0:
            if send_mail(message,
                         smtp_host,
                         smtp_port,
                         mail_user,
                         mail_pass,
                         smtptype):
                pass
            else:
                delay = 10  # 如果发送失败，延迟60秒重试
                loguru.logger.error("邮件发送失败，延迟10秒重试")
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
            email_queue.put((message,
                             smtp_host,
                             smtp_port,
                             mail_user,
                             mail_pass,
                             smtptype, delay))


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
):
    """发送邮件功能"""
    loguru.logger.info(f"准备发送邮件: {Subject}")

    # 创建邮件对象
    message = MIMEMultipart()
    message["From"] = sender_email

    # 处理多种格式的收件人列表
    if isinstance(tomail, str):
        tomail_list = [addr.strip() for addr in tomail.split(",")]
    elif isinstance(tomail, (list, tuple)):
        tomail_list = tomail
    else:
        loguru.logger.error(f"无效的收件人格式: {type(tomail)}")
        return False

    # 去除空地址
    tomail_list = [addr for addr in tomail_list if addr.strip()]
    if not tomail_list:
        loguru.logger.error("未提供有效的收件人地址")
        return False

    # 设置收件人字段
    message["To"] = ", ".join(tomail_list)
    loguru.logger.info(f"邮件收件人: {tomail_list}")

    # 设置主题并添加内容
    message["Subject"] = Subject
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8")
        except:
            loguru.logger.warning("邮件内容解码失败，尝试原始字节数据")

    part1 = MIMEText(str(content), "html", "utf-8")
    message.attach(part1)

    # 发送邮件
    return put_email_queue(message,
                           smtp_host,
                           smtp_port,
                           mail_user,
                           mail_pass,
                           smtptype)


def send_mail(
    message, smtp_host, smtp_port, user=None, passwd=None, security=None
):
    """邮件发送实现"""
    try:
        # 创建SMTP连接
        if security == "SSL":
            s = smtplib.SMTP_SSL(smtp_host, smtp_port)
            loguru.logger.debug("使用SSL安全连接")
        else:
            s = smtplib.SMTP(smtp_host, smtp_port)
            loguru.logger.debug("使用不加密连接")

        # 设置调试级别
        s.set_debuglevel(0)

        # 发送EHLO
        s.ehlo()

        # 处理TLS加密
        if security == "TLS":
            loguru.logger.info("启动TLS加密...")
            s.starttls()
            s.ehlo()
            loguru.logger.debug("TLS握手成功")

        # 认证处理
        if user and passwd:
            s.login(user, passwd)
            loguru.logger.debug("登录成功")
        else:
            loguru.logger.warning("未提供SMTP登录凭证")

        # 准备收件人列表
        to_addr_list = []

        # 处理To字段
        if message["To"]:
            for addr in message["To"].split(","):
                to_addr_list.append(addr.strip())

        # 去重和清理
        to_addr_list = list(set([addr for addr in to_addr_list if addr]))

        # 发送邮件
        s.sendmail(message["From"], to_addr_list, message.as_string())
        loguru.logger.info("邮件已成功发送")
        return True

    except smtplib.SMTPException as e:
        loguru.logger.error(f"SMTP协议错误: {str(e)}")
    except OSError as e:
        loguru.logger.error(f"网络错误: {str(e)}")
    except Exception as e:
        loguru.logger.exception(f"发送邮件时发生未处理的异常: {str(e)}")

    loguru.logger.error("邮件发送失败")
    return False


def send_wxmsg(wxmsg_content):
    """发送微信消息（空实现）"""
    loguru.logger.warning("微信消息发送功能尚未实现")
    return True


def addtwodimdict(thedict, key_a, key_b, val):
    if key_a in thedict:
        thedict[key_a].update({key_b: val})
    else:
        thedict.update({key_a: {key_b: val}})


def serial_send(type, temp_data):
    """串口发送数据"""
    global global_uart

    # 扫描端口
    if not global_uart or not global_uart.is_open:
        loguru.logger.error("串口未打开，无法发送数据")
        return

    uart1 = global_uart

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

    # 发送起始信号
    for _ in range(3):
        txbuf = '{"c":"b","iv":{}}'
        try:
            uart_send_data(uart1, txbuf)
            loguru.logger.info(f"发送开始信号: {txbuf}")
        except Exception as e:
            loguru.logger.error(f"发送开始信号失败: {str(e)}")
        time.sleep(0.001)

    # 发送数据
    if type == "rt":
        for item in temp_data:
            txbuf = '{"c":"rtd","iv":{"t":"' + \
                str(item[0]) + '","v":"' + str(item[1]) + '\"}}'
            try:
                uart_send_data(uart1, txbuf)
                loguru.logger.info(f"发送实时数据: {txbuf}")
            except Exception as e:
                loguru.logger.error("发送实时数据失败: " + str(e))

    elif type == "file":
        fn = (temp_data.replace("\\", "/").split("/"))[-1]
        txbuf = '{"c":"f","fn":"'+fn+'","fs":""}'
        try:
            uart_send_data(uart1, txbuf)
            loguru.logger.info(f"发送文件元数据: {txbuf}")

            # 发送文件
            status = send_ymodem(temp_data)
            if status:
                loguru.logger.info(f"文件发送成功: {temp_data}")
            else:
                loguru.logger.error(f"文件发送失败: {temp_data}")
        except Exception as e:
            loguru.logger.error("发送文件元数据失败: " + str(e))

    # 发送结束信号
    for _ in range(3):
        txbuf = '{"c":"e","iv":{}}'
        try:
            uart_send_data(uart1, txbuf)
            loguru.logger.info(f"发送结束信号: {txbuf}")
        except Exception as e:
            loguru.logger.error(f"发送结束信号失败: {str(e)}")
        time.sleep(0.001)


def check_uart_port():
    port_list = list(serial.tools.list_ports.comports())
    if len(port_list) == 0:
        loguru.logger.error('无法找到可用串口')
        return False
    else:
        loguru.logger.info("找到以下串口:")
        for port in port_list:
            loguru.logger.info(f"  {port}")
    return True


def open_uart(port, bps, timeout):
    """打开串口"""
    try:
        uart = serial.Serial(port, bps, timeout=timeout)
        loguru.logger.success(f"成功打开串口 {port} (波特率: {bps}, 超时: {timeout}s)")
        return uart
    except Exception as e:
        loguru.logger.error(f"打开串口失败: {str(e)}")
        return None


def uart_send_data(uart, txbuf):
    """发送串口数据"""
    len_sent = uart.write(txbuf.encode('utf-8'))
    loguru.logger.debug(f"已发送 {len_sent} 字节数据")
    return len_sent


def handle_serial_error():
    """处理串口错误并尝试恢复连接"""
    global global_uart, conf_serial
    loguru.logger.warning("处理串口错误...")

    try:
        # 关闭无效串口连接
        if global_uart and global_uart.is_open:
            loguru.logger.warning("关闭当前串口连接")
            global_uart.close()
        global_uart = None
    except Exception as e:
        loguru.logger.error(f"关闭串口时出错: {str(e)}")

    # 尝试重新打开串口
    if keep_running and conf_serial:
        loguru.logger.info("尝试重新打开串口...")
        if serial_recv():
            loguru.logger.success("串口已成功重新连接")
        else:
            loguru.logger.warning("串口重连失败")


def close_uart(uart):
    """关闭串口"""
    if uart and uart.is_open:
        try:
            uart.close()
            loguru.logger.info("串口已关闭")
        except Exception as e:
            loguru.logger.error(f"关闭串口时出错: {str(e)}")


def prepare_conf_file(configpath):
    """准备配置文件"""
    if os.path.isfile(configpath):
        loguru.logger.info(f"配置文件已存在: {configpath}")
        return

    # 创建新配置文件
    config = configparser.ConfigParser()

    # 添加配置部分
    config.add_section("config")
    config.set("config", "alert_mp3_file", r"alert.mp3")
    config.set("config", "send_wxmsg", r"1")
    config.set("config", "send_email", r"1")
    config.set("config", "send_serial", r"1")

    config.add_section("Email")
    config.set("Email", "smtp_host", r"smtp.qq.com")
    config.set("Email", "smtp_port", r"465")
    config.set("Email", "mail_user", r"your_email@qq.com")
    config.set("Email", "mail_pass", r"your_authorization_code")
    config.set("Email", "sender_email", r"your_email@qq.com")
    config.set("Email", "email_receivers",
               r"your_email@qq.com,another@example.com")
    config.set("Email", "smtptype", r"SSL")

    config.add_section("micromsg")
    config.set("micromsg", "wxmsg_url_get",
               r"http://example.com/app/wxadminsiteerr.asp")
    config.set("micromsg", "wxmsg_url_post",
               r"https://example.com/app/overlimwx.php")
    config.set("micromsg", "wxmsg_method", r"POST")
    config.set("micromsg", "secret_seed", r"your_secret")
    config.set("micromsg", "wxmsg_touser", r"user1|user2|user3")

    config.add_section("serial")
    config.set("serial", "serialdev_out", r"COM1,9600,1")

    # 写入文件
    with open(configpath, "w") as configfile:
        config.write(configfile)
    loguru.logger.info(f"已创建新配置文件: {configpath}")


def get_conf_from_file(config_path, config_section, conf_list):
    """从配置文件获取配置项"""
    conf_default = {
        "alert_mp3_file": "alert.mp3",
        "send_wxmsg": "1",
        "send_email": "1",
        "send_serial": "0",
        "wxmsg_url_get": "http://example.com/app/wxadminsiteerr.asp",
        "wxmsg_url_post": "https://example.com/app/overlimwx.php",
        "wxmsg_method": "POST",
        "secret_seed": "your_secret",
        "wxmsg_touser": "user1|user2",
        "smtp_host": "smtp.qq.com",
        "smtp_port": "465",
        "mail_user": "your_email@qq.com",
        "mail_pass": "your_authorization_code",
        "sender_email": "your_email@qq.com",
        "smtptype": "SSL",
        "email_receivers": "your_email@qq.com",
        "serialdev_out": "COM1,9600,1",
    }

    config = configparser.ConfigParser()

    # 检测文件编码
    with open(config_path, "rb") as f:
        result = chardet.detect(f.read())
        encoding = result["encoding"] or 'utf-8'

    config.read(config_path, encoding=encoding)

    conf_item_settings = []
    for conf_item in conf_list:
        try:
            conf_item_setting = config.get(config_section, conf_item)

            # 处理列表类型配置
            if conf_item in ["email_receivers", "wxmsg_touser"]:
                item_list = [item.strip()
                             for item in conf_item_setting.split(",")]
                conf_item_settings.append(item_list)
            else:
                conf_item_settings.append(conf_item_setting)
        except Exception as e:
            default_value = conf_default.get(conf_item, "")
            conf_item_settings.append(default_value)
            loguru.logger.warning(
                f"配置项缺失: [{config_section}]{conf_item}，使用默认值: {default_value}")

    return tuple(conf_item_settings) if len(conf_list) > 1 else conf_item_settings[0]


class SerialReceiveThread(threading.Thread):
    """更健壮的串口数据接收线程"""

    def __init__(self, uart):
        super().__init__()
        self.uart = uart
        self.daemon = True
        self.name = "Serial-Receiver"
        self.last_data_time = time.time()

    def run(self):
        global global_uart, serialdev
        global keep_running, stop_event
        loguru.logger.info("串口接收线程已启动")

        while keep_running and not stop_event.is_set():
            try:
                # 检查串口连接状态
                if self.uart is None or not self.uart.is_open:
                    loguru.logger.warning("串口连接已断开，接收线程暂停")
                    time.sleep(1)
                    # 打开新串口
                    # 解析串口配置
                    port = serialdev.split(',')[0]
                    bps = int(serialdev.split(',')[1])
                    timeout = int(serialdev.split(',')[2])
                    global_uart = open_uart(port, bps, timeout)
                    if not global_uart:
                        loguru.logger.error(f"无法打开串口 {port}")
                        return False
                    continue

                # 尝试读取数据
                uart_receive_data(self.uart)

                # 更新最后数据接收时间
                self.last_data_time = time.time()

                # time.sleep(0.01)
            except Exception as e:
                loguru.logger.error(f"串口接收异常: {str(e)}")
                time.sleep(1)


def serial_recv():
    """串口接收管理"""
    global global_uart, serialdev

    # 关闭现有串口
    if global_uart and global_uart.is_open:
        close_uart(global_uart)

    # 解析串口配置
    port = serialdev.split(',')[0]
    bps = int(serialdev.split(',')[1])
    timeout = int(serialdev.split(',')[2])

    # 打开新串口
    global_uart = open_uart(port, bps, timeout)
    if not global_uart:
        loguru.logger.error(f"无法打开串口 {port}")
        return False

    # 创建接收线程
    try:
        serial_thread = SerialReceiveThread(global_uart)
        serial_thread.start()
        thread_list.append(serial_thread)
        loguru.logger.info("串口接收线程已启动")
        return True
    except Exception as e:
        loguru.logger.error(f"启动串口接收线程失败: {str(e)}")
        return False


@new_thread
def s2e_worker():
    """串口工作管理 - 更健壮地处理连接问题"""
    loguru.logger.info("启动串口管理线程")

    # 初次连接尝试
    if serial_recv():
        loguru.logger.info("串口初始化成功")
    else:
        loguru.logger.warning("串口初始化失败")

    # 主循环监控连接状态
    while keep_running and not stop_event.is_set():
        # 检查串口状态
        if not global_uart or not global_uart.is_open:
            loguru.logger.error("串口连接丢失，尝试重新连接...")
            if serial_recv():
                loguru.logger.success("串口已重新连接")
            else:
                loguru.logger.warning("串口重连失败")

        time.sleep(5)  # 每5秒检查一次连接状态


def clean_msg_store():
    """清理消息存储"""
    global recv_msgs, temp_recv_msg, completed_emails, last_clean_time
    loguru.logger.info("清理过期的消息存储")

    # 清理完成的消息
    current_time = time.time()
    expired_keys = [k for k in completed_emails if float(
        k) < current_time - 86400]  # 保留1天
    for k in expired_keys:
        del completed_emails[k]

    # 重置临时存储
    recv_msgs = []
    temp_recv_msg = {}
    last_clean_time = current_time


@new_thread
def email_daemon():
    """邮件守护进程 - 重构为实时处理"""
    global emr, report_email_waiting, pending_emails

    if emr == 0:
        loguru.logger.info("邮件守护进程已启动")
        emr = 1

    # 设置为活动状态
    email_daemon_active.set()

    try:
        while keep_running and not stop_event.is_set():
            # 检查是否有待处理邮件
            with email_send_lock:
                if pending_emails:
                    # 找到最旧的完整邮件
                    for timestamp in list(pending_emails.keys()):
                        email_data = pending_emails[timestamp]
                        if len(email_data['parts']) == email_data['total_parts']:
                            process_completed_email(timestamp)
                            break

                    # 处理超时未完成的邮件（超过30秒）
                    current_time = time.time()
                    for timestamp in list(pending_emails.keys()):
                        email_data = pending_emails[timestamp]
                        if current_time - email_data['timestamp'] > 600:
                            received = len(email_data['parts'])
                            total = email_data['total_parts']
                            loguru.logger.warning(
                                f"邮件 {timestamp} 超时未完成 ({received}/{total}部分):{current_time}~{email_data['timestamp']}"
                            )
                            del pending_emails[timestamp]

            # 短暂休眠
            time.sleep(0.5)
    except Exception as e:
        loguru.logger.error(f"邮件守护进程异常: {str(e)}")
    finally:
        email_daemon_active.clear()

# 在run_email_daemon函数中取消调度


@new_thread
def run_email_daemon():
    """启动邮件守护进程"""
    # 不再使用schedule
    email_daemon()

# 在clean_msg_store中添加清理逻辑


def clean_msg_store():
    """清理消息存储"""
    global recv_msgs, temp_recv_msg, completed_emails, last_clean_time, pending_emails

    # 清理完成的消息
    current_time = time.time()

    # 清理pending_emails中过期的部分邮件
    expired_timestamps = [
        ts for ts, data in pending_emails.items()
        if current_time - data['timestamp'] > 3600  # 超过1小时未完成
    ]

    for ts in expired_timestamps:
        received = len(pending_emails[ts]['parts'])
        total = pending_emails[ts]['total_parts']
        loguru.logger.warning(f"清理过期部分邮件 {ts}: {received}/{total}")
        del pending_emails[ts]

    # 清理其他存储
    expired_keys = [k for k in completed_emails if float(
        k) < current_time - 86400]  # 保留1天
    for k in expired_keys:
        del completed_emails[k]

    # 重置临时存储
    recv_msgs = []
    temp_recv_msg = {}
    last_clean_time = current_time


def print_email_queue():
    """打印当前邮件队列状态"""
    with email_send_lock:
        if not pending_emails:
            loguru.logger.info("邮件队列为空")
            return

        total_emails = len(pending_emails)
        complete_count = 0
        partial_count = 0

        loguru.logger.info("==== 当前邮件队列状态 ====")
        for timestamp, data in pending_emails.items():
            status = "完成" if len(
                data['parts']) == data['total_parts'] else "部分"
            age = int(time.time() - data['timestamp'])

            if status == "完成":
                complete_count += 1
            else:
                partial_count += 1

            loguru.logger.info(
                f"ID: {timestamp} | 状态: {status} | "
                f"部分: {len(data['parts'])}/{data['total_parts']} | "
                f"创建: {age}秒前"
            )

        loguru.logger.info(
            f"==== 总计: 完成 {complete_count}, 部分 {partial_count}/{total_emails} ====")


def force_send_email(timestamp):
    """强制发送指定邮件"""
    if timestamp not in pending_emails:
        loguru.logger.error(f"邮件 {timestamp} 不在队列中")
        return False

    loguru.logger.warning(f"强制发送邮件: {timestamp}")
    with email_send_lock:
        return process_completed_email(timestamp)


def main():
    """主程序入口"""
    global email_receivers, smtp_host, smtp_port, mail_user, mail_pass, sender_email, smtptype
    global serialdev

    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 初始化日志
        log_path = './logs'
        if not os.path.isdir(log_path):
            os.makedirs(log_path)
        loguru.logger.add(
            os.path.join(log_path, "serial-email.log"),
            rotation="1 day",
            retention="7 days",
            level="DEBUG",
            encoding="utf-8"
        )

        # 定义配置文件路径
        configpath = "setup.ini"

        # 准备配置文件
        prepare_conf_file(configpath)

        # 读取基本配置
        alert_mp3_file, conf_wxmsg, conf_email, conf_serial = get_conf_from_file(
            configpath,
            "config",
            ["alert_mp3_file", "send_wxmsg", "send_email", "send_serial"]
        )

        # 处理配置标志
        conf_wxmsg = conf_wxmsg == "1"
        conf_email = conf_email == "1"
        conf_serial = conf_serial == "1"
        conf_serial = True
        loguru.logger.info(
            f"配置状态: 微信消息={conf_wxmsg}, 邮件发送={conf_email}, 串口通信={conf_serial}")

        # 读取邮件配置
        if conf_email:
            email_conf = get_conf_from_file(
                configpath,
                "Email",
                ["email_receivers", "smtp_host", "smtp_port", "mail_user",
                 "mail_pass", "sender_email", "smtptype"]
            )
            email_receivers, smtp_host, smtp_port, mail_user, mail_pass, sender_email, smtptype = email_conf

        # 读取串口配置
        if conf_serial:
            serialdev = get_conf_from_file(
                configpath, 'serial', ['serialdev_out'])
            loguru.logger.info(f"串口配置: {serialdev}")

        # 启动邮件守护进程
        run_email_daemon()

        process_email_queue(email_queue)
        # 启动串口工作
        if conf_serial:
            s2e_worker()

        loguru.logger.success("程序已启动，按Ctrl+C退出")

        # 主循环
        while keep_running:
            time.sleep(1)

    except Exception as e:
        loguru.logger.critical(f"程序启动失败: {str(e)}")
    finally:
        # 清理资源
        stop_event.set()
        if global_uart and global_uart.is_open:
            close_uart(global_uart)


if __name__ == "__main__":
    email_queue = Queue()
    main()
