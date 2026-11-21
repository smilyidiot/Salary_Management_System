"""HTTP layer.

Each module in this package is a FastAPI ``APIRouter`` that maps URL routes to
service-layer calls, handling only HTTP concerns (status codes, query params, error
translation). All business logic lives in ``app.services``.
"""
