from base64 import b64encode

def tags_str(tags):
    tags_list = []
    for tag in tags:
        tags_list.append(tag['names'][0])

    return ' '.join(tags_list)

def parse_query(query : str) -> str:
    queries = query.split(' ')
    for q in queries:
        if 'rating' in q:
            rating = q.split(':')[-1]
            rating = convert_rating(rating)
            query = query.replace(q, f'safety:{rating}')
        if 'ordfav:' in q:
            name = q.split(':')[-1]
            query = query.replace(q, f'fav:{name}')
    return query

@staticmethod
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