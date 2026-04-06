"""Example usage of the ksef SDK."""

from ksef import AsyncKSeFClient, Environment


async def main() -> None:
    async with AsyncKSeFClient(environment=Environment.TEST) as client:
        challenge = await client.auth.get_challenge()
        print(f"Got challenge: {challenge.challenge}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
