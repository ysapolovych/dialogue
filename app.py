import os
import itertools
from pathlib import Path

from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
# from langchain.memory import ConversationBufferMemory
# from langchain.chains import ConversationChain

load_dotenv()

# colors
RED = "\033[91m"
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"  # Reset to default color

# memory = ConversationBufferMemory(k=5, memory_key="history")

# Create base models
socrates_model = ChatOpenAI(temperature=1.0, model_name="gpt-4o-mini")
interlocutor_model = ChatOpenAI(temperature=1.0, model_name="gpt-4o-mini")

socrates_template: ChatPromptTemplate = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are Socrates, the wisest man in Athens. You would like to get to the bottom of {topic}."
        "Be inventive and critical of what your interlocutor says. Question what may seem obvious."
        "Limit your response to 50 words."
        "Previous context: {context}"
    ),
    ("human", "{name}: {line}"),
    ("ai", "Socrates: ")
])

# Create prompt templates
interlocutor_template: ChatPromptTemplate = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are {name}, an Athenian speaking to Socrates, a philosopher whose reputation speaks for itself."
        "Today you feel like talking about {topic}. Be respectful but critical."
        "Limit your response to 50 words."
        "Previous context: {context}"
    ),
    ("human", "Socrates: {line}"),
    ("ai", "{name}: ")
])

# generic_line: ChatPromptTemplate = ChatPromptTemplate.from_messages([
#     ("system", "Limit your response to 50 words.\nPrevious context: {context}"),
#     ("human", "{prev_line}"),
#     ("ai", "{speaker}: ")
#     # add name?
# ])

def give_context(full_dialogue: list, n: int = 3):
    return "\n".join(full_dialogue[-3:])

def main():
    # chain1, chain2 = create_chains()

    full_dialogue: list = []

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
    starter_line = input("> ")
    print(f"{GREEN}{user_name}{RESET}: {starter_line}")

    full_dialogue.append(f"{user_name}: {starter_line}")

    speakers: dict[int, str] = {
        1: socrates_model,
        2: interlocutor_model,
    }

    speaker_names: dict[int, str] = {
        1: "Socrates",
        2: user_name,
    }

    speaker_colors: dict[int, str] = {
        1: RED,
        2: GREEN,
    }

    speaker_templates:  dict[int, ChatPromptTemplate] = {
        1: socrates_template,
        2: interlocutor_template,
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
    print("\n")

    # print(f"{RED}Socrates{RESET}: {socrates_first}")

    full_dialogue.append(f"Socrates: {line}")

    new_line: str = ""
    optional_line = input()
    if optional_line:
        line = optional_line
        print(f"{GREEN}{user_name}{RESET}: {new_line}")
    else:
        print(f"{GREEN}{user_name}{RESET}: ", end="")
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

        print("\n")

    full_dialogue.append(f"{user_name}: {new_line}\n")

    line = new_line

    while True:
        try:
            for current_speaker in itertools.cycle([1, 2]):
                if current_speaker == 2:
                    optional_line: str = input()
                    if optional_line:
                        line = optional_line

                        print(f"{speaker_colors[current_speaker]}{speaker_names[current_speaker]}{RESET}: {line}")

                        full_dialogue.append(f"{speaker_names[current_speaker]}: {line}")

                        continue
                # Select chain based on current speaker
                chain = speaker_templates[current_speaker] | speakers[current_speaker] | StrOutputParser()
                # Generate response using the chain
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

                print("\n")

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