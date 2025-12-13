import pymysql
config = {
    'host': "gateway01.eu-central-1.prod.aws.tidbcloud.com",
    'port': 4000,
    'user': "48pvdQxqqjLneBr.root",
    'password': "o46hvbIhibN3tTPp",  # 请替换
    'database': "python_project",
    'ssl_ca': "####",
    'ssl_verify_cert': True,
    'ssl_verify_identity': True
}
connection = pymysql.connect(**config)