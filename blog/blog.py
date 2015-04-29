# -*- coding: utf-8 -*-

import asyncio

import asyncio_mongo
import aiohttp_jinja2

from aiohttp import web

db_host, db_port = 'localhost', 27017

@aiohttp_jinja2.templat('index.jinja2')
@asyncio.coroutine
def root(request):
    mongo = yield from asyncio_mongo.Connection.create(db_host, db_port)
    blog = mongo.blog
    post = blog.post
    body = ''
    posts = yield from post.find(limit=10)
    print(posts)
    for post in posts:
        body += post['body']
    return web.Response(body=bytes(body, 'utf-8'))

app = web.Application()
aiohttp_jinja2.setup(app,
                     aiohttp_jinja2.jinja2.FileSystemLoader('./templates/'))
app.router.add_route('GET', '/', root)


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
