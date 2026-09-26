"""
اسکریپت ساخت patients/iran_locations.py
با استفاده از داده‌های استاندارد armezit/iran-geo-data
"""
import json
import requests

PROVINCES_URL = "https://raw.githubusercontent.com/armezit/iran-geo-data/main/dist/json/provinces.json"
CITIES_URL = "https://raw.githubusercontent.com/armezit/iran-geo-data/main/dist/json/cities.json"


def fetch_json(url):
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ❌ خطا در دریافت {url}: {e}")
        return None


def main():
    print("🔍 دریافت لیست استان‌ها...")
    provinces_data = fetch_json(PROVINCES_URL)
    if not provinces_data:
        return

    # ساخت نگاشت: province_id → province_name
    province_map = {}
    for p in provinces_data:
        pid = p.get("id")
        name = p.get("name")
        if pid and name:
            province_map[pid] = name

    print(f"✓ {len(province_map)} استان دریافت شد.")

    print("🔍 دریافت لیست شهرها...")
    cities_data = fetch_json(CITIES_URL)
    if not cities_data:
        return

    print(f"✓ {len(cities_data)} شهر دریافت شد.")

    # گروه‌بندی شهرها بر اساس استان
    locations = {name: [] for name in province_map.values()}

    for city in cities_data:
        pid = city.get("province_id")
        city_name = city.get("name")
        if pid in province_map and city_name:
            province_name = province_map[pid]
            if city_name not in locations[province_name]:
                locations[province_name].append(city_name)

    # مرتب‌سازی شهرهای هر استان
    for prov in locations:
        locations[prov] = sorted(locations[prov])

    total_cities = sum(len(c) for c in locations.values())
    print(f"✓ {total_cities} شهر در {len(locations)} استان گروه‌بندی شد.")

    # نوشتن فایل
    lines = [
        '"""',
        'این فایل به صورت خودکار تولید شده است.',
        'منبع: armezit/iran-geo-data',
        '"""',
        '',
        'IRAN_LOCATIONS = {',
    ]
    for prov, cities in locations.items():
        lines.append(f'    "{prov}": {{')
        lines.append('        "cities": [')
        for city in cities:
            lines.append(f'            "{city}",')
        lines.append('        ],')
        lines.append('    },')
    lines.append('}')
    lines.append('')
    lines.append('')
    lines.append('def get_provinces():')
    lines.append('    return sorted(IRAN_LOCATIONS.keys())')
    lines.append('')
    lines.append('')
    lines.append('def get_cities(province):')
    lines.append('    if province not in IRAN_LOCATIONS:')
    lines.append('        return []')
    lines.append('    return IRAN_LOCATIONS[province]["cities"]')
    lines.append('')
    lines.append('')
    lines.append('def get_districts(province, city):')
    lines.append('    """لیست مناطق — فعلاً خالی (منشی دستی وارد می‌کند)."""')
    lines.append('    return []')

    with open("patients/iran_locations.py", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n✅ فایل patients/iran_locations.py با موفقیت ساخته شد.")


if __name__ == "__main__":
    main()