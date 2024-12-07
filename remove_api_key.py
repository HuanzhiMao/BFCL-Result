import glob
import json
import os

ENV_VARS = ("GEOCODE_API_KEY", "RAPID_API_KEY", "OMDB_API_KEY", "EXCHANGERATE_API_KEY")
PLACEHOLDERS = {}

"""
This script is the _apply_function_credential_config.py, but reversed. It replaces the actual API keys with placeholders.
"""


def replace_placeholders(data):
    """
    Recursively replace placeholders in a nested dictionary or list using string.replace.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                replace_placeholders(value)
            elif isinstance(value, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in value:
                        data[key] = value.replace(placeholder, actual_value)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                replace_placeholders(item)
            elif isinstance(item, str):
                for placeholder, actual_value in PLACEHOLDERS.items():
                    if placeholder in item:
                        data[idx] = item.replace(placeholder, actual_value)
    return data


def process_file(input_file_path, output_file_path):
    changed = False
    modified_data = []

    with open(input_file_path, "r") as f:
        original_lines = f.readlines()

    for line in original_lines:

        try:
            data = json.loads(line)
            original_data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

            replaced_data = replace_placeholders(data)
            modified_data_str = json.dumps(
                replaced_data, ensure_ascii=False, separators=(",", ":")
            )

            if modified_data_str != original_data_str:
                changed = True

            modified_data.append(modified_data_str)

        except json.JSONDecodeError:
            # The line is not valid JSON, we skip it.
            # Skipping it means this file is changed compared to original.
            changed = True
            continue

    # Only write if there's a change
    if changed:
        with open(output_file_path, "w") as f:
            for i, modified_line in enumerate(modified_data):
                if modified_line:  # If not an empty line we attempted to skip
                    f.write(modified_line)
                if i < len(modified_data) - 1:
                    f.write("\n")
        print(f"Changes applied to {output_file_path}")


def process_dir(input_dir, output_dir):
    entries = os.scandir(input_dir)
    json_files_pattern = os.path.join(input_dir, "*.json")
    for input_file_path in glob.glob(json_files_pattern):
        file_name = os.path.basename(input_file_path)
        output_file_path = os.path.join(output_dir, file_name)
        process_file(input_file_path, output_file_path)

    subdirs = [entry.path for entry in entries if entry.is_dir()]
    for subdir in subdirs:
        process_dir(subdir, subdir)


if __name__ == "__main__":
    # Load the actual API keys, and verify that they are present
    for var in ENV_VARS:
        if var not in os.environ or not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set.")
        PLACEHOLDERS[os.getenv(var)] = f"REDACTED_{var}"

    input_path = output_path = "./"

    if os.path.isdir(input_path):
        process_dir(input_path, output_path)
    else:
        process_file(input_path, output_path)

    print("All API keys have been replaced. 🦍")
