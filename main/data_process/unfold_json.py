import json
import re

def expand_json_data(file_path):
    """
    Loads a JSON file, expands nested JSON strings in 'source_text' and 'response' fields,
    and returns the processed data as a Python list of dictionaries.

    Args:
        file_path (str): The path to the input JSON file.

    Returns:
        list: A list of dictionaries with nested JSON strings parsed into objects.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
        return None

    expanded_data = []

    for item in data:
        processed_item = {
            "index": item.get("index"),
            "image_path": item.get("image_path"),
        }

        # --- Process the 'source_text' field ---
        source_text = item.get("source_text", "")
        # Find the JSON part of the string, which starts with '{' and ends with '}'
        match = re.search(r'{.*}', source_text, re.DOTALL)
        if match:
            json_string = match.group(0)
            try:
                processed_item["source_text"] = json.loads(json_string)
            except json.JSONDecodeError:
                # If parsing fails, keep the original text
                processed_item["source_text"] = source_text
        else:
            # If no JSON object is found, keep the original text
            processed_item["source_text"] = source_text

        # --- Process the 'response' field ---
        response_text = item.get("response", "")
        # Clean the string by removing markdown code fences
        cleaned_response = re.sub(r'```json\n|```', '', response_text).strip()
        if cleaned_response:
            try:
                processed_item["response"] = json.loads(cleaned_response)
            except json.JSONDecodeError:
                # If parsing fails, keep the original text
                processed_item["response"] = response_text
        else:
            processed_item["response"] = response_text
            
        expanded_data.append(processed_item)

    return expanded_data

# --- Main execution ---
# Replace 'results_part2.json' with the actual path to your file if it's different.
file_to_process = 'results_part3.json'
final_data = expand_json_data(file_to_process)

if final_data:
    # Print the expanded data in a readable, indented JSON format
    with open('expanded_results_part3.json', 'w', encoding='utf-8') as output_file:
        json.dump(final_data, output_file, indent=2, ensure_ascii=False)
    # print(json.dumps(final_data, indent=2, ensure_ascii=False))