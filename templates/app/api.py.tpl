from rusjango import Router

router = Router()


@router.get("/students")
async def list_students():
    return [{"name": "Ali"}, {"name": "Sara"}]
