from freenit.config import getConfig

config = getConfig()
print()
print(f"    http://{config.hostname}:{config.port}/api/v1/docs")
print(f"    http://{config.hostname}:{config.port}/api/v1/redoc")
print()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "freenit.app:app",
        host="0.0.0.0",
        port=config.port,
        log_level="info",
        reload=True,
    )
