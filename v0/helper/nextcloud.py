import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from v0.helper.progress import FileWithProgress
import certifi
import ssl
from aiohttp import AsyncIterablePayload
from v0.helper.logger import logger
from urllib.parse import quote
from v0.config import Configs

class nextcloud:
    upload_point = Configs.UPLOAD_POINT
    nextcloud_server = "https://dms.uom.lk"
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.islogged_in = False
        self.used_quota = None
        self.available_quota = None
        self.infile_quota = 0

    async def get_available_quota(self):
        if self.islogged_in:
            await self.login()
            return self.available_quota if self.available_quota else 0
        else:
            return 0

    async def login(self):
        username = self.username
        password = self.password
        uploadpoint = nextcloud.upload_point

        headers = {
            'Depth': '1',  # Important: Tells WebDAV to list folder contents (not just the folder itself)
            'Content-Type': 'application/xml'
        }

        # This is the XML body that requests file properties
        xml_body = '''<?xml version="1.0" encoding="UTF-8"?>
        <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
        <d:prop>
            <d:gxetlastmodified/>
            <d:getcontentlength/>
            <d:quota-available-bytes />
            <d:quota-used-bytes />
            <d:getcontenttype/>
            <oc:permissions/>
            <d:resourcetype/>
            <d:getetag/>
        </d:prop>
        </d:propfind>'''
        
        async with aiohttp.ClientSession() as session:
            async with session.request('PROPFIND', uploadpoint, data=xml_body,
                                    headers=headers,
                                    auth=aiohttp.BasicAuth(username, password),ssl=nextcloud.ssl_context) as resp:
                response_text = await resp.text()
                root = ET.fromstring(response_text)
                ns = {
                    'd': 'DAV:',
                    'oc': 'http://owncloud.org/ns',
                    'nc': 'http://nextcloud.org/ns'
                }

                response = root.find('.//d:response', ns)
                if response is not None:
                    self.islogged_in = True
                    available_quota = response.find('.//d:quota-available-bytes', ns)
                    used_quota = response.find('.//d:quota-used-bytes', ns)
                    if available_quota is not None and used_quota is not None:
                        self.available_quota = int(available_quota.text)
                        self.used_quota = int(used_quota.text)
                    else:
                        print("Quota information not found in the response.")
                        return False

                if resp.status in [200, 201, 204,207]:
                    return True
                else:
                    print(f"Login failed with status {resp.status}: {response_text}")
                    return False
    
    
    async def upload(self,file_path,file_name,message):
        
        async with aiohttp.ClientSession() as session:
            try:                
                logger.info(f"Starting upload of file: {file_name}")
                file_stream = FileWithProgress(file_path,message)
                headers = {'Content-Length': str(file_stream.total_size)}

                # Encode the file name for URL compatibility to manage special characters
                encoded_file_name = quote(str(file_name))
                upload_url = f"{nextcloud.upload_point}{encoded_file_name}"
                logger.info(f"Upload URL: {upload_url}")

                # Perform the PUT request to upload the file
                logger.info(f"Initiating upload - File size: {file_stream.total_size} bytes")
                async with session.put(upload_url, data=file_stream ,headers=headers ,auth=aiohttp.BasicAuth(self.username,self.password),ssl=nextcloud.ssl_context) as response:
                    if response.status in [200,201,204]:
                        logger.info(f"Upload successful for {file_name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Upload failed - Status: {response.status}, Error: {error_text}")
                        print(f"Upload failed with status {response.status}: {error_text}")
                        return response.status
            except Exception as e:
                logger.error(f"Upload error for {file_name}: {str(e)}", exc_info=True)
                await message.edit_text(f"**Upload failed!**\nError: {str(e)}")
                return False
            finally:
                logger.info(f"Upload operation completed for {file_name}")

    def share(self, upload_path):
        pass