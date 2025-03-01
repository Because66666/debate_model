import json
from zheng_chatbox import *
from fan_chatbox import *
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1, CreateMessageRequest, CreateMessageRequestBody, ListMessageRequest
import lark_oapi as lark
import traceback
import time

replace_map = {
    '@_user_1': ''
}

conversation_id = CreateConversationRequest()
conversation_id_fan = CreateConversationRequest_2()

used_message_id = []
rows = 10  # 对话论数限制
model_name ='Deepseek R1 32B' # 当模型要@对面的时候，如何显示。
# 创建 LarkClient 对象，用于调用 OpenAPI
client_zheng = lark.Client.builder().app_id(zAPP_ID).app_secret(zAPP_SECRET).build()
client_fan = lark.Client.builder().app_id(fAPP_ID).app_secret(fAPP_SECRET).build()
start_flag = False
def replace_msg_by_map(msg):
    if not msg:
        return msg
    for k, v in replace_map.items():
        msg = msg.replace(k, v)
    return msg


def send_msg_back_zheng(chat_id, msg):
    content = {
        "zh_cn": {
            "content": [
                [
                    {"tag": "text", "text": msg},
                    {"tag": "at", "user_id": fAPP_ID, "user_name": f"{model_name}反方辩论员"}
                ]
            ]
        }
    }
    # 构造请求
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("post")
                      .content(json.dumps(content))
                      .build()) \
        .build()
    # 发送请求
    response = client_zheng.im.v1.message.create(request)
    # 处理响应
    if response.success():
        print("消息发送成功:", response.data)
    else:
        print(f"发送失败: code={response.code}, msg={response.msg}")

def send_msg_back_fan(chat_id, msg):
    content = {
        "zh_cn": {
            "content": [
                [
                    {"tag": "text", "text": msg},
                    {"tag": "at", "user_id": zAPP_ID, "user_name": f"{model_name}辩论员1"}
                ]
            ]
        }
    }
    # 构造请求
    request = CreateMessageRequest.builder() \
        .receive_id_type("chat_id") \
        .request_body(CreateMessageRequestBody.builder()
                      .receive_id(chat_id)
                      .msg_type("post")
                      .content(json.dumps(content))
                      .build()) \
        .build()
    # 发送请求
    response = client_fan.im.v1.message.create(request)
    # 处理响应
    if response.success():
        print("消息发送成功:", response.data)
    else:
        print(f"发送失败: code={response.code}, msg={response.msg}")


# 定义事件处理函数
def handle_message_event(data: P2ImMessageReceiveV1) -> None:
    global start_flag
    if start_flag:
        print('正在辩论，无法处理')
        return
    start_flag = True
    # print(f"收到消息事件: {lark.JSON.marshal(data, indent=4)}")
    msg_body = data.event
    chat_id = msg_body.message.chat_id
    message_type = msg_body.message.message_type
    message_id = msg_body.message.message_id
    if message_id in used_message_id:
        print("已处理过该消息，跳过")
        return
    used_message_id.append(message_id)
    raw_content = replace_msg_by_map(json.loads(msg_body.message.content)[message_type])
    history = f'[主持]{raw_content}\n'
    zheng_last = ''
    fan_last = ''
    with open("history.txt", "w",encoding='utf8') as f:
        f.write(history)
    for row in range(1,rows+1):
        if row==1:
            ai_message = Chat(conversation_id, f"{history}请开始你的第{row}轮发言。")
            send_msg_back_zheng(chat_id, f"[正方{row}辩]:{ai_message}")
            history +=f'[正方{row}辩]:{ai_message}\n'
            zheng_last = ai_message
            time.sleep(3)
            ai_message2 = Chat_fan(conversation_id_fan,history+f'请开始你的第{row}轮发言。')
            send_msg_back_fan(chat_id, f"[反方{row}辩]:{ai_message2}")
            history +=f'[反方{row}辩]:{ai_message2}\n'
            fan_last = ai_message2
        elif row==rows:
            ai_message = Chat(conversation_id, f"{fan_last}\n这是最后一轮发言，请你总结你的观点。")
            send_msg_back_zheng(chat_id, f"[正方{row}辩]:{ai_message}")
            history +=f'[正方{row}辩]:{ai_message}\n'
            zheng_last = ai_message
            time.sleep(3)
            ai_message2 = Chat_fan(conversation_id_fan,f"{zheng_last}\n这是最后一轮发言，请你总结你的观点。")
            send_msg_back_fan(chat_id, f"[反方{row}辩]:{ai_message2}")
            history +=f'[反方{row}辩]:{ai_message2}\n'
            fan_last = ai_message2
        else:
            ai_message = Chat(conversation_id, f"{fan_last}\n请开始你的第{row}轮发言。")
            send_msg_back_zheng(chat_id, f"[正方{row}辩]:{ai_message}")
            history +=f'[正方{row}辩]:{ai_message}\n'
            zheng_last = ai_message
            time.sleep(3)
            ai_message2 = Chat_fan(conversation_id_fan,f"{zheng_last}\n请开始你的第{row}轮发言。")
            send_msg_back_fan(chat_id, f"[反方{row}辩]:{ai_message2}")
            history +=f'[反方{row}辩]:{ai_message2}\n'
            fan_last = ai_message2
        time.sleep(3)
        print(zheng_last)
        print(fan_last)
        with open("history.txt", "w",encoding='utf8') as f:
            f.write(history)
    print('辩论已经完成。')
    start_flag = False

# 初始化事件处理器
event_handler = lark.EventDispatcherHandler.builder("", "") \
    .register_p2_im_message_receive_v1(handle_message_event) \
    .build()
ws_client = lark.ws.Client(
    app_id=zAPP_ID,  # 替换为你的 App ID
    app_secret=zAPP_SECRET,  # 替换为你的 App Secret
    event_handler=event_handler,  # 注册事件处理器
    log_level=lark.LogLevel.DEBUG  # 可选：设置日志级别
)


# 初始化长连接客户端
def main():
    ws_client.start()  # 启动长连接


if __name__ == "__main__":
    main()
