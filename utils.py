from base64 import b64encode

def tags_str(tags):
    tags_list = []
    for tag in tags:
        tags_list.append(tag['names'][0])

    return ' '.join(tags_list)

# Danbooru order: values and the szurubooru sort tokens they map to
order_map = {
    'id': 'sort:id,asc',
    'id_asc': 'sort:id,asc',
    'id_desc': 'sort:id',
    'score': 'sort:score',
    'score_desc': 'sort:score',
    'score_asc': 'sort:score,asc',
    'favcount': 'sort:fav-count',
    'favcount_asc': 'sort:fav-count,asc',
    'filesize': 'sort:file-size',
    'filesize_asc': 'sort:file-size,asc',
    'mpixels': 'sort:image-area',
    'mpixels_asc': 'sort:image-area,asc',
    'tagcount': 'sort:tag-count',
    'tagcount_asc': 'sort:tag-count,asc',
    'comment': 'sort:comment-date',
    'comment_bumped': 'sort:comment-date',
    'note': 'sort:note-count',
    'change': 'sort:last-edit-date',
    'random': 'sort:random',
}

# Danbooru is: values and the szurubooru tokens they map to
is_map = {
    'general': 'safety:safe',
    'safe': 'safety:safe',
    'sfw': 'safety:safe',
    'sensitive': 'safety:sketchy',
    'questionable': 'safety:sketchy',
    'explicit': 'safety:unsafe',
    'nsfw': 'safety:sketchy,unsafe',
    'jpg': 'type:image',
    'png': 'type:image',
    'webp': 'type:image',
    'gif': 'type:animation',
    'mp4': 'type:video',
    'webm': 'type:video',
}

# Danbooru has: values and the szurubooru tokens they map to
has_map = {
    'comments': 'comment-count-min:1',
    'notes': 'note-count-min:1',
}

# Danbooru metatags that are renamed in szurubooru
key_map = {
    'user': 'uploader',
    'favcount': 'fav-count',
    'tagcount': 'tag-count',
}

# Danbooru metatags without a szurubooru equivalent, dropped instead of failing the search
dropped_keys = {'order', 'random', 'is', 'has', 'status', 'parent', 'child', 'limit', 'filetype', 'mpixels'}

# Named tokens szurubooru understands for posts
szuru_post_keys = {
    'ar', 'area', 'aspect-ratio', 'comment', 'comment-count', 'comment-date', 'comment-time',
    'content-checksum', 'creation-date', 'creation-time', 'date', 'disliked', 'edit-date', 'edit-time',
    'fav', 'fav-count', 'fav-date', 'fav-time', 'feature-count', 'feature-date', 'feature-time',
    'file-size', 'flag', 'height', 'id', 'image-ar', 'image-area', 'image-aspect-ratio', 'image-height',
    'image-width', 'last-edit-date', 'last-edit-time', 'liked', 'md5', 'note-count', 'note-text', 'pool',
    'relation-count', 'safety', 'score', 'sha1', 'source', 'submit', 'tag', 'tag-count', 'time', 'type',
    'upload', 'uploader', 'width', 'sort', 'special',
}

def convert_range(value: str) -> str:
    """Convert Danbooru comparisons (>=5, >5, <=5, <5) to szurubooru ranges (5.., ..5)"""
    for op in ('>=', '<=', '>', '<'):
        if value.startswith(op):
            number = value[len(op):]
            if op == '>' and number.isdigit():
                return f'{int(number) + 1}..'
            if op == '<' and number.isdigit():
                return f'..{int(number) - 1}'
            return f'{number}..' if op.startswith('>') else f'..{number}'
    return value

def convert_query_token(token: str) -> str:
    """Translate one Danbooru search token, returns '' to drop it"""
    negated = token.startswith('-')
    body = token[1:] if negated else token
    if ':' not in body:
        return token
    key, value = body.split(':', 1)
    key = key.lower()
    prefix = '-' if negated else ''

    if key == 'rating':
        ratings = [convert_rating(r) for r in value.split(',')]
        ratings = [r for r in ratings if r]
        return f"{prefix}safety:{','.join(ratings)}" if ratings else ''
    if key == 'ordfav':
        return f'fav:{value}'
    if key == 'order' and not negated:
        return order_map.get(value.lower(), '')
    if key == 'random' and not negated:
        return 'sort:random'
    if key == 'is' and value.lower() in is_map:
        return prefix + is_map[value.lower()]
    if key == 'has' and value.lower() in has_map:
        return prefix + has_map[value.lower()]
    if key in dropped_keys:
        return ''

    key = key_map.get(key, key)
    base_key = key.removesuffix('-min').removesuffix('-max')
    if base_key in szuru_post_keys:
        return f'{prefix}{key}:{convert_range(value)}'
    # Not a metatag, e.g. the tag re:zero, so escape the colons
    return prefix + body.replace(':', '\\:')

def parse_query(query : str) -> str:
    tokens = [convert_query_token(token) for token in query.split()]
    return ' '.join(token for token in tokens if token)

def encode_auth_headers(u: str, p: str) -> str:
    return b64encode(f"{u}:{p}".encode("utf-8")).decode("ascii")

def convert_rating(rating: str) -> str:
    if rating is None:
        return None
    rating = rating.lower()
    switch = {
        'safe': 'safe',
        's': 'safe',
        'g': 'safe',
        'general': 'safe',
        'questionable': 'sketchy',
        'sketchy': 'sketchy',
        'q': 'sketchy',
        'sensitive': 'sketchy',
        'explicit': 'unsafe',
        'e': 'unsafe',
        'unsafe': 'unsafe',
        'rating:safe': 'safe',
        'rating:questionable': 'sketchy',
        'rating:explicit': 'unsafe',
        'rating:s': 'safe',
        'rating:q': 'sketchy',
        'rating:e': 'unsafe',
    }

    new_rating = switch.get(rating)

    return new_rating

def convert_back_rating(rating: str) -> str:
    if rating is None:
        return None
    rating = rating.lower()
    switch = {
        'safe': 's',
        'sketchy': 'q',
        'unsafe': 'e',
    }

    new_rating = switch.get(rating)

    return new_rating

def parse_tags(tags: str) -> list:
    try:
        tag_str = tags.replace(',', ' ').replace('[', '').replace(']', '').replace('\"', '')
        tags = tag_str.split(' ')
        for tag in tags:
            if tag == '' or tag == ' ':
                tags.remove(tag)
        return tags
    except Exception as e:
        print(f"Error parsing tags: {repr(e)}\n{tags}")
        raise e

def parse_tags_str(tags: str) -> str:
    tags_list = parse_tags(tags)
    tags_str = ' '.join(tags_list)
    return tags_str

def check_supported_format(url: str) -> bool:
    '''Check if the url is a supported format,
    returns True if the format is supported,
      False if it is not supported'''
    url = url.lower()
    supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'webm', 'avif', 'swf', 'heic']
    ext = url.split('.')[-1]
    if ext in supported_formats:
        return True
    return False

def check_desired_format(url: str) -> bool:
    url = url.lower()
    desired_formats = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic']
    ext = url.split('.')[-1]
    if ext in desired_formats:
        return True
    return False

def dict_factory(cursor, row):
   d = {}
   for idx, col in enumerate(cursor.description):
       d[col[0]] = row[idx]
   return d

def filtered_posts(posts: list, banned_tags: list) -> list:
    '''Method to filter posts by tags,
    returns a list of filtered posts'''
    filtered_posts = []
    for post in posts:
        tags = parse_tags(post['tags'])
        if not filtered_post_by_tags(tags, banned_tags):
            continue
        filtered_posts.append(post)
    return filtered_posts

def filtered_posts(posts: list, banned_tags: list) -> tuple[list, list]:
    '''Method to filter posts by tags,
    returns a tuple of two lists,
      the first list contains the filtered posts,
      the second list contains the blacklisted posts'''
    filtered_posts = []
    blacklisted_posts = []
    for post in posts:
        tags = parse_tags(post['tags'])
        if (not filtered_post_by_tags(tags, banned_tags)):
            blacklisted_posts.append(post)
            continue
        filtered_posts.append(post)
    return filtered_posts, blacklisted_posts

def filtered_post_by_tags(tags: list, banned_tags: list) -> bool:
    '''Method to filter posts by tags, 
    returns True if the post is not blacklisted,
      False for blacklisted posts'''
    if any(tag in banned_tags for tag in tags):
        return False
    return True

def merge_lists(list1: list, list2: list) -> list:
    '''Merge two lists evenly,
    returns a merged list'''
    if len(list1) < len(list2):
        list1, list2 = list2, list1
    for i in range(len(list2)):
        list1.insert(i*2+1, list2[i])
    return list1

def average_time(time_list: list, size = 100) -> tuple[list, float]:
    '''Method to calculate the average time of a list of times,
    returns a tuple of the time list and the average time'''
    if len(time_list) == 0:
        return time_list, 0
    elif len(time_list) > size:
        time_list = time_list[-size:]
    return time_list, sum(time_list) / len(time_list)

def size_str_to_int(size: str) -> int:
    '''Converts a size string to an integer'''
    size = size.lower()
    if 'kb' in size:
        return int(float(size.replace('kb', '')) * 1024)
    elif 'mb' in size:
        return int(float(size.replace('mb', '')) * 1024 * 1024)
    elif 'gb' in size:
        return int(float(size.replace('gb', '')) * 1024 * 1024 * 1024)
    return int(size)

def check_size_limit_str_valid(size: str) -> bool:
    try:
        size_str_to_int(size)
        return True
    except ValueError:
        return False