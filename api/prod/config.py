import os

jwt_algorithm = 'HS256'
jwt_secret_key = os.getenv('JWT_SECRET', 'default_secret_key')
