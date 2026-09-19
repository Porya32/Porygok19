import asyncio
import json
import os
from aiohttp import web

from splusthon import SoroushClient, events
from splusthon.sessions import StringSession


# ==================================================
# تنظیمات
# ==================================================

API_KEY = os.environ.get("API_KEY", "CHANGE_THIS_KEY")
TARGET_ID = 777000

# فقط آخرین پیام نگه داشته می‌شود
last_message = None

client = None
account_phone = None
connected = False


# ==================================================
# بررسی API KEY
# ==================================================

def check_key(request):
    key = request.headers.get("X-API-Key")

    if key != API_KEY:
        return False

    return True


# ==================================================
# دریافت پیام‌های 777000
# ==================================================

async def message_handler(event):
    global last_message

    try:
        chat = await event.get_chat()
        chat_id = getattr(chat, "id", None)

        if chat_id != TARGET_ID:
            return

        text = event.raw_text or ""

        last_message = {
            "text": text,
            "chat_id": chat_id
        }

        print("\n" + "=" * 60)
        print("🎯 پیام جدید از 777000")
        print("=" * 60)
        print(text)
        print("=" * 60)

    except Exception as e:
        print("❌ Message Error:", type(e).__name__, e)


# ==================================================
# اتصال اکانت
# ==================================================

async def connect_account(session):
    global client
    global account_phone
    global connected

    try:
        # اگر اتصال قبلی وجود دارد
        if client is not None:
            try:
                await client.disconnect()
            except:
                pass

        print("🔄 در حال اتصال به اکانت...")

        client = SoroushClient(StringSession(session))

        client.add_event_handler(
            message_handler,
            events.NewMessage()
        )

        await client.start()

        me = await client.get_me()

        account_phone = getattr(me, "phone", None)

        if account_phone:
            account_phone = str(account_phone)

        connected = True

        print("✅ اکانت متصل شد")
        print("📱 شماره:", account_phone)
        print("🎯 هدف:", TARGET_ID)

        return True, None

    except Exception as e:

        connected = False

        print("❌ Connection Error:")
        print(type(e).__name__, e)

        return False, str(e)


# ==================================================
# API اتصال
# ==================================================

async def connect_api(request):

    if not check_key(request):
        return web.json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            status=401
        )

    try:
        data = await request.json()

        session = data.get("session")

        if not session:
            return web.json_response(
                {
                    "ok": False,
                    "error": "Session is empty"
                },
                status=400
            )

        success, error = await connect_account(session)

        if not success:
            return web.json_response(
                {
                    "ok": False,
                    "error": error
                },
                status=400
            )

        return web.json_response(
            {
                "ok": True,
                "phone": account_phone,
                "target": TARGET_ID,
                "message": "Connected successfully"
            }
        )

    except Exception as e:

        return web.json_response(
            {
                "ok": False,
                "error": str(e)
            },
            status=400
        )


# ==================================================
# API وضعیت
# ==================================================

async def status_api(request):

    if not check_key(request):
        return web.json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            status=401
        )

    return web.json_response(
        {
            "ok": True,
            "connected": connected,
            "phone": account_phone,
            "target": TARGET_ID
        }
    )


# ==================================================
# API پیام جدید
# ==================================================

async def message_api(request):

    if not check_key(request):
        return web.json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            status=401
        )

    return web.json_response(
        {
            "ok": True,
            "message": last_message
        }
    )


# ==================================================
# API پاک کردن پیام
# ==================================================

async def clear_message_api(request):

    global last_message

    if not check_key(request):
        return web.json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            status=401
        )

    last_message = None

    return web.json_response(
        {
            "ok": True
        }
    )


# ==================================================
# صفحه تست
# ==================================================

async def home(request):

    return web.Response(
        text="SPlus Monitor Server is running.",
        content_type="text"
    )


# ==================================================
# اجرای سرور
# ==================================================

app = web.Application()

app.router.add_get("/", home)
app.router.add_post("/connect", connect_api)
app.router.add_get("/status", status_api)
app.router.add_get("/message", message_api)
app.router.add_post("/clear", clear_message_api)


async def main():

    runner = web.AppRunner(app)

    await runner.setup()

    port = int(os.environ.get("PORT", "8080"))

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        port
    )

    await site.start()

    print("=" * 60)
    print("🚀 SPLUS SERVER STARTED")
    print("🌐 Port:", port)
    print("🎯 Target:", TARGET_ID)
    print("=" * 60)

    # سرور همیشه فعال بماند
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
