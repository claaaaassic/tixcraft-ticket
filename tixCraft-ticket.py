#-*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from lxml import etree
import re
import json
import time
import sys

##########################
#
#  按下 F5 執行
#
#################################

# login mode and email and password
mode = "facebook"  # facebook / google
email = "facebook@gmail.com"
password = "password"

# activity detail url
rootUrl = "https://tixcraft.com/activity/detail/17_JRI_TP"

# activity date
date = "12/23(五)"

# area name
price = u"3880"

# ticket quantity
buyNumber = "1"


baseUrl = "https://tixcraft.com"
ticketBaseUrl = "/ticket/ticket"
paymentURL = "/ticket/payment"
orderUrl = "/ticket/order"
checkUrl = "/ticket/check"
sendPaymentURL = "/ticket/sendPayment"
finishURL = "/ticket/finish"


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


def doLogin():
    if mode == 'facebook':
        s = SessionFacebook(email, password)
        s.get("https://tixcraft.com/login/facebook")
    elif mode == 'google':
        s = SessionGoogle(email, password)
        s.get("https://tixcraft.com/login/google")
    else:
        print 'mode must be facebook or google'
        sys.exit()
    return s


def doCheckLogin(s):
    response = s.get(baseUrl)
    printConnectDetail(response)
    root = etree.HTML(response.text)
    userData = root.xpath("//a[@id='logout']/text()")
    if len(userData) == 0:
        print 'login fail'
        print 'len(userData) : ' + str(len(userData))
        sys.exit()
    else:
        print 'userData : ' + userData[0]
        

# 找到指定場次前往選擇區域的URL
# 從立即購票中進入
def getActivityUrl(s):
    response = s.get(rootUrl)
    printConnectDetail(response)
    root = etree.HTML(response.text)
    activityUrlList = root.xpath("//ul[@class='btn']/li/a/@href")
    activityNameList = root.xpath("//ul[@class='btn']/li/a/div/span/text()")

    for index in range(len(activityUrlList)):
        print activityNameList[index] + " : " + activityUrlList[index]
        if activityUrlList[index].startswith("/activity/game"):
            return s, activityUrlList[index]

    print 'not found activityUrl 購票按鈕'
    sys.exit()


# 找到指定票價區間前往選擇張數的URL
# 選擇區域
def getAreaSelectUrl(s, activityUrl):
    response = s.get(baseUrl + activityUrl)
    printConnectDetail(response)
    root = etree.HTML(response.text)

    detailDateList = root.xpath("//table/tbody//tr/td[1]")
    detailUrlList = root.xpath("//table/tbody//tr/td[4]/input/@data-href")

    for index in range(len(detailDateList)):
        print detailDateList[index].text + " : " + detailUrlList[index]
        if detailDateList[index].text.encode("utf-8").startswith(date):
            areaSelectUrl = detailUrlList[index]
            print "\nareaSelectUrl : " + areaSelectUrl
            return s, areaSelectUrl

    print 'not found activityUrl 購票按鈕'
    sys.exit()


# 在網頁中取得規則並且轉換成真正選擇張數的URL
# 轉換成選擇數量的URL
def getOrderQuantityUrl(s, areaSelectUrl):
    response = s.get(baseUrl + areaSelectUrl)
    printConnectDetail(response)

    if not str(response.url).startswith(baseUrl + areaSelectUrl):
        print "no page https://tixcraft.com/ticket/area"
        reList = re.findall('(?<=https://tixcraft.com).+', response.url)
        return s, reList[0]
    root = etree.HTML(response.text)

    priceList = root.xpath("//div[@class='zone area-list']/div/b/text()")  # 價錢
    priceIDList = root.xpath(
        "//div[@class='zone area-list']/div/@data-id")  # 價錢 id

    areaPriceList = root.xpath(
        "//div[@class='zone area-list']/ul/li/a/text()")  # 區域

    areaUrlList = root.xpath("/html/body/script")

    areaID = str()
    for index in range(len(priceList)):
        if priceList[index] == None:
            print price[index]
            continue
        if price in priceList[index]:
            zoneID = priceIDList[index]
            areaList = root.xpath(
                "//div[@class='zone area-list']/ul[@id='" + str(zoneID) + "']/li/a/text()")  # 區域
            areaIDList = root.xpath(
                "//div[@class='zone area-list']/ul[@id='" + str(zoneID) + "']/li/a/@id")
            area = areaList[0]
            areaID = areaIDList[0]
            print "price : " + price + ", area : " + area + ", areaID : " + areaID
            break

    for content in areaUrlList:
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

                print "OrderQuantitUrl : " + matchAreaIDRoleJosnFile[areaID]
                return s, matchAreaIDRoleJosnFile[areaID]

    print 'not found OrderQuantitUrl 訂票區域按鈕'
    sys.exit()


# 送出選取的數量
def sendOrderQuantity(s, orderQuantitUrl):
    response = s.get(baseUrl + orderQuantitUrl)
    printConnectDetail(response)
    postUrl = response.url
    root = etree.HTML(response.text)

    csrftokenList = root.xpath("//input[@id='CSRFTOKEN']/@value")
    TicketForm = root.xpath("//select/@name")

    print "CSRFTOKEN : " + csrftokenList[0]
    print TicketForm[0] + " : " + buyNumber
    payload = {
        "CSRFTOKEN": csrftokenList[0],
        TicketForm[0]: buyNumber,
        "ticketPriceSubmit": "確認張數"
    }

    print "\nstart post"
    response = s.post(postUrl, payload)  # 訂票
    printConnectDetail(response)
    

    print "\nstart get order"
    response = s.get(baseUrl + orderUrl)
    printConnectDetail(response)

    print "\nstart get check"
    response = s.get(baseUrl + checkUrl)
    printConnectDetail(response)

    print "\nstart get payment"
    response = s.get(baseUrl + paymentURL)
    printConnectDetail(response)

    if str(response.url).startswith(baseUrl + paymentURL):
        root = etree.HTML(response.text)
        ticketID = root.xpath("//div[@class='fcBlue']/text()")
        detailList = root.xpath("//table[@id='cartList']/tbody/tr/td/text()")
        print "\nsuccessful!!!\n\nticketID : " + ticketID[0].encode("utf-8")
        for detail in detailList:
            print detail
        return csrftokenList[0]

    print 'not refer to payment page 訂票區域按鈕'
    sys.exit()


# # 付款方式 not use
# def sendPayment(s, csrftoken):
#     data = s.get(baseUrl + paymentURL)
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
#     data = s.post(baseUrl + sendPaymentURL, payload)  # 付款方式
#     return s


# # not use
# def getFinishPage(s):
#     data = s.get(baseUrl + finishURL)
#     print "FinishPage"

def printConnectDetail(response):
    print '\nstatus : ' + str(response.status_code)
    print '   url : ' + str(response.url)
    if ( len(response.history) > 0 ):
        print 'history : '
        for i in response.history:
            print i


def main():

    tStart = time.time()

    print "============ doLogin  ========================="
    s = doLogin()
    doCheckLogin(s)

    print "\n\n============ getActivityUrl =================="
    s, activityUrl = getActivityUrl(s)

    print "\n\n============ getAreaSelectUrl ================"
    s, areaSelectUrl = getAreaSelectUrl(s, activityUrl)

    print "\n\n============ getOrderQuantityUrl  ============"
    s, orderQuantitUrl = getOrderQuantityUrl(
        s, areaSelectUrl)

    print "\n\n============ sendOrderQuantity  =============="
    sendOrderQuantity(s, orderQuantitUrl)

    tEnd = time.time()
    print "It cost " + str(tEnd - tStart) + " sec"

if __name__ == '__main__':
    main()
