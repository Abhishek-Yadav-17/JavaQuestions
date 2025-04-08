import os
import subprocess
import google.generativeai as genai
import re
import datetime
import sys
import json # Added for parsing Gemini's question response
from dotenv import load_dotenv
import time # Added for potential rate limiting

# --- Configuration ---
load_dotenv()
API_KEY = "AIzaSyDmcJtvzo5ZAnvf2KebPPaTWc-cUCbiTe0"
OUTPUT_DIR = "java_solutions"
LOG_FILE = "solver.log"
GEMINI_MODEL = 'gemini-1.5-flash' # Or 'gemini-pro' or other compatible model

# --- Helper Functions ---

# --- Helper Function to Run Shell Commands ---
def run_command(command, cwd=None):
    """Runs a shell command and returns its output or raises an exception."""
    print(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            check=True,         # Raise CalledProcessError if command returns non-zero exit code
            capture_output=True,# Capture stdout and stderr
            text=True,          # Decode stdout/stderr as text
            cwd=cwd             # Set working directory if provided
        )
        print("STDOUT:\n", result.stdout)
        if result.stderr:
            print("STDERR:\n", result.stderr)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(command)}")
        print("Return Code:", e.returncode)
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)

def log_message(message):
    """Appends a timestamped message to the log file and prints it."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    try:
        # Use absolute path for cron reliability
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_filepath = os.path.join(script_dir, LOG_FILE)
        with open(log_filepath, "a") as f:
            f.write(full_message + "\n")
    except Exception as e:
        print(f"[{timestamp}] Error writing to log file {log_filepath}: {e}")

def configure_gemini():
    """Configures the Gemini API client."""
    if not API_KEY:
        log_message("Error: GEMINI_API_KEY environment variable not set.")
        return None
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel(GEMINI_MODEL)
        log_message(f"Gemini API configured with model '{GEMINI_MODEL}'.")
        return model
    except Exception as e:
        log_message(f"Error configuring Gemini API: {e}")
        return None

def generate_safe_filename(title):
    """Generates a safe filename from a question title."""
    # Remove invalid chars, replace spaces with underscores, lowercase
    safe_title = re.sub(r'[^\w\-]+', '_', title).lower()
    # Avoid excessively long filenames
    return safe_title[:50] # Limit length

def extract_json_block(text):
    """Extracts the first JSON block ({} or []) from a string."""
    # Regex to find content within ```json ... ``` or the first standalone { ... } or [ ... ]
    json_block_match = re.search(r"```json\s*({.*?}|\[.*?\])\s*```", text, re.DOTALL)
    if json_block_match:
        log_message("Found JSON block inside ```json ... ```")
        return json_block_match.group(1)

    # Fallback: find the first occurrence of { ... } or [ ... ]
    # This is less precise but handles cases where markdown isn't used
    first_brace = text.find('{')
    first_bracket = text.find('[')

    if first_brace == -1 and first_bracket == -1:
        log_message("No JSON block ({...} or [...]) found in the text.")
        return None

    start_index = -1
    if first_brace != -1 and first_bracket != -1:
        start_index = min(first_brace, first_bracket)
    elif first_brace != -1:
        start_index = first_brace
    else: # first_bracket != -1
        start_index = first_bracket

    # Try to find the corresponding closing bracket/brace
    # This is a simplified approach and might fail for nested structures if not careful
    # It assumes the first '{' or '[' marks the beginning of the desired JSON
    text_subset = text[start_index:]
    if text_subset.startswith('{'):
        match = re.search(r"(\{.*?\})(?:\s*\Z|\s*\n)", text_subset, re.DOTALL) # Non-greedy search for }
    else: # starts with '['
        match = re.search(r"(\[.*?\])(?:\s*\Z|\s*\n)", text_subset, re.DOTALL) # Non-greedy search for ]

    if match:
         log_message("Found standalone JSON block ({...} or [...]).")
         return match.group(1)
    else:
        log_message("Could not accurately extract standalone JSON block.")
        return None


def get_leetcode_question_from_gemini(model):
    """
    Uses Gemini API to generate a LeetCode-style question.
    Returns a dictionary with question details or None on failure.
    """
    if not model:
        log_message("Gemini model not configured for question generation.")
        return None

    log_message("Generating LeetCode question using Gemini...")
    prompt = """
    Generate a LeetCode-style programming problem suitable for solving in Java.
    The difficulty should be easy or medium.
    Provide the output STRICTLY as a JSON object containing the following keys:
    - "title": A concise title for the problem (string).
    - "description": A clear description of the problem (string).
    - "constraints": A list of constraints for the input/output (list of strings).
    - "examples": A list of example inputs and outputs, clearly formatted (list of strings).

    Example JSON format:
    {
      "title": "Example Problem Title",
      "description": "Detailed description of what the function should do.",
      "constraints": ["Constraint 1", "Constraint 2"],
      "examples": ["Input: nums = [1, 2], target = 3\nOutput: [0, 1]", "Input: nums = [4, 5], target = 9\nOutput: [0, 1]"]
    }

    Do NOT include any text before or after the JSON object. Just output the raw JSON.
    """

    try:
        response = model.generate_content(prompt)
        log_message("Received question generation response from Gemini.")
        # log_message(f"Raw Question Response Text:\n{response.text}") # Uncomment for debugging

        # Extract JSON potentially embedded in markdown or with surrounding text
        json_string = extract_json_block(response.text)

        if not json_string:
            log_message("Error: Could not extract JSON block from Gemini's question response.")
            log_message(f"Full Response: {response.text}")
            return None

        log_message("Attempting to parse JSON data for the question...")
        question_data = json.loads(json_string)

        # Basic validation
        required_keys = ["title", "description", "constraints", "examples"]
        if not all(key in question_data for key in required_keys):
            log_message(f"Error: Generated JSON is missing required keys. Found: {list(question_data.keys())}")
            return None
        if not isinstance(question_data["constraints"], list) or not isinstance(question_data["examples"], list):
             log_message(f"Error: 'constraints' or 'examples' is not a list in the generated JSON.")
             return None

        # Generate an 'id' from the title for filename safety
        question_data['id'] = generate_safe_filename(question_data['title'])

        log_message(f"Successfully generated and parsed question: '{question_data['title']}'")
        return question_data

    except json.JSONDecodeError as e:
        log_message(f"Error: Failed to decode JSON from Gemini response: {e}")
        log_message(f"Extracted Text that failed parsing: {json_string}")
        return None
    except Exception as e:
        log_message(f"Error during Gemini question generation call: {e}")
        # Consider adding a small delay before retrying or exiting if it's a rate limit issue
        if "rate limit" in str(e).lower():
             log_message("Rate limit likely exceeded. Consider increasing cron interval.")
        return None


def generate_java_solution(model, question_data):
    """Uses Gemini API to generate a Java solution for the given question data."""
    if not model:
        log_message("Gemini model not configured for solution generation.")
        return None
    if not question_data:
        log_message("Error: No question data provided for solution generation.")
        return None

    log_message(f"Generating Java solution for '{question_data.get('title', 'Unknown Problem')}'...")

    prompt = f"""
    You are an expert Java programmer specializing in LeetCode problems.
    Solve the following LeetCode problem and provide ONLY the complete, runnable Java class solution.
    Include necessary imports (like java.util.* if needed). Use standard Java conventions.
    The main logic should be within a method, typically named based on the problem title or description (e.g., using camelCase).
    Enclose the final Java code within ```java ... ``` markdown blocks.
    Do not add any explanation, commentary, or text outside the code block.

    Problem Title: {question_data.get('title', 'N/A')}

    Problem Description:
    {question_data.get('description', 'N/A')}

    Constraints:
    {'; '.join(question_data.get('constraints', []))}

    Examples:
    {' | '.join(question_data.get('examples', []))}

    Provide the Java code now:
    ```java
    // Start Java code here
    ```
    """

    try:
        log_message("Sending solution request to Gemini API...")
        response = model.generate_content(prompt)
        log_message("Received solution response from Gemini.")
        # log_message(f"Raw Solution Response Text:\n{response.text}") # Uncomment for debugging
        return response.text

    except Exception as e:
        log_message(f"Error during Gemini solution generation call: {e}")
        if "rate limit" in str(e).lower():
             log_message("Rate limit likely exceeded. Consider increasing cron interval or adding delays.")
        return None

def extract_java_code(raw_response):
    """Extracts the Java code block from the Gemini response."""
    if not raw_response:
        return None

    match = re.search(r"```java\s*(.*?)\s*```", raw_response, re.DOTALL)
    if match:
        log_message("Java code block found and extracted.")
        return match.group(1).strip()
    else:
        log_message("Warning: Could not find ```java ... ``` block in the solution response. Attempting to return raw response as code.")
        # Fallback - be cautious, might include unwanted text.
        # If the prompt is strictly followed by Gemini, this might not be needed.
        # Check if the raw response looks like Java code (simple check)
        if "class" in raw_response and "public" in raw_response and ("{" in raw_response and "}" in raw_response):
             return raw_response.strip()
        else:
             log_message("Raw response does not appear to be Java code. Extraction failed.")
             return None


def save_solution(question_id, java_code):
    """Saves the Java code to a file using the question_id."""
    if not java_code:
        log_message("No Java code provided to save.")
        return
    if not question_id:
        log_message("No question ID provided for saving.")
        question_id = "unknown_solution" # Fallback ID

    try:
        # Use absolute path for cron reliability
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, OUTPUT_DIR)
        log_message(f"Ensuring output directory '{output_path}' exists...")
        os.makedirs(output_path, exist_ok=True)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{question_id}_{timestamp}.java"
        filepath = os.path.join(output_path, filename)

        log_message(f"Saving Java solution to '{filepath}'...")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(java_code)
        log_message(f"Successfully saved '{filename}'.")

    except Exception as e:
        log_message(f"Error saving file '{filepath}': {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure logs and output are relative to the script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir) # Change current working directory

    log_message("--- Starting LeetCode Solver Script ---")

    # 1. Configure Gemini API Client
    gemini_model = configure_gemini()
    if not gemini_model:
        log_message("Failed to configure Gemini API. Exiting.")
        sys.exit(1)

    # 2. Get Question from Gemini
    question = get_leetcode_question_from_gemini(gemini_model)
    if not question:
        log_message("Failed to get LeetCode question from Gemini. Exiting.")
        sys.exit(1)

    # Optional: Add a small delay between API calls to avoid rate limits
    # time.sleep(5) # Sleep for 5 seconds

    # 3. Generate Java Solution using Gemini
    raw_solution_text = generate_java_solution(gemini_model, question)
    if not raw_solution_text:
        log_message("Failed to generate Java solution using Gemini. Exiting.")
        sys.exit(1)

    # 4. Extract Java Code
    java_code = extract_java_code(raw_solution_text)
    if not java_code:
         log_message("Failed to extract Java code from Gemini solution response. Exiting.")
         # Optional: Save raw response for debugging
         # save_solution(question.get('id', 'unknown') + "_raw_solution_response", raw_solution_text)
         sys.exit(1)

    # 5. Save Solution
    save_solution(question.get('id'), java_code) # Use the generated 'id'
    
    run_command(["git", "add", "."])

    log_message("--- LeetCode Solver Script Finished ---")