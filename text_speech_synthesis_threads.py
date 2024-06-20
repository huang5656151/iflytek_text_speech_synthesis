#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author : Kerwin Wong


import requests
import json
import base64
import hashlib
import time
from urllib.parse import urlencode
import hmac
from datetime import datetime
from wsgiref.handlers import format_date_time
from time import mktime
import sys
from concurrent.futures import ThreadPoolExecutor
import glob
import re
import os


class TestTask():

    def __init__(self):
        self.host = HOST
        self.app_id = APP_ID
        self.api_key = API_KEY
        self.api_secret = API_SECRET

    # 生成鉴权的url
    def assemble_auth_url(self, path):
        params = self.assemble_auth_params(path)
        # 请求地址
        request_url = "http://" + self.host + path
        # 拼接请求地址和鉴权参数，生成带鉴权参数的url
        auth_url = request_url + "?" + urlencode(params)
        return auth_url

    # 生成鉴权的参数
    def assemble_auth_params(self, path):
        # 生成RFC1123格式的时间戳
        format_date = format_date_time(mktime(datetime.now().timetuple()))
        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + format_date + "\n"
        signature_origin += "POST " + path + " HTTP/1.1"
        # 进行hmac-sha256加密
        signature_sha = hmac.new(self.api_secret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()
        signature_sha = base64.b64encode(signature_sha).decode(encoding='utf-8')
        # 构建请求参数
        authorization_origin = 'api_key="%s", algorithm="%s", headers="%s", signature="%s"' % (
            self.api_key, "hmac-sha256", "host date request-line", signature_sha)
        # 将请求参数使用base64编码
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
        # 将请求的鉴权参数组合为字典
        params = {
            "host": self.host,
            "date": format_date,
            "authorization": authorization
        }
        return params

    # 创建任务
    def test_create(self, text):
        # 创建任务的路由
        create_path = "/v1/private/dts_create"
        # 拼接鉴权参数后生成的url
        auth_url = self.assemble_auth_url(create_path)
        pattern = re.compile(r"(\d)+(“)") 
        matches = pattern.search(text)
        vcn_id_t = ""
        if matches:
            if matches.group(1) == "1":
                vcn_id_t = "x4_lingbosong" # x4_lingxiaozhen_eclives, x4_feidie， x4_xiuying， x4_lingfeihao_upbeatads， x4_mingge
            elif matches.group(1) == "2":
                vcn_id_t = "x4_feidie"
            elif matches.group(1) == "3":
                vcn_id_t = "x4_xiuying"
            elif matches.group(1) == "4":
                vcn_id_t = "x4_lingfeihao_upbeatads"
            elif matches.group(1) == "5":
                vcn_id_t = "x4_mingge"
            text = text.replace(matches.group(1), "")
        else:
            vcn_id_t = "x4_yeting"

        # 合成文本
        encode_str = base64.encodebytes(text.encode("UTF8"))
        txt = encode_str.decode()
        # 请求头
        headers = {'Content-Type': 'application/json'}
        # 请求参数，字段具体含义见官网文档：https://aidocs.xfyun.cn/docs/dts/%E6%8E%A5%E5%8F%A3%E5%8D%8F%E8%AE%AEv3.html
        data = {
            "header": {
                "app_id": self.app_id,
                # "callback_url": "",
                # "request_id": ""
            },
            "parameter": {
                "dts": {
                    "vcn": "{0}".format(vcn_id_t),#请先在控制台开通明哥发音人权限
                    "language": "zh",
                    "speed": 50,
                    "volume": 50,
                    "pitch": 50,
                    "rhy": 1,
                    "bgs": 0,
                    "reg": 0,
                    "rdn": 0,
                    "scn": 0,
                    "audio": {
                        "encoding": "lame", # 下方下载的文件后缀需要保持一致
                        "sample_rate": 16000,
                        "channels": 1,
                        "bit_depth": 16,
                        "frame_size": 0
                    },
                    "pybuf": {
                        "encoding": "utf8",
                        "compress": "raw",
                        "format": "plain"
                    }
                }
            },
            "payload": {
                "text": {
                    "encoding": "utf8",
                    "compress": "raw",
                    "format": "plain",
                    "text": txt
                }
            },
        }
        try:
            #print("创建任务请求参数:", json.dumps(data))
            res = requests.post(url=auth_url, headers=headers, data=json.dumps(data))
            res = json.loads(res.text)
            return res
        except Exception as e:
            print("创建任务接口调用异常，错误详情:%s" % e)
            sys.exit(1)

    # 查询任务
    def test_query(self, task_id):
        # 查询任务的路由
        query_path = "/v1/private/dts_query"
        # 拼接鉴权参数后生成的url
        auth_url = self.assemble_auth_url(query_path)
        # 请求头
        headers = {'Content-Type': 'application/json'}
        # 请求参数，字段具体含义见官网文档：https://aidocs.xfyun.cn/docs/dts/%E6%8E%A5%E5%8F%A3%E5%8D%8F%E8%AE%AEv3.html
        data = {
            "header": {
                "app_id": self.app_id,
                "task_id": task_id
            }
        }
        try:
            #print("\n查询任务请求参数:",json.dumps(data))
            res = requests.post(url=auth_url, headers=headers, data=json.dumps(data))
            res = json.loads(res.text)
            return res
        except Exception as e:
            print("查询任务接口调用异常，错误详情:%s" % e)
            sys.exit(1)


# 创建任务
def do_create(text):
    # 调用创建任务接口
    test_task = TestTask()
    create_result = test_task.test_create(text)
    #print("create_response:",json.dumps(create_result))
    # 创建任务接口返回状态码
    code = create_result.get('header', {}).get('code')
    # 状态码为0，创建任务成功，打印task_id, 用于后续查询任务
    if code == 0:
        task_id = create_result.get('header', {}).get('task_id')
        #print("创建任务成功，task_id: %s" % task_id)
        return task_id
    # 状态码非0，创建任务失败, 相关错误码参考官网文档：https://aidocs.xfyun.cn/docs/dts/%E6%8E%A5%E5%8F%A3%E5%8D%8F%E8%AE%AEv3.html
    else:
        print("创建任务失败，返回状态码: %s" % code)

# 查询任务
def do_query(task_id):
    test_task = TestTask()
    # 这里循环调用查询结果，当task_status状态为'5'（即大文本合成任务完成）时停止循环，循环次数和sleep时间可酌情定义
    for i in range(30):
        # 等待1秒
        time.sleep(1)
        # 调用查询任务接口
        query_result = test_task.test_query(task_id)
        #print("query_response:",json.dumps(query_result))
        # 查询任务接口返回状态码
        code = query_result.get('header', {}).get('code')
        # 状态码为0，查询任务成功
        if code == 0:
            # 任务状态码：1-任务创建成功 2-任务派发失败 4-结果处理中 5-结果处理完成
            task_status = query_result.get('header', {}).get('task_status')
            if task_status == '5':
                audio = query_result.get('payload', {}).get('audio').get('audio')
                # base64解码audio，打印下载链接
                decode_audio = base64.b64decode(audio)
                #print("查询任务成功，音频下载链接: %s" % decode_audio.decode())
                return decode_audio
                break
            else:
                print("第%s次查询，处理未完成，任务状态码:%s" % (i + 1, task_status))
        else:
            print("查询任务失败，返回状态码: %s" % code)
            sys.exit(1)



if __name__ == "__main__":
    # 1、用户参数，相关参数注意修改
    HOST = "api-dx.xf-yun.com"
    APP_ID = "********" #input your own ID and KEY and SECRET
    API_KEY = "********"
    API_SECRET = "********"

    # 2、执行创建任务
    if os.path.exists("temp.txt"):
        os.remove("temp.txt")
    file = open("input.txt",encoding='utf-8')
    lines = file.readlines()
    for line in lines:
        line = line.strip() 
        if len(line):
            if line.split("-")[0]:
                if line.split("-")[0] == "旁白":
                    line = line.replace("旁白-", "")
                    vcn_id = 0
                elif line.split("-")[0] == "黑衣人":
                    vcn_id = 1
                    line = line.replace("黑衣人-", "")
                elif line.split("-")[0] == "风无痕":
                    vcn_id = 2
                    line = line.replace("风无痕-", "")
                elif line.split("-")[0] == "烈火心":
                    vcn_id = 3
                    line = line.replace("烈火心-", "")
                elif line.split("-")[0] == "白素贞":
                    vcn_id = 4
                    line = line.replace("白素贞-", "")
                elif line.split("-")[0] == "梦凝音":
                    vcn_id = 5
                    line = line.replace("梦凝音-", "")
                replaced_text = re.sub(r'：“', '：\n{0}“'.format(vcn_id), line)
                replaced_text = re.sub(r'”', '”', replaced_text)
            else:
                replaced_text = line
            tempfile = open("temp.txt",'a',encoding='utf-8')
            tempfile.write(replaced_text)
            tempfile.close()
        else:
            replaced_text = "\n"
            tempfile = open("temp.txt",'a',encoding='utf-8')
            tempfile.write(replaced_text)
            tempfile.close()
    file.close()
    
    newfile = open("temp.txt",encoding='utf-8')
    newtext = newfile.read()
    text_spt = newtext.splitlines()
    #print(text_spt)

    with ThreadPoolExecutor(max_workers=9) as executor:
        results = executor.map(do_create, text_spt)
        query_results = executor.map(do_query, results)
        if query_results:
            for index, Download_addres in enumerate(query_results):
                f = requests.get(Download_addres)
                filename = "{0}.mp3".format(index)
                with open(filename, "wb") as code:
                    code.write(f.content)
    newfile.close()
    code.close()
    if os.path.exists("temp.txt"):
        os.remove("temp.txt")

    MP3_list = sorted(glob.glob(r"*.mp3"),key=len)
    f3_write = open('combine.mp3', 'wb')
    for mp3 in MP3_list:
        with open(mp3, 'rb') as f:
            f3_write.write(f.read())
        os.remove(mp3)
    f3_write.flush()
    f3_write.close()
    if filename:
        print("\n音频保存成功！")