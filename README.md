## 在线站点

[Oasis](http://60.205.186.74)

## 说明
- 使用JWT进行认证，所有需要身份认证的Http请求均需要加入Token(令牌)，其最大有效期为2天，可以使用7天内的旧令牌换取新令牌。建议使用Http拦截器实现，其Http请求头部格式如下：

		Authorization：Token xxx
- 站点[Oasis](http://60.205.186.74)上DRF的Session认证已关闭，导致可视化浏览界面无法直接使用，如需使用请下载Chrome插件[modheader](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj)，并为浏览器配置对应的请求头部进行查看。

- 所有列表接口均可在路径后加载page _size=x参数来调整每页显示个数，如访问[http://60.205.186.74/user/?page_size=1](http://60.205.186.74/user/?page_size=1)将返回每页为1个用户的列表。需要特别注意，page _size=0时将返回未分页的列表。


## 配置相关
- 生产环境置`DEBUG=False`并重设域名
- 创建虚拟环境

		python -m venv environment

- 开启虚拟环境

	Windows：

	    cd environment;
	    cd Scripts;
	    activate.bat;
	    cd ..;
	    cd ..;

	Linux:

	    source environment/bin/activate

- 安装插件

    	pip install -r requirements.txt -i https://pypi.douban.com/simple

- 同步数据库

	    python manage.py makemigrations
	    python manage.py migrate

- 创建超级管理员

    	python manage.py createsuperuser

- 开启测试服务器

    	python manage.py runserver 0:80

- [apache2配置](http://blog.dreamgotech.com/article/49/)

## App说明

### user 用户体系
- User 用户
- TelVerify 短信验证码
- Agreement 协议许可