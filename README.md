## 在线站点

[Oasis](http://60.205.186.74)

## 说明
- 使用JWT进行认证，所有需要身份认证的Http请求均需要加入Token(令牌)，其最大有效期为2天，可以使用7天内的旧令牌换取新令牌。建议使用Http拦截器实现，其Http请求头部格式如下：

		Authorization：Token xxx
- 站点[Oasis](http://60.205.186.74)上DRF的Session认证已关闭，导致可视化浏览界面无法直接使用，如需使用请下载Chrome插件[modheader](https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj)，并为浏览器配置对应的请求头部进行查看。

- 对于所有列表接口，如url为`/list/`:

	- 希望以性别升序、ID降序排列，请求url为`/user/?ordering=gender,-id`;
	- 希望得到性别为男的列表，请求url为`/user/?gender=1`；
	- 希望搜索用户时，请求url为`/user/?search=xxx`；
	- 希望每页显示10条数据，请求url为`/user/?page_size=10`；
	- 希望访问未分页的列表，请求url为`/user/?page_size=0`；
	- 希望访问列表的第二页，请求url为`/user/?page=2`；
	- 排序、过滤、检索、每页个数、页数条件可以混合使用，请求url可为`/user/?ordering=gender,-id&gender=1&search=xxx&page_size=10&page=2`；


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