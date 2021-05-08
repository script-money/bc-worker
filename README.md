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

## 使用

### 获取reclout名单

reclout名单是从notification中获取。`driver/get_notifications.py`的`if __name__ == "__main__":`里，修改`generate_reclout_csv`的第一个参数为要查询的PublicKey，默认是myreclout的。第二个参数填写要查询的原帖hash，从浏览器中帖子的URL获取。第三个参数是每次查询的消息数，一般设置为250-500的随意数字。end_index参数是查询停止的index，每条消息都有一个index，-1为最新的消息，一般不用查询到0。
改完参数后，用`python driver/get_notifications.py`运行，会生成结果在csv文件夹下。

### 群控

把要运行的助记词放入pk文件夹的某个文件夹中，修改`driver/get_pk.py`的最后一行参数。file指向要读取的助记词文件，由于单IP反复请求会激活CF，所以需要使用代理并切换。
运行`python driver/get_pk.py`，会读取私钥登录并读取余额。其他功能也可以按需求添加。

### 发送message给特定多个账户

在`python driver/run.py`运行的情况下，运行`python driver/send_dm_multiple_signal.py`，需修改15-16行的参数。多个账户用`/`分隔。

### 发送message给投资者们

在`python driver/run.py`运行的情况下，运行`python driver/send_dm_investors_signal.py`，需修改15-16行的参数。
