import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import re
from datetime import datetime, timedelta

def connect_db():
    conn = psycopg2.connect(
        dbname="PCN_human",
        user="PCN_human_owner",
        password="x1XE2AFmKTrU",
        host="ep-polished-brook-a121ao7c.ap-southeast-1.aws.neon.tech",
        port="5432"  # Cổng mặc định của PostgreSQL
    )
    return conn

def ensure_user_exists(cursor, user_id, username, first_name, last_name):
    cursor.execute("""SELECT COUNT(*) FROM public."PCN_employees" WHERE "UserId" = %s""", (user_id,))
    if cursor.fetchone()[0] == 0:
        # Nếu chưa tồn tại, thêm mới
        query = """
        INSERT INTO public."PCN_employees" ("UserId", "Username", "Firstname", "Lastname")
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, username, first_name, last_name))

# Hàm xử lý tin nhắn và cập nhật cơ sở dữ liệu
def echo(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    user_id = str(update.message.from_user.id)  # userId dạng chuỗi
    username = update.message.from_user.username or "Unknown"
    first_name = update.message.from_user.first_name or ""
    last_name = update.message.from_user.last_name or ""

    # Kết nối cơ sở dữ liệu
    conn = connect_db()
    cursor = conn.cursor()

    is_sap = 0
    no_off = 0
    today = datetime.now()

    try:
        ensure_user_exists(cursor, user_id, username, first_name, last_name)

        if "nghỉ" in message_text:
            match = re.search(r"nghỉ (\d{1,2}) ngày", message_text)
            if match:
                no_off = int(match.group(1))
            elif "hôm nay" in message_text.lower():
                no_off = 1
                today = datetime.now()
            elif "ngày mai" in message_text.lower():
                no_off = 1
                today = datetime.now() + timedelta(days=1)
            elif "sáng mai" in message_text.lower() or "chiều mai" in message_text.lower():
                no_off = 0.5
                today = datetime.now() + timedelta(days=1)
            elif any(phrase in message_text.lower() for phrase in ["sáng nay", "chiều nay"]):
                no_off = 0.5

            if "sap" in message_text.lower():
                is_sap = 1
                # Gửi phản hồi
                update.message.reply_text(f"BOT đã ghi nhận {no_off} ngày nghỉ có phép cho {first_name} {last_name} ({username}).")
            else:
                # Gửi phản hồi
                update.message.reply_text(f"BOT đã ghi nhận {no_off} ngày nghỉ không phép cho {first_name} {last_name} ({username}).")

            query = """
            INSERT INTO public."PCN_work_time" ("UserId", "Username", "Year", "Month", "Day", "Date", "No_off", "Is_sap")
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, username, today.year, today.month, today.day, today, no_off, is_sap))
            conn.commit()
    except Exception as e:
        update.message.reply_text(f"Đã xảy ra lỗi: {e}")

    finally:
        # Đóng kết nối
        cursor.close()
        conn.close()

# Hàm main để khởi động bot
def main():
    # Token bot của bạn
    TOKEN = "7901367514:AAFfM-Hjk3ULmyd8Ol7TYoem7PAoQ1pobGU"

    # Tạo Updater và Dispatcher
    updater = Updater(TOKEN)

    # Lấy dispatcher để đăng ký các handler
    dispatcher = updater.dispatcher

    # Đăng ký handler cho tin nhắn (MessageHandler)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Khởi động bot và bắt đầu lắng nghe
    updater.start_polling()

    # Đảm bảo bot hoạt động liên tục
    updater.idle()

if __name__ == '__main__':
    main()
