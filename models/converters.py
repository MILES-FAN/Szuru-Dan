from config import config
from utils import convert_back_rating
from services.url_helper import build_resource_url
from services.timing import Timer

# Global state for favorites mapping
fav_map = {}

category_map = {
    'General': 0,
    'Artist': 1,
    'Series': 3,
    'Character': 4,
    'Meta': 5,
    'default': 0,
    'general': 0,
    'artist': 1,
    'series': 3,
    'character': 4,
    'meta': 5,
    0: 'General',
    1: 'Artist',
    3: 'Series',
    4: 'Character',
    5: 'Meta'
}

def get_fav(post_id, login):
    post_id = int(post_id)
    if not post_id in fav_map:
        return False
    if login in fav_map[post_id]:
        print(f"{login} has favorited {post_id}")
        return True
    return False

def tags_str(tags):
    tags_list = []
    for tag in tags:
        tags_list.append(tag['names'][0])
    return ' '.join(tags_list)

def convert_user_format(user_profile):
    user_profile = user_profile['results'][0]
    print(user_profile)
    profile = {
        'last_logged_in_at': user_profile['lastLoginTime'],
        'id': 1,
        'name': user_profile['name'],
        'level': 20,
        'created_at': user_profile['creationTime'],
        'blacklisted_tags': '',
        'favorite_tags': '',
        'is_deleted': False,
        'is_banned': False,
        'level_string': user_profile['rank'],
        'time_zone': 'Eastern Time (US & Canada)',
        'post_upload_count': user_profile['uploadedPostCount'],
        'updated_at': user_profile['lastLoginTime']
    }
    return profile

def convert_post_format(szuru_post, login=None):
    with Timer("Build resource URLs"):
        contentUrl = build_resource_url(szuru_post['contentUrl'])
        thumbnailUrl = build_resource_url(szuru_post['thumbnailUrl'])
        ext = contentUrl.split('.')[-1]
    
    with Timer("Process tags"):
        favorited = ''
        artist_tag_string = ''
        artist_tag_list = []
        general_tag_string = ''
        general_tag_list = []
        character_tag_string = ''
        character_tag_list = []
        copyright_tag_string = ''
        copyright_tag_list = []
        meta_tag_string = ''
        meta_tag_list = []
        
        for tag in szuru_post['tags']:
            if tag['category'].lower() == 'default':
                general_tag_list.append(tag['names'][0])
            elif tag['category'].lower() == 'artist':
                artist_tag_list.append(tag['names'][0])
            elif tag['category'].lower() == 'character':
                character_tag_list.append(tag['names'][0])
            elif tag['category'].lower() == 'series':
                copyright_tag_list.append(tag['names'][0])
            elif tag['category'].lower() == 'meta':
                meta_tag_list.append(tag['names'][0])
    
    with Timer("Process favorites"):
        favoritedBy = szuru_post['favoritedBy']
        post_id = szuru_post['id']

        for fav in favoritedBy:
            if post_id in fav_map:
                fav_map[post_id].append(fav['name'])
            else:
                fav_map[post_id] = [fav['name']]
    
    with Timer("Build tag strings"):
        tag_count_artist = len(artist_tag_list)
        tag_count_general = len(general_tag_list)
        tag_count_character = len(character_tag_list)
        tag_count_copyright = len(copyright_tag_list)
        tag_count_meta = len(meta_tag_list)
        artist_tag_string = ' '.join(artist_tag_list)
        general_tag_string = ' '.join(general_tag_list)
        character_tag_string = ' '.join(character_tag_list)
        copyright_tag_string = ' '.join(copyright_tag_list)
        meta_tag_string = ' '.join(meta_tag_list)
    
    with Timer("Process source and favorites check"):
        source = ''
        if szuru_post['source']:
            source = szuru_post['source']
        if '\n' in source:
            source = source.split('\n')[0]
        if login:
            favorited = get_fav(szuru_post['id'], login)
    
    with Timer("Build response object"):
        ret = {
            'id': szuru_post['id'],
            'created_at': szuru_post['creationTime'],
            'uploader_id': 1,
            'score': szuru_post['score'],
            'file_url': contentUrl,
            'large_file_url': contentUrl,
            'preview_file_url': thumbnailUrl,
            'file_ext': ext,
            'rating': convert_back_rating(szuru_post['safety']),
            'source': source,
            'tag_string': tags_str(szuru_post['tags']),
            'fav_string': 'fav:1' if favorited else '',
            'tag_string_general': general_tag_string,
            'tag_string_artist': artist_tag_string,
            'tag_string_character': character_tag_string,
            'tag_string_copyright': copyright_tag_string,
            'tag_string_meta': meta_tag_string,
            'tag_count': len(szuru_post['tags']),
            'tag_count_artist': tag_count_artist,
            'tag_count_general': tag_count_general,
            'tag_count_character': tag_count_character,
            'tag_count_copyright': tag_count_copyright,
            'tag_count_meta': tag_count_meta,
            'image_width': szuru_post['canvasWidth'],
            'image_height': szuru_post['canvasHeight'],
            'file_size': szuru_post['fileSize'],
            'has_large': True,
            'has_visible_children': False,
            'has_active_children': False,
            'has_children': False,
            'media_asset': {
                'id': szuru_post['id'],
                'created_at': szuru_post['creationTime'],
                'updated_at': szuru_post['creationTime'],
                'md5': szuru_post['checksumMD5'],
                'file_ext': ext,
                'image_width': szuru_post['canvasWidth'],
                'image_height': szuru_post['canvasHeight'],
                'variants': [
                    {
                        'type': 'sample',
                        'url': contentUrl,
                        'width': szuru_post['canvasWidth'],
                        'height': szuru_post['canvasHeight'],
                        'file_ext': ext
                    },
                    {
                        'type': 'original',
                        'url': contentUrl,
                        'width': szuru_post['canvasWidth'],
                        'height': szuru_post['canvasHeight'],
                        'file_ext': ext
                    }
                ]
            }
        }

    return ret 