from config import configs
from freenit import create_app

app = create_app(configs['testing'])

if __name__ == '__main__':
    app.run()
