import streamlit as st
import time

st.set_page_config(
    layout="centered",
    page_icon="tt.jpg",
    page_title="BSK ICT Club | Python Coding",
    initial_sidebar_state="expanded"
)

st.title("BSK ICT Club Python Coding Quiz")

st.write("1. **What is the output of this code ?**")

code = "print('Hello World')"

st.code(code)

response = st.radio("Choose one",["Hello World","print('Hello World')"],disabled=False)

btn1 = st.button(label="Submit",type="primary",key=1)

if btn1:
    if response == "Hello World":
        st.write("✔ Your submission is correct")
    else:
        st.write("👎 Wrong response . Keep Trying")


code = '''
first_name = "Mpoza"
last_name = "Christopher"
print(first_name,last_name)
'''

st.sidebar.markdown("# :blue-background[About the BSK ICT Club]")

st.sidebar.markdown("> :red[The BSK ICT Club was started in 2022 by Tumwine Kelly.\n It was founded with an aim of promoting earlier exposure of students to advanced technology in areas of of coding, robotics , artificial intelligence, etc.]")

st.sidebar.subheader("Why this Quiz ?")
st.sidebar.radio("Hey",["Hands on Learning","Real time feedback"])

st.sidebar.markdown(" ##### :green-background[Kindly subscribe to our newsletter]")

name = st.sidebar.text_input(label="Your Surname : ")
email = st.sidebar.text_input(label="Email Address : ")

btn0 = st.sidebar.button(label="Subscribe...")

if btn0:
    if name and email:
        st.sidebar.write(f"Thanks {name} for subscribing to our newsletter .")
    else:
        pass

st.write("2. **Now guess the output of this ...**")

st.code(code,language="python")

response2 = st.radio("Choose one",["MpozaChristopher","print('Mpoza','Christopher')","Mpoza Christopher"])

btn2 = st.button(label="Submit",type="primary",key=2)

if btn2:
    if response2 == "Mpoza Christopher":
        st.write("✔ Your submission is correct")
    else:
        st.write("👎 Wrong response . Keep Trying")

st.write("3. **What data type is this ?**")

code = """
names = {'Mpoza','Mark','Christopher','Henry','Mark'}
"""

st.code(code,language="python")

response2 = st.radio("Choose one",["List","Set","Dictionary"])

btn2 = st.button(label="Submit",type="primary",key=3)

if btn2:
    if response2 == "Set":
        st.write("✔ Your submission is correct")
    else:
        st.write("👎 Wrong response . Keep Trying")


st.write("4. **What type of operators are these in python ?** ")

code = "+ , - ,* , / "

st.code(code)

response3 = st.radio("Choose one",["Assignment operators","Arithmetic Operators","Logical operators","Comparison operators","Membership operators"])

btn2 = st.button(label="Submit",type="primary",key=4)

if btn2:
    if response3 == "Arithmetic Operators":
        st.write("✔ Your submission is correct")
    else:
        st.write("👎 Wrong response . Keep Trying")
    time.sleep(5)
    st.markdown("### :green-background[Congratulations ....! You've made it to the end of this level ]")

    st.button("Next Level")
