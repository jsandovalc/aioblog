import asyncio

import asyncio_mongo
import aiohttp_jinja2

import config

from aiohttp import web

db_host, db_port = config.DBHOST, config.DBPORT
host, port = config.HOST, config.PORT

static = config.STATIC

@aiohttp_jinja2.template('index.jinja2')
@asyncio.coroutine
def root(request):
    try:
        page = int(request.match_info['page'])
        older = 'index{}.html'.format(page+1)
        newer = 'index{}.html'.format(page-1)
    except KeyError:
        page = 1
        newer = ''
        older = 'index2.html'
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo[config.DATABASE]
    post = blog.post
    body = ''
    f = asyncio_mongo.filter.sort(asyncio_mongo.filter.DESCENDING("date"))
    posts = yield from post.find(skip=5*(page-1), limit=5, filter=f)
    if not posts:
        raise web.HTTPNotFound(reason='no older posts')
    for post in posts:
        post['url'] = 'http://{}:{}/post/{}'.format(host, port,
                                                    str(post['_id']))
        post['date'] = post['date'].strftime("%a %d %B %Y")
        post['tags'] = post['tags'] if 'tags' in post else []
    return {'posts': posts,
            'newer': newer,
            'older': older,
            'host': host,
            'port': port,
            'cssfile': 'http://{}:{}/{}css/main.css'.format(host, port, static)}


@aiohttp_jinja2.template('post.jinja2')
@asyncio.coroutine
def post(request):
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo[config.DATABASE]
    post = blog.post
    try:
        post = (yield from post.find_one(
            {'_id': asyncio_mongo.bson.ObjectId(request.match_info['postid'])}))
    except asyncio_mongo._bson.errors.InvalidId:
        raise web.HTTPNotFound(reason='Id not found')
    post['date'] = post['date'].strftime("%a %d %B %Y")
    post['url'] = 'http://{}:{}/post/{}'.format(host, port, str(post['_id']))
    return {'post': post, 'cssfile': 'http://{}:{}/{}css/main.css'.format(host,
                                                                      port,
                                                                      static)}


@aiohttp_jinja2.template('tag.jinja2')
@asyncio.coroutine
def tag(request):
    try:
        tag = request.match_info['name']
    except KeyError:
        raise web.HTTPNotFound(reason='Tag not included')
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo[config.DATABASE]
    post = blog.post
    body = ''
    f = asyncio_mongo.filter.sort(asyncio_mongo.filter.DESCENDING("date"))
    posts = yield from post.find({'tags': tag}, filter=f)
    if not posts:
        raise web.HTTPNotFound(reason='Posts not found for tag')
    for post in posts:
        post['url'] = 'http://{}:{}/post/{}'.format(host, port,
                                                    str(post['_id']))
        post['date'] = post['date'].strftime("%a %d %B %Y")
        post['tags'] = post['tags'] if 'tags' in post else []
    return {'posts': posts,
            'host': host,
            'port': port,
            'cssfile': 'http://{}:{}/{}css/main.css'.format(host, port, static)}

app = web.Application()
aiohttp_jinja2.setup(
    app,
    loader=aiohttp_jinja2.jinja2.FileSystemLoader(config.TEMPLATESPATH))

app.router.add_route('GET', '/', root)
app.router.add_route('GET', '/index{page}.html', root)
app.router.add_route('GET', '/post/{postid}', post)
app.router.add_route('GET', '/tag/{name}.html', tag)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ip = config.SERVE
    port = config.PORT
    f = loop.create_server(app.make_handler(), ip, port)
    srv = loop.run_until_complete(f)
    print('serving on', ip, port)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
