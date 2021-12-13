from typing import Literal, Union
from cv2 import cv2
import urllib
import numpy as np
import os


class Paintable:
    def __init__(self):
        self.img_loaded = False

    @staticmethod
    def int_as_words(x: int) -> str:
        if x < 1000:
            return str(x)
        if x < 1000000:
            if (x // 100)%10 == 0:
                return f'{x // 1000}K'
            else:
                return f'{x//1000}.{(x // 100)%10}K'
        if x < 1000000000:
            if (x // 100000)%10 == 0:
                return f'{x // 1000000}M'
            else:
                return f'{x//1000000}.{(x // 100000)%10}M'
        if x < 1000000000000:
            if (x // 100000000)%10 == 0:
                return f'{x // 1000000000}B'
            else:
                return f'{x//1000000000}.{(x // 100000000)%10}B'
        if (x // 100000000000)%10 == 0:
            return f'{x // 1000000000000}T'
        else:
            return f'{x//1000000000000}.{(x // 100000000000)%10}T'
        

    def load_img(self, video_id: str, like_count:int, dislike_count: int, thumbnail: Union[str, None] = None) -> None:
        self.video_id = video_id
        self.thumbnail = thumbnail
        self.like_count = like_count
        self.dislike_count = dislike_count

        if not os.path.exists(f'data/{self.video_id}'):
            os.makedirs(f'data/{self.video_id}')
        # try to get image from local storage using opencv: file - data/<video id>/thumbnail.jpg
        # check if file exists
        if os.path.exists(f'data/{self.video_id}/thumbnail.jpg'):
            self.img = cv2.imread(f'data/{self.video_id}/thumbnail.jpg')
        elif self.thumbnail:
            try:
                # get image from url: https://i.ytimg.com/vi/<video id>/hqdefault.jpg
                req = urllib.urlopen(self.thumbnail['url'])
                arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
                img = cv2.imdecode(arr, -1) # 'Load it as it is'
                # save this image to local storage using opencv: file - data/<video id>/thumbnail.jpg
                cv2.imwrite(f'data/{self.video_id}/thumbnail.jpg', img)
                self.img = img
            except:
                # TODO: Do proper error handling
                print('Error: Could not get image from url')
                raise
        else:
            raise Exception('Error: No image found')

        # load height and width of image
        self.height, self.width = self.img.shape[:2]
        self.img_loaded = True

    def details(self):
        print(f'Video ID: {self.video_id}')
        print(f'Like Count: {self.like_count}')
        print(f'Dislike Count: {self.dislike_count}')
        print(f'Position: {self.position}')
        print(f'Thumbnail: {self.thumbnail}')
        print(f'Height: {self.height}')
        print(f'Width: {self.width}')

    def display(self, window_name='Image'):
        cv2.imshow(window_name, self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

class Painter(Paintable):
    def __init__(self, position: Literal['top-left', 'top-right', 'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right', 'center']):
        self.position = position

    def paint(self):
        if not self.img_loaded:
            raise Exception('Error: Image not loaded')
        margin_percent = 0.035

        rectangle_width = int(self.width * 0.25)
        rectangle_height = int(self.height * 0.07)
        opacity = 0
        
        # get average color of the image
        color = np.average(self.img, axis=(0, 1))
        
        # set text color to light or dark based on color
        if color[0] > 127 and color[1] > 127 and color[2] > 127:
            text_color = (0, 0, 0)
        else:
            text_color = (255, 255, 255)

        positions = {
            'top': (int(self.width * 0.5) - rectangle_width//2, int(self.height * margin_percent)),
            'bottom': (int(self.width * 0.5) - rectangle_width//2, int(self.height * (1 - margin_percent)) - rectangle_height),
            'left': (int(self.width * margin_percent), int(self.height * 0.5) - rectangle_height//2),
            'right': (int(self.width * (1 - margin_percent)) - rectangle_width, int(self.height * 0.5) - rectangle_height//2),
            'top-left': (int(self.width * margin_percent), int(self.height * margin_percent)),
            'top-right': (int(self.width * (1 - margin_percent)) - rectangle_width, int(self.height * margin_percent)),
            'bottom-left': (int(self.width * margin_percent), int(self.height * (1 - margin_percent)) - rectangle_height),
            'bottom-right': (int(self.width * (1 - margin_percent)) - rectangle_width, int(self.height * (1 - margin_percent)) - rectangle_height),
            'center': (int(self.width * 0.5) - rectangle_width//2, int(self.height * 0.5) - rectangle_height//2)
        }

        # draw black rectangle on image at position with opacity
        # cv2.rectangle(self.img, positions[self.position], (positions[self.position][0] + rectangle_width, positions[self.position][1] + rectangle_height), (30, 30, 30), -1)
        
        sub_rect = self.img[positions[self.position][1]:positions[self.position][1] + rectangle_height, positions[self.position][0]:positions[self.position][0] + rectangle_width]
        white_rect = np.full(sub_rect.shape, color, np.uint8)
        cv2.addWeighted(sub_rect, opacity, white_rect, 1 - opacity, 1.0, dst=sub_rect)
        self.img[positions[self.position][1]:positions[self.position][1] + rectangle_height, positions[self.position][0]:positions[self.position][0] + rectangle_width] = sub_rect

        # draw text in rectangle: L: <like count> / D: <dislike count>
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = text_color
        line_type = 2
        text = f'L: {Paintable.int_as_words(self.like_count)} / D: {Paintable.int_as_words(self.dislike_count)}'
        # get text size
        text_size = cv2.getTextSize(text, font, font_scale, line_type)[0]
        # get text position
        text_x = positions[self.position][0] + rectangle_width//2 - text_size[0]//2
        text_y = positions[self.position][1] + rectangle_height//2 + text_size[1]//2
        # draw text
        cv2.putText(self.img, text, (text_x, text_y), font, font_scale, font_color, line_type)
        


    

if __name__ == '__main__':
    painter = Painter("bottom-right")
    painter.load_img(
        'test',
        like_count=1001,
        dislike_count=100,
    )
    painter.details()
    painter.display("Unpainted Image")
    painter.paint()
    painter.display("Painted Image")
