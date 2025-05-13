import json
import httpx

BASE_URL = 'http://api:8000'

admin_user = 'admin'
admin_pass = 'admin'
admin_code = 'admin_password'
student_user = 'student'
student_pass = 'student'
jwt_headers = {}

def create_user(username: str, password: str) -> httpx.Response:
	payload = {
		'username': username,
		'password': password
	}

	with httpx.Client() as client:
		response = client.post(f'{BASE_URL}/user', json=payload)
		print(f'User created: {response.text}')

	return response

def login(username: str, password: str) -> httpx.Response:
	payload = {
		'username': username,
		'password': password
	}
	headers = {'Content-Type': 'application/x-www-form-urlencoded'}

	with httpx.Client() as client:
		response = client.post(f'{BASE_URL}/token', data=payload, headers=headers)

		jwt = response.json()['access_token']
		print(f'Access token: {jwt}')

		jwt_headers['Authorization'] = f'Bearer {jwt}'

	return response

def api_call(method: str, endpoint: str, body: dict | None = None) -> httpx.Response:
	with httpx.Client() as client:
		response = client.request(
			method,
			f'{BASE_URL}{endpoint}',
			json=body,
			headers=jwt_headers
		)

		print(f'Response: HTTP{response.status_code} {response.reason_phrase}')
		if response.text:
			print(response.text)

	return response

def main():
	create_user(admin_user, admin_pass)
	res = create_user(student_user, student_pass)
	student_uid = res.text
	login(admin_user, admin_pass)

	api_call('POST', f'/admin/promote?code={admin_code}')

	with open('json/0_POST_quiz_0.json', 'r') as f:
		quiz_body = json.load(f)
		res = api_call('POST', '/admin/quiz', quiz_body)
		api_call('POST', f'/admin/assign?user={student_uid}&quiz={res.text}')

	with open('json/0_POST_quiz_1.json', 'r') as f:
		quiz_body = json.load(f)
		res = api_call('POST', '/admin/quiz', quiz_body)
		api_call('POST', f'/admin/assign?user={student_uid}&quiz={res.text}')

	login(student_user, student_pass)
	api_call('POST', f'/student/quiz/{res.text}/submit', {
		"page_idx": 0,
		"answers": [
			{
				"question_idx": 0,
				"answer_idx": 0
			},
			{
				"question_idx": 1,
				"answer_idx": 0
			}
		]
	})
	api_call('POST', f'/student/quiz/{res.text}/submit', {
		"page_idx": 1,
		"answers": [
			{
				"question_idx": 0,
				"answer_idx": 0
			},
			{
				"question_idx": 1,
				"answer_idx": 0
			}
		]
	})
	api_call('POST', f'/student/quiz/{res.text}/submit', {
		"page_idx": 2,
		"answers": [
			{
				"question_idx": 0,
				"answer_idx": 0
			}
		]
	})
	api_call('POST', f'/student/quiz/{res.text}/grade')

if __name__ == '__main__':
	main()
