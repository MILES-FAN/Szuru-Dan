import zlib
from config import config
from utils import convert_back_rating
from services.url_helper import build_resource_url
from services.timing import Timer

# Szurubooru has no public numeric user ids, the logged in user is always reported as 1
CURRENT_USER_ID = 1

# Danbooru tag categories: 0 general, 1 artist, 3 copyright, 4 character, 5 meta
danbooru_category_map = {
    'default': 0,
    'general': 0,
    'artist': 1,
    'series': 3,
    'copyright': 3,
    'character': 4,
    'meta': 5,
}

def danbooru_category(szuru_category):
    """Map a szurubooru tag category name to a Danbooru category id, unknown categories are general"""
    return danbooru_category_map.get((szuru_category or '').lower(), 0)

def stable_id(name):
    """Derive a stable positive integer id for resources that szurubooru only identifies by name"""
    return zlib.crc32(name.encode('utf-8')) & 0x7fffffff

def user_id_for(user, login=None):
    """Danbooru user id for a szurubooru micro user resource"""
    if not user:
        return None
    if login and user['name'].lower() == login.lower():
        return CURRENT_USER_ID
    # Never collide with the current user's id
    return stable_id(user['name']) or 2

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
        'id': CURRENT_USER_ID,
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
        # Indexed by Danbooru category id
        tag_lists = {0: [], 1: [], 3: [], 4: [], 5: []}
        for tag in szuru_post['tags']:
            tag_lists[danbooru_category(tag['category'])].append(tag['names'][0])
        general_tag_list = tag_lists[0]
        artist_tag_list = tag_lists[1]
        copyright_tag_list = tag_lists[3]
        character_tag_list = tag_lists[4]
        meta_tag_list = tag_lists[5]
    
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
        # ownFavorite/ownScore are only meaningful for authenticated requests
        favorited = bool(login) and szuru_post.get('ownFavorite', False)
        score = szuru_post.get('score', 0)
        updated_at = szuru_post.get('lastEditTime') or szuru_post['creationTime']
        # Szurubooru doesn't track note/comment times, the last edit time is the closest match
        last_noted_at = updated_at if szuru_post.get('noteCount') else None
        last_commented_at = updated_at if szuru_post.get('commentCount') else None
    
    with Timer("Build response object"):
        ret = {
            'id': szuru_post['id'],
            'created_at': szuru_post['creationTime'],
            'updated_at': updated_at,
            'uploader_id': user_id_for(szuru_post.get('user'), login),
            'approver_id': None,
            'score': score,
            # Szurubooru only stores the sum of votes
            'up_score': max(score, 0),
            'down_score': min(score, 0),
            'fav_count': szuru_post.get('favoriteCount', 0),
            'md5': szuru_post['checksumMD5'],
            'file_url': contentUrl,
            'large_file_url': contentUrl,
            'preview_file_url': thumbnailUrl,
            'file_ext': ext,
            'rating': convert_back_rating(szuru_post['safety']),
            'source': source,
            'pixiv_id': None,
            'tag_string': tags_str(szuru_post['tags']),
            'fav_string': f'fav:{CURRENT_USER_ID}' if favorited else '',
            'is_favorited': favorited,
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
            'last_noted_at': last_noted_at,
            'last_commented_at': last_commented_at,
            'last_comment_bumped_at': last_commented_at,
            'is_pending': False,
            'is_flagged': False,
            'is_deleted': False,
            'is_banned': False,
            'bit_flags': 0,
            # Szurubooru relations have no parent/child direction
            'parent_id': None,
            'has_large': True,
            'has_visible_children': False,
            'has_active_children': False,
            'has_children': False,
            'media_asset': {
                'id': szuru_post['id'],
                'created_at': szuru_post['creationTime'],
                'updated_at': updated_at,
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

def convert_creator_format(user, login=None):
    if not user:
        return None
    return {
        'id': user_id_for(user, login),
        'name': user['name'],
        'level': 20,
        'level_string': 'Member',
        'is_banned': False,
    }

def convert_comment_format(szuru_comment, login=None):
    creator = convert_creator_format(szuru_comment.get('user'), login)
    return {
        'id': szuru_comment['id'],
        'post_id': szuru_comment['postId'],
        'creator_id': creator['id'] if creator else None,
        'creator': creator,
        'updater_id': creator['id'] if creator else None,
        'body': szuru_comment['text'],
        'score': szuru_comment.get('score', 0),
        'created_at': szuru_comment['creationTime'],
        'updated_at': szuru_comment.get('lastEditTime') or szuru_comment['creationTime'],
        'do_not_bump_post': False,
        'is_deleted': False,
        'is_sticky': False,
    }

def convert_vote_format(target_key, target_id, score, updated_at=None):
    """Danbooru post/comment vote. Szurubooru keeps one vote per user and target,
    so the target id doubles as the vote id."""
    return {
        'id': target_id,
        target_key: target_id,
        'user_id': CURRENT_USER_ID,
        'score': score,
        'created_at': updated_at,
        'updated_at': updated_at,
        'is_deleted': score == 0,
    }

def convert_note_format(note, index, szuru_post):
    """Convert a szurubooru note (polygon with 0..1 coordinates) to a Danbooru note box in pixels"""
    width = szuru_post['canvasWidth']
    height = szuru_post['canvasHeight']
    xs = [point[0] for point in note['polygon']]
    ys = [point[1] for point in note['polygon']]
    updated_at = szuru_post.get('lastEditTime') or szuru_post['creationTime']
    return {
        # Notes have no id in szurubooru
        'id': szuru_post['id'] * 1000 + index,
        'post_id': szuru_post['id'],
        'x': round(min(xs) * width),
        'y': round(min(ys) * height),
        'width': round((max(xs) - min(xs)) * width),
        'height': round((max(ys) - min(ys)) * height),
        'body': note['text'],
        'is_active': True,
        'version': 1,
        'created_at': updated_at,
        'updated_at': updated_at,
    }

def convert_pool_format(szuru_pool):
    category = (szuru_pool.get('category') or '').lower()
    post_ids = [post['id'] for post in szuru_pool.get('posts', [])]
    return {
        'id': szuru_pool['id'],
        'name': szuru_pool['names'][0],
        'created_at': szuru_pool.get('creationTime'),
        'updated_at': szuru_pool.get('lastEditTime') or szuru_pool.get('creationTime'),
        'description': szuru_pool.get('description') or '',
        'is_active': True,
        'is_deleted': False,
        'post_ids': post_ids,
        'category': 'collection' if category == 'collection' else 'series',
        'post_count': szuru_pool.get('postCount', len(post_ids)),
    }

def convert_tag_format(szuru_tag):
    name = szuru_tag['names'][0]
    return {
        # Tags are identified by name in szurubooru
        'id': stable_id(name),
        'name': name,
        'post_count': szuru_tag.get('usages', 0),
        'category': danbooru_category(szuru_tag.get('category')),
        'created_at': szuru_tag.get('creationTime'),
        'updated_at': szuru_tag.get('lastEditTime') or szuru_tag.get('creationTime'),
        'is_deprecated': False,
        'words': name.split('_'),
    }
