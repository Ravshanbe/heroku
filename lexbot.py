from openai import OpenAI
import time
import pandas as pd
import pickle
import streamlit as st
from transliterate import transliterate


openai_client = OpenAI(api_key=st.secrets["openai"])


lexf = openai_client.beta.assistants.retrieve("asst_gvG9B9hktrD3wVEtMC01tX4x")

def create_thread(query: str):

    query = transliterate(query, to_variant='latin')
    thread = openai_client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": query,
            }
        ]
    )
    return thread


def get_answer(input):
  if len(input) > 5:
    thread = create_thread(input)

    run = openai_client.beta.threads.runs.create_and_poll(
      thread_id=thread.id, assistant_id=lexf.id
    )
    count=0
    status = run.status
    while (status != 'completed'):
        if count == 100:
            break
        count+=1
        time.sleep(1)
        status = run.status
        
    messages = list(openai_client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    for index, annotation in enumerate(annotations):
      message_content.value = message_content.value.replace(annotation.text, '')




    return message_content.value

  else:
    return "Savol juda kichkina(minimum 6 ta belgi kiriting)"





st.title("LexF")
st.caption("O'zbekiston qonun qoidalariga doir savollarga javob beraman.")


if "messages" not in st.session_state:
    st.session_state["messages"]=[
        {
            "role": "assistant",
            "content": 'Sizga qanday yordam ber olaman',
        }
    ]


if prompt := st.chat_input("Savol qoldiring..."):
    with st.chat_message("user"):
      st.write(prompt)
    message = get_answer(prompt)
    with st.chat_message("assistant"):
      st.write(message)
    # st.session_state.messages.append({"role": "user", "content": prompt})
    # st.chat_message("user").write(prompt)
    # response = client.chat.completions.create(model="gpt-3.5-turbo", messages=st.session_state.messages)
    # msg = response.choices[0].message.content
    # st.session_state.messages.append({"role": "assistant", "content": msg})
    # st.chat_message("assistant").write(msg)

