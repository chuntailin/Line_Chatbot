import os
from flask import Flask, request, abort
from enum import Enum
from imdb import IMDb

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

class MenuFunction(Enum):
	RESUME = "履歷"
	MOVIE = "電影"

ACCESS_TOKEN = '6HCT75JRE2ltDaznitgI8g4uJjJZHEf+311Uf9cEQus6rC2n0qIsXWDqdCADGlerleRjpLElqd1iziHEchUqSj43trQG/FREni7UsRTAIr+piJjTRU5vZiWBw0pmJlXDrSNL4PSTWruWV+vy1U2KJAdB04t89/1O/w1cDnyilFU='
SECRET = 'ba071c1b08c2ef9ada5730e996d0ee7b'

app = Flask(__name__)

# Channel Access Token
line_bot_api = LineBotApi(ACCESS_TOKEN)
# Channel Secret
handler = WebhookHandler(SECRET)

ia = IMDb()

resume_thumbnail_url = "https://i.imgur.com/8YjqF87.png"
resume_url = "https://raw.githubusercontent.com/chuntailin/Resume/master/Resume.pdf"

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
		temp_message = TemplateSendMessage(
	    	alt_text='Buttons template',
		    template=ButtonsTemplate(
		        thumbnail_image_url=resume_thumbnail_url,
		        title='【Resume】',
		        text='【姓名】\n\t林均泰\n\n【碩士】\n\t國立臺灣大學\n\t資訊管理研究所',
		        actions=[
		            URITemplateAction(
		                label='See more',
		                uri=resume_url
		            )
		        ]
	    	)
		)

		line_bot_api.reply_message(event.reply_token, temp_message)




if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
