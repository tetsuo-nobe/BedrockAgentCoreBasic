# 実行 streamlit run your_script.py --server.port 8082
# 実行時に表示される Faild to detach context のエラーは下記の Bug の可能性
# https://github.com/google/adk-python/issues/1670
# http://ec2-54-201-247-239.us-west-2.compute.amazonaws.com:8082

import uuid
import json
import boto3
import streamlit as st

USER = "user"
ASSISTANT = "assistant"

# model ID の設定
model_id = "amazon.nova-lite-v1:0"

# システムメッセージの設定
system_prompts = "あなたは優秀なアシスタントです。質問に日本語で回答して下さい。"

contentType='application/json',
accept='application/json',
  

# セッションステートに agent が無ければ初期化
if "client" not in st.session_state:
    # Agent の作成
    client = boto3.client('bedrock-agentcore', region_name="us-east-1")
    st.session_state.client = client

# チャット履歴保存用のセッションを初期化
if "chat_log" not in st.session_state:
    st.session_state.chat_log = []

# タイトル設定
st.title("Bedrock AgentCore Runtime チャット")


if prompt := st.chat_input("質問を入力してください。"):
    # 以前のチャットログを表示
    messages = st.session_state.chat_log
    for message in messages:
      with st.chat_message(message["role"]):
          st.write(message["msg"])
    
    with st.chat_message(USER):
        st.markdown(prompt)

    with st.chat_message(ASSISTANT):

        with st.spinner("回答を生成中..."):
            message_placeholder = st.empty()
            # Agent への問い合わせ実行
            payload = json.dumps({"prompt": prompt}).encode()
            response = st.session_state.client.invoke_agent_runtime(
              agentRuntimeArn='arn:aws:bedrock-agentcore:us-east-1:068048081706:runtime/my_agent-WQYg5iA14o',
              payload=payload
            )
            response_body = response['response'].read()
            response_data = json.loads(response_body)
            result = response_data['result']["content"][0]["text"]
            # 実行結果の表示
            st.write(result)
    
    # セッションにチャットログを追加
    st.session_state.chat_log.append({"role": USER, "msg": prompt})
    st.session_state.chat_log.append({"role": ASSISTANT, "msg": result})

   

