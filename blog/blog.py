# -*- coding: utf-8 -*-

import asyncio

import asyncio_mongo
import aiohttp_jinja2

from aiohttp import web

db_host, db_port = 'localhost', 27017

@aiohttp_jinja2.template('index.jinja2')
@asyncio.coroutine
def root(request):
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo.blog
    post = blog.post
    body = ''
    f = asyncio_mongo.filter.sort(asyncio_mongo.filter.DESCENDING("date"))
    posts = yield from post.find(limit=5, filter=f)
    for post in posts:
        post['date'] = post['date'].strftime("%a %d %B %Y")
    return {'posts': posts, 'cssfile': 'http://localhost:8080/main.css'}


@aiohttp_jinja2.template('post.jinja2')
@asyncio.coroutine
def post(request):
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo.blog
    post = blog.post
    try:
        post = (yield from post.find_one(
            {'_id': asyncio_mongo.bson.ObjectId(request.match_info['postid'])}))
    except asyncio_mongo._bson.errors.InvalidId:
        raise web.HTTPNotFound(reason='Id not found')
    post['date'] = post['date'].strftime("%a %d %B %Y")
    return {'post': post, 'cssfile': 'http://localhost:8080/main.css'}


@asyncio.coroutine
def css(request):
    return web.Response(
        headers={'content-type': 'text/css'},
        text=open('./blog/templates/main.css').read())


app = web.Application()
aiohttp_jinja2.setup(
    app,
    loader=aiohttp_jinja2.jinja2.FileSystemLoader('./blog/templates'))

app.router.add_route('GET', '/', root)
app.router.add_route('GET', '/main.css', css)
app.router.add_route('GET', '/post/{postid}', post)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ip = '0.0.0.0'
    port = 8080
    f = loop.create_server(app.make_handler(), ip, port)
    srv = loop.run_until_complete(f)
    print('serving on', ip, port)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
