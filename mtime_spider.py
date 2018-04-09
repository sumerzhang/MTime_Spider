#coding: utf-8

import requests
import re
import time
import sqlite3
import json

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
	