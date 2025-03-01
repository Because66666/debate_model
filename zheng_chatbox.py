import json
import requests
from codecs import getincrementaldecoder
from zheng_config import *
def CreateConversationRequest():
    url = "https://xxx/api/proxy/api/v1/create_conversation"
    headers = {
        "Apikey": zcoze_apikey,
        "Content-Type": "application/json"
    }
    data = {
        "AppKey": zcoze_apikey,
        "Inputs": {"var": "variable"},
        "UserID": "321"
    }
    response = requests.post(url,headers=headers,json=data)
    app_conversation_id = response.json()['Conversation']['AppConversationID']
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"请求失败，状态码：{response.status_code}")
    return app_conversation_id

def Chat(Conversation_id,MESSAGE):
    url = "https://xxx/api/proxy/api/v1/chat_query"
    headers = {
        "Apikey": zcoze_apikey,
        "Content-Type": "application/json"
    }
    data = {
        "Query": MESSAGE,
        "AppConversationID": Conversation_id,
        "AppKey": zcoze_apikey,
        "ResponseMode": "streaming",
        "UserID": "321"
    }
    Chat_response = requests.post(url, headers=headers, json=data, stream=True)
    Chat_response.raise_for_status()
    buffer = ""
    Add_response = ""
    utf8_decoder = getincrementaldecoder('utf-8')(errors='replace')
    text_buffer = ""
    line_buffer = ""
    Add_response = ""
    for chunk in Chat_response.iter_content(chunk_size=1024):
        if chunk:
            text_buffer += utf8_decoder.decode(chunk)
            while "\n" in text_buffer:
                line, text_buffer = text_buffer.split("\n", 1)
                line = line.strip()
                if line.startswith("data:data:"):
                    json_str = line[10:]
                elif line.startswith("data:"):
                    json_str = line[5:]
                else:
                    continue
                if json_str:
                    try:
                        event_data = json.loads(json_str)
                        if event_data.get("event") == "message_end":
                            # print("完整响应结束:", event_data)
                            # print("回复内容："+"\n"+Add_response)
                            return Add_response
                        elif not event_data.get("answer", "") or event_data.get("answer", "") == "\n\n":
                            continue
                        else:
                            Add_response += event_data.get("answer", "")
                    except json.JSONDecodeError:
                        print("解析失败的行:", line)
    final_text = utf8_decoder.decode(b'', final=True)
    if final_text:
        text_buffer += final_text
if __name__ == "__main__":
    conversation_id=CreateConversationRequest()
    while True:
        message=input("请输入聊天内容，或直接回车以取消当前对话："+"\n")
        if message:
            print("思考中")
            ds_response=Chat(conversation_id,message)
        else:
            print("对话已取消")
            break
