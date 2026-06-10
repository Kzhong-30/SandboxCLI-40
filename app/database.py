from .config import settings
from .mock_mongo import MockMongoClient

client = None
db = None


async def connect_to_mongo():
    global client, db
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        real_client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=2000)
        await real_client.admin.command("ping")
        client = real_client
        db = client[settings.DATABASE_NAME]
        print("✅ 已连接到真实 MongoDB 数据库")
    except Exception as e:
        print(f"⚠️  MongoDB 连接失败 ({str(e)[:50]})，使用内存模拟数据库")
        client = MockMongoClient()
        db = client[settings.DATABASE_NAME]
        print("✅ 已启动内存模拟数据库（数据仅在运行时保留）")


async def close_mongo_connection():
    global client
    if client:
        try:
            client.close()
        except Exception:
            pass
        print("🔌 数据库连接已关闭")


def get_database():
    return db
