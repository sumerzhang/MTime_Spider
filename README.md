# MTime_Spider动态爬虫

用Chrome分析MTime的影评数据，在网页源码中没有发现票房等相关的数据，基本可以确定是JS动态加载。分析JS中的Ajax相关的文件，有这样的链接：
```
http://service.library.mtime.com/Movie.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Library.Services&Ajax_CallBackMethod=GetMovieOverviewRating&Ajax_CrossDomain=1&Ajax_RequestUrl=http%3A%2F%2Fmovie.mtime.com%2F251494%2F&t=201849033474578&Ajax_CallBackArgument0=251494

```
我们可以看到评分和票房数据。

找到链接后，我们需要知道如下两件事：
### 1. 如何构造链接，参数的特征
### 2. 如何提取响应的内容

对比分析链接的规律：
```
http://service.library.mtime.com/Movie.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Library.Services&Ajax_CallBackMethod=GetMovieOverviewRating&Ajax_CrossDomain=1&Ajax_RequestUrl=http%3A%2F%2Fmovie.mtime.com%2F251494%2F&t=201849033474578&Ajax_CallBackArgument0=251494


http://service.library.mtime.com/Movie.api?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Library.Services&Ajax_CallBackMethod=GetMovieOverviewRating&Ajax_CrossDomain=1&Ajax_RequestUrl=http%3A%2F%2Fmovie.mtime.com%2F234616%2F&t=20184910482249235&Ajax_CallBackArgument0=234616
```

分析异同，发现只有三个参数在变化：
#### 1. Ajax\_RequestUrl 代表当前网页的链接
#### 2. Ajax\_CallBackArgument0 代表链接后面的数字
#### 3. t 时间戳

下面我们看一下网页的响应内容。

```
正在上映有票房纪录
var result_20184910482249235 = { "value":{"isRelease":true,"movieRating":{"MovieId":234616,"RatingFinal":7.5,"RDirectorFinal":7.7,"ROtherFinal":7.3,"RPictureFinal":7.5,"RShowFinal":0,"RStoryFinal":7.7,"RTotalFinal":0,"Usercount":460,"AttitudeCount":727,"UserId":0,"EnterTime":0,"JustTotal":0,"RatingCount":0,"TitleCn":"","TitleEn":"","Year":"","IP":0},"movieTitle":"暴裂无声","tweetId":0,"userLastComment":"","userLastCommentUrl":"","releaseType":1,"boxOffice":{"Rank":3,"TotalBoxOffice":"3679.0","TotalBoxOfficeUnit":"万","TodayBoxOffice":"79.3","TodayBoxOfficeUnit":"万","ShowDays":6,"EndDate":"2018-04-09 10:45","FirstDayBoxOffice":"804","FirstDayBoxOfficeUnit":"万"}},"error":null};var movieOverviewRatingResult=result_20184910482249235;

即将上映
var result_20184911404629761 = { "value":{"isRelease":true,"movieRating":{"MovieId":219782,"RatingFinal":5.7,"RDirectorFinal":5,"ROtherFinal":6,"RPictureFinal":6,"RShowFinal":0,"RStoryFinal":5.2,"RTotalFinal":0,"Usercount":144,"AttitudeCount":222,"UserId":0,"EnterTime":0,"JustTotal":0,"RatingCount":0,"TitleCn":"","TitleEn":"","Year":"","IP":0},"movieTitle":"夺命来电","tweetId":0,"userLastComment":"","userLastCommentUrl":"","releaseType":2,"boxOffice":{"Rank":0,"TotalBoxOffice":"0.0","TotalBoxOfficeUnit":"万","TodayBoxOffice":"0.0","TodayBoxOfficeUnit":"万","ShowDays":0,"EndDate":"2018-04-09 05:15"},"hotValue":{"MovieId":219782,"Ranking":5,"Changing":1,"YesterdayRanking":6}},"error":null};var movieOverviewRatingResult=result_20184911404629761;


较长时间上映
var result_20184911425171356 = { "value":{"isRelease":false,"movieRating":{"MovieId":211987,"RatingFinal":-1,"RDirectorFinal":0,"ROtherFinal":0,"RPictureFinal":0,"RShowFinal":0,"RStoryFinal":0,"RTotalFinal":0,"Usercount":36,"AttitudeCount":1197,"UserId":0,"EnterTime":0,"JustTotal":0,"RatingCount":0,"TitleCn":"","TitleEn":"","Year":"","IP":0},"movieTitle":"战神纪","tweetId":0,"userLastComment":"","userLastCommentUrl":"","releaseType":2,"hotValue":{"MovieId":211987,"Ranking":6,"Changing":-1,"YesterdayRanking":5}},"error":null};var movieOverviewRatingResult=result_20184911425171356;

```
这三种可以只是多了或者少了一些内容，加个try/except异常处理就可以。

"="和";"之间是一个JSON格式，可以用**正则匹配**然后用`json`库解析。

确定要提取的字段，
MovieId, RatingFinal, RDirectorFinal, RPictureFinal,RStoryFinal,ROtherFinal,
Usercount, AttitudeCount, movieTitle, Rank, TotalBoxOffice,TotalBoxOfficeUnit,
TodayBoxOffice, TodayBoxOfficeUnit, ShowDays。

接下来介绍，我们爬虫的架构。

如下
1. 网页下载 
```python

#coding: utf-8
import requests

class HtmlDownloader(object):
	
	def download(self, url):
		if url is None:
			return None
		user_agent = ""
		headers = {"User-Agent": user_agent}
		res = requests.get(url, headers=headers)
		if res.status_code == 200:
			res.encoding='utf-8'
			return res.text
		return None
```

2. 网页解析 分为两部分，一个解析电影链接，一个解析动态加载的内容。

```python
class HtmlParser(object):		
	def parser_url(self, page_url, response):
		pattern = re.compile(r"(http://movie.mtime.com.(\d+)/)")
		urls = pattern.findall(response)
		if urls != None:
			#去重
			return list(set(urls))
		else:
			return None 
			
	def parser_json(self, page_url, response):
		'''
		解析响应
		:param response
		:return 
		'''
		#将=和；之间的内容提取出来
		pattern = re.compile(r'=(.*?);var.*')
		result = pattern.findall(response)[0].strip()
		#print(result)
		if result != None:
			#json模块加载字符串
			value = json.loads(result)
			#print(value)
			try:
				isRelease = value.get('value').get('isRelease')
			except Exception as e:
				print(e)
				return None
			if isRelease:
				if value.get('value').get('hotValue') == None:
					return self._parser_release(page_url, value)
				else:
					return self._parser_no_release(page_url, value, isRelease=2)
			else:
				return self._parser_no_release(page_url, value)
				
	def _parser_release(self, page_url, value):
		'''
		解析已经上映的电影
		：param page_url 电影链接
		;param value json数据
		:return ;
		'''
		try:
			isRelease = 1
			movieRating = value.get('value').get('movieRating')
			#print(movieRating)
			boxOffice = value.get('value').get('boxOffice')
			movieTitle = value.get('value').get('movieTitle')
			RPictureFinal = movieRating.get('RPictureFinal')
			RStoryFinal = movieRating.get('RStoryFinal')
			RDirectorFinal = movieRating.get('RDirectorFinal')
			ROtherFinal = movieRating.get('ROtherFinal')
			RatingFinal = movieRating.get('RatingFinal')
			
			MovieId = movieRating.get('MovieId')
			Usercount = movieRating.get('Usercount')
			AttitudeCount = movieRating.get('AttitudeCount')
			if boxOffice:
				TotalBoxOffice = boxOffice.get('TotalBoxOffice')
				TotalBoxOfficeUnit = boxOffice.get('TotalBoxOfficeUnit')
				TodayBoxOffice = boxOffice.get('TodayBoxOffice')
				TodayBoxOfficeUnit = boxOffice.get('TodayBoxOfficeUnit')
				
				ShowDays = boxOffice.get('ShowDays')
				try:
					Rank = boxOffice.get('Rank')
				except Exception as e:
					Rank = 0
			else:
				TotalBoxOffice='无'
				TotalBoxOfficeUnit = '无'
				TodayBoxOffice = '无'
				TodayBoxOfficeUnit = '无'
				ShowDays = '无'
				Rank = 0
				
			return (MovieId, movieTitle, RatingFinal,
			ROtherFinal, RPictureFinal, RDirectorFinal,
			RStoryFinal, Usercount, AttitudeCount,
			TotalBoxOffice+TotalBoxOfficeUnit,
			TodayBoxOffice+TodayBoxOfficeUnit,
			Rank, ShowDays, isRelease )
			
		except Exception as e:
			print(e, page_url, value)
			return None 
			
	
			
			
			
	def _parser_no_release(self, page_url, value, isRelease=0):
		'''
		解析未上映的电影
		:param page_url
		:param value
		:return 
		'''
		try:
			movieRating = value.get('value').get('movieRating')
			
			movieTitle = value.get('value').get('movieTitle')
			RPictureFinal = movieRating.get('RPictureFinal')
			RStoryFinal = movieRating.get('RStoryFinal')
			RDirectorFinal = movieRating.get('RDirectorFinal')
			ROtherFinal = movieRating.get('ROtherFinal')
			RatingFinal = movieRating.get('RatingFinal')
			
			MovieId = movieRating.get('MovieId')
			Usercount = movieRating.get('Usercount')
			AttitudeCount = movieRating.get('AttitudeCount')
			
			try:
				Rank = value.get('value').get('hotValue').get('Ranking')
			except Exception as e:
				Rank = 0
			return (MovieId, movieTitle, RatingFinal,
			ROtherFinal, RPictureFinal, RDirectorFinal,
			RStoryFinal, Usercount, AttitudeCount,u'无',
			u'无', Rank, 0, isRelease )
		except Exception as e:
			print(e, page_url, value)
			return None
```

3. 数据存储器 主要包括连接数据库，建表，插入数据和关闭数据库等操作

```python
class DataOutput(object):
	def __init__(self):
		self.cx = sqlite3.connect("MTime.db")
		self.create_table("MTime")
		self.datas = []
		
	def create_table(self, table_name):
		'''
		创建表
		：param table_name
		:return 
		'''
		value = '''
		id integer primary key,
		MovieId integer,
		MovieTitle varchar(40) NOT NULL,
		RatingFinal REAL NOT NULL DEFAULT 0.0,
		ROtherFinal REAL NOT NULL Default 0.0,
		RPictureFinal Real not null default 0.0,
		RDirectorFinal real not null default 0.0,
		RStoryFinal real not null default 0.0,
		Usercount integer not null default 0,
		AttitudeCount integer not null default 0,
		TotalBoxOffice varchar(20) not null,
		TodayBoxOffice varchar(20) not null,
		Rank integer not null default 0,
		ShowDays integer not null default 0,
		isRelease integer not null
		'''
		self.cx.execute("CREATE TABLE IF NOT EXISTS %s(%s) " % (table_name, value))
		print(table_name)
	def store_data(self, data):
		'''
		数据存储
		:param data;
		:return 
		'''
		if data is None:
			return 
		self.datas.append(data)
		if len(self.datas) > 10:
			self.output_db("MTime")
			
	def output_db(self, table_name):
		'''
		将数据存储在sqlite
		: return 
		'''
		for data in self.datas:
			self.cx.execute("INSERT INTO %s (MovieId, MovieTitle,"
			"RatingFinal, ROtherFinal, RPictureFinal,"
			"RDirectorFinal, RStoryFinal, Usercount,"
			"AttitudeCount,TotalBoxOffice, TodayBoxOffice,"
			"Rank, ShowDays, isRelease) VALUES(?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?)"
			"" % table_name, data)
			
			self.datas.remove(data)
		self.cx.commit()
		
	def output_end(self):
		'''
		关闭数据库
		'''
		if len(self.datas) > 0:
			self.output_db("MTime")
		self.cx.close()
```


4. 爬虫调度器- 协调上述模块,同时负责构造动态链接。
```python

class SpiderMan(object):
	def __init__(self):
		self.downloader = HtmlDownloader()
		self.parser = HtmlParser()
		self.output = DataOutput()
		
	def crawl(self, root_url):
		content = self.downloader.download(root_url)
		
		urls = self.parser.parser_url(root_url, content)
		
		#构造一个获取评分和票房的链接
		for url in urls:
			#print(url)
			try:
				t = time.strftime("%Y%m%d%H%M%S3282", time.localtime())
				rank_url = 'http://service.library.mtime.com/Movie.api' \
							'?Ajax_CallBack=true&Ajax_CallBackType=Mtime.Library.Services' \
							'&Ajax_CallBackMethod=GetMovieOverviewRating' \
							'&Ajax_CrossDomain=1' \
							'&Ajax_RequestUrl=%s' \
							'&t=%s' \
							'&Ajax_CallBackArgument0=%s' % (url[0], t, url[1])
				#print(rank_url)
				
				rank_content = self.downloader.download(rank_url)
				#print(rank_content)
				data = self.parser.parser_json(rank_url, rank_content)
				#print(data)
				self.output.store_data(data)
				print("Crawl Success")
			except Exception as e:
				print("Crawler failed")
		self.output.output_end()
		print("Crawl finish")
		
if __name__ == "__main__":
	spider = SpiderMan()
	spider.crawl("http://theater.mtime.com/China_Beijing/")
```

详细的信息和相应的依赖库查看源代码
在命令行运行`python mtime_spider.py`即可查看运行结果。
命令行中数据`sqlite3 MTime.db`进入数据库，`SELECT * FORM MTime`查看数据是否正常插入。


感谢你的时间, (~ ~) 
