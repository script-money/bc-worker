# recloutme worker端

## 安装

1. 保证有Python 3.9环境，然后使用 `pip install -r requirements.txt` 安装依赖
2. `cp .env.example .env`
3. `.env` 中第一行添加12位助记词到PRIVATE_KEY，第六行修改本地代理到PROXY_URL（用于翻墙访问bitclout网站）,二到五是推特开发者相关，不用管

## 启动

输入`python driver/run.py`运行worker，会打开chrome自动登录账户并读取余额，并监听信号。
