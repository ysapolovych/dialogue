import itertools
import logging
import os
from pathlib import Path
import warnings
import sys

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationChain

from load_template import load_template, DialogueTemplate, DEFAULT_TEMPLATE
from load_config import load_config, Config


load_dotenv()


def input_no_newline(prompt=""):
    sys.stdout.write(prompt)
    sys.stdout.flush()
    line: str = sys.stdin.readline()
    if line == '\n':  # Empty line (just Enter pressed)
        sys.stdout.write('\033[F\033[' + str(len(prompt)) + 'C')  # Move up and right
        sys.stdout.write('\033[K') # Clear from cursor to end of line
        sys.stdout.flush()
    else:
        # For non-empty input, move cursor up and after the input
        sys.stdout.write('\033[F\033[' + str(len(prompt) + len(line.rstrip('\n'))) + 'C')
        sys.stdout.flush()
    return line.rstrip('\n')


# while True:
#     name = input_no_newline("Enter name: ")
#     if not name:
#         print("hi", end='')
#     print()


def template_selection() -> DialogueTemplate:
    print("Would you like to see available custom templates for system prompts? (y/n):")
    answer = input("> ")

    if answer.lower() == 'y':
        template_dir: Path = Path("templates")
        files: list[Path] = list(template_dir.glob("*.yaml"))

        if not files:
            print("No YAML templates found in templates directory. Proceeding with default template.")
            return DEFAULT_TEMPLATE
        print("Available templates:")

        for i, file in enumerate(files, start=1):
            print(f"{i}: {file.name}")
        print("Enter the number of the template you want to load (type \"d\" for default)")
        selection: str = input("> ")

        if selection == "d":
            return DEFAULT_TEMPLATE

        try:
            index: int = int(selection) - 1
            chosen_file: Path = files[index]
        except (ValueError, IndexError):
            print(f"Invalid {selection}.")
            return template_selection()

        return load_template(chosen_file)

    return DEFAULT_TEMPLATE


def give_context(full_dialogue: list, n: int = 3):
    return "\n".join(full_dialogue[-3:])

def color_speaker(name: str, color=str) -> str:
    return f"{color}{name}{RESET}"

def clear_user_input(input_: str, colored_name: str) -> str:
    return input_.replace(f"{colored_name}: ", "")


# colors
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset to default color
PURPLE = "\033[95m"
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'

# hide warnings in non-debug mode
DEBUG_MODE = os.getenv("DEBUG", "").lower() in ("true", "1", "yes")
if not DEBUG_MODE:
    warnings.filterwarnings("ignore", category=UserWarning, module="langchain")
    logging.getLogger("langchain").setLevel(logging.ERROR)

# memory = ConversationBufferMemory(k=5, memory_key="history")

config = load_config()
print(PURPLE + "Configuration Loaded. You may change it by editing config.yaml file" + RESET)
for key, value in config.model_dump().items():
    print(PURPLE + f"{key}: {value}" + RESET, end=" | ")
print("")

# Create base models
socrates_model = ChatOpenAI(temperature=1.0, model_name="gpt-4o-mini")
user_model = ChatOpenAI(temperature=1.0, model_name="gpt-4o-mini")


def main():
    full_dialogue: list = []

    system_templates: DialogueTemplate = template_selection()

    socrates_template: ChatPromptTemplate = ChatPromptTemplate.from_messages([
        (
            "system",
            f"{system_templates.socrates}"
            "Your response should be between 10 and 50 words long."
            "Previous context: {context}"
        ),
        ("human", "{name}: {line}"),
        ("ai", "Socrates: ")
    ])

    # Create prompt templates
    user_template: ChatPromptTemplate = ChatPromptTemplate.from_messages([
        (
            "system",
            f"{system_templates.user}"
            "Your response should be between 10 and 50 words long."
            "Previous context: {context}"
        ),
        ("human", "Socrates: {line}"),
        ("ai", "{name}: ")
    ])

    print(
        "We'll try to write a Platonic dialogue with AI.\n"
        "You'll need to write the first line, and then language models will do things for you.\n"
        "After Socrates voices his opinion, you may click Return to proceed or write a line yourself if you'd like to interfere.\n"
        "Let's start by providing your name:"
    )
    user_name = input("> ")
    print("You would like to talk about:")
    topic = input("> ")
    print("Enter your first line to kick things off:")
    starter_line = input(f"{GREEN}{user_name}{RESET}: ")
    # print(f"{GREEN}{user_name}{RESET}: {starter_line}")

    full_dialogue.append(f"{user_name}: {starter_line}")

    speakers: dict[int, str] = {
        1: socrates_model,
        2: user_model,
    }

    speaker_names: dict[int, str] = {
        1: "Socrates",
        2: user_name,
    }

    speaker_colors: dict[int, str] = {
        1: color_speaker("Socrates", RED),
        2: color_speaker(user_name, GREEN),
    }

    speaker_templates:  dict[int, ChatPromptTemplate] = {
        1: socrates_template,
        2: user_template,
    }

    starting_chain = speaker_templates[1] | speakers[1] | StrOutputParser()

    line: str = ""
    print(f"{RED}Socrates{RESET}: ", end="")
    for chunk in starting_chain.stream(
        {
            "topic": topic,
            "name": user_name,
            "line": starter_line,
            "context": ""
        }
    ):
        print(chunk, end="")
        line += chunk
    print()

    # print(f"{RED}Socrates{RESET}: {socrates_first}")

    full_dialogue.append(f"Socrates: {line}")

    new_line: str = ""
    # user_input: str = clear_user_input(
    #     input_no_newline(f"{speaker_colors[2]}: "),
    #     speaker_colors[2],
    # )
    user_input: str = input_no_newline(f"{speaker_colors[2]}:")
    if len(user_input) > 0:
        new_line = user_input
        # print()
        # print(f"{color_speaker(user_name, GREEN)}: {new_line}")
    else:
        # print(f"{GREEN}{user_name}{RESET}: ", end="")
        response_chain = speaker_templates[2] | speakers[2] | StrOutputParser()
        # Get the interlocutor's response
        for chunk in response_chain.stream({
            "name": user_name,
            "topic": topic,
            "line": line,
            "context": give_context(full_dialogue),
        }):
            print(chunk, end="")
            new_line += chunk

        print()

    full_dialogue.append(f"{user_name}: {new_line}\n")

    line = new_line

    while True:
        try:
            for current_speaker in itertools.cycle([1, 2]):
                user_input: str = input_no_newline(
                    f"{speaker_colors[current_speaker]}:" if current_speaker != 1 else ""
                )
                if current_speaker == 2 and len(user_input) > 0:
                    line = user_input
                    # print(f"{speaker_colors[current_speaker]}{speaker_names[current_speaker]}{RESET}: {line}")
                    full_dialogue.append(f"{speaker_names[current_speaker]}: {line}")
                    continue

                # Create chain based on current speaker
                chain = speaker_templates[current_speaker] | speakers[current_speaker] | StrOutputParser()

                new_line: str = ""

                print(f"{speaker_colors[current_speaker]}{speaker_names[current_speaker]}{RESET}: ", end="")
                for chunk in chain.stream({
                    "line": line,
                    "topic": topic,
                    "name": speaker_names[current_speaker],
                    "context": give_context(full_dialogue),
                }):
                    print(chunk, end="")
                    new_line += chunk

                print()

                full_dialogue.append(f"{speaker_names[current_speaker]}: {line}")

                line = new_line

        except Exception as e:
            print(f"Spartans are attacking! {e}")
            break

        finally:
            print("If you'd like to save the dialogue, enter its name or a full path. Otherwise press Return")

            name_or_str_path: str = input("> ")

            if name_or_str_path:
                out_path: Path = Path(name_or_str_path).with_suffix(".txt")

                with out_path.open(mode="w", encoding="utf8") as f:
                    f.write("\n".join(full_dialogue))

                print(f"Dialogue saved to {out_path.resolve()}")



if __name__ == "__main__":
    main()