#-*- coding: utf-8 -*-
import sys
import time
import datetime
import json
import re

import requests
from bs4 import BeautifulSoup
from lxml import etree

##########################
#
#  按下 F5 執行
#
#################################

# login MODE and EMAIL and PASSWORD
MODE = "facebook"  # facebook / google
EMAIL = "email"
PASSWORD = "password"

# activity detail url
TICKET_URL = "https://tixcraft.com/activity/detail/17_JRI_TP"
TICKET_DATE = "12/23(五)"
TICKET_PRICE = u"4880"

# ticket quantity
BUY_NUMBER = "1"


# 等待開始
WAIT_START = True
START_DATE = [2016, 11, 25, 12, 33]  # YYYY,MM,dd,HH,mm

# 持續尋找購票按鈕
WAIT_OPEN = True

# 持續尋找未售完按鈕
WAIT_SELL = True

BASE_URL = "https://tixcraft.com"
PAYMENT_URL = BASE_URL + "/ticket/payment"
ORDER_URL = BASE_URL + "/ticket/order"
CHECK_URL = BASE_URL + "/ticket/check"
SENDPAYMENT_URL = BASE_URL + "/ticket/sendPayment"
FINISH_URL = BASE_URL + "/ticket/finish"


class SessionFacebook:

    def __init__(self, login, pwd):
        url_login = "https://www.facebook.com/login/"
        url_auth = "https://www.facebook.com/login.php?login_attempt=1&next=https%3A%2F%2Fwww.facebook.com%2Fv2.2%2Fdialog%2Foauth%3Fredirect_uri%3Dhttps%253A%252F%252Ftixcraft.com%252Flogin%252Ffacebook%26state%3D3971221be1b52ec2647ba8f83e5e3be2%26scope%3Demail%26client_id%3D1432131563664985%26ret%3Dlogin%26sdk%3Dphp-sdk-4.0.23%26logger_id%3D8341234e-6776-4c1e-91eb-8f90481826cc&lwv=100"
        self.ses = requests.session()
        login_html = self.ses.get(url_login)
        soup_login = BeautifulSoup(login_html.content, 'lxml').find(
            'form').find_all('input')
        my_dict = {}
        for u in soup_login:
            if u.has_attr('value'):
                my_dict[u['name']] = u['value']
        # override the inputs without login and pwd:
        my_dict['email'] = login
        my_dict['pass'] = pwd
        self.ses.post(url_auth, data=my_dict)

    def get(self, URL):
        return self.ses.get(URL)

    def post(self, URL, payload):
        return self.ses.post(URL, data=payload)


class SessionGoogle:

    def __init__(self, login, pwd):
        url_login = "https://accounts.google.com/ServiceLogin"
        url_auth = "https://accounts.google.com/ServiceLoginAuth"
        self.ses = requests.session()
        login_html = self.ses.get(url_login)
        soup_login = BeautifulSoup(login_html.content, 'lxml').find(
            'form').find_all('input')
        my_dict = {}
        for u in soup_login:
            if u.has_attr('value'):
                my_dict[u['name']] = u['value']
        # override the inputs without login and pwd:
        my_dict['Email'] = login
        my_dict['Passwd'] = pwd
        self.ses.post(url_auth, data=my_dict)

    def get(self, URL):
        return self.ses.get(URL).text

    def post(self, URL, payload):
        return self.ses.post(URL, data=payload)


def do_login():
    print "============ do_login  ========================="
    if MODE == 'facebook':
        s = SessionFacebook(EMAIL, PASSWORD)
        s.get("https://tixcraft.com/login/facebook")
    elif MODE == 'google':
        s = SessionGoogle(EMAIL, PASSWORD)
        s.get("https://tixcraft.com/login/google")
    else:
        print 'MODE must be facebook or google'
        sys.exit()
    return s


def check_login(s):
    response = s.get(BASE_URL)
    print_response_detail(response)
    root = etree.HTML(response.text)
    user_data = root.xpath("//a[@id='logout']/text()")
    if len(user_data) == 0:
        print 'login fail'
        print 'len(user_data) : ' + str(len(user_data))
        sys.exit()
    else:
        print '  user : ' + user_data[0]


# 找到指定場次的URL
def get_activity_url(s):
    print "\n\n============ get_activity_url =================="
    while WAIT_OPEN:
        for i in range(40):
            response = s.get(TICKET_URL)
            root = etree.HTML(response.text)
            activity_url_list = root.xpath("//ul[@class='btn']/li/a/@href")
            activity_name_list = root.xpath(
                "//ul[@class='btn']/li/a/div/span/text()")
            for index in range(len(activity_url_list)):
                if activity_url_list[index].startswith("/activity/game"):
                    print_response_detail(response)
                    print activity_name_list[index] + " : " + activity_url_list[index]
                    return s, activity_url_list[index]
        print_response_detail(response)

    response = s.get(TICKET_URL)
    print_response_detail(response)
    root = etree.HTML(response.text)
    activity_url_list = root.xpath("//ul[@class='btn']/li/a/@href")
    activity_name_list = root.xpath("//ul[@class='btn']/li/a/div/span/text()")

    for index in range(len(activity_url_list)):
        print activity_name_list[index] + " : " + activity_url_list[index]
        if activity_url_list[index].startswith("/activity/game"):
            return s, activity_url_list[index]

    print 'not found activityUrl 購票按鈕'
    sys.exit()


# 找到指定票價區間的URL
def get_section_url(s, activityUrl):
    print "\n\n============ get_section_url ================"
    while WAIT_SELL:
        for i in range(40):
            response = s.get(BASE_URL + activityUrl)
            root = etree.HTML(response.text)
            detail_date_list = root.xpath("//table/tbody//tr/td[1]")
            detail_url_list = root.xpath("//table/tbody//tr/td[4]/input/@data-href")

            if len(detail_url_list) == 0:
                continue

            for index in range(len(detail_date_list)):
                print detail_date_list[index].text
                if detail_date_list[index].text.encode("utf-8").startswith(TICKET_DATE):
                    print_response_detail(response)
                    section_url = detail_url_list[index]
                    print detail_date_list[index].text + " : " + section_url
                    return s, section_url
        print_response_detail(response)
        print "not found 立即訂購"

    response = s.get(BASE_URL + activityUrl)
    print_response_detail(response)
    root = etree.HTML(response.text)

    detail_date_list = root.xpath("//table/tbody//tr/td[1]")
    detail_url_list = root.xpath("//table/tbody//tr/td[4]/input/@data-href")

    for index in range(len(detail_date_list)):
        print detail_date_list[index].text
        if detail_date_list[index].text.encode("utf-8").startswith(TICKET_DATE):
            section_url = detail_url_list[index]
            print "section_url : " + section_url
            return s, section_url

    print 'not found section_url 立即訂購'
    sys.exit()


# 在網頁中取得規則並且轉換成真正選擇張數的URL
# 轉換成選擇數量的URL
def get_orderquantity_url(s, section_url):
    print "\n\n============ get_orderquantity_url  ============"    
    response = s.get(BASE_URL + section_url)
    print_response_detail(response)

    # 如果跳過選擇區域的頁面
    if not str(response.url).startswith(BASE_URL + section_url):
        print "no page https://tixcraft.com/ticket/area"
        reList = re.findall('(?<=https://tixcraft.com).+', response.url)
        return s, reList[0]
    root = etree.HTML(response.text)

    price_list = root.xpath("//div[@class='zone area-list']/div/b/text()")  # 價錢
    price_ID_list = root.xpath("//div[@class='zone area-list']/div/@data-id")  # 價錢 id
    section_url_list = root.xpath("/html/body/script")

    areaID = str()
    for index in range(len(price_list)):
        if price_list[index] == None:
            continue
        if TICKET_PRICE in price_list[index]:
            zoneID = price_ID_list[index]
            areaList = root.xpath(
                "//div[@class='zone area-list']/ul[@id='" + str(zoneID) + "']/li/a/text()")  # 區域
            areaIDList = root.xpath(
                "//div[@class='zone area-list']/ul[@id='" + str(zoneID) + "']/li/a/@id")
            area = areaList[0]
            areaID = areaIDList[0]
            print " TICKET_PRICE : " + TICKET_PRICE + ", area : " + area + ", areaID : " + areaID
            break

    for content in section_url_list:
        if content.text != None:
            scriptContent = content.text.encode("utf-8")

            if areaID in scriptContent:
                print "areaID '" + areaID + "' is in scriptContent"
                reList = re.findall(
                    '(?<=var areaUrlList =).+\}\;', scriptContent)

                matchAreaIDRole = reList[0]
                matchAreaIDRole = matchAreaIDRole.replace('\\', '')
                matchAreaIDRole = matchAreaIDRole[:-1]  # 去掉多餘字元
                print matchAreaIDRole

                matchAreaIDRoleJosnFile = json.loads(matchAreaIDRole)

                print "orderquantity_url : " + matchAreaIDRoleJosnFile[areaID]
                return s, matchAreaIDRoleJosnFile[areaID]

    print 'not found orderquantity_url 訂票區域按鈕'
    sys.exit()


# 送出選取的數量
def send_orderquantity(s, orderquantity_url):
    print "\n\n============ send_orderquantity  =============="
    response = s.get(BASE_URL + orderquantity_url)
    print_response_detail(response)
    post_url = response.url
    root = etree.HTML(response.text)

    csrftoken_list = root.xpath("//input[@id='CSRFTOKEN']/@value")
    ticketform_list = root.xpath("//select/@name")

    print "CSRFTOKEN : " + csrftoken_list[0]
    print ticketform_list[0] + " : " + BUY_NUMBER

    payload = {
        "CSRFTOKEN": csrftoken_list[0],
        ticketform_list[0]: BUY_NUMBER,
        "ticketPriceSubmit": "確認張數"
    }

    print "\nstart post"
    response = s.post(post_url, payload)  # 訂票
    print_response_detail(response)

    print "\nstart get order"
    response = s.get(ORDER_URL)
    print_response_detail(response)

    print "\nstart get check"
    response = s.get(CHECK_URL)
    print_response_detail(response)

    print "\nstart get payment"
    response = s.get(PAYMENT_URL)
    print_response_detail(response)

    if str(response.url).startswith(PAYMENT_URL):
        root = etree.HTML(response.text)
        ticket_ID_list = root.xpath("//div[@class='fcBlue']/text()")
        detail_list = root.xpath("//table[@id='cartList']/tbody/tr/td/text()")
        print "\nsuccessful!!!\n\nticketID : " + ticket_ID_list[0].encode("utf-8")
        for detail in detail_list:
            print detail
        return csrftoken_list[0]

    print 'not refer to payment page 訂票區域按鈕'
    sys.exit()


# # 付款方式 not use
# def sendPayment(s, csrftoken):
#     data = s.get(PAYMENT_URL)
#     root = etree.HTML(data)
#     paymentLabel = root.xpath(
#         "//form[@id='PaymentForm']/table/tbody/tr/td/label/text()")
#     paymentValue = root.xpath(
#         "//form[@id='PaymentForm']/table/tbody/tr/td/label/input/@value")

#     print "paymentLabel len :"
#     print len(paymentLabel)
#     if len(paymentLabel) == 0:
#         return 0
#     value = str()
#     for label in paymentLabel:
#         print label
#         if ibon in label:
#             value = paymentValue[paymentLabel.index(label)]

#     print "payment_id : " + value
#     payload = {
#         "CSRFTOKEN": csrftoken,
#         "PaymentForm[payment_id]": value,
#         "PaymentForm[shipment_id]": "23"
#     }
#     data = s.post(SENDPAYMENT_URL, payload)  # 付款方式
#     return s


# # not use
# def getFinishPage(s):
#     data = s.get(FINISH_URL)
#     print "FinishPage"

def print_response_detail(response):
    print time.ctime()
    print 'status : ' + str(response.status_code)
    print '   url : ' + str(response.url)
    if (len(response.history) > 0):
        print 'history : '
        for i in response.history:
            print i


def wait_start():
    print "  now : " + time.ctime()
    print "start : " + datetime.datetime(START_DATE[0], START_DATE[1], START_DATE[2], START_DATE[3], START_DATE[4]).ctime()
    now = time.localtime()
    difference = datetime.datetime(START_DATE[0], START_DATE[1], START_DATE[2], START_DATE[3], START_DATE[4]) - datetime.datetime(now[0], now[1], now[2], now[3], now[4])
    print "difference.seconds : " + str(difference.seconds)
    if difference.seconds > 90 :
        print "start sleep for " + str(difference.seconds - 90) + " seconds"
        time.sleep(difference.seconds - 90)
    print time.ctime()


def main():

    if WAIT_START:
        wait_start()

    tStart = time.time()

    s = do_login()
    check_login(s)

    s, activityUrl = get_activity_url(s)

    s, section_url = get_section_url(s, activityUrl)
  
    s, orderquantity_url = get_orderquantity_url(s, section_url)

    send_orderquantity(s, orderquantity_url)

    tEnd = time.time()
    print "It cost " + str(tEnd - tStart) + " sec"

if __name__ == '__main__':
    main()
