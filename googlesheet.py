import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 🔹 ตั้งค่า Scope สำหรับ Google Sheets API
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# 🔹 โหลด Credentials จากไฟล์ JSON
CREDENTIALS_FILE = "credentials.json"  # ไฟล์ที่ใช้เชื่อมต่อ Google API
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)

# 🔹 เชื่อมต่อ Google Sheets API
client = gspread.authorize(creds)

# 🔹 เปิดไฟล์ Google Sheets โดยใช้ ID (เปลี่ยนเป็น ID ของคุณ)
SHEET_ID = "1DZn-4n7XMfn0Q2efyt7JA9-w7oBdtj5ZtMkV3U2oHFQ"
spreadsheet = client.open_by_key(SHEET_ID)

# 🔹 เลือกชีตที่ต้องการ (เปลี่ยนเป็นชื่อชีตที่ถูกต้อง)
SHEET_NAME = "User"
sheet = spreadsheet.worksheet(SHEET_NAME)


def get_user_data(username: str):
    """🔍 ค้นหาผู้ใช้จาก Google Sheets ตาม CupidCall Username"""
    records = sheet.get_all_records()
    for user in records:
        if user["CupidCall Username"].strip().lower() == username.strip().lower():
            return user  # คืนค่าข้อมูลของผู้ใช้
    return None  # ถ้าไม่พบข้อมูล


if __name__ == "__main__":
    # ทดสอบดึงข้อมูล
    test_username = "alice123"
    user_data = get_user_data(test_username)

    if user_data:
        print(f"✅ พบข้อมูลของ {test_username}: {user_data}")
    else:
        print(f"❌ ไม่พบบัญชี {test_username}")
