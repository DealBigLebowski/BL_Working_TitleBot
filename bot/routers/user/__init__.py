from ...filters.registered import RegisteredFilter
from ...utils.router import Router
from .. import root_handlers_router

router = Router()
router.filter(RegisteredFilter(registered=True))

root_handlers_router.include_router(router)
