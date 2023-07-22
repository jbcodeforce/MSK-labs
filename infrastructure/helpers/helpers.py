import os

def getAppEnv():
    appName=os.getenv("APP_NAME").lower()
    if not appName:
        appName="app"
    if not os.path.isfile(f"./config/{appName}.yaml"):
        raise RuntimeError(f"File config/{appName}.yaml not found")
    return appName
