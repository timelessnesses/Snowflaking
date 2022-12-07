import asyncio

import asyncpg

url = f"postgresql://{input('Username: ')}:{input('Password: ')}@{input('Host: ')}:{input('Port: ')}/{input('Database name: ')}"


async def main():
    try:
        g: asyncpg.Connection = await asyncpg.connect(url)
    except Exception as e:
        print("Looks like something is wrong with your information: ", e)
        exit(1)
    print("Your database url is: ", url, " and it works!")
    await g.close()


asyncio.run(main())
