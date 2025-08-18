import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"  # Change if your backend runs elsewhere


def test_create_prompt():
    """Test creating a prompt"""
    url = f"{BASE_URL}/prompts/"
    payload = {
        "name": "Test Prompt",
        "content": "This is a test prompt",
        "tenant_id": 1
    }
    response = requests.post(url, json=payload)
    pprint("Create Prompt:", response.status_code, response.json())
    return response.json().get("id")


def test_get_prompt(prompt_id: int):
    """Test retrieving a prompt"""
    url = f"{BASE_URL}/prompts/{prompt_id}"
    response = requests.get(url)
    pprint("Get Prompt:", response.status_code, response.json())


def test_list_prompts():
    """Test listing all prompts"""
    url = f"{BASE_URL}/prompts/"
    response = requests.get(url)
    pprint("List Prompts:", response.status_code, response.json())


def run_all_tests():
    prompt_id = test_create_prompt()
    if prompt_id:
        test_get_prompt(prompt_id)
    test_list_prompts()


if __name__ == "__main__":
    run_all_tests()
