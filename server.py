from aiohttp import web
import aiofiles
import asyncio
import os
import logging


logger = logging.getLogger(__file__)


async def archivate(request):
    name = request.match_info.get('archive_hash')
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'multipart/form-data'
    response.headers['Content-Disposition'] = f'attachment;filename={name}.zip'

    if not os.path.exists(f'test_photos/{name}/'):
        raise web.HTTPNotFound(text='Archive doesn\'t exist or was deleted.')

    process = await asyncio.create_subprocess_shell(
        f'zip -j -r - test_photos/{name}/',
        stdout=asyncio.subprocess.PIPE
    )
    await response.prepare(request)
    try:
        while True:
            content = await process.stdout.read(500000)
            if not content:
                break
            logger.info('Sending archive chunk ...')
            await response.write(content)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.debug('Download was interrupted!')
        raise
    finally:
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    web.run_app(app)
