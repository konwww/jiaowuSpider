import resss as res

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299",
    "Referer": "http://jiaowu.sicau.edu.cn/web/web/lanmu/jshi.asp",
    "Cookie": "Hm_lvt_20274609f261feba8dcea77ff3f7070c=1523195886; ASPSESSIONIDCCAADCDT=GPKEFCGBHNKNLHIJBDMHBMGD;jcrj%5Fuser=web; jcrj%5Fpwd=web; jcrj%5Fauth=True;jcrj%5Fsession=jwc%5Fcheck%2Cauth%2Cuser%2Cpwd%2Cjwc%5Fcheck%2Ctymfg%2Csf%2C;jcrj%5Fjwc%5Fcheck=y;jcrj%5Ftymfg=%C0%B6%C9%AB%BA%A3%CC%B2;jcrj%5Fsf=%D1%A7%C9%FA"}
result = res.initReq(url='http://jiaowu.sicau.edu.cn/web/web/lanmu/jshi.asp', header=headers)
table = result.find_all("table", width="650")
result = table[0]
result = result.find_all("tr", height="20")
with open("file1.txt", "w", encoding="utf-8") as file:
    for i in result:
        item = i.find_all("td")
        print(item)
        if str.strip(item[4].get_text()) not in ["普通", "其他", "多媒体"]:
            continue
        file.write(str({"area": str.strip(item[1].get_text()), "address": str.strip(item[2].get_text()),
                        "population": str.strip(item[3].get_text()), "category": str.strip(item[4].get_text()),
                        "link": (item[5].find("a")).get("href"),"room_id":str.strip(item[5].find("a").get("href"))[-4:]
                        })
                   + "\n")
    file.close()
