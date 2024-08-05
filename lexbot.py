from openai import OpenAI
import pandas as pd
import pickle
import streamlit as st
from transliterate import transliterate


client = OpenAI(api_key=st.secrets["openai"])

def remove_duplicates(original_list):
  seen = set()
  unique_list = []
  for element in original_list:
    if element not in seen:
      unique_list.append(element)
      seen.add(element)
  return unique_list


# Open the file for reading in binary mode
with open('list_data_json.pkl', 'rb') as f:
  # Unpickle the list using the load() function
  loaded_list = pickle.load(f)


def get_first_words(text):
  words = text.split()
  if len(words) >= 3:
    return ' '.join(words[:3])
  else:
    return ' '.join(words)



def format_reference(cited_file):
    law = cited_file.Law_reference[0]
    law3 = get_first_words(law)
    title = cited_file.Law_title[0]
    if law3 == "O‘zbekiston Respublikasi Vazirlar":
        name = law[25:47]
        date = law[56:74].replace(' ','-')
        num = law[75:]
        full_r = f"{name} {date} {num} qaroriga ko'ra, "
        return full_r
    elif law3 == "":
        return title[:-1]+'ning '
    elif law3 == "O‘zbekiston Respublikasi Prezidentining":
        name = law[:39]
        date = law[48:66].replace(' ','-')
        num = law[67:]
        full_r = f"{name} {date} {num} qaroriga ko'ra, "
        return full_r
    elif law3 == "O‘zbekiston Respublikasining Qonuni,":
        name = title
        date = law[37:55].replace(' ','-')
        num = law[56:]
        full_r = f"O'zbekiston Respublikasining \"{name}\"gi {date} {num} Qonunining, "
        return full_r
    elif law3 == "O‘zbekiston Respublikasi Investitsiyalar":
        full_r = "Investitsiyalar va tashqi savdo vazirligi huzuridagi O‘zbekiston texnik jihatdan tartibga solish agentligi bosh direktorining 24.01.2022-yildagi 05-1370-son buyrug‘iga ko'ra, "
        return full_r
    elif law3 == "O‘zbekiston Respublikasi Transport":
        full_r = "Transport vazirligi va Raqamli texnologiyalar vazirligining 03.10.2023-yildagi 3462-son qaroriga ko'ra, "
        return full_r
    elif law3 == "O‘zbekiston Respublikasi transport":
        name = law[26:45]
        date = law[56:72].replace(' ','-')
        num = law[107:]
        full_r = f"T{name} {date}gi {num}-son buyrug'iga ko'ra, "
        return full_r
    elif law3 == "O‘zbekiston Respublikasi ichki":
        name = law[26:48]
        date = law[59:75].replace(' ','-')
        num = law[110:]
        full_r = f"I{name} {date}gi {num}-son buyrug'iga ko'ra, "
        return full_r




assistant = client.beta.assistants.update(
  assistant_id="asst_BPyNHTpeb5Tc0TQvMfTBxfvO",
  tool_resources={"file_search": {"vector_store_ids": ["vs_tr2AgxgQfwW8zNMnxUr2KRmP"]}},
)

def get_last_word(text):
  words = text.split()
  return words[-1]


def sred(question):
  thread = client.beta.threads.create(
    messages=[
      {
        "role": "user",
        "content": question,
      }
    ]
  )
  return thread


def get_answer(input):
  if len(input) > 5:
    input = transliterate(input, 'latin')
    thread = sred(input)

    run = client.beta.threads.runs.create_and_poll(
      thread_id=thread.id, assistant_id=assistant.id
    )

    messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    citations = []
    for index, annotation in enumerate(annotations):
      message_content.value = message_content.value.replace(annotation.text, f"[{index}]")
      if file_citation := getattr(annotation, "file_citation", None):
        cited_file = client.files.retrieve(file_citation.file_id)
        citations.append(f"{cited_file.filename[:-5]} [{index}]")
    links = ''


    try:
        for i in citations:
          links += f"https://lex.uz/docs/{i}\n"
        deta = pd.read_json(f"data1/{citations[0][:-4]}.json")
        final_answer = format_reference(deta) + message_content.value + "\n\n" + links
    except IndexError:
        final_answer = message_content.value
    return final_answer

  else:
    return "Savol juda kichkina(minimum 6 ta belgi kiriting)"





st.title("LexBot")
st.caption("Yo'l harakati qoidasiga doir barcha savollarinigizga javob oling")


if "messages" not in st.session_state:
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "assistant",
                "content": 'Sizga qanday yordam ber olaman',
            }
        ]
    )


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

