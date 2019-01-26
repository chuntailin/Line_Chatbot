import os
from flask import Flask, request, abort
from enum import Enum
from imdb import IMDb, IMDbError
import pyowm

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
	WEATHER = "天氣"

# Static variable
ACCESS_TOKEN = '6HCT75JRE2ltDaznitgI8g4uJjJZHEf+311Uf9cEQus6rC2n0qIsXWDqdCADGlerleRjpLElqd1iziHEchUqSj43trQG/FREni7UsRTAIr+piJjTRU5vZiWBw0pmJlXDrSNL4PSTWruWV+vy1U2KJAdB04t89/1O/w1cDnyilFU='
SECRET = 'ba071c1b08c2ef9ada5730e996d0ee7b'
OWM_API_KEY = "3e2af77b4e6d26ab9208b20388cfc4a5"

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

	try:
		# 履歷
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
		# 電影
		elif message == MenuFunction.MOVIE.value:
			content = "透過輸入[@電影]，\n例如：@Interstellar，\n可以為您搜尋與該電影相關的資訊\n\nP.S. 片名須為英文"
			text_message = TextMessage(text=content)
			line_bot_api.reply_message(event.reply_token, text_message)

		# 天氣
		elif message == MenuFunction.WEATHER.value:
			temp_message = TemplateSendMessage(
                alt_text='Buttons template',
                template=ButtonsTemplate(
                    thumbnail_image_url='https://i.imgur.com/Y1DWfaU.jpg',
                    title='【Weather】',
                    text='Check the weather information by location.',
                    actions=[
                        URITemplateAction(
                            label="Send location",
                            uri="line://nv/location"
                        )
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, temp_message)

		# 片名
		elif message.startswith("@"):
			movie_name = message[1:]
			results = movie_info_search(movie_name)

			if results:
				text_message, temp_message = results[0], results[1]
				line_bot_api.reply_message(event.reply_token, [text_message, temp_message])

			else:
				content = "不好意思，\n沒有為您搜尋到相關的電影資訊"
				text_message =  TextMessage(text=content)
				line_bot_api.reply_message(event.reply_token, text_message)

	except Exception as e:
		print("Exception: ", e)
		error_message = "機器人目前繁忙中，請稍後再試"
		line_bot_api.reply_message(event.reply_token, error_message)


# 處理定位
@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    try:
        lat, lon = event.message.latitude, event.message.longitude
        result = weather_observe(lat, lon)

        if result:
        	line_bot_api.reply_message(event.reply_token, result)

        else:
        	content = "不好意思，\n沒有為您搜尋到附近的氣候資訊"
        	text_message = TextMessage(text=content)
        	line_bot_api.reply_message(event.reply_token, text_message)
        	
    except Exception as e:
    	print("Exception: ", e)
    	error_message = "機器人目前繁忙中，請稍後再試"
		line_bot_api.reply_message(event.reply_token, error_message)

# IMDB search
def movie_info_search(name):
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

			temp_title = title if len(title) < 40 else "{}...".format(title[:37])

			temp_message = TemplateSendMessage(
		    	alt_text='Buttons template',
			    template=ButtonsTemplate(
			        thumbnail_image_url=poster_url,
			        title='{}'.format(temp_title),
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

	except Exception as e:
		print("IMDbError: ", e)
		return None

# Weather observation
# lat = 緯度, lon = 經度
def weather_observe(lat, lon):
	try:
		owm = pyowm.OWM(OWM_API_KEY)
		obs = owm.weather_at_coords(lat, lon)
		weather_info = obs.get_weather()

		wind_info = weather_info.get_wind()
		wind_deg, wind_spd = wind_info["deg"], wind_info["speed"]
		temp_info = weather_info.get_temperature(unit="celsius")
		temp, temp_max, temp_min = temp_info["temp"], temp_info["temp_max"], temp_info["temp_min"]
		clouds = weather_info.get_clouds()
		humidity = weather_info.get_humidity()
		status = weather_info.get_detailed_status()
		pressure = weather_info.get_pressure()["press"]

		content = "【天氣狀況】: {} \n".format(status) + \
					"【均溫】: 攝氏 {} 度 \n".format(temp) + \
					"【高溫】: 攝氏 {} 度 \n".format(temp_max) + \
					"【低溫】: 攝氏 {} 度 \n".format(temp_min) + \
					"【雲層覆蓋率】: {} % \n".format(clouds) + \
					"【濕度】: {} % \n".format(humidity) + \
					"【氣壓】: {} 百帕 \n".format(pressure) + \
					"【風速】: {} m/s \n".format(wind_spd) + \
					"【風向】: {} \n".format(wind_deg)

		return TextMessage(text=content)

	except Exception as e:
		print("Exception: ", e)
		return None





if __name__ == "__main__":
    # port = int(os.environ.get('PORT', 5000))
    # app.run(host='0.0.0.0', port=port)