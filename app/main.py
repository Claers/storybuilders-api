from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.exceptions import RequestValidationError, StarletteHTTPException
from fastapi.encoders import jsonable_encoder
from app.config import settings
from app.routers import user, auth
from app.routers.storybuilders import cards, cards_extension, cards_types

app = FastAPI()

origins = [
    settings.CLIENT_ORIGIN,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, tags=["Auth"], prefix="/api/auth")
app.include_router(user.router, tags=["Users"], prefix="/api/users")
app.include_router(
    cards.router, tags=["Storybuilders Cards"], prefix="/api/storybuilders/cards"
)
app.include_router(
    cards_types.router, tags=["Storybuilders Types"], prefix="/api/storybuilders/types"
)
app.include_router(
    cards_extension.router,
    tags=["Storybuilders Extensions"],
    prefix="/api/storybuilders/extensions",
)


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/api/healthchecker")
def root():
    return {"message": "Hello World"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # print(await request.json())
    print(exc.errors())
    print(exc.body)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


# @app.exception_handler(500)
# async def validation_exception_handler(request: Request, exc):
#     # print(await request.json())
#     print(exc.errors())
#     print(exc.body)
#     return JSONResponse(
#         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#         content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
#     )
