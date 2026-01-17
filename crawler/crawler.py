import requests
#
filename1, url1 = "各機組過去發電量20250501-20250731.json", "https://service.taipower.com.tw/data/opendata/apply/file/d006010/001.json"
# filename2, url2 = "pg_flow_ 03_05.json", "https://service.taipower.com.tw/data/opendata/apply/file/d006009/001.json"

response = requests.get(url1, verify=False)
print("START")
if response.status_code == 200:
    with open(filename1, "w", encoding="utf-8") as file:
        file.write(response.text)
    print(f"下載成功，已儲存為 {filename1}")
else:
    print(f"下載失敗，狀態碼：{response.status_code}")


# response = requests.get(url2, verify=False)
# if response.status_code == 200:
#     with open(filename2, "w", encoding="utf-8") as file:
#         file.write(response.text)
#     print(f"下載成功，已儲存為 {filename2}")
# else:
#     print(f"下載失敗，狀態碼：{response.status_code}")


# import json

# with open(r'data/2024/power_generation/各機組過去發電量20240501-20240731.json', 'r', encoding='utf-8-sig') as file:
#     data = json.load(file)

# # 使用字典來依照 FUEL_TYPE 分類 UNIT_NAME
# fuel_type_dict = {}

# for entry in data['records']['NET_P']:
#     if "UNIT_NAME" in entry and "FUEL_TYPE" in entry:
#         unit_name = entry["UNIT_NAME"]
#         fuel_type = entry["FUEL_TYPE"]
        
#         if fuel_type not in fuel_type_dict:
#             fuel_type_dict[fuel_type] = []
        
#         # 確保同一個機組名稱不重複
#         if unit_name not in fuel_type_dict[fuel_type]:
#             fuel_type_dict[fuel_type].append(unit_name)

# # 輸出每個燃料類型及其對應的機組名稱
# for fuel_type, units in fuel_type_dict.items():
#     print(f"Fuel Type: {fuel_type}")
#     for unit in units:
#         print(f"  {unit}")