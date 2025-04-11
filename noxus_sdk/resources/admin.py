from typing import TYPE_CHECKING

from noxus_sdk.resources.base import BaseResource, BaseService

if TYPE_CHECKING:
    from noxus_sdk.client import Client


class ApiKey(BaseResource):
    id: str
    name: str
    tenant_admin: bool
    value: str


class Workspace(BaseResource):
    id: str
    name: str
    description: str | None = None

    def delete(self) -> None:
        self.client.delete(f"/v1/admin/groups/{self.id}")

    async def adelete(self) -> None:
        await self.client.adelete(f"/v1/admin/groups/{self.id}")

    def add_api_key(self, name: str, is_admin: bool = False) -> ApiKey:
        api_key = self.client.post(
            f"/v1/admin/groups/{self.id}/api-keys",
            {"name": name, "tenant_admin": is_admin},
        )
        return ApiKey(client=self.client, **api_key)

    async def aadd_api_key(self, name: str, is_admin: bool = False) -> ApiKey:
        api_key = await self.client.apost(
            f"/v1/admin/groups/{self.id}/api-keys",
            {"name": name, "tenant_admin": is_admin},
        )
        return ApiKey(client=self.client, **api_key)


class AdminService(BaseService[Workspace]):
    def __init__(self, client: "Client", enabled: bool = True):
        self.client = client
        self.enabled = enabled

    def get_me(self) -> ApiKey:
        try:
            response = self.client.get("/v1/admin/me")
            return ApiKey(client=self.client, **response)
        except Exception:
            return ApiKey(client=self.client, id="", name="", tenant_admin=False)

    async def aget_me(self) -> ApiKey:
        try:
            response = await self.client.aget("/v1/admin/me")
            return ApiKey(client=self.client, **response)
        except Exception:
            return ApiKey(client=self.client, id="", name="", tenant_admin=False)

    async def alist_workspaces(self) -> list[Workspace]:
        if not self.enabled:
            raise ValueError(
                "Admin service is disabled because client was not initialized with an admin API key"
            )
        response = await self.client.apget(
            f"/v1/admin/groups",
        )
        return [Workspace(client=self.client, **group) for group in response]

    def list_workspaces(self) -> list[Workspace]:
        if not self.enabled:
            raise ValueError(
                "Admin service is disabled because client was not initialized with an admin API key"
            )
        response = self.client.pget(
            f"/v1/admin/groups",
        )
        return [Workspace(client=self.client, **group) for group in response]

    def create_workspace(self, name: str, description: str | None = None) -> Workspace:
        if not self.enabled:
            raise ValueError(
                "Admin service is disabled because client was not initialized with an admin API key"
            )
        response = self.client.post(
            f"/v1/admin/groups",
            {"name": name, "description": description},
        )
        return Workspace(client=self.client, **response)

    async def acreate_workspace(
        self, name: str, description: str | None = None
    ) -> Workspace:
        if not self.enabled:
            raise ValueError(
                "Admin service is disabled because client was not initialized with an admin API key"
            )
        response = await self.client.apost(
            f"/v1/admin/groups",
            {"name": name, "description": description},
        )
        return Workspace(client=self.client, **response)
