import json
import os
os.chdir(r"C:\aiml cohort")
print("PWD:", os.getcwd())
#print("Does hello.py exist?", os.path.exists("hello.py"))

import requests
from dotenv import load_dotenv
import google.generativeai as genai
import subprocess
load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')


def run_command(command):
    result = os.system(command=command)
    return result

def get_weather(city: str):
    # TODO!: Do an actual API Call
    print("🔨 Tool Called: get_weather", city)
    
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)

    if response.status_code == 200:
        return f"The weather in {city} is {response.text}."
    return "Something went wrong"

def write_file(file_path, content):
    with open(file_path, "w") as f:
        f.write(content)
    return f"File '{file_path}' created successfully."



 
avaiable_tools = {
    "get_weather": {
        "fn": get_weather,
        "description": "Takes a city name as an input and returns the current weather for the city"
    },
    "run_command": {
        "fn": run_command,
        "description": "Takes a command as input to execute on system and returns ouput"
    },
    "write_file": {
    "fn": write_file,
    "description": "Creates or overwrites a file with the specified content"
}
    

}

system_prompt = f"""
    You are an helpfull AI Assistant who is specialized in resolving user query.
    You work on start, plan, action, observe mode.
    For the given user query and available tools, plan the step by step execution, based on the planning,
    select the relevant tool from the available tool. and based on the tool selection you perform an action to call the tool.
    Wait for the observation and based on the observation from the tool call resolve the user query.
    You are running on a Windows system. Always generate Windows command-line commands:
    - Use `dir` instead of `ls`
    - Use `type` instead of `cat`
    - Use `del` or `rmdir` instead of `rm`
    - Avoid using `chmod`, it's not available
    - Use `echo some code > file.py` or `with open()` in Python for writing files
    -listen, when the user ask you to simply create a file and write something to it then use write file tool; unless the user ask you to run it,but for small tasks like simply running commands ,creatiing file,folder use run command tool.
    now- Before using write_file, always check if the file already exists using os.path.exists.
        Never overwrite an existing file unless the user explicitly says "overwrite" or "create new file".
        If the user says "run file", just use run_command("python filename.py") after checking the file exists.
        If the file exists, do not attempt to create it again.
        Always confirm the working directory using os.getcwd() and make sure it is correct.
        Avoid assumptions — ask user before overwriting or creating new files.
        When checking the current directory, trust the output of the run_command("cd") or os.getcwd() command. If the output contains a valid path, do not assume failure unless there is an actual error or traceback.
        Always trust the output of run_command("cd") or run_command("dir") if a valid directory or file path is present in the output. Do not assume failure unless an actual error or missing file is confirmed through a second check using os.path.exists() or os.getcwd().
        Before running or creating any file, always use os.path.exists(filename) to double-check existence, regardless of prior assumptions.

    Rules:
    - Follow the Output JSON Format.
    - Always perform one step at a time and wait for next input
    - Carefully analyse the user query

    Output JSON Format:
    {{
        "step": "string",
        "content": "string",
        "function": "The name of function if the step is action",
        "input": "The input parameter for the function",
    }}

    Available Tools:
    - get_weather: Takes a city name as an input and returns the current weather for the city
    - run_command: Takes a command as input to execute on system and returns ouput
    - write_file:  Creates or overwrites a file with the specified content
    Example:
    User Query: What is the weather of new york?
    Output: {{ "step": "plan", "content": "The user is interseted in weather data of new york" }}
    Output: {{ "step": "plan", "content": "From the available tools I should call get_weather" }}
    Output: {{ "step": "action", "function": "get_weather", "input": "new york" }}
    Output: {{ "step": "observe", "output": "12 Degree Cel" }}
    Output: {{ "step": "output", "content": "The weather for new york seems to be 12 degrees." }}
"""

messages = [
    { "role": "user", "parts": [system_prompt] }
]

while True:
    user_query = input('> ')
    messages.append({ "role": "user", "parts": [user_query] })

    while True:
        response = model.generate_content(
            contents=messages,
            generation_config={"response_mime_type": "application/json"}
        )
        print(response.text)  

        parsed_output = json.loads(response.text)
        messages.append({ "role": "model", "parts": [json.dumps(parsed_output)] })

        if parsed_output.get("step") == "plan":
            print(f"🧠: {parsed_output.get('content')}")
            continue

        if parsed_output.get("step") == "action":
            tool_name = parsed_output.get("function")
            tool_input = parsed_output.get("input")

            if avaiable_tools.get(tool_name, False):
                tool_fn = avaiable_tools[tool_name]["fn"]

                if tool_name == "write_file":
                    # Expecting input as a dict like: {"filename": "hello.py", "content": "print(2+3)"}
                    filename = tool_input.get("filename")
                    content = tool_input.get("content")
                    output = tool_fn(filename, content)
                else:
                    output = tool_fn(tool_input)

                messages.append({ "role": "user", "parts": [json.dumps({ "step": "observe", "output":  output})] })
                continue

        if parsed_output.get("step") == "output":
            print(f"🤖: {parsed_output.get('content')}")
            break




