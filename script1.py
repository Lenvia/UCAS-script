import requests
from PIL import Image
import re
import json
import keras
import numpy as np
import time
from urllib import request
from http import cookiejar
from bs4 import BeautifulSoup
import sys

ocrJson = open('ocr.json', 'r')
data = json.load(ocrJson)
ch2index = data['ch2index']
index2ch = data['index2ch']
ocrJson.close()

model = keras.models.load_model('ocr.h5')

name_student = None

signal = False

def post_data(url, data = None, time_out = 3, retry = 5):
    for _ in range(retry):
        try:
            page = sess.post(url, data=data, timeout=time_out)
            return page
        except:
            pass
    return None

def post_data2(url, data = None, time_out = 3, retry = 5, headers=None):
    for _ in range(retry):
        try:
            page = sess.post(url, data=data, timeout=time_out, headers=headers)
            return page
        except:
            pass
    return None

def login_jwxt(ava, add_id_to_name = 0):
    page_jump = post_data('http://sep.ucas.ac.cn/portal/site/226/821')
    if page_jump is None:
        print('网页超时','请检查是否断网或者延迟过高')
        return "high delay"

    pattern_jwxt_id = re.compile('Identity=([\w-]*)') # 匹配数字、字母、下划线和-
    try:
        iden = re.search(pattern_jwxt_id, page_jump.text).group(1)
    except:
        print( '未预料的错误',  '没有成功匹配到Identity，请及时联系维护人员')
        print('登录失败了\t\tT_T')
        return

    jump_payload = {'Identity': iden}
    page_jwxt = post_data('http://jwxk.ucas.ac.cn/login', data=jump_payload)
    if page_jwxt is None:
        print( '网页超时',  '请检查是否断网或者延迟过高')
        return "high delay"

    headers = {
        'Host': 'jwxk.ucas.ac.cn',
        'Proxy-Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Referer': 'http://jwxk.ucas.ac.cn/notice/view/1',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    link_course_manage = 'http://jwxk.ucas.ac.cn/courseManage/main'
    # link_course_manage = 'http://jwxk.ucas.ac.cn/courseManageBachelor/main' if ava == '本科生' else 'http://jwxk.ucas.ac.cn/courseManage/main'
    page_course_manage = sess.get(link_course_manage, headers=headers)

    if page_course_manage is None:
        print( '网页超时',  '请检查是否断网或者延迟过高')
        return "high delay"

    global Avatar
    Avatar = ava
    
    pattern_select_course_s = re.compile('\?s=(.*?)";')
    select_course_s = re.search(pattern_select_course_s, page_course_manage.text).group(1)

    deptIds = []
    config = json.load(open("config.json", "r"))
    deptIds = config.get('labels')

    if len(deptIds) == 0:  # 未指定，将选中全部学院
        pattern_deptIds = re.compile('label for="id_(\d+)"')
        deptIds = re.findall(pattern_deptIds, page_course_manage.text)

    global select_course_payload
    select_course_payload = {'s': select_course_s, 'deptIds': deptIds}

    # print(select_course_payload)
    
    return 'ok'

def login(event = None):
    config = json.load(open("config.json", "r"))
    user = config.get('username')
    pwd = config.get('password')
    code = recognizeVerificationCode()
    login_payload = {'userName': user, 'pwd': pwd, 'certCode': code, 'sb': 'sb'}

    global login_info, root
    print('登录SEP...\t\t=_ = ')

    # 尝试连接sep来登录
    page_after_login = post_data('http://sep.ucas.ac.cn/slogin', data = login_payload)
    if page_after_login is None:
        print( '网页超时',  '请检查是否断网或者延迟过高')
        print('登录失败了\t\tT_T')
        return
    # 判断是否仍停留在选课界面
    pattern_login_error = re.compile('<div class="alert alert-error">(.+?)</div>', re.S)
    try:
        err_type = re.search(pattern_login_error, page_after_login.text).group(1)
        print( '信息有误',  err_type)
        print('登录失败了\t\tT_T :' + err_type)
        return
    except:
        pass # 信息没有错误

    # 尝试用正则表达式匹配姓名来判断是否成功进入sep主页面
    pattern_name = re.compile('"当前用户所在单位"> (.+?)&nbsp;(.+?)</li>', re.S)
    try:
        global name_student
        name_student = re.search(pattern_name, page_after_login.text).group(2)
        # print(name)
    except:
        print( '未能成功进入 SEP',  '请仔细检查输入的用户名、密码以及验证码')
        print('登录失败了\t\tT_T :')
        return

    print('登录选课系统...\t\t>_<')

    res = login_jwxt('x研究生', add_id_to_name = 0)
    
    if res != 'ok':
        print('登录失败了\t\tT_T')
        return
    print('欢迎 ' + name_student + ' ^_^')

def relogin():
    page_jump = post_data('http://sep.ucas.ac.cn/appStore')
    if page_jump is None:
        print( '请重新登录',  '请检查是否断网或者延迟过高')
        return "high delay"

    pattern_offline = re.compile('SEP 教育业务接入平台')
    if re.search(pattern_offline, page_jump.text) != None:
        print( '请重新登录',  '看起来已经好久没有操作了')
        return "sign out"
    
    global Avatar
    res = login_jwxt(Avatar)
    return res

def download_image_file(event):
    global sess, login_info

    try:
        html = sess.get('http://sep.ucas.ac.cn/randomcode.jpg', timeout = 3)
    except:
        print('网页超时 请重新获取验证码')
        return

    fp = open("certcode.jpg", 'wb')
    fp.write(html.content)
    fp.close()


def recognizeVerificationCode():
    im = Image.open("certcode.jpg").convert('L')
    pred_res = model.predict(np.array(np.asarray(im, dtype=np.float32)).reshape(1, 50, 200, 1))
    char_res = ""
    for i in range(0, 5):
        char_res += index2ch[str(pred_res[i].argmax(1)[0])]
    return char_res

# 初始化
def init():
    cookies = cookiejar.CookieJar()
    handler = request.HTTPCookieProcessor(cookies)
    openr = request.build_opener(handler)
    openr.open("http://sep.ucas.ac.cn")
    # 全局变量
    global select_course_payload # 用于选课的 payload，记录用于选课的 cid 和 要选的课程编号
    select_course_payload = None

    global auto_working # 标记是否在捡漏，0 表示不在捡漏，1 表示在捡漏
    auto_working = 0

    global sess # 全局session
    sess = requests.session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4261.0 Safari/537.36'}) # 给 seesion 做伪装，通过浏览器检测
    sess.cookies.update(cookies)
    global Avatar # 标明用本科生/研究生身份登录
    Avatar = None

    download_image_file(None)

def check_before_select():

    global select_course_payload, Avatar

    if Avatar is None:
        print( '错误',  '您还未登录')
        global auto_working # 标记是否在捡漏，0 表示不在捡漏，1 表示在捡漏
        auto_working = 1
        return None

    link_select_course = 'http://jwxk.ucas.ac.cn/courseManageBachelor/selectCourse' if Avatar == '本科生' else 'http://jwxk.ucas.ac.cn/courseManage/selectCourse'
    page_select_course = post_data(link_select_course, select_course_payload)

    soup = BeautifulSoup(page_select_course.text, "html.parser")
    csrf = soup.find(id='_csrftoken').attrs['value']



    if page_select_course is None:
        print('网页超时 没有进行选课')
        return None
#    print(page_select_course.text)
    off_line = re.search('你的会话已失效或身份已改变，请重新登录', page_select_course.text)
    if off_line: # 至少已经从选课系统中掉线
        global login_info, root
        print('掉线了，自动重连中...\t=_ = ')
        
        res = relogin()
        if res != 'ok': # 甚至从SEP系统中掉线
            init()
            login()
            if relogin() != 'ok':
                return None
        else:
            print('欢迎 ' + name_student + '\t^_^')

            page_select_course = post_data(link_select_course, select_course_payload)
            if page_select_course is None:
                print('网页超时 没有进行选课')
                return None

    system_closed = re.search('为了给您提供更好的服务', page_select_course.text)
    if system_closed:
        print('选课系统未开放')
        return None

    print('正在选课')
    return page_select_course, csrf

def generate_log(select_result_page):
    pattern = re.compile('class="success">(.+?)</label>')
    success_message =  re.search(pattern, select_result_page.text)
    pattern = re.compile('class="error">(.+?)</label>')
    error_message = re.search(pattern, select_result_page.text)
    success = 0
    if success_message is not None:
        messages = success_message.group(1).split('<br/>')
        success = 1
    elif error_message is not None:
        messages = error_message.group(1).split('<br/>')
    else:
        messages = ['403 Forbidden']

    for single_message in messages:
        message_str = single_message
        if len(message_str) == 0:
            continue
        if len(message_str) > 25:
            message_str = message_str[:25] + '\n' + message_str[25:]
        if success:
            print(message_str)
        print(message_str)

def add_course_code_to_payload(course, select_course_page):
    pattern = re.compile('id="courseCode_(.*?)">%s' % course)
    course_code = re.search(pattern, select_course_page.text)
    # print(course_code.group(1))
    if course_code is None:
        print(course + ': 该课程编码不可用（可能已经选过了）, 请将该课程编码从抢课列表中移除。')
        return 0
    else:
        select_course_payload['sids'].append(course_code.group(1))
        return 1


def select_separately(event):
    global signal
    select_course_page, csrf = check_before_select()
    if select_course_page is None:
        return

    config = json.load(open("config.json", "r"))
    course_list = config.get('courses')


    global Avatar
    link_save_course = 'http://jwxk.ucas.ac.cn/courseManage/saveCourse'
    # link_save_course = 'http://jwxk.ucas.ac.cn/courseManageBachelor/saveCourse' if Avatar == '本科生' else 'http://jwxk.ucas.ac.cn/courseManage/saveCourse'
    for course in course_list:
        select_course_payload['sids'] = []
        select_course_payload['_csrftoken'] = csrf

        if add_course_code_to_payload(course, select_course_page) == 0:
            course_list.remove(course)
            continue

        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Content-Length": "81",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "jwxk.ucas.ac.cn",
            "Origin": "http://jwxk.ucas.ac.cn",
            "Referer": select_course_page.url,
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
        }
        select_result_page = post_data2(link_save_course, select_course_payload, headers=headers)
        if select_result_page.status_code == 200:
            print("选课请求发送成功！ ")

            soup = BeautifulSoup(select_result_page.text, "html.parser")
            res = soup.find(text=re.compile(course))
            if res is not None:
                print("#########选课成功！课程编码为 %s #############" % course)
                course_list.remove(course)

                if len(course_list) == 0:
                    print("已全部完成，即将退出程序")
                    signal = True
            else:
                print("暂时无法选课，即将重试！")
                collision = soup.find(text=re.compile("冲突"))
                if collision is not None:
                    print("%s 与已有课程冲突！" % course)

        if select_result_page is None:
            print(course + ': 网页超时')

    print('\n')

while True:
    try:
        init()
        login()
        select_separately(None)

        if signal is True:
            break
        time.sleep(3)


    except:
        pass