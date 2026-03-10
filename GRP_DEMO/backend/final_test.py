import requests
import json

# 最简单的测试数据
test_data = {
    "username": "finaltest",
    "email": "finaltest@test.com",
    "password": "123456",
    "confirm_password": "123456"
}

url = "http://localhost:8000/api/auth/register"

print("🔧 测试注册API...")
print(f"数据: {test_data}")

try:
    response = requests.post(url, json=test_data, timeout=10)
    print(f"✅ 请求成功")
    print(f"状态码: {response.status_code}")
    
    # 打印完整响应
    print(f"响应内容: {response.text}")
    
    # 如果是JSON，格式化输出
    if response.headers.get('content-type', '').startswith('application/json'):
        try:
            result = response.json()
            print("\n📋 格式化响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except:
            pass
    
except Exception as e:
    print(f"❌ 请求失败: {e}")