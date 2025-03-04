import psycopg2
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
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

def update_new_toDb(conn, cursor, no_off, message_text, first_name, last_name, username, user_id, today):
    _is_sap = 0
    if "sap" in message_text.lower() or "nghỉ phép" in message_text.lower():
        _is_sap = 1
        # Gửi phản hồi
        reply_text = f"BOT đã ghi nhận {no_off} ngày nghỉ có phép từ {today.date()} cho {first_name} {last_name} ({username})."
    else:
        # Gửi phản hồi
        reply_text = f"BOT đã ghi nhận {no_off} ngày nghỉ không phép từ {today.date()} cho {first_name} {last_name} ({username})."

    query = """INSERT INTO public."PCN_work_time" ("UserId", "Username", "Year", "Month", "Day", "Date", "No_off", "Is_sap") VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
    cursor.execute(query, (user_id, username, today.year, today.month, today.day, today, no_off, _is_sap))
    conn.commit()

    # Trả về chuỗi reply_text
    return reply_text

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

    today = datetime.now()

    try:
        ensure_user_exists(cursor, user_id, username, first_name, last_name)

        if "nghỉ" in message_text.lower():

            match = re.search(r"nghỉ (\d{1,2}(\.\d{1,2})?) ngày", message_text.lower())
            if match:
                no_off = float(match.group(1))
                update.message.reply_text(update_new_toDb(conn, cursor, no_off, message_text, first_name,last_name,username,user_id,today,))
            else:
                if "hôm nay" in message_text.lower():
                    no_off = 1
                    update.message.reply_text(update_new_toDb(conn, cursor, no_off, message_text, first_name,last_name,username,user_id,today,))
                if "ngày mai" in message_text.lower():
                    no_off = 1
                    today = datetime.now() + timedelta(days=1)
                    update.message.reply_text(update_new_toDb(conn, cursor, no_off, message_text, first_name,last_name,username,user_id,today,))
                if "sáng mai" in message_text.lower() or "chiều mai" in message_text.lower():
                    no_off = 0.5
                    today = datetime.now() + timedelta(days=1)
                    update.message.reply_text(update_new_toDb(conn, cursor, no_off, message_text, first_name,last_name,username,user_id,today,))
                if any(phrase in message_text.lower() for phrase in ["sáng nay", "chiều nay"]):
                    no_off = 0.5
                    update.message.reply_text(update_new_toDb(conn, cursor, no_off, message_text, first_name,last_name,username,user_id,today,))

            # if no_off > 0:
            #     if "sap" in message_text.lower() or "nghỉ phép" in message_text.lower():
            #         is_sap = 1
            #         # Gửi phản hồi
            #         update.message.reply_text(f"BOT đã ghi nhận {no_off} ngày nghỉ có phép cho {first_name} {last_name} ({username}).")
            #     else:
            #         # Gửi phản hồi
            #         update.message.reply_text(f"BOT đã ghi nhận {no_off} ngày nghỉ không phép cho {first_name} {last_name} ({username}).")
            #
            # query = """
            # INSERT INTO public."PCN_work_time" ("UserId", "Username", "Year", "Month", "Day", "Date", "No_off", "Is_sap")
            # VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            # """
            # cursor.execute(query, (user_id, username, today.year, today.month, today.day, today, no_off, is_sap))
            # conn.commit()

    except Exception as e:
        update.message.reply_text(f"Đã xảy ra lỗi: {e}")

    finally:
        # Đóng kết nối
        cursor.close()
        conn.close()

# Hàm main để khởi động bot
def main():
    # Token bot của bạn
    TOKEN = "7901367514:AAH8Zu7Li88Lg2rWgKPdsVxOyO5RGnAB0wc"

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
