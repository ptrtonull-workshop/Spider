from bs4 import BeautifulSoup
import requests
import MySQLdb
import bs4
import sys

mainWeb = "http://www.pianyuan.la"

host = "localhost"
username = "root"
password = ""


def mysql_creator():
    db = MySQLdb.connect(host, username, password, "sys", charset="utf8")
    cursor = db.cursor()
    cursor.execute("CREATE DATABASE if Not Exists pianyuan;")
    cursor.execute("USE pianyuan;")
    cursor.execute("create table if Not Exists film(quality char(50),moive_name mediumblob, url mediumblob,size char(50),flash_time char(50))ENGINE=MyISAM DEFAULT CHARSET=utf8;")
    db.commit()
    db.close()


def setMysql(host_t, username_t, password_t):
    global host
    host = host_t
    global username
    username = username_t
    global password
    password = password_t


def add_data_to_mysql(info):
    db = MySQLdb.connect(host, username, password, "pianyuan", charset="utf8")
    cursor = db.cursor()
    sql = "insert into film(quality,moive_name,url,size,flash_time) values(%s,%s,%s,%s,%s)"
    cursor.execute(
        sql,
        (
            str(info["quality"]),
            str(info["movie_name"]),
            str(info["url"]),
            str(info["size"]),
            str(info["flash_time"]),
        ),
    )  # 使用execute方法执行SQL语句
    cursor.execute("select *from film")
    db.commit()
    db.close()


# get film page from main page's recommend
# page : page number of main recommend list
# number : the film position in page


# Question A: how can we get the recommend movies' name and match with its href?
def get_recommend(page, number):
    if page == 1:
        web = mainWeb
    else:
        web = mainWeb + "/" + "?p=" + str(page)
    response = requests.get(web)
    # else: page >100
    # 相应的保护措施（或者前端做限制）
    soup = BeautifulSoup(response.text, "html.parser")
    film = soup.find_all(
        name="a", attrs={"class": "ico ico_bt"}
    )  # lass located to find the target
    for i in film:
        i["href"] = mainWeb + i["href"]
    return film[number]["href"]


# SUGGESTION:
# This is a film_download_link, not the download function.
# Can we change this function's name?
def get_film_download(url):
    res = {"url": "null", "bt": "null", "subtitle": "null"}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    film = soup.find_all(name="a", attrs={"class": "btn btn-danger btn-sm"})
    res["url"] = mainWeb + film[0]["href"]
    film = soup.find_all(name="a", attrs={"class": "btn btn-primary btn-sm"})
    res["bt"] = film[0]["href"]
    film = soup.find_all(name="a", attrs={"class": "btn btn-success btn-sm"})
    res["subtitle"] = film[0]["href"]
    return res


def get_link(url):
    res = {"douban": "null", "more": "null"}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    douban = soup.find_all(name="a", attrs={"title": "豆瓣链接"})
    more = soup.find_all(name="a", attrs={"class": "text-danger"})
    res["douban"] = "https:" + douban[0]["href"]
    res["more"] = "http://pianyuan.la" + more[0]["href"]
    return res


def get_res_type(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    douban = soup.find_all(name="span", attrs={"class": "label label-warning"})
    print(douban[0].string)


def get_inf(url):
    inf = {"name": "null", "number": "null", "douban": "null"}
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    douban = soup.find_all(name="a", attrs={"title": "豆瓣链接", "target": "_blank"})
    douban = "https:" + douban[0]["href"]
    inf["douban"] = douban
    print(soup.html.body.h1.string)


def get_more_film(url):
    info = {
        "quality": "null",
        "movie_name": "null",
        "url": "null",
        "size": "null",
        "flash_time": "null",
    }
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all(name="table", attrs={"class": "data"})  # 所有的资源列表，每一个代表一个清晰度
    for i in items:  # 取其中一个清晰度
        quatify = i.find(name="span", attrs={"class": "label label-warning"}).text
        films = i.find_all(name="tr", attrs={"class": "odd"})
        films += i.find_all(name="tr", attrs={"class": "even"})  # 取得所有子资源
        for j in films:  # 抽取其中一个子资源
            htxt = j.find(name="td", attrs={"class": "nobr"})  # 找到它带名字的超文本
            url = htxt.find(name="a", attrs={"class": "ico ico_bt"})  # 取得更细节的超文本信息
            if isinstance(url, bs4.element.Tag) is False:
                url = htxt.find(name="a", attrs={"class": "ico ico_ed2k"})
                if isinstance(url, bs4.element.Tag) is False:
                    url = htxt.find(name="a", attrs={"class": "ico"})  # 取得更细节的超文本信息
            name = url.string  # 取得名字
            url = "http://pianyuan.la" + url["href"]  # 取得链接 btn  btn-primary btn-sm
            size = j.find(name="td", attrs={"class": "nobr center"}).string  # 取得大小信息
            time = j.find(
                name="td", attrs={"class": "nobr lasttd center"}
            ).string  # 取得更新时间信息
            info["quality"] = quatify  # 收录此子资信息到字典
            info["movie_name"] = name
            info["url"] = url
            info["size"] = size
            info["flash_time"] = time
            add_data_to_mysql(info)
    return info


def next_page(page):
    return "http://pianyuan.la/mv?order=score&p=" + str(page)


mv_web = "http://pianyuan.la/mv?order=score"


def get_list(url, page):
    film_list_number = 0
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.find_all(
        name="div", attrs={"class": "col-sm-3 col-md-3 col-xs-4 col-lg-2 nopl"}
    )
    for x in range(0, 118, 3):
        i = items[film_list_number]
        film = i.find(name="a")
        film["href"] = "http://pianyuan.la" + film["href"]
        get_more_film(film["href"])
        num = x // 2
        if x == 107:
            process = "\r[%d#NO.%d]: |%-51s|\n" % (page, x / 3 + 1, "|" * (num - 1))
        else:
            process = "\r[%d#NO.%d]: |%-51s|" % (page, x / 3 + 1, "|" * (num - 1))
        print(process, end="", flush=True)
        if film_list_number == 35:
            return 0
        else:
            film_list_number = film_list_number + 1


def run(s, f):
    page = int(s)
    while page <= int(f):
        get_list(next_page(page), page)
        page = page + 1


def main():
    local = "-G"
    Len = len(sys.argv)
    if Len < 4:
        print("too less value")
    else:
        if sys.argv[3] == str(local):
            if Len < 6:
                print("too less value")
            elif Len == 6:
                setMysql(sys.argv[4], sys.argv[5], "")
            else:
                setMysql(sys.argv[4], sys.argv[5], sys.argv[6])
            mysql_creator()
            run(sys.argv[1], sys.argv[2])
        else:
            print("I can't understand you.")


main()
