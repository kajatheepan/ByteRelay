

def humanbytes(bytes:int):
    if(bytes is None) | (bytes == 0):
        return "0 B"
    if(bytes/pow(2,30))>=1:
        return f"{bytes/pow(2,30):.2f} GB"
    elif(bytes/pow(2,20))>=1:
        return f"{bytes/pow(2,20):.2f} MB"
    elif(bytes/pow(2,10))>=1:
        return f"{bytes/pow(2,10):.2f} KB"
    else:
        return f"{bytes} B"
    
