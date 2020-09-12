from aiohttp import web
import aiofiles
import asyncio
import os
import logging


logger = logging.getLogger(__file__)


async def archivate(request):
    archive_hash = request.match_info.get('archive_hash')
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'multipart/form-data'
    response.headers['Content-Disposition'] = f'attachment;filename={archive_hash}.zip'

    if not os.path.exists(f'test_photos/{archive_hash}/'):
        raise web.HTTPNotFound(text='Archive doesn\'t exist or was deleted.')

    archiving_process = await asyncio.create_subprocess_exec(
        'zip', '-j', '-r', '-', f'test_photos/{archive_hash}/',
        stdout=asyncio.subprocess.PIPE
    )
    await response.prepare(request)
    try:
        while True:
            archive_chunk = await archiving_process.stdout.read(500000)
            if not archive_chunk:
                break
            logger.info('Sending archive chunk ...')
            await response.write(archive_chunk)
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.debug('Download was interrupted!')
        raise
    finally:
        archiving_process.kill()
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
