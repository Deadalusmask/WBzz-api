import requests
import base64
import re
import json
from configparser import ConfigParser


def login(username, password):
    su = base64.b64encode(username.encode('utf-8')).decode('utf-8')
    postData = {
        'entry': 'sso',
        'gateway': '1',
        'savestate': '30',
        'userticket': '0',
        'vsnf': '1',
        'su': su,
        'service': 'sso',
        'sp': password,
        'encoding': 'UTF-8',
        'cdult': '3',
        'returntype': 'TEXT',
    }
    loginURL = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.15)'
    session = requests.Session()
    res = session.post(loginURL, data = postData)
    info = res.json()
    #print(info)

    if info["retcode"] == "0":
        print("登录成功")
        ret = session.get(info['crossDomainUrlList'][0])
        #print(ret.text)
    else:
        print("登录失败，原因： {}".format(info["reason"]))

    return session,info


def profile(con, query_id):
    s,info = con
    profile_url = 'https://m.weibo.cn/api/container/getIndex?uid={}&containerid=100505{}'
    addr_url = 'https://weibo.com/p/100505{}/info'
    user = {}
    try:
        res = s.get(profile_url.format(query_id, query_id)).json()
        #print(res)
        if 'userInfo'in res['data'].keys():
            resu = res['data']['userInfo']
            user['uid'] = resu['id']
            user['screen_name'] = resu['screen_name']
            user['gender'] = resu['gender']
            user['description'] = resu['description']
            user['profile_image_url'] = resu['profile_image_url']
    except Exception as e:
        print(e)

    if 'uid' in user.keys():
        response = s.get(addr_url.format(query_id))
        if response.status_code is 200:
            reArr = re.findall(r'pt_detail\\\"\>(.+?)\<\\\/span', response.text)
            if len(reArr)>1 and reArr[1]:
                user['addr'] = reArr[1]

    return user


def crawl(con, query_id):
    s,info = con
    fans_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{}&type=all&since_id={}'
    followers_url = 'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{}&page={}'

    fans_result = []
    result = []

    since_id = 1
    while True:
        res = s.get(fans_url.format(query_id, str(since_id)))
        res_json = res.json()
        if not len(res_json['data']['cards'])>0:
            break
        for card in res_json['data']['cards']:
            if 'card_group' in card.keys():
                for user in card['card_group']:
                    if 'user' in user.keys():
                        fans_result.append(user['user']['id'])
        since_id += 1


    page = 1
    while True:
        res = s.get(followers_url.format(query_id, str(page)))
        res_json = res.json()
        if not len(res_json['data']['cards'])>0:
            break
        for card in res_json['data']['cards']:
            if 'card_group' in card.keys():
                for user in card['card_group']:
                    if 'user' in user.keys() and user['user']['id'] in fans_result:
                        result.append({
                            'uid': user['user']['id'],
                            'screen_name': user['user']['screen_name'],
                            'gender': user['user']['gender'],
                            'description': user['user']['description'],
                            'profile_image_url': user['user']['profile_image_url']
                        })
                        print(user['user']['id'],user['user']['screen_name'])
        page += 1

    return result


def search_by_name(con, query_name):
    s,info = con
    #containerid: 100103type=3&q=query_name&t=0
    query_url = 'https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D3%26q%3D{}%26t%3D0&&page={}'

    result = []
    page = 1
    while True:
        res = s.get(query_url.format(query_name, str(page)))
        res_json = res.json()
        if not len(res_json['data']['cards'])>0:
            break
        for card in res_json['data']['cards']:
            if 'card_group' in card.keys():
                for user in card['card_group']:
                    if 'user' in user.keys():
                        result.append({
                            'uid': user['user']['id'],
                            'screen_name': user['user']['screen_name'],
                            'gender': user['user']['gender'],
                            'description': user['user']['description'],
                            'profile_image_url': user['user']['profile_image_url']
                        })
                        print(user['user']['id'],user['user']['screen_name'])
        page += 1

    return result


def with_addr(con, result):
    s,info = con
    addr_url = 'https://weibo.com/p/100505{}/info'
    for user in result:
        response = s.get(addr_url.format(user['uid']))
        if response.status_code is 200:
            reArr = re.findall(r'pt_detail\\\"\>(.+?)\<\\\/span', response.text)
            if len(reArr)>1 and reArr[1]:
                user['addr'] = reArr[1]
    return result

if __name__ == '__main__':
    cfg = ConfigParser()
    cfg.read('.env')
    username = cfg.get('account','username')
    password = cfg.get('account','password')

    con = login(username,password)
    result = search_by_name(con, 'Deadalus_')
    print('count: ', len(result))


# foo = [{'id':1,'name':'a'},{'id':2,'name':'b'}]
# any(d['id'] == 3 for d in foo)