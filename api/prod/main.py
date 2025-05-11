import uvicorn

def main():
	uvicorn.run(
		'app:app',
		host='0.0.0.0',
		port=8000,
		workers=1,
		log_level='info',
		use_colors=True
	)

if __name__ == '__main__':
	main()
