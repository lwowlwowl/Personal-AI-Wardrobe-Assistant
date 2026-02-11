import requests
import jwt
import time
#填ed25519-private.pem里的内容
private_key='''-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIJUbdvSQB1l3YC6/myOnHC1BhGBx5BtsGiuZvW31K6an
-----END PRIVATE KEY-----'''

headers = {
    "kid": "CBB6C3X4J9"#凭据id
}
payload={
    "sub": "2K85Y53MXG",#项目id
    'iat': int(time.time()) - 30,
    'exp': int(time.time()) + 900
}

encoded_jwt = jwt.encode(payload, private_key, algorithm='EdDSA', headers = headers)

print(f"JWT:  {encoded_jwt}")


#api host headers
api_host = 'https://kd7h2rj63b.re.qweatherapi.com'#填写自己的apihost
headers = {'Authorization': f'Bearer {encoded_jwt}'}
city_api = '/geo/v2/city/lookup'  #城市代码查询api
now_api = '/v7/weather/now'#实时天气api

#城市代码查询
city='广安'#填写城市名查询天气
params = {'location': city}
url = f'{api_host}{city_api}'
response = requests.get(url,headers=headers,params=params)
city_id = response.json()['location'][0]['id']  # 获取城市代码
city_name = response.json()['location'][0]['name']  # 获取城市名称
country = response.json()['location'][0]['country']  # 获取国家名
#实时天气数据获取

url= f'{api_host}{now_api}'
headers = {'Authorization': f'Bearer {encoded_jwt}'}
params = {
    'location': city_id,  #城市代码(必须)
    'lang': 'zh',#语言
    'unit': 'm'#数据单位设置，可选值包括unit=m（公制单位，默认）和unit=i（英制单位）
}
response = requests.get(url,headers=headers,params=params)
print(response)
print(response.text)
now_weather_data = response.json()
# 打印当前天气数据
print(f'城市: {country} {city_name}')  # 打印城市名
print(now_weather_data['now']['text'])  # 打印当前天气状况
print(f'温度: {now_weather_data["now"]["temp"]}°C')  # 打印当前温度
print(f'体感温度: {now_weather_data["now"]["feelsLike"]}°C')  # 打印当前体感温度
print(f'湿度: {now_weather_data["now"]["humidity"]}%')  # 打印当前湿度
print(f'风向: {now_weather_data["now"]["windDir"]}')  # 打印当前风向
print(f'风力等级: {now_weather_data["now"]["windScale"]}')  # 打印当前风力等级
print(f'风速: {now_weather_data["now"]["windSpeed"]} km/h')  # 打印当前风速
print(f'数据更新时间: {now_weather_data["updateTime"]}')  # 打印数据更新时间

"""报错NotImplementedError: Algorithm 'EdDSA' could not be found. Do you have cryptography installed?
解决pip install --upgrade cryptography
"""
