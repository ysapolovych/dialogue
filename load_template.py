import os
from pydantic import BaseModel, field_validator
import yaml


class DialogueTemplate(BaseModel):
    socrates: str
    user: str

    @field_validator("socrates", "user")
    @classmethod
    def check_socrates_system_message(cls, val: str):
        if "{topic}" not in val or "{name}" not in val:
            raise ValueError(
                "System prompt must contain fields {topic} for a discussion topic"
                "and {name} for interlocutor name."
            )
        return val


DEFAULT_TEMPLATE: DialogueTemplate = DialogueTemplate(
    socrates=(
        "You are Socrates, the wisest man in Athens. You would like to get to the bottom of {topic}."
        "You speak to {name}, an old friend from Syracuse"
        "Be perceptive and critical of what your interlocutor says."
        ),
    user=(
        "You are {name}, a Syracusan speaking to Socrates, a philosopher whose reputation speaks for itself."
        "Today you feel like talking about {topic}. Be respectful but critical."
    )
)


def load_template(
    template_path: str | os.PathLike = "templates/example_template.yaml",
) -> DialogueTemplate:
    """
    Loads a template from template.yaml under key template_name.
    Validates that the template dict has at least 'system' and 'human' and that the system string
    contains the required substitutions.
    Returns a dictionary representing the template.
    """
    try:
        with open(template_path, "r", encoding="utf8") as f:
            template_dict: dict[str, dict[str, str]] = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"{template_path} not found")

    template: DialogueTemplate = DialogueTemplate.model_validate(template_dict)

    return template
