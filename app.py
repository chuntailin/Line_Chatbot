import os
from flask import Flask, request, abort
from enum import Enum
from imdb import IMDb, IMDbError

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

# Function Type Enum
class MenuFunction(Enum):
	RESUME = "履歷"
	MOVIE = "電影"

# Static variable
ACCESS_TOKEN = '6HCT75JRE2ltDaznitgI8g4uJjJZHEf+311Uf9cEQus6rC2n0qIsXWDqdCADGlerleRjpLElqd1iziHEchUqSj43trQG/FREni7UsRTAIr+piJjTRU5vZiWBw0pmJlXDrSNL4PSTWruWV+vy1U2KJAdB04t89/1O/w1cDnyilFU='
SECRET = 'ba071c1b08c2ef9ada5730e996d0ee7b'

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(ACCESS_TOKEN)
# Channel Secret
handler = WebhookHandler(SECRET)


# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	message = event.message.text

	if message == MenuFunction.RESUME.value:
		resume_thumbnail_url = "https://i.imgur.com/8YjqF87.png"
		resume_url = "https://drive.google.com/open?id=1ktsuFJ6YUSHYqrZu8HBe0fFSASGLZmHc"
		
		temp_message = TemplateSendMessage(
	    	alt_text='Buttons template',
		    template=ButtonsTemplate(
		        thumbnail_image_url=resume_thumbnail_url,
		        title='【Resume】',
		        text='Tap see more button to check the resume for Chun-Tai, Lin.',
		        actions=[
		            URITemplateAction(
		                label='See more',
		                uri=resume_url
		            )
		        ]
	    	)
		)

		line_bot_api.reply_message(event.reply_token, temp_message)

	elif message == MenuFunction.MOVIE.value:
		content = "透過輸入[@電影]，\n例如：@Interstellar，\n可以為您搜尋與該電影相關的資訊\n\nP.S. 片名須為英文"
		text_message = TextMessage(text=content)
		line_bot_api.reply_message(event.reply_token, text_message)

	elif message.startswith("@"):
		movie_name = message[1:]
		results = search_movie_info(movie_name)

		if results:
			text_message, temp_message = results[0], results[1]
			line_bot_api.reply_message(event.reply_token, [text_message, temp_message])

		else:
			content = "不好意思，\n沒有為您搜尋到相關的電影資訊"
			text_message =  TextMessage(text=content)
			line_bot_api.reply_message(event.reply_token, text_message)


# IMDB search
def search_movie_info(name):
	try:
		imdb_search_base_url = "https://www.imdb.com/title/"
		ia = IMDb()
		results = ia.search_movie(name)

		if len(results) > 0:
			movie = results[0]
			movie_id = movie.movieID
			movie_info = ia.get_movie(movie_id)

			title = movie_info["long imdb title"]
			rating = movie_info["rating"]
			votes = movie_info["votes"]
			runtime = movie_info["runtimes"][:1][0]
			genres = movie_info["genres"][:3]

			# [Person]
			directors = movie_info["director"][:3]
			writers = movie_info["writer"][:3]
			casts = movie_info["cast"][:3]

			director_names = [d["name"] for d in directors]
			writer_names = [w["name"] for w in writers]
			cast_names = [c["name"] for c in casts]

			# ButtonTemplate
			poster_url = movie_info["cover url"]
			summary = movie_info["plot"][0]

			content = "【名稱】: {} \n".format(title) + \
						"【片長】: {} 分鐘 \n".format(runtime) + \
						"【IMDb評分】: {} \n".format(rating) + \
						"【票數】: {} \n".format(votes) + \
						"【分類】: {} \n".format(", ".join(genres)) + \
						"【導演】: {} \n".format(", ".join(director_names)) + \
						"【編劇】: {} \n".format(", ".join(writer_names)) + \
						"【演員】: {} \n".format(", ".join(cast_names))
			
			text_message = TextMessage(text=content)
			temp_message = TemplateSendMessage(
		    	alt_text='Buttons template',
			    template=ButtonsTemplate(
			        thumbnail_image_url=poster_url,
			        title='{}'.format(title),
			        text='{}...'.format(summary[:57]),
			        actions=[
			            URITemplateAction(
			                label='See more',
			                uri=imdb_search_base_url + "tt{}".format(movie_id)
			            )
			        ]
		    	)
			)

			return (text_message, temp_message)

		else:
			print("result not found.")
			return None

	except IMDbError as e:
		print("IMDbError: ", e)
		return None

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
