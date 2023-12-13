from freenit.config import getConfig
import uvicorn

config = getConfig()
print()
print(f"    http://{config.hostname}:{config.port}/api/v1/docs")
print(f"    http://{config.hostname}:{config.port}/api/v1/redoc")
print()

if __name__ == "__main__":
    uvicorn.run(
        "NAME.app:app",
        host="0.0.0.0", #nosec
        port=config.port,
        log_level="info",
        reload=True,
    )
