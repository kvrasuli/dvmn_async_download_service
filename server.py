from aiohttp import web
import aiofiles
import asyncio
import os
import logging
import argparse


CHUNK_SIZE = 1000
logger = logging.getLogger(__file__)


async def archivate(request):
    archive_hash = request.match_info.get('archive_hash')
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'multipart/form-data'
    response.headers['Content-Disposition'] = f'attachment;filename={archive_hash}.zip'

    path = os.path.join(app.path, archive_hash)
    if not os.path.exists(path):
        raise web.HTTPNotFound(text='Archive doesn\'t exist or was deleted.')

    archiving_process = await asyncio.create_subprocess_exec(
        'zip', '-j', '-r', '-', path,
        stdout=asyncio.subprocess.PIPE
    )
    await response.prepare(request)
    try:
        while True:
            archive_chunk = await archiving_process.stdout.read(CHUNK_SIZE)
            if not archive_chunk:
                break
            logger.info('Sending archive chunk ...')
            await response.write(archive_chunk)
            await asyncio.sleep(app.delay)
    except asyncio.CancelledError:
        logger.debug('Download was interrupted!')
        raise
    finally:
        archiving_process.kill()
        await archiving_process.communicate()
        return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--log', help='Enable logging', action='store_true'
    )
    parser.add_argument(
        '--delay', help='Enable answer delay', default=0, type=int
    )
    parser.add_argument(
        '--path', help='Path to photos folder', default='test_photos'
    )
    args = parser.parse_args()
    return args.log, args.delay, args.path


if __name__ == '__main__':
    log, delay, path = parse_args()
    if log:
        logging.basicConfig(level=logging.DEBUG)

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', archivate),
    ])
    app.path = path
    app.delay = delay
    web.run_app(app)
