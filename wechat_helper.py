import requests
import json
import os

# 获取Access Token
def get_access_token(appid, appsecret):
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={appsecret}"
    response = requests.get(url)
    return response.json()["access_token"]

# 上传图文素材
def upload_news(access_token, articles):
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
    payload = {"articles": articles}
    response = requests.post(url, json=payload)
    result = response.json()
    
    print('upload_news', result)
    
    return result.get("media_id") or result.get("draft_id")

# 群发文章
def send_article(access_token, media_id):
    # 1. 先发布草稿
    publish_url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
    publish_payload = {"draft_id": media_id}
    publish_response = requests.post(publish_url, json=publish_payload)
    publish_result = publish_response.json()
    
    if 'errcode' in publish_result and publish_result['errcode'] != 0:
        print('发布失败:', publish_result)
        return publish_result
        
    # 2. 获取发布后的 article_id
    article_id = publish_result.get('publish_id')
    
    # 3. 群发
    url = f"https://api.weixin.qq.com/cgi-bin/message/mass/sendall?access_token={access_token}"
    payload = {
        "filter": {"is_to_all": True},
        "mpnews": {"media_id": article_id},
        "msgtype": "mpnews"
    }
    response = requests.post(url, json=payload)
    return response.json()

def get_materials(access_token):
    url = f"https://api.weixin.qq.com/cgi-bin/material/batchget_material?access_token={access_token}"
    payload = {
        "type": "image",
        "offset": 0,
        "count": 20
    }
    response = requests.post(url, json=payload)
    return response.json()

# 主流程
appid = os.environ.get('WECHAT_APP_ID')
appsecret = os.environ.get('WECHAT_APP_SECRET')
access_token = get_access_token(appid, appsecret)

# 获取并打印素材列表
# materials = get_materials(access_token)
# print("现有素材列表：")
# for item in materials.get('item', []):
#     print(f"media_id: {item.get('media_id')}, name: {item.get('name')}, url: {item.get('url')}")

articles = [{
    "title": "示例文章",
#    "thumb_media_id": "LJGNckXOaezci8bZiAJY7N5lP_SNHYnbxxotzCnwe1sMOWIgCNm6GmbQhvVRyT_e",
    "content": "<p>正文内容</p>",
    "show_cover_pic": 0
}]
media_id = upload_news(access_token, articles)
print(media_id)

# result = send_article(access_token, media_id)
#print(result)


