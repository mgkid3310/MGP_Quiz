import json
import httpx

BASE_URL = 'http://api:8000'

username = 'admin'
password = 'admin'
jwt_header = {}

def create_user(username: str, password: str) -> None:
	payload = {
		'username': username,
		'password': password
	}

	with httpx.Client() as client:
		response = client.post(f'{BASE_URL}/user', json=payload)
		print(f'User created: {response.text}')

def login(username: str, password: str) -> None:
	payload = {
		'username': username,
		'password': password
	}
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}

	with httpx.Client() as client:
		response = client.post(f'{BASE_URL}/token', data=payload, headers=headers)

		jwt = response.json()['access_token']
		print(f'Access token: {jwt}')

		jwt_header['Authorization'] = f'Bearer {jwt}'

def api_call(method: str, endpoint: str, body: dict | None = None) -> None:
	with httpx.Client() as client:
		response = client.request(
			method,
			f'{BASE_URL}{endpoint}',
			json=body,
			headers=jwt_header
		)

		print(f'Response: HTTP{response.status_code} {response.reason_phrase}')
		if response.text:
			print(response.text)

def main():
	create_user(username, password)
	login(username, password)

	api_call('POST', '/admin/promote?code=admin_password')

	with open('json/0_POST_quiz_0.json', 'r') as f:
		quiz_body = json.load(f)

	api_call('POST', '/admin/quiz', quiz_body)

if __name__ == '__main__':
	main()
