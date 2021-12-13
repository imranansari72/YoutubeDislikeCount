# Retrieve the authenticated user's uploaded videos.
# Sample usage:
# python my_uploads.py

import argparse
import os
import re

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

import pickle
from google.auth.transport.requests import Request
import config



# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = 'client_secret.json'

# This OAuth 2.0 access scope allows for read-only access to the authenticated
# user's account, but not other types of account access.
SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Authorize the request and store authorization credentials.
def get_authenticated_service():
    
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    credentials = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            if config.AUTH_TYPE == 'server':
                credentials = flow.run_local_server(port=0)
            elif config.AUTH_TYPE == 'console':
                credentials = flow.run_console()
            else: 
                raise ValueError("Invalid auth type. Auth type must be either console or server")
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)


    return build(API_SERVICE_NAME, API_VERSION, credentials = credentials)

def get_my_uploads_list():
  # Retrieve the contentDetails part of the channel resource for the
  # authenticated user's channel.
  channels_response = youtube.channels().list(
    mine=True,
    part='contentDetails'
  ).execute()

  for channel in channels_response['items']:
    # From the API response, extract the playlist ID that identifies the list
    # of videos uploaded to the authenticated user's channel.
    return channel['contentDetails']['relatedPlaylists']['uploads']

  return None

def list_my_uploaded_videos(uploads_playlist_id):
  # Retrieve the list of videos uploaded to the authenticated user's channel.
  playlistitems_list_request = youtube.playlistItems().list(
    playlistId=uploads_playlist_id,
    part='snippet',
    maxResults=5
  )

  print ('Videos in list %s' % uploads_playlist_id)
  while playlistitems_list_request:
    playlistitems_list_response = playlistitems_list_request.execute()

    # Print information about each video.
    for playlist_item in playlistitems_list_response['items']:
        title = playlist_item['snippet']['title']
        video_id = playlist_item['snippet']['resourceId']['videoId']
        stats = youtube.videos().list(
            id=video_id,
            part='statistics'
        ).execute()['items'][0]['statistics']
        views = stats['viewCount']
        like_count = stats['likeCount']
        dislike_count = stats['dislikeCount']
        description = playlist_item['snippet']['description']
        #TODO check if thumbnail doesn't exists
        thumbnails = playlist_item['snippet']['thumbnails']
        thumbnail = thumbnails['maxres'] if 'maxres' in thumbnails else thumbnails['standard'] if 'standard' in thumbnails else thumbnails['high'] if 'high' in thumbnails else thumbnails['medium'] if 'medium' in thumbnails else thumbnails['default'] if 'default' in thumbnails else None
        yield {
            'title': title,
            'video_id': video_id,
            'views': views,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'description': description,
            'thumbnails': thumbnails,
            'thumbnail': thumbnail
        }


    playlistitems_list_request = youtube.playlistItems().list_next(
      playlistitems_list_request, playlistitems_list_response)

if __name__ == '__main__':
  youtube = get_authenticated_service()
  try:
    uploads_playlist_id = get_my_uploads_list()
    if uploads_playlist_id:
      for z in list_my_uploaded_videos(uploads_playlist_id):
        print(z)
    else:
      print('There is no uploaded videos playlist for this user.')
  except HttpError as e:
    print ('An HTTP error %d occurred:\n' % (e.resp.status))
    print (e.content.decode('utf-8'))
