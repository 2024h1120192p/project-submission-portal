import httpx
from libs.events.schemas import User
from typing import List, Optional

class AsyncHTTPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def get(self, url: str, **kwargs):
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self._client.delete(url, **kwargs)


    async def close(self):
        await self._client.aclose()


# Internal async client for other services
class UserServiceClient:
    def __init__(self, base_url: str):
        self.client = AsyncHTTPClient(base_url)

    async def get_user(self, user_id: str) -> Optional[User]:
        resp = await self.client.get(f"/users/{user_id}")
        if resp.status_code == 200:
            return User(**resp.json())
        return None

    async def get_all(self) -> List[User]:
        resp = await self.client.get("/users")
        if resp.status_code == 200:
            return [User(**u) for u in resp.json()]
        return []

    async def create(self, user: User) -> Optional[User]:
        resp = await self.client.post("/users", json=user.model_dump())
        if resp.status_code in (200, 201):
            return User(**resp.json())
        return None

    async def update(self, user_id: str, user: User) -> Optional[User]:
        resp = await self.client.put(f"/users/{user_id}", json=user.model_dump())
        if resp.status_code == 200:
            return User(**resp.json())
        return None

    async def delete(self, user_id: str) -> bool:
        resp = await self.client.delete(f"/users/{user_id}")
        return resp.status_code == 200
