from fastapi import Request
from ss.postgres import PostgresProvider

class Container:
    def __init__(self, db: PostgresProvider):
        self.db = db
        
    def dispose(self):
        self.db.dispose()
        
async def get_container(request: Request) -> Container:
    return request.app.state.container