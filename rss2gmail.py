#!/usr/bin/env python
#-*- coding:utf-8 -*-

import urllib
import smtplib
import feedparser
import simplejson as json
from time import gmtime, strftime
from email.mime.text import MIMEText

class rssGmail:
	"""Parse DOM or Rss/ATOM then send to a gamil."""

	def __init__(self, sender, pwd, receiver):
		"""init class parameters"""
		self.sender = sender
		self.pwd = pwd
		self.receiver = receiver

	def parse_163(self, url):
	"""Parse the DOM of the url,return json."""
		#: load the url and get it's DOM content
		try:
			htmls = urllib.urlopen(url).read()
		except IOError:
			print 'IOError'
		#: filter the tie text
		tie_json = json.loads(htmls.replace('var replyData=','')[:-1])
		self.html_page = self.parse_html(tie_json)
		return self.html_page
	
	def parse_html(self, tie_json):
		"""Filter tie's content,return html."""
		html_body = ''
		for tie in tie_json['finePosts']:
			html_body += '''
			<span class='author'>@:{0}</span>
			<div class='body'>
				<div class='content'>{1}</div>
			</div>
			'''.format(tie['1']['s'].encode('utf-8'),tie['1']['b'].encode('utf-8'))
		return html_body

	def parse_rss(self, rss_url):
		"""Parse RSS/ATOM,return html."""
		html_body = ''
		rss = feedparser.parse(rss_url)
		for i in range(len(rss['entries'])):
			html_body += '''
			<span class='author'>@:{0}</span>
			<div class='body'>
				<div class='content'>{1}</div>
			</div>
			'''.format(rss.entries[i].title.encode('utf-8'),rss.entries[i].description.encode('utf-8'))
		return html_body

	def mail(self, mail_body):
		"""Send the mail content."""
		host = 'smtp.gmail.com'
		port = 465
		body = mail_body
		msg = MIMEText(body, 'html')
		msg['subject'] = strftime('%Y-%m-%d %H-%M-%S', gmtime())+'_rssGmailData'
		msg['from'] = self.sender
		msg['to'] = self.receiver

		try:
			s = smtplib.SMTP_SSL(host, port);
			s.set_debuglevel(1)
			s.login(self.sender, self.pwd)
			s.sendmail(self.sender, self.receiver, msg.as_string())
			s.close()
			print 'successfully sent the mail'
		except:
			print 'failed to send mail'

if __name__ == "__main__":
	"""Start to works."""

	#: Gmail
	r =	rssGmail('send@gmail.com', 'password', 'receive@gmail.com')
	#: The html content's stylesheet
	mail_body = '''
	<style>
	.author{
	position: relative;float: left;display: block;color: #1e50a2;
	}
	.body{
	font-size: 14px;clear: both;white-space: normal;word-break: break-all;background-color: #ffffee;border: 1px solid #ddd;
	}
	.content{
	line-height: 21px; margin-bottom: 3px; zoom: 1; word-wrap: break-word;overflow:hidden;
	}
	</style>
	'''

	#: 163_tie_recommend
	for x in range(1, 4):
		tie_body = ''
		tie_html = r.parse_163('http://tie.163.com/plaza/data/%d/recommend.html' %x)
		tie_body += tie_html
	r.mail(mail_body+tie_body)

	#: zhihu_rss
	zhihu_body = r.parse_rss('http://www.zhihu.com/rss')
	r.mail(mail_body+zhihu_body)

	#: beta_rss
	beta_body = r.parse_rss('http://www.cnbeta.com/commentrss.php')
	r.mail(mail_body+beta_body)
