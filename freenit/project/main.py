from NAME.app import app

if __name__ == '__main__':
    from freenit.config import getConfig
    import uvicorn

    config = getConfig()
    print()
    print(f"    http://{config.hostname}:{config.port}/api/v1/docs")
    print(f"    http://{config.hostname}:{config.port}/api/v1/redoc")
    print()

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.port,
        log_level="info",
        reload=True,
    )
