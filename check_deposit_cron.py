import json, requests, sqlite3
import datetime
from pytz import timezone
import time

with open('/home/py_bot/config.json', encoding='utf-8-sig') as fh:
    data = json.load(fh)

def send_message(chat_id, text):
    url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={text}&parse_mode=HTML".format(token=data['bot_token'], chat_id=chat_id, text=text)
    requests.get(url)


start_time = time.time()
conn = sqlite3.connect(str(data['database_uri']).replace("sqlite://", "/home/py_bot/"))
cur = conn.cursor()
while(time.time() - start_time <= 45):
    user_chats = cur.execute("SELECT user_chat.id, SUM('order'.amount) as total, user_chat.'limit' FROM 'order' INNER JOIN user_chat ON ( user_chat.id = 'order' .user_chat_id ) OR ( user_chat.id = 'order'.other_user_chat_id)  WHERE 'order'.status != 'Paid' AND notify_deposit = 1 AND user_chat.started_date <= 'order'.created_date GROUP BY user_chat.id HAVING total > user_chat.'limit' ORDER BY total ASC").fetchall()
    for user_chat in user_chats:
        current_date = datetime.datetime.now(timezone(data['timezone']))
        notify = cur.execute("SELECT notify_date, created_date, notify_count FROM notify WHERE user_chat_id = ? AND type = ?", [user_chat[0], 'Deposit']).fetchone()
        if notify is None:
            next_date = current_date + datetime.timedelta(minutes=3) 
            result = cur.execute("INSERT INTO notify (user_chat_id, created_date, notify_date, type) VALUES (?, ?, ?, ?)", [user_chat[0], current_date, next_date, 'Deposit'])
            conn.commit()
        else:
            notfiy_date = datetime.datetime.strptime(notify[0], '%Y-%m-%d %H:%M:%S.%f%z')
            if current_date >= notfiy_date:
                if notify[2] >= 2:
                    next_date = current_date + datetime.timedelta(minutes=20)
                    result = cur.execute("UPDATE notify SET notify_count = 0, notify_date = ? WHERE user_chat_id = ?", [next_date, user_chat[0]])
                else:
                    next_date = current_date + datetime.timedelta(minutes=3)
                    result = cur.execute("UPDATE notify SET notify_count = notify_count + 1, notify_date = ? WHERE user_chat_id = ?", [next_date, user_chat[0]])
                conn.commit()
                send_message(user_chat[0], "❗️Внимание, превышен лимит депозита")
            
conn.close()
