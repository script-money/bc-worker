# recloutme worker端

## 安装

1. 保证有Python 3.9环境，然后使用 `pip install -r requirements.txt` 安装依赖
2. `cp .env.example .env`
3. `.env` 中第一行添加12位助记词到PRIVATE_KEY，第六行修改本地代理到PROXY_URL（用于翻墙访问bitclout网站，如果不用翻墙则改为""或者删除），二到五是推特开发者相关，不用管

## 部署(ubuntu20.04)

1. 不能用root账户
2. 安装python3.9。`sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.9`
3. 安装pip，`curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3.9 get-pip.py && python3.9 -m pip install -r requirements.txt`
4. 安装chromedriver的依赖`sudo apt install libnss3-dev`

## 启动

1. 输入`python driver/run.py`运行worker，会打开chrome自动登录账户并读取余额，并监听信号。
2. 新开一个窗口，输入`export FLASK_APP=driver/server.py`，然后输入`flask run --host=0.0.0.0`启动web服务
