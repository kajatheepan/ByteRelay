

def check_quota(nextcloud_client,dir):
    try:
        file_info = nextcloud_client.list(dir,get_info=True)
        quota = 0
        for file in file_info:
            if file['isdir'] and file['name'] != None:
                prev_quota = check_quota(nextcloud_client, file['name'])
                if prev_quota is not None:
                    quota += int(prev_quota)
                print(f"Directory: {file['name']}, Size: {file['size']} bytes")
                
            else:
                quota += int(file['size']) if file['size'] not in (None, "") else 0

                print(f"File: {file['name']}, Size: {file['size']} bytes")
        return quota
    except Exception as e:
        print(f"Error: {str(e)}")
        return None