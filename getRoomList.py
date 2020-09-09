from lxml.html import etree
import requests
from flask_mysqldb import MySQLdb
import multiprocessing.pool as pool

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Referer": "http://jiaowu.sicau.edu.cn/web/web/lanmu/jshi.asp",
    "Cookie": "Hm_lvt_20274609f261feba8dcea77ff3f7070c=1523195886; ASPSESSIONIDCCAADCDT=GPKEFCGBHNKNLHIJBDMHBMGD;jcrj%5Fuser=web; jcrj%5Fpwd=web; jcrj%5Fauth=True;jcrj%5Fsession=jwc%5Fcheck%2Cauth%2Cuser%2Cpwd%2Cjwc%5Fcheck%2Ctymfg%2Csf%2C;jcrj%5Fjwc%5Fcheck=y;jcrj%5Ftymfg=%C0%B6%C9%AB%BA%A3%CC%B2;jcrj%5Fsf=%D1%A7%C9%FA"}


def getTable():
    response = requests.get('http://jiaowu.sicau.edu.cn/web/web/lanmu/jshi.asp', headers=headers)
    response.encoding = "gb18030"
    with open("RoomTable.html", "w") as file:
        file.write(response.text)


def replaceCoding(s):
    if s is None:
        return ""
    return str.strip(s.replace("\xa0", ""))


def getCode(link):
    code = "null"
    for i in range(0, len(link)):
        code = "null"
        if link[i] == "=":
            code = link[i + 1:]
            break
    return code


db = MySQLdb.connect("localhost", "root", "123456", "classroom", charset="utf8")
cur = db.cursor()


def resolving():
    html = etree.parse('RoomTable.html', etree.HTMLParser())
    tr_list = html.xpath("//center/table[3]")
    cell = tr_list[0].xpath("./tr/td/text() | ./tr/td/a/attribute::href")
    a = tr_list[0].xpath("./tr/td/a/attribute::*")
    print(cell)
    data = []
    tmp_obj = []
    k = 0
    for i in cell:
        content = replaceCoding(i)
        if (content.__len__() == 0):
            continue
        k += 1
        if (k == 6):
            tmp_obj.append(getCode(i))
            data.append(tmp_obj)
            tmp_obj = []
            k = 0
        else:
            tmp_obj.append(content)
    # result=html.xpath("//center/table/tr/td/a[1]/attribute::*")
    # print(result)
    sql = ""
    for i in data:
        sql += "('%s','%s',%s,'%s','%s')," % (i[1], i[2], i[3], i[4], i[5])
    sql = "insert into c_origin_data (`city`,`location`,`num`,`category`,`code`) values " + sql[0:-1]
    print(sql)
    cur.execute(sql)
    db.commit()


def setBuildingData():
    cur.execute(
        "select city,left(`location`,2) as building,location from c_origin_data where `location` regexp '^[0-9]{1,2}-' group by `city`,`building`")
    data = cur.fetchall()
    map = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二', '十三', '十四', '十五']
    result = []
    k = []
    sql = ""
    for i in data:
        k.append(i[0])
        if ('-' in i[1]):
            k.append('第' + map[int(i[1][0]) - 1] + '教学楼')
            k.append(i[1])
        else:
            k.append('第' + map[int(i[1]) - 1] + '教学楼')
            k.append(i[1] + '-')
        result.append(k)
        sql += "('%s','%s','%s',%s,%s)," % (k[0], k[1], k[2], 'NOW()', 'NOW()')
        # sql += "('%s','%s','%s','%s','%s')," % (k[0], k[1], k[2],datetime.datetime.now(),datetime.datetime.now())
        k = []
    cur.execute(
        """
    select city,left(`location`,1) as building,location from c_origin_data where length(`location`)=4 
and `city`='都江堰' and location regexp '^[0-9]*$' group by `city`,`building` 
union select city,left(`location`,2) as building,location from c_origin_data where length(`location`)=5 
and `city`='都江堰' and location regexp '^[0-9]*$' group by `city`,`building`
union select city,left(`location`,1) as building,location from c_origin_data where length(`location`)=5 
and `city`='都江堰' and location regexp '^[0-9]{1,2}[A-Z]{1}.*' group by `city`,`building`"""
    )
    data = cur.fetchall()
    for i in data:
        k.append(i[0])
        k.append("第" + map[int(i[1]) - 1] + "教学楼")
        k.append(i[1])
        result.append(k)
        sql += "('%s','%s','%s',%s,%s)," % (k[0], k[1], k[2], 'NOW()', 'NOW()')
        k = []
    sql = "insert into c_building (`city`,`buildingAlias`,`prefix`,`createTime`,`updateTime`)values " + sql
    print(sql)
    cur.execute(sql[:-1])
    db.commit()


def setRoomData():
    # 清空旧数据
    cur.execute("delete from c_classroom")
    # 导入新数据
    cur.execute(
        "insert into c_classroom (`city`,`location`,`classroomAlias`,`room_id`) select `city`,`location`,`location`,`code` from c_origin_data")
    # 更新bid
    cur.execute("select * from c_building")
    building = cur.fetchall()
    print(building)
    sql = ""
    for i in building:
        sql = "update c_classroom set bid=" + str(i[0]) + ",updateTime=NOW() where `location` like '" + i[
            6] + "%' and `city`='" + i[4] + "';"
        print(sql)
        cur.execute(sql)
    db.commit()


def resolvingCourseTable(code):
    with open("../table/" + code + ".html", "r", encoding="utf8", errors="ignore") as file:
        html = file.read()
    html = etree.HTML(html + "</div></td></tr></table></center></div></BODY></HTML></body></BODY>")
    table = html.xpath("//td/div[@align]/center/table")[0]
    tr_list = table.xpath("./tr")
    # 节次
    week = {}
    s_times = 0
    for i in tr_list[2:]:
        s_times += 1
        w_times = 0
        week[str(s_times)] = {}
        td_list = i.xpath("./td")
        index = 1
        # 星期
        if len(td_list) == 9:
            td_list = td_list[2:]
        else:
            td_list = td_list[1:]
        for td in td_list:
            w_times += 1
            # 周次
            cell_list = td.xpath("./text() |./*/text() ")
            week_list = []
            if (len(cell_list) > 1):
                week_list += weekPicker(cell_list[1], casePicker(cell_list[3]))
            if (len(cell_list) > 9):
                week_list += weekPicker(cell_list[9], casePicker(cell_list[11]))
            week[str(s_times)][str(w_times)] = week_list
    return week


def convertToCourseTable(old):
    pass


"""
转换“n-m”格式为周次
"""


def convertNToM(old):
    new = old.split("-")
    week_list = []
    for i in range(int(new[0]), int(new[1]) + 1):
        week_list.append(i)
    return week_list


"""
转换“n，n+1，m，n+m”格式为周次
"""


def convertWeekNumNToMList(old):
    new = old.split(",")
    week_list = []
    for i in new:
        week_list.append(int(i))
    return week_list
    pass


"""
解决列表和区间混合模式 例如“1,2,3,4,6-10”
"""


def convertMix(old):
    new = old.split(",")
    NToM = []
    week_list = []
    for i in new:
        if "-" in i:
            NToM = convertNToM(i)
            week_list += NToM
            continue
        week_list.append(int(i))
    return week_list
    pass


def casePicker(old):
    # 1-2
    if ("-" in old and "," not in old):
        return convertNToM(old)
    # 1,2,3,4,5-9
    if ("-" in old and "," in old):
        return convertMix(old)
    # 1-3,5-9
    if ("," in old and "-" not in old):
        return convertWeekNumNToMList(old)
    # 特殊情况，只有一个周
    return old


def weekPicker(method, week_list):
    new = []
    if ("（单）" in method):
        for i in week_list:
            if i % 2 != 0:
                new.append(i)
    elif ("(双)" in method):
        for i in week_list:
            if i % 2 == 0:
                new.append(i)
    else:
        new = week_list
    return new


# 设置课程数据
def setCourseData():
    cur.execute("select id,room_id from c_classroom")
    data = cur.fetchall()
    for i in data:
        result = resolvingCourseTable(i[1])
        result = reversalWeekTimes(result)
        insertDB(i[1], result)


# 获取课程表
def getCourseTable():
    cur.execute("select id,room_id from c_classroom")
    data = cur.fetchall()
    for i in data:
        code = i[1]
        response = requests.get('http://jiaowu.sicau.edu.cn/web/web/lanmu/kbjshi.asp?bianhao=' + code, headers=headers)
        response.encoding = "gb18030"
        with open("../table/" + code + ".html", "w", encoding="utf8") as file:
            file.write(response.text)
            file.close()


# 建立状态矩阵表
def reversalWeekTimes(data):
    status = {}
    for week_times in range(1, 20):
        status[str(week_times)] = {}
        for section in data:
            status[str(week_times)][str(section)] = []
            cach = []
            for week_num in data[section]:
                cach.append(True if (week_times in data[section][week_num]) else False)
            status[str(week_times)][str(section)] = cach
    return status


# 插入数据到数据库
def insertDB(cid, data):
    section_map = {
        "1": ["08:00", "10:00"],
        "2": ["10:00", "12:00"],
        "3": ["14:00", "16:00"],
        "4": ["16:00", "18:00"],
        "5": ["19:30", "21:10"]
    }
    sql = ""
    for w_times in data:
        for section in data[w_times]:
            for w_num in range(0, len(data[w_times][section])):
                if data[w_times][section][w_num]:
                    sql += "('%s',%s,%s,'%s','%s',%s)," % (
                        cid, w_num, w_times, section_map[section][0], section_map[section][1], section)
    if len(sql) > 0:
        cur.execute(
            "insert into c_course_table (`cid`,`weekNum`,`weekTimes`,`startTime`,`endTime`,`fieldNum`)values " + sql[
                                                                                                                 :-1])
        db.commit()


def setFloor():
    cur.execute("select location,room_id from c_classroom where location regexp '-[1-9]{1}'")
    data = cur.fetchall()
    for i in data:
        print(i)
# setCourseData()
setFloor()