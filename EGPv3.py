try:
    import mysql.connector
    import requests
    import datetime
#    from datetime import date
    import os
    import json
    import re
    from rich import print
    import sys
    import time
except Exception as e:
    print("[!] ERROR on importing module:\n",e)
    exit(0)

def isRunnableTime():
    current = datetime.datetime.now().time()
    if (datetime.time(0, 0, 0) <= current <= datetime.time(8, 59, 0)) or (datetime.time(12, 1, 0) <= current <= datetime.time(12, 59, 0)) or (datetime.time(17,1, 0) <= current <= datetime.time(23,59,59)):
        print(":white_check_mark: [bright_green]Runnable Time.[/bright_green]")
    else:
        print(":warning: [orange1]Warning, You are running in a out of service time.[/orange1]")
        exit(0)

def readJSON(f):
    if os.path.exists(f):
        print(":white_check_mark: [bright_green]File is already exist.[/bright_green]")
        return json.load(open(f,"r", encoding="utf-8"))
    else:
        return []

dbconnector = None
if (len(sys.argv) > 1 and "--database" in sys.argv):
    dbconnector = mysql.connector.connect(
        host='localhost',
        user='p0ndja',
        password='P0ndJ@1103',
        database='EGP'
    )

if __name__ == "__main__": 
    isRunnableTime()
    ann = ["P0", "15", "B0", "D0", "W0", "D1", "W1", "D2", "W2"]
    met = ["15", "16", "18", "19"]
    date = datetime.now()
    # date = datetime.datetime(2022,10,12)
    # date = date.today() # Move backward 1 day.
    if (len(sys.argv) > 1 and (("--autorun" in sys.argv and datetime.datetime.now().hour == 0) or ("--yesterday" in sys.argv))):
        date -= datetime.timedelta(days=1)
    elif ("--backward" in sys.argv):
        ann = ["P0", "15", "D0", "W0"]
        met = ["19"]
        date -= datetime.timedelta(days=365)
        if (date < datetime.datetime(2022,8,1)):
            date = datetime.datetime(2022,8,1)
    # today = datetime.datetime(2022,10,12).strftime('%Y%m%d') #Testing Propose
    today = datetime.date.today().strftime('%Y%m%d')
    while(1): 
        nicedate = date.strftime('%Y%m%d')

        new_data = []
        print(f"=============\n:calendar: [bold]Date: {date.strftime('%d/%m/%Y')}[/bold]") 
        
        saved_in_file_data = []
        d = readJSON(f"{os.path.dirname(__file__)}/file/{nicedate}.json")
        if (len(d) > 0):
            for dd in d:
                print(f"{dd['id']}-{dd['type']}-{dd['method']}")
                saved_in_file_data.append(f"{dd['id']}-{dd['type']}-{dd['method']}")
        print(saved_in_file_data)
        
        for a in ann:
            for m in met:
                print(datetime.datetime.now(),f"[bright_yellow]Checking[/bright_yellow] T:{a}, M:{m}")
                response2 = requests.get(f"http://p0nd.ga/EGP/{nicedate}-{a}-{m}?json").text
                data_json = (json.loads(response2))["channel"]
                if int(data_json["countbyday"]) > 0:
                    current_data = data_json["item"]
                    print("[bright_green]Founded[/bright_green]",data_json["countbyday"],f"in T:[magenta]{a}[/magenta], M:[aqua]{m}[/aqua]")
                    if int(data_json["countbyday"]) > 20:
                        print(f"[bright_yellow]:warning: The amount is reached the limit, not all data can be get by automatic.[/bright_yellow] ")
                    if int(data_json["countbyday"]) == 1:
                        current_data = [data_json["item"]]
                    for ai in current_data:
                        aid = re.search("[&?]projectId=([A-Za-z0-9]{1,15})", ai["link"]).group(1)
                        if "(เวชภัณฑ์ยา)" in ai["title"] or "รายการยา" in ai["title"]:
                            if (f"{aid}-{a}-{m}") not in saved_in_file_data:
                                new_data.append({"id": aid, "title": " ".join(ai["title"].split()), "link": ai["link"], "date": nicedate, "type": a, "method": m})
                                print(f":white_check_mark: [bright_green]{aid}[/bright_green] - {ai['title']}")
                            else:
                                print(f":o: Duplicated [bright_yellow]{aid} - {ai['title']}[/bright_yellow]")
                        else:
                            print(f":next_track_button: Skipped {aid} (title not match with keyword)")
        if (len(new_data) > 0):
            if (dbconnector != None):
                for ai in new_data:
                    cursor = dbconnector.cursor()
                    cursor.execute(f"INSERT INTO `pharmmd_EGP` (`pharmmd_EGP`.`id`, `pharmmd_EGP`.`title`, `pharmmd_EGP`.`link`, `pharmmd_EGP`.`date`, `pharmmd_EGP`.`type`, `pharmmd_EGP`.`method`) VALUES ('{ai['id']}', '{ai['title']}', '{ai['link']}', {nicedate}, '{ai['type']}', '{ai['method']}')")
                    dbconnector.commit()
            d.extend(new_data)
            with open(f"{os.path.dirname(__file__)}/file/{nicedate}.json", "w", encoding="utf-8") as outfile:
                json.dump(d, outfile, indent=4, ensure_ascii=False)
                outfile.close()
                print(f":floppy_disk: Saved {len(d)} data(s) to [bright_green bold]{nicedate}.json[/bright_green bold]")
        else:
            print(f":o: No new data for [bright_green bold]{nicedate}.json[/bright_green bold]")
        date += datetime.timedelta(days=1)
        if (int(today) == int(nicedate)):
            break
        time.sleep(1)