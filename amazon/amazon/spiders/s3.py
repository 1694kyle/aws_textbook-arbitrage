# import tinys3
# import os
#
# access_key = os.environ.get('AWS_ACCESS_KEY')
# secret_key = os.environ.get('AWS_SECRET_KEY')
#
#
# def create_conection(access_key, secret_key):
#     if access_key and secret_key:
#         conn = tinys3.Connection(access_key, secret_key, endpoint='s3-us-west-2.amazonaws.com')
#     else:
#         conn = None
#     return conn
#
#
# def upload(file_stream, f_name, bucket_path='textbook-arbitrage'):
#     conn.upload(f_name, file_stream, bucket_path)
#
#
# conn = create_conection(access_key, secret_key)
